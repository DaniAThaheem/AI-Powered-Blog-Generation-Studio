import pytest
from app.db.checkpointer import get_checkpointer, close_checkpointer
from app.workflows.blog_graph import build_blog_graph

@pytest.mark.asyncio
async def test_checkpointer_initialization_and_compilation():
    """Verify checkpointer initializes cleanly and graph compiles with checkpointer."""
    chk = await get_checkpointer()
    assert chk is not None

    graph = build_blog_graph()
    workflow = graph.compile(checkpointer=chk)
    assert workflow is not None

    await close_checkpointer()
