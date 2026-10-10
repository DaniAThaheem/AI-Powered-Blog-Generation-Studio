from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.document_service import document_service
from app.services.gemini_service import gemini_service
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_documents(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Chat with uploaded reference documents using RAG."""
    # 1. Retrieve context
    retrieved = await document_service.retrieve_context(
        query=req.message,
        selected_document_ids=req.selected_document_ids if req.selected_document_ids else None,
        top_k=4,
        db=db
    )

    context_str = "\n".join(
        f"[{c.get('filename', 'Doc')} (Page {c.get('page_number', 1)})]: {c.get('content', '')}"
        for c in retrieved
    )

    system_prompt = (
        "You are an AI research assistant helping users query and synthesize their reference documents.\n"
        "Use the provided document excerpts to ground your answers. Always cite the document name.\n"
        "If the answer cannot be determined from the excerpts, state that clearly.\n\n"
        f"Document Excerpts:\n{context_str}"
    )

    # 2. Generate response
    if gemini_service.is_configured:
        llm = gemini_service.get_llm()
        messages = [SystemMessage(content=system_prompt)]
        for h in req.history:
            if h.role == "user":
                messages.append(HumanMessage(content=h.content))
            else:
                messages.append(AIMessage(content=h.content))
        messages.append(HumanMessage(content=req.message))

        ai_response = await llm.ainvoke(messages)
        reply_text = ai_response.content if hasattr(ai_response, "content") else str(ai_response)
    else:
        if retrieved:
            reply_text = (
                f"I found {len(retrieved)} relevant references in your documents:\n\n"
                + "\n\n".join(f"- **{r.get('filename')}** (Page {r.get('page_number')}):\n{r.get('content')[:200]}..." for r in retrieved)
            )
        else:
            reply_text = "I couldn't find any relevant sections in the selected documents for your query."

    return ChatResponse(
        reply=reply_text,
        sources=retrieved
    )
