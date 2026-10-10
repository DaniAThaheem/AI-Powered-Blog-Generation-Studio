from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from app.services.gemini_service import gemini_service
from app.core.logging import logger

class HITLState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    action_description: str
    is_approved: Optional[bool]
    result: Optional[str]

def approvalCheckNode(state: HITLState):
    """Interrupt execution and request user approval."""
    action = state.get("action_description", "Perform automated action")
    
    # Request approval from human
    decision = interrupt({
        "type": "approval_request",
        "action": action,
        "message": f"Do you approve the execution of: '{action}'?"
    })

    # Resumed state
    is_approved = bool(decision) if not isinstance(decision, dict) else decision.get("approved", True)
    return {
        "is_approved": is_approved,
        "result": "Action executed successfully" if is_approved else "Action was rejected by user"
    }

def build_hitl_graph():
    graph = StateGraph(HITLState)
    graph.add_node("approval", approvalCheckNode)
    graph.add_edge(START, "approval")
    graph.add_edge("approval", END)
    return graph.compile(checkpointer=MemorySaver())

hitl_workflow = build_hitl_graph()
