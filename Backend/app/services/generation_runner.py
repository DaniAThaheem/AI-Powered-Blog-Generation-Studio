import asyncio
import json
import uuid
import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import select, update
from app.db.session import AsyncSessionLocal
from app.db.models import GenerationModel, MediaAssetModel
from app.schemas.events import WorkflowEvent, StageType, StageStatus
from app.workflows.state import WorkflowState
from app.workflows.nodes.router import routerNode
from app.workflows.nodes.research import researchNode
from app.workflows.nodes.orchestrator import orchestratorNode
from app.workflows.nodes.workers import fanOut, workerNode
from app.workflows.nodes.merge import mergeNode
from app.workflows.nodes.image_planner import imageDeciderNode
from app.workflows.nodes.image_gen import gNpImagePlace
from app.services.document_service import document_service
from app.core.logging import logger

class GenerationRunner:
    def __init__(self):
        # Map of generation_id -> list of asyncio.Queue subscribers
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        # Keep recent events for late subscribers / reconnection
        self._event_history: Dict[str, List[WorkflowEvent]] = {}

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

    async def execute_generation(self, generation_id: str):
        """Asynchronously execute workflow stages, update DB, and stream events."""
        logger.info(f"Starting execution for generation {generation_id}...")

        async with AsyncSessionLocal() as db:
            stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
            gen = (await db.execute(stmt)).scalars().first()
            if not gen:
                logger.error(f"Generation {generation_id} not found in database")
                return

            gen.status = "running"
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

        state: WorkflowState = {
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

        try:
            # 1. ANALYZE TOPIC
            await self._update_stage(generation_id, "analyze_topic", "running", "Analyzing topic and determining research strategy...")
            router_res = routerNode(state)
            state["needs_research"] = router_res.get("needs_research", False)
            state["mode"] = router_res.get("mode", "closed_book")
            state["queries"] = router_res.get("queries", [])
            await self._update_stage(
                generation_id, "analyze_topic", "completed",
                f"Topic routed: mode={state['mode']}, queries={len(state['queries'])}"
            )

            # 2. RESEARCH (Conditional)
            if state["needs_research"]:
                await self._update_stage(generation_id, "research", "running", f"Searching Tavily for {len(state['queries'])} queries...")
                research_res = researchNode(state)
                state["evidence"] = research_res.get("evidence", [])
                if "warnings" in research_res:
                    state["warnings"].extend(research_res["warnings"])
                await self._update_stage(
                    generation_id, "research", "completed",
                    f"Retrieved {len(state['evidence'])} verified web sources"
                )
            else:
                await self._update_stage(generation_id, "research", "skipped", "Web research not required for this evergreen topic")

            # 2b. RAG RETRIEVAL (If user uploaded/selected documents)
            if state["selected_document_ids"]:
                logger.info(f"Retrieving RAG context from {len(state['selected_document_ids'])} selected documents...")
                try:
                    async with AsyncSessionLocal() as db:
                        rag_chunks = await document_service.retrieve_context(
                            query=state["topic"],
                            selected_document_ids=state["selected_document_ids"],
                            top_k=5,
                            db=db
                        )
                        state["document_chunks"] = rag_chunks
                        logger.info(f"Retrieved {len(rag_chunks)} RAG context chunks")
                except Exception as rag_err:
                    logger.warning(f"RAG retrieval error: {rag_err}")
                    state["warnings"].append(f"RAG document retrieval warning: {str(rag_err)}")

            # 3. PLAN
            await self._update_stage(generation_id, "plan", "running", "Creating detailed blog outline and section plan...")
            orchestrator_res = orchestratorNode(state)
            state["plan"] = orchestrator_res.get("plan")
            plan_title = state["plan"].get("blog_title") if state["plan"] else state["topic"]
            await self._update_stage(
                generation_id, "plan", "completed",
                f"Plan generated: '{plan_title}' with {len(state['plan'].get('tasks', []))} sections"
            )

            # 4. WRITE SECTIONS (Parallel)
            task_count = len(state["plan"].get("tasks", []))
            await self._update_stage(generation_id, "write_sections", "running", f"Generating {task_count} sections in parallel...")
            
            sends = fanOut(state)
            worker_results = []
            
            # Execute workers concurrently
            loop = asyncio.get_event_loop()
            futures = [
                loop.run_in_executor(None, workerNode, send.node_input)
                for send in sends
            ]
            completed_workers = await asyncio.gather(*futures, return_exceptions=True)

            for w_idx, res in enumerate(completed_workers):
                if isinstance(res, Exception):
                    logger.error(f"Worker {w_idx} encountered exception: {res}")
                    state["warnings"].append(f"Worker {w_idx} error: {str(res)}")
                elif isinstance(res, dict) and "sections" in res:
                    state["sections"].extend(res["sections"])
                    if "warnings" in res:
                        state["warnings"].extend(res["warnings"])

            await self._update_stage(
                generation_id, "write_sections", "completed",
                f"Generated {len(state['sections'])} sections successfully"
            )

            # 5. MERGE
            await self._update_stage(generation_id, "merge", "running", "Merging sections into ordered document...")
            merge_res = mergeNode(state)
            state["merged_md"] = merge_res.get("merged_md", "")
            await self._update_stage(generation_id, "merge", "completed", "Merged sections cleanly")

            # 6. PLAN IMAGES
            await self._update_stage(generation_id, "plan_images", "running", "Evaluating need for architecture diagrams and figures...")
            img_plan_res = imageDeciderNode(state)
            state["md_with_placeholders"] = img_plan_res.get("md_with_placeholders", state["merged_md"])
            state["image_specs"] = img_plan_res.get("image_specs", [])
            await self._update_stage(
                generation_id, "plan_images", "completed",
                f"Planned {len(state['image_specs'])} images/diagrams"
            )

            # 7. GENERATE IMAGES
            if state["image_specs"]:
                await self._update_stage(
                    generation_id, "generate_images", "running",
                    f"Generating and uploading {len(state['image_specs'])} images..."
                )
                loop = asyncio.get_event_loop()
                img_gen_res = await loop.run_in_executor(None, gNpImagePlace, state)
                state["final"] = img_gen_res.get("final", state["merged_md"])
                state["image_specs"] = img_gen_res.get("image_specs", state["image_specs"])
                if "warnings" in img_gen_res:
                    state["warnings"].extend(img_gen_res["warnings"])
                await self._update_stage(
                    generation_id, "generate_images", "completed",
                    f"Images processed: {len(state['image_specs'])} uploaded"
                )
            else:
                state["final"] = state["merged_md"]
                await self._update_stage(generation_id, "generate_images", "skipped", "No images required for this article")

            # 8. SAVE
            await self._update_stage(generation_id, "save", "running", "Persisting blog content and assets to database...")
            
            async with AsyncSessionLocal() as db:
                stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
                gen_rec = (await db.execute(stmt)).scalars().first()
                if gen_rec:
                    gen_rec.blog_title = state["plan"].get("blog_title", state["topic"]) if state["plan"] else state["topic"]
                    gen_rec.plan = state["plan"]
                    gen_rec.sections = state["sections"]
                    gen_rec.final_markdown = state["final"]
                    gen_rec.evidence = state["evidence"]
                    gen_rec.document_chunks_used = state["document_chunks"]
                    gen_rec.image_specs = state["image_specs"]
                    gen_rec.warnings = state["warnings"]
                    gen_rec.status = "completed"
                    gen_rec.current_stage = "completed"
                    gen_rec.stage_statuses["save"] = "completed"

                    # Save media asset records
                    for spec in state["image_specs"]:
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
            
            # Broadcast completed event
            await self.broadcast_event(WorkflowEvent(
                event_type="completed",
                generation_id=generation_id,
                message="Blog generation completed successfully!",
                data={
                    "blog_title": state["plan"].get("blog_title", state["topic"]) if state["plan"] else state["topic"],
                    "image_count": len(state["image_specs"]),
                    "evidence_count": len(state["evidence"])
                }
            ))

            logger.info(f"Generation {generation_id} completed successfully")

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
