import pytest
from app.workflows.state import WorkflowState
from app.workflows.nodes.merge import mergeNode

def test_parallel_worker_aggregation_and_ordering():
    """Verify that sections arriving out of order are deterministically sorted by section ID."""
    state: WorkflowState = {
        "topic": "Distributed Consensus",
        "plan": {
            "blog_title": "Understanding Raft & Paxos",
            "tasks": []
        },
        # Sections arrived out of order from parallel workers
        "sections": [
            {"id": 3, "title": "Log Replication", "content": "## Log Replication\n\nReplicating log entries reliably."},
            {"id": 1, "title": "Introduction to Consensus", "content": "## Introduction to Consensus\n\nFundamental challenges."},
            {"id": 2, "title": "Leader Election", "content": "## Leader Election\n\nElecting the leader node."}
        ],
        "audience": "Engineers",
        "tone": "Engaging",
        "blog_kind": "explainer",
        "target_word_count": 1500,
        "enable_research": False,
        "enable_hitl": False,
        "selected_document_ids": [],
        "document_chunks": [],
        "mode": "closed_book",
        "needs_research": False,
        "queries": [],
        "evidence": [],
        "merged_md": "",
        "md_with_placeholders": "",
        "image_specs": [],
        "final": "",
        "output_path": "",
        "warnings": [],
        "error": None
    }

    result = mergeNode(state)
    merged_md = result["merged_md"]

    assert "# Understanding Raft & Paxos" in merged_md
    pos1 = merged_md.find("## Introduction to Consensus")
    pos2 = merged_md.find("## Leader Election")
    pos3 = merged_md.find("## Log Replication")

    # Section 1 must precede Section 2 which precedes Section 3
    assert pos1 != -1 and pos2 != -1 and pos3 != -1
    assert pos1 < pos2 < pos3

def test_empty_and_failed_worker_handling():
    """Verify that empty or failed worker results are handled gracefully without exceptions."""
    state: WorkflowState = {
        "topic": "Fault Tolerance",
        "plan": {
            "blog_title": "Building Resilient Systems"
        },
        "sections": [
            {"id": 1, "title": "Overview", "content": ""}, # empty section
            {"id": 2, "title": "Failover", "content": "## Failover\n\nAutomated cluster recovery."}
        ],
        "audience": "Engineers",
        "tone": "Engaging",
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
        "merged_md": "",
        "md_with_placeholders": "",
        "image_specs": [],
        "final": "",
        "output_path": "",
        "warnings": [],
        "error": None
    }

    result = mergeNode(state)
    assert "# Building Resilient Systems" in result["merged_md"]
    assert "## Failover" in result["merged_md"]
