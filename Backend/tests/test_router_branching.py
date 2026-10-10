import pytest
from app.workflows.state import WorkflowState, RouterDecision
from app.workflows.nodes.router import routerNode, route_next

def test_router_disabled_by_user():
    """Verify that when enable_research=False, router always selects closed_book."""
    state: WorkflowState = {
        "topic": "Python Async Fundamentals",
        "enable_research": False,
        "audience": "Developers",
        "tone": "Technical",
        "blog_kind": "explainer",
        "target_word_count": 1000,
        "enable_hitl": False,
        "selected_document_ids": [],
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

    result = routerNode(state)
    assert result["needs_research"] is False
    assert result["mode"] == "closed_book"
    assert len(result["queries"]) == 0

    state["needs_research"] = result["needs_research"]
    assert route_next(state) == "orchestrator"

def test_route_next_logic():
    """Verify conditional edge routing logic."""
    state_research = {"needs_research": True}
    assert route_next(state_research) == "research"

    state_no_research = {"needs_research": False}
    assert route_next(state_no_research) == "orchestrator"
