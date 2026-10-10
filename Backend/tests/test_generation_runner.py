import pytest
import asyncio
from unittest.mock import MagicMock
from sqlalchemy import select
from app.workflows.state import WorkflowState, Plan, Task
from app.workflows.nodes.workers import fanOut, workerNode
from app.services.generation_runner import generation_runner
from app.services.gemini_service import gemini_service
from app.workflows.blog_graph import get_compiled_workflow
from app.db.models import GenerationModel
from app.db.session import AsyncSessionLocal

def test_write_sections_stage_with_mocked_gemini(monkeypatch):
    """Verify write sections stage runs with mocked gemini_service and Send.arg."""
    state: WorkflowState = {
        "topic": "Event-Driven Architecture",
        "audience": "Developers",
        "tone": "Technical",
        "blog_kind": "explainer",
        "target_word_count": 1000,
        "enable_research": False,
        "enable_hitl": False,
        "selected_document_ids": [],
        "document_chunks": [],
        "mode": "closed_book",
        "needs_research": False,
        "queries": [],
        "evidence": [],
        "plan": {
            "blog_title": "Modern Event-Driven Architecture",
            "audience": "Developers",
            "tone": "Technical",
            "blog_kind": "explainer",
            "constraint": ["Clear examples"],
            "tasks": [
                {
                    "id": 1,
                    "title": "Introduction to EDA",
                    "goal": "Explain event brokers and decouple systems",
                    "bullets": ["Brokers", "Event streams"],
                    "brief": "Foundations of EDA",
                    "target_word": 300,
                    "requires_code": False,
                    "requires_citation": False
                },
                {
                    "id": 2,
                    "title": "Event Sourcing & CQRS",
                    "goal": "Explain state hydration and projections",
                    "bullets": ["Event stores", "Projections"],
                    "brief": "Advanced EDA patterns",
                    "target_word": 400,
                    "requires_code": True,
                    "requires_citation": False
                }
            ]
        },
        "sections": [],
        "merged_md": "",
        "md_with_placeholders": "",
        "image_specs": [],
        "final": "",
        "output_path": "",
        "warnings": [],
        "error": None
    }

    # Fan out generates Send objects
    sends = fanOut(state)
    assert len(sends) == 2
    for s in sends:
        # LangGraph Send has .arg, not .node_input
        assert hasattr(s, "arg")
        assert not hasattr(s, "node_input")

    # Mock Gemini service
    monkeypatch.setattr(gemini_service, "api_key", "test-key")
    mock_invoke = MagicMock(side_effect=lambda system_prompt, user_prompt: "## Generated Section\n\nDetailed content.")
    monkeypatch.setattr(gemini_service, "invoke_text", mock_invoke)

    # Execute worker nodes using send.arg
    worker_results = []
    for s in sends:
        res = workerNode(s.arg)
        worker_results.append(res)

    assert len(worker_results) == 2
    for res in worker_results:
        assert "sections" in res
        assert len(res["sections"]) == 1
        sec = res["sections"][0]
        assert sec["id"] in (1, 2)
        assert "## Generated Section" in sec["content"]

@pytest.mark.asyncio
async def test_end_to_end_generation_completes_mocked():
    """Verify an end-to-end execution completes through compiled graph with non-empty final markdown and status completed."""
    gen_id = "test-e2e-phase2"
    thread_id = f"thread_{gen_id}"
    
    # Insert generation into test db
    async with AsyncSessionLocal() as db:
        gen = GenerationModel(
            id=gen_id,
            thread_id=thread_id,
            topic="Distributed Tracing in Cloud Native Microservices",
            audience="Software Engineers",
            tone="Technical",
            blog_kind="explainer",
            target_word_count=1000,
            enable_research=False,
            enable_hitl=False,
            status="queued",
            current_stage="queued",
            stage_statuses={}
        )
        db.add(gen)
        await db.commit()

    # Execute generation workflow through compiled LangGraph
    await generation_runner.execute_generation(gen_id)

    # Verify results in DB
    async with AsyncSessionLocal() as db:
        stmt = select(GenerationModel).where(GenerationModel.id == gen_id)
        result = (await db.execute(stmt)).scalars().first()

        assert result is not None
        assert result.status == "completed"
        assert result.current_stage == "completed"
        assert result.stage_statuses.get("save") == "completed"
        assert result.stage_statuses.get("research") == "skipped"
        assert result.final_markdown is not None
        assert len(result.final_markdown.strip()) > 0
        assert len(result.sections) > 0
        assert result.blog_title is not None

    # Verify checkpoint exists in checkpointer for the thread
    workflow = await get_compiled_workflow()
    snapshot = await workflow.aget_state({"configurable": {"thread_id": thread_id}})
    assert snapshot is not None
    assert snapshot.values is not None
    assert "sections" in snapshot.values

