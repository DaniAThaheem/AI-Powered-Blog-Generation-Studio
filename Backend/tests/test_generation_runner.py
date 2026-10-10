import pytest
from unittest.mock import MagicMock
from sqlalchemy import select
from app.workflows.state import WorkflowState, Plan, Task
from app.workflows.nodes.workers import fanOut, workerNode
from app.workflows.nodes.orchestrator import orchestratorNode
from app.services.generation_runner import generation_runner
from app.services.gemini_service import gemini_service
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
    """Verify an end-to-end execution completes with non-empty final markdown and status completed."""
    gen_id = "test-e2e-phase1"
    
    # Insert generation into test db
    async with AsyncSessionLocal() as db:
        gen = GenerationModel(
            id=gen_id,
            thread_id=f"thread_{gen_id}",
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

    # Execute generation workflow
    await generation_runner.execute_generation(gen_id)

    # Verify results in DB
    async with AsyncSessionLocal() as db:
        stmt = select(GenerationModel).where(GenerationModel.id == gen_id)
        result = (await db.execute(stmt)).scalars().first()

        assert result is not None
        assert result.status == "completed"
        assert result.current_stage == "completed"
        assert result.stage_statuses.get("save") == "completed"
        assert result.final_markdown is not None
        assert len(result.final_markdown.strip()) > 0
        assert len(result.sections) > 0
        assert result.blog_title is not None

def test_orchestrator_hitl_safeguard_outside_graph():
    """Verify orchestratorNode does not raise when enable_hitl=True outside a compiled graph."""
    state: WorkflowState = {
        "topic": "Edge Computing Architectures",
        "audience": "Developers",
        "tone": "Technical",
        "blog_kind": "explainer",
        "target_word_count": 800,
        "enable_research": False,
        "enable_hitl": True,
        "selected_document_ids": [],
        "document_chunks": [],
        "mode": "closed_book",
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

    # Must complete without crashing
    res = orchestratorNode(state)
    assert "plan" in res
    assert res["plan"] is not None
    assert len(res["plan"]["tasks"]) > 0
