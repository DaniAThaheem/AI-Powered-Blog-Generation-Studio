import asyncio
import json
import uuid
import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import select, update
from langgraph.types import Command
from app.db.session import AsyncSessionLocal
from app.db.models import GenerationModel, MediaAssetModel
from app.schemas.events import WorkflowEvent, StageType, StageStatus
from app.workflows.state import WorkflowState
from app.workflows.blog_graph import get_compiled_workflow
from app.services.document_service import document_service
from app.core.logging import logger

class GenerationRunner:
    def __init__(self):
        # Map of generation_id -> list of asyncio.Queue subscribers
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        # Keep recent events for late subscribers / reconnection
        self._event_history: Dict[str, List[WorkflowEvent]] = {}
        self._cleanup_tasks: Dict[str, asyncio.Task] = {}

    def subscribe(self, generation_id: str) -> asyncio.Queue:
        q = asyncio.Queue()
        if generation_id not in self._subscribers:
            self._subscribers[generation_id] = []
        self._subscribers[generation_id].append(q)

        # Backfill history if available
        if generation_id in self._event_history:
            for ev in self._event_history[generation_id]:
                q.put_nowait(ev)

        return q

    def unsubscribe(self, generation_id: str, q: asyncio.Queue):
        if generation_id in self._subscribers:
            try:
                self._subscribers[generation_id].remove(q)
                if not self._subscribers[generation_id]:
                    del self._subscribers[generation_id]
            except ValueError:
                pass

    def schedule_cleanup(self, generation_id: str, delay: float = 60.0):
        """Clean up _event_history and subscribers shortly after reaching a terminal state."""
        try:
            # Cancel any existing cleanup task for this generation
            if generation_id in self._cleanup_tasks and not self._cleanup_tasks[generation_id].done():
                self._cleanup_tasks[generation_id].cancel()
            task = asyncio.create_task(self._delayed_cleanup(generation_id, delay))
            self._cleanup_tasks[generation_id] = task
        except Exception as e:
            logger.debug(f"Failed to schedule cleanup for generation {generation_id}: {e}")

    async def _delayed_cleanup(self, generation_id: str, delay: float):
        try:
            await asyncio.sleep(delay)
            self._event_history.pop(generation_id, None)
            self._subscribers.pop(generation_id, None)
            self._cleanup_tasks.pop(generation_id, None)
            logger.debug(f"Cleaned up event history and subscribers for generation {generation_id}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"Delayed cleanup error for {generation_id}: {e}")

    async def cleanup_orphaned_generations(self):
        """Mark any generation left in 'running' as 'failed' on application startup."""
        try:
            async with AsyncSessionLocal() as db:
                stmt = (
                    update(GenerationModel)
                    .where(GenerationModel.status == "running")
                    .values(
                        status="failed",
                        error_message="Generation failed: background task was interrupted due to server restart.",
                        updated_at=datetime.datetime.utcnow()
                    )
                )
                result = await db.execute(stmt)
                await db.commit()
                if result.rowcount > 0:
                    logger.warning(f"Marked {result.rowcount} orphaned running generation(s) as failed on startup.")
        except Exception as e:
            logger.error(f"Error cleaning up orphaned generations on startup: {e}")

    async def broadcast_event(self, event: WorkflowEvent):
        gen_id = event.generation_id
        if gen_id not in self._event_history:
            self._event_history[gen_id] = []
        self._event_history[gen_id].append(event)

        # Cap history to 50 items
        if len(self._event_history[gen_id]) > 50:
            self._event_history[gen_id] = self._event_history[gen_id][-50:]

        if gen_id in self._subscribers:
            for q in list(self._subscribers[gen_id]):
                try:
                    q.put_nowait(event)
                except Exception as e:
                    logger.warning(f"Failed to queue event for subscriber: {e}")

    async def execute_generation(self, generation_id: str, resume_decision: Any = None):
        """Execute or resume workflow using compiled LangGraph StateGraph, checkpointer, and astream."""
        logger.info(f"Executing generation {generation_id} (resuming={resume_decision is not None})...")

        async with AsyncSessionLocal() as db:
            stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
            gen = (await db.execute(stmt)).scalars().first()
            if not gen:
                logger.error(f"Generation {generation_id} not found in database")
                return

            gen.status = "running"
            if resume_decision is None:
                # Fresh run initialization
                gen.stage_statuses = {
                    "analyze_topic": "pending",
                    "research": "pending",
                    "plan": "pending",
                    "write_sections": "pending",
                    "merge": "pending",
                    "plan_images": "pending",
                    "generate_images": "pending",
                    "save": "pending"
                }
            await db.commit()
            thread_id = gen.thread_id

        # Compile workflow with checkpointer
        workflow = await get_compiled_workflow()
        config = {"configurable": {"thread_id": thread_id}}

        try:
            if resume_decision is not None:
                # Resuming from human approval interrupt
                input_data = Command(resume=resume_decision)
                await self._update_stage(
                    generation_id, "plan", "running", "Resuming workflow with approved plan..."
                )
            else:
                # Initial execution state
                initial_state: WorkflowState = {
                    "topic": gen.topic,
                    "audience": gen.audience,
                    "tone": gen.tone,
                    "blog_kind": gen.blog_kind,
                    "target_word_count": gen.target_word_count,
                    "enable_research": gen.enable_research,
                    "enable_hitl": gen.enable_hitl,
                    "selected_document_ids": gen.selected_document_ids or [],
                    "document_chunks": [],
                    "mode": "",
                    "needs_research": False,
                    "queries": [],
                    "evidence": [],
                    "plan": None,
                    "sections": [],
                    "merged_md": "",
                    "md_with_placeholders": "",
                    "image_specs": [],
                    "final": "",
                    "output_path": "",
                    "warnings": [],
                    "error": None
                }

                # Pre-fetch RAG chunks if reference documents selected
                if initial_state["selected_document_ids"]:
                    logger.info(f"Retrieving RAG context from {len(initial_state['selected_document_ids'])} selected documents...")
                    try:
                        async with AsyncSessionLocal() as db:
                            rag_chunks = await document_service.retrieve_context(
                                query=initial_state["topic"],
                                selected_document_ids=initial_state["selected_document_ids"],
                                top_k=5,
                                db=db
                            )
                            initial_state["document_chunks"] = rag_chunks
                            logger.info(f"Retrieved {len(rag_chunks)} RAG context chunks")
                    except Exception as rag_err:
                        logger.warning(f"RAG retrieval error: {rag_err}")
                        initial_state["warnings"].append(f"RAG document retrieval warning: {str(rag_err)}")

                input_data = initial_state
                await self._update_stage(
                    generation_id, "analyze_topic", "running", "Analyzing topic and determining research strategy..."
                )

            # Stream updates from the compiled graph
            interrupted = False
            async for chunk in workflow.astream(input_data, config=config, stream_mode="updates"):
                # Check for HITL interrupt
                if "__interrupt__" in chunk:
                    interrupted = True
                    interrupt_info = chunk["__interrupt__"][0]
                    interrupt_val = interrupt_info.value if hasattr(interrupt_info, "value") else interrupt_info
                    plan_dict = interrupt_val.get("plan") if isinstance(interrupt_val, dict) else None

                    async with AsyncSessionLocal() as db:
                        stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
                        gen_rec = (await db.execute(stmt)).scalars().first()
                        if gen_rec:
                            gen_rec.status = "interrupted"
                            gen_rec.current_stage = "plan"
                            if plan_dict:
                                gen_rec.plan = plan_dict
                                gen_rec.blog_title = plan_dict.get("blog_title", gen_rec.topic)
                            statuses = dict(gen_rec.stage_statuses or {})
                            statuses["plan"] = "completed"
                            gen_rec.stage_statuses = statuses
                            await db.commit()

                    await self.broadcast_event(WorkflowEvent(
                        event_type="interrupted",
                        generation_id=generation_id,
                        stage="plan",
                        stage_status="completed",
                        message=interrupt_val.get("message", "Blog plan awaiting approval") if isinstance(interrupt_val, dict) else "Plan awaiting approval",
                        data={"plan": plan_dict}
                    ))
                    logger.info(f"Workflow interrupted for HITL approval in generation {generation_id}")
                    break

                # Map graph nodes to the 8 UI stages
                if "router" in chunk:
                    router_res = chunk["router"]
                    needs_research = router_res.get("needs_research", False)
                    mode = router_res.get("mode", "closed_book")
                    queries = router_res.get("queries", [])

                    await self._update_stage(
                        generation_id, "analyze_topic", "completed",
                        f"Topic routed: mode={mode}, queries={len(queries)}"
                    )
                    if needs_research:
                        await self._update_stage(
                            generation_id, "research", "running",
                            f"Searching Tavily for {len(queries)} queries..."
                        )
                    else:
                        await self._update_stage(
                            generation_id, "research", "skipped",
                            "Web research not required for this evergreen topic"
                        )
                        await self._update_stage(
                            generation_id, "plan", "running",
                            "Creating detailed blog outline and section plan..."
                        )

                if "research" in chunk:
                    research_res = chunk["research"]
                    evidence = research_res.get("evidence", [])
                    await self._update_stage(
                        generation_id, "research", "completed",
                        f"Retrieved {len(evidence)} verified web sources"
                    )
                    await self._update_stage(
                        generation_id, "plan", "running",
                        "Creating detailed blog outline and section plan..."
                    )

                if "orchestrator" in chunk:
                    orchestrator_res = chunk["orchestrator"]
                    plan = orchestrator_res.get("plan")
                    plan_title = plan.get("blog_title") if plan else "Blog Plan"
                    task_count = len(plan.get("tasks", [])) if plan else 0

                    async with AsyncSessionLocal() as db:
                        stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
                        gen_rec = (await db.execute(stmt)).scalars().first()
                        if gen_rec and plan:
                            gen_rec.plan = plan
                            gen_rec.blog_title = plan_title
                            await db.commit()

                    await self._update_stage(
                        generation_id, "plan", "completed",
                        f"Plan generated: '{plan_title}' with {task_count} sections"
                    )
                    await self._update_stage(
                        generation_id, "write_sections", "running",
                        f"Generating {task_count} sections in parallel..."
                    )

                if "merge" in chunk:
                    await self._update_stage(
                        generation_id, "write_sections", "completed",
                        "Generated sections successfully"
                    )
                    await self._update_stage(
                        generation_id, "merge", "completed",
                        "Merged sections cleanly"
                    )
                    await self._update_stage(
                        generation_id, "plan_images", "running",
                        "Evaluating need for architecture diagrams and figures..."
                    )

                if "decideimage" in chunk:
                    decide_res = chunk["decideimage"]
                    image_specs = decide_res.get("image_specs", [])
                    await self._update_stage(
                        generation_id, "plan_images", "completed",
                        f"Planned {len(image_specs)} images/diagrams"
                    )
                    if image_specs:
                        await self._update_stage(
                            generation_id, "generate_images", "running",
                            f"Generating and uploading {len(image_specs)} images..."
                        )
                    else:
                        await self._update_stage(
                            generation_id, "generate_images", "skipped",
                            "No images required for this article"
                        )

                if "generateimage" in chunk:
                    gen_img_res = chunk["generateimage"]
                    specs = gen_img_res.get("image_specs", [])
                    if specs:
                        await self._update_stage(
                            generation_id, "generate_images", "completed",
                            f"Images processed: {len(specs)} uploaded"
                        )

            if not interrupted:
                # 8. SAVE STAGE
                await self._update_stage(
                    generation_id, "save", "running", "Persisting blog content and assets to database..."
                )

                # Fetch final accumulated state from the checkpointer
                state_snapshot = await workflow.aget_state(config)
                final_state = state_snapshot.values or {}

                async with AsyncSessionLocal() as db:
                    stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
                    gen_rec = (await db.execute(stmt)).scalars().first()
                    if gen_rec:
                        plan = final_state.get("plan")
                        gen_rec.blog_title = plan.get("blog_title", gen_rec.topic) if plan else gen_rec.topic
                        gen_rec.plan = plan
                        gen_rec.sections = final_state.get("sections", [])
                        gen_rec.final_markdown = final_state.get("final") or final_state.get("merged_md", "")
                        gen_rec.evidence = final_state.get("evidence", [])
                        gen_rec.document_chunks_used = final_state.get("document_chunks", [])
                        gen_rec.image_specs = final_state.get("image_specs", [])
                        gen_rec.warnings = final_state.get("warnings", [])
                        gen_rec.status = "completed"
                        gen_rec.current_stage = "completed"

                        statuses = dict(gen_rec.stage_statuses or {})
                        statuses["save"] = "completed"
                        gen_rec.stage_statuses = statuses

                        # Save media asset records
                        for spec in final_state.get("image_specs", []):
                            if spec.get("url"):
                                asset = MediaAssetModel(
                                    generation_id=generation_id,
                                    placeholder=spec.get("placeholder"),
                                    filename=spec.get("filename", "image.png"),
                                    alt_text=spec.get("alt"),
                                    caption=spec.get("caption"),
                                    prompt=spec.get("prompt", ""),
                                    cloudinary_url=spec.get("url"),
                                    cloudinary_public_id=spec.get("cloudinary_public_id")
                                )
                                db.add(asset)

                        await db.commit()

                await self._update_stage(generation_id, "save", "completed", "Blog generated and saved successfully")

                async with AsyncSessionLocal() as db:
                    stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
                    gen_rec = (await db.execute(stmt)).scalars().first()
                    if gen_rec:
                        gen_rec.current_stage = "completed"
                        await db.commit()

                # Broadcast completion event
                blog_title = final_state.get("plan", {}).get("blog_title", gen.topic) if final_state.get("plan") else gen.topic
                await self.broadcast_event(WorkflowEvent(
                    event_type="completed",
                    generation_id=generation_id,
                    message="Blog generation completed successfully!",
                    data={
                        "blog_title": blog_title,
                        "image_count": len(final_state.get("image_specs", [])),
                        "evidence_count": len(final_state.get("evidence", []))
                    }
                ))

                logger.info(f"Generation {generation_id} completed successfully via LangGraph workflow")
                self.schedule_cleanup(generation_id)

        except Exception as e:
            logger.error(f"Generation {generation_id} failed: {e}", exc_info=True)
            async with AsyncSessionLocal() as db:
                stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
                gen_rec = (await db.execute(stmt)).scalars().first()
                if gen_rec:
                    gen_rec.status = "failed"
                    gen_rec.error_message = str(e)
                    await db.commit()

            await self.broadcast_event(WorkflowEvent(
                event_type="failed",
                generation_id=generation_id,
                message=f"Generation failed: {str(e)}"
            ))
            self.schedule_cleanup(generation_id)

    async def _update_stage(
        self,
        generation_id: str,
        stage: StageType,
        status: StageStatus,
        message: str
    ):
        async with AsyncSessionLocal() as db:
            stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
            gen = (await db.execute(stmt)).scalars().first()
            if gen:
                gen.current_stage = stage
                st_map = dict(gen.stage_statuses or {})
                st_map[stage] = status
                gen.stage_statuses = st_map
                await db.commit()

        await self.broadcast_event(WorkflowEvent(
            event_type="stage",
            generation_id=generation_id,
            stage=stage,
            stage_status=status,
            message=message
        ))

generation_runner = GenerationRunner()
