import asyncio
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Response
from fastapi.responses import PlainTextResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.db.models import GenerationModel
from app.schemas.generation import (
    GenerationCreateRequest,
    GenerationResponse,
    GenerationSummary,
    GenerationUpdateRequest,
    ResumeRequest
)
from app.services.generation_runner import generation_runner
from app.core.logging import logger

router = APIRouter()

@router.post("/generations", response_model=GenerationResponse, status_code=201)
async def create_generation(
    req: GenerationCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Start a new blog generation workflow."""
    if req.enable_hitl:
        raise HTTPException(
            status_code=400,
            detail="Human-in-the-loop (HITL) mode is temporarily unavailable until Phase 2 compiled graph execution is enabled."
        )

    generation_id = str(uuid.uuid4())
    thread_id = f"thread_{generation_id}"

    gen_record = GenerationModel(
        id=generation_id,
        thread_id=thread_id,
        topic=req.topic,
        audience=req.audience or "Developers & Technical Practitioners",
        tone=req.tone or "Technical and Engaging",
        blog_kind=req.blog_kind or "explainer",
        target_word_count=req.target_word_count or 1500,
        enable_research=req.enable_research if req.enable_research is not None else True,
        enable_hitl=req.enable_hitl if req.enable_hitl is not None else False,
        selected_document_ids=req.selected_document_ids or [],
        status="queued",
        current_stage="queued",
        stage_statuses={
            "analyze_topic": "pending",
            "research": "pending",
            "plan": "pending",
            "write_sections": "pending",
            "merge": "pending",
            "plan_images": "pending",
            "generate_images": "pending",
            "save": "pending"
        }
    )

    db.add(gen_record)
    await db.commit()
    await db.refresh(gen_record)

    # Launch generation in background
    background_tasks.add_task(generation_runner.execute_generation, generation_id)
    logger.info(f"Enqueued generation job {generation_id} for topic: {req.topic}")

    return gen_record

@router.get("/generations", response_model=List[GenerationSummary])
async def list_generations(
    status: Optional[str] = Query(None, description="Filter by status: queued, running, completed, failed"),
    search: Optional[str] = Query(None, description="Search by topic or blog title"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List blog generations with optional filters."""
    query = select(GenerationModel).order_by(desc(GenerationModel.created_at))

    if status:
        query = query.where(GenerationModel.status == status)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (GenerationModel.topic.ilike(search_pattern)) |
            (GenerationModel.blog_title.ilike(search_pattern))
        )

    query = query.limit(limit).offset(offset)
    results = (await db.execute(query)).scalars().all()

    summaries = []
    for g in results:
        summaries.append(GenerationSummary(
            id=g.id,
            thread_id=g.thread_id,
            topic=g.topic,
            blog_title=g.blog_title,
            blog_kind=g.blog_kind,
            status=g.status,
            current_stage=g.current_stage,
            created_at=g.created_at,
            updated_at=g.updated_at,
            image_count=len(g.image_specs or []),
            source_count=len(g.evidence or []) + len(g.document_chunks_used or [])
        ))

    return summaries

@router.get("/generations/{generation_id}", response_model=GenerationResponse)
async def get_generation(generation_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve full generation details by ID."""
    stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
    gen = (await db.execute(stmt)).scalars().first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")
    return gen

@router.put("/generations/{generation_id}", response_model=GenerationResponse)
async def update_generation(
    generation_id: str,
    req: GenerationUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update blog title and/or markdown content (supports autosave)."""
    stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
    gen = (await db.execute(stmt)).scalars().first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")

    if req.blog_title is not None:
        gen.blog_title = req.blog_title
    if req.final_markdown is not None:
        gen.final_markdown = req.final_markdown

    await db.commit()
    await db.refresh(gen)
    return gen

@router.delete("/generations/{generation_id}")
async def delete_generation(generation_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a blog generation and associated records."""
    stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
    gen = (await db.execute(stmt)).scalars().first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")

    await db.delete(gen)
    await db.commit()
    return {"message": "Generation deleted successfully", "id": generation_id}

@router.get("/generations/{generation_id}/events")
async def stream_generation_events(generation_id: str, db: AsyncSession = Depends(get_db)):
    """Stream real-time workflow progress events using Server-Sent Events (SSE)."""
    stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
    gen = (await db.execute(stmt)).scalars().first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")

    async def event_generator():
        # If generation is already completed or failed, send immediate status
        if gen.status in ("completed", "failed"):
            yield {
                "event": gen.status,
                "data": json.dumps({
                    "event_type": gen.status,
                    "generation_id": generation_id,
                    "message": f"Generation is already {gen.status}",
                    "stage_statuses": gen.stage_statuses
                })
            }
            return

        q = generation_runner.subscribe(generation_id)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=25.0)
                    yield {
                        "event": event.event_type,
                        "data": event.model_dump_json()
                    }
                    if event.event_type in ("completed", "failed"):
                        break
                except asyncio.TimeoutError:
                    # Send keep-alive ping
                    yield {
                        "event": "ping",
                        "data": json.dumps({"event_type": "ping", "generation_id": generation_id})
                    }
        finally:
            generation_runner.unsubscribe(generation_id, q)

    return EventSourceResponse(event_generator())

@router.get("/generations/{generation_id}/export")
async def export_generation_markdown(generation_id: str, db: AsyncSession = Depends(get_db)):
    """Export and download generated blog as Markdown file."""
    stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
    gen = (await db.execute(stmt)).scalars().first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")

    content = gen.final_markdown or f"# {gen.blog_title or gen.topic}\n\n*No content generated.*"
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in (gen.blog_title or gen.topic).lower())[:40]
    filename = f"{safe_name}.md"

    return PlainTextResponse(
        content=content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@router.post("/generations/{generation_id}/resume", response_model=GenerationResponse)
async def resume_generation(
    generation_id: str,
    req: ResumeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Resume an interrupted generation (HITL approval)."""
    stmt = select(GenerationModel).where(GenerationModel.id == generation_id)
    gen = (await db.execute(stmt)).scalars().first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")

    gen.status = "running"
    await db.commit()
    await db.refresh(gen)

    # Continue execution
    background_tasks.add_task(generation_runner.execute_generation, generation_id)
    return gen