@pytest.mark.asyncio
async def test_hitl_interrupt_and_resume_with_edited_plan():
    """Verify workflow pauses on HITL interrupt, checkpoints state, and resumes with edited plan."""
    gen_id = "test-hitl-flow"
    thread_id = f"thread_{gen_id}"

    async with AsyncSessionLocal() as db:
        gen = GenerationModel(
            id=gen_id,
            thread_id=thread_id,
            topic="Microservices Service Mesh Architectures",
            audience="Solutions Architects",
            tone="Technical",
            blog_kind="system_design",
            target_word_count=1200,
            enable_research=False,
            enable_hitl=True,
            status="queued",
            current_stage="queued",
            stage_statuses={}
        )
        db.add(gen)
        await db.commit()

    # 1. Execute initial run -> must halt at orchestrator interrupt
    await generation_runner.execute_generation(gen_id)

    async with AsyncSessionLocal() as db:
        stmt = select(GenerationModel).where(GenerationModel.id == gen_id)
        result = (await db.execute(stmt)).scalars().first()
        assert result.status == "interrupted"
        assert result.current_stage == "plan"
        assert result.plan is not None

    # Checkpoint must have captured the interrupt
    workflow = await get_compiled_workflow()
    snapshot = await workflow.aget_state({"configurable": {"thread_id": thread_id}})
    assert len(snapshot.tasks) > 0
    assert snapshot.tasks[0].interrupts is not None

    # 2. Resume with an edited plan
    edited_plan = {
        "blog_title": "Custom Service Mesh Deep Dive",
        "audience": "Senior Architects",
        "tone": "Technical",
        "blog_kind": "system_design",
        "constraint": ["Focus on Envoy and Istio"],
        "tasks": [
            {
                "id": 1,
                "title": "Envoy Data Plane Mechanics",
                "goal": "Deep dive into Envoy sidecar proxying",
                "bullets": ["Sidecar proxies", "mTLS handshake"],
                "brief": "Data plane deep dive",
                "target_word": 350,
                "requires_code": True
            }
        ]
    }

    await generation_runner.execute_generation(gen_id, resume_decision={"plan": edited_plan})

    # Verify execution resumed and completed with the edited plan
    async with AsyncSessionLocal() as db:
        stmt = select(GenerationModel).where(GenerationModel.id == gen_id)
        completed_gen = (await db.execute(stmt)).scalars().first()
        assert completed_gen.status == "completed"
        assert completed_gen.blog_title == "Custom Service Mesh Deep Dive"
        assert completed_gen.plan["blog_title"] == "Custom Service Mesh Deep Dive"
        assert len(completed_gen.sections) == 1
        assert completed_gen.sections[0]["title"] == "Envoy Data Plane Mechanics"
        assert "Envoy Data Plane Mechanics" in completed_gen.final_markdown

@pytest.mark.asyncio
async def test_cleanup_orphaned_generations_on_startup():
    """Verify that any generations stuck in 'running' are marked 'failed' on startup."""
    orphan_id = "orphan-gen-test"
    async with AsyncSessionLocal() as db:
        gen = GenerationModel(
            id=orphan_id,
            thread_id=f"thread_{orphan_id}",
            topic="Orphaned generation",
            status="running",
            current_stage="write_sections"
        )
        db.add(gen)
        await db.commit()

    await generation_runner.cleanup_orphaned_generations()

    async with AsyncSessionLocal() as db:
        stmt = select(GenerationModel).where(GenerationModel.id == orphan_id)
        res = (await db.execute(stmt)).scalars().first()
        assert res.status == "failed"
        assert "restart" in res.error_message.lower()

@pytest.mark.asyncio
async def test_event_history_cleanup():
    """Verify _delayed_cleanup purges event history and subscriber queues."""
    gen_id = "test-cleanup-id"
    q = generation_runner.subscribe(gen_id)
    assert gen_id in generation_runner._subscribers
    
    # Run delayed cleanup with 0 delay
    await generation_runner._delayed_cleanup(gen_id, delay=0.01)
    
    assert gen_id not in generation_runner._subscribers
    assert gen_id not in generation_runner._event_history
