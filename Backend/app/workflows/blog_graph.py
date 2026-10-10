from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from app.workflows.state import WorkflowState
from app.workflows.nodes.router import routerNode, route_next
from app.workflows.nodes.research import researchNode
from app.workflows.nodes.orchestrator import orchestratorNode
from app.workflows.nodes.workers import fanOut, workerNode
from app.workflows.nodes.merge import mergeNode
from app.workflows.nodes.image_planner import imageDeciderNode
from app.workflows.nodes.image_gen import gNpImagePlace
from app.db.checkpointer import get_checkpointer
from app.core.logging import logger

def build_blog_graph():
    """Build and compile the blog generation StateGraph."""
    graph = StateGraph(WorkflowState)

    # Add core workflow nodes
    graph.add_node("router", routerNode)
    graph.add_node("research", researchNode)
    graph.add_node("orchestrator", orchestratorNode)
    graph.add_node("worker", workerNode)
    graph.add_node("merge", mergeNode)
    graph.add_node("decideimage", imageDeciderNode)
    graph.add_node("generateimage", gNpImagePlace)

    # Routing logic
    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        route_next,
        {
            "research": "research",
            "orchestrator": "orchestrator"
        }
    )
    graph.add_edge("research", "orchestrator")
    
    # Parallel fan-out to workers
    graph.add_conditional_edges("orchestrator", fanOut, ["worker"])
    
    # Fan-in aggregation to merge
    graph.add_edge("worker", "merge")
    
    # Image planning and generation sequence
    graph.add_edge("merge", "decideimage")
    graph.add_edge("decideimage", "generateimage")
    graph.add_edge("generateimage", END)

    return graph

_compiled_workflow = None

async def get_compiled_workflow(checkpointer=None):
    """Retrieve compiled workflow with persistent checkpointer."""
    global _compiled_workflow
    if _compiled_workflow is not None:
        return _compiled_workflow

    graph = build_blog_graph()
    chk = checkpointer if checkpointer is not None else await get_checkpointer()
    _compiled_workflow = graph.compile(checkpointer=chk)
    logger.info("Compiled LangGraph blog generation workflow with checkpointer")
    return _compiled_workflow
