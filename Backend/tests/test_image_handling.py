import pytest
from app.workflows.state import WorkflowState
from app.workflows.nodes.image_gen import gNpImagePlace

def test_placeholder_replacement_and_fallback():
    """Verify placeholders are replaced or gracefully cleaned without losing markdown text."""
    sample_md = (
        "# Graph Neural Networks\n\n"
        "Here is an overview of message passing in graph networks.\n\n"
        "[[IMAGE_1]]\n\n"
        "And next we examine node classification.\n\n"
        "[[IMAGE_2]]\n\n"
        "Conclusion."
    )

    state: WorkflowState = {
        "topic": "Graph Neural Networks",
        "plan": {"blog_title": "Graph Neural Networks"},
        "merged_md": sample_md,
        "md_with_placeholders": sample_md,
        # Image spec without generation to test cleanup/fallback
        "image_specs": [],
        "audience": "Researchers",
        "tone": "Academic",
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
        "sections": [],
        "final": "",
        "output_path": "",
        "warnings": [],
        "error": None
    }

    result = gNpImagePlace(state)
    final_md = result["final"]

    # Verify blog text is preserved intact
    assert "Here is an overview of message passing" in final_md
    assert "And next we examine node classification" in final_md
    assert "Conclusion" in final_md

    # Placeholders should be cleaned up safely
    assert "[[IMAGE_1]]" not in final_md
    assert "[[IMAGE_2]]" not in final_md
