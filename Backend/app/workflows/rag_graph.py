from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, add_messages
from app.services.gemini_service import gemini_service
from app.services.document_service import document_service
from app.core.logging import logger

class RAGChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    selected_document_ids: List[str]
    retrieved_context: List[Dict[str, Any]]

async def ragChatNode(state: RAGChatState) -> Dict[str, Any]:
    """Retrieve relevant context and answer user query."""
    messages = state.get("messages", [])
    if not messages:
        return {"messages": [AIMessage(content="Hello! How can I assist you with your documents?")]}

    last_user_message = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), "")
    selected_doc_ids = state.get("selected_document_ids", [])

    # Retrieve context
    retrieved = []
    if last_user_message:
        retrieved = await document_service.retrieve_context(
            query=last_user_message,
            selected_document_ids=selected_doc_ids if selected_doc_ids else None,
            top_k=4
        )

    context_str = "\n".join(
        f"[{c.get('filename', 'Doc')} (Page {c.get('page_number', 1)})]: {c.get('content', '')}"
        for c in retrieved
    )

    system_prompt = (
        "You are an expert technical assistant with access to reference documents.\n"
        "Answer the user's questions accurately using the provided context excerpts.\n"
        "Cite the document name and page number when referring to specific details.\n"
        "If the answer cannot be found in the context, state that clearly.\n\n"
        f"Context Excerpts:\n{context_str}"
    )

    if gemini_service.is_configured:
        llm = gemini_service.get_llm()
        chat_messages = [SystemMessage(content=system_prompt)] + list(messages)
        response = await llm.ainvoke(chat_messages)
        ai_msg = response
    else:
        # Fallback response for offline/testing
        ai_msg = AIMessage(
            content=f"Based on reference context ({len(retrieved)} citations found):\n{context_str[:250]}..."
        )

    return {
        "messages": [ai_msg],
        "retrieved_context": retrieved
    }

def build_rag_graph():
    graph = StateGraph(RAGChatState)
    graph.add_node("chat", ragChatNode)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    return graph.compile()

rag_chat_workflow = build_rag_graph()
