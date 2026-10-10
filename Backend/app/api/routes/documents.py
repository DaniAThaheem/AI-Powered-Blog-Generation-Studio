import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.db.models import DocumentModel, DocumentChunkModel
from app.schemas.document import (
    DocumentResponse,
    DocumentChunkResponse,
    DocumentQueryRequest,
    DocumentQueryResponse,
    DocumentQueryResult
)
from app.services.document_service import document_service, ALLOWED_EXTENSIONS
from app.services.pinecone_service import pinecone_service
from app.config import settings
from app.core.logging import logger

router = APIRouter()

@router.post("/documents/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload reference document (PDF, TXT, MD), extract text, chunk, and index."""
    original_name = file.filename or "uploaded_file"
    ext = Path(original_name).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Validate file size
    file_bytes = await file.read()
    file_size = len(file_bytes)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Cannot upload an empty file")

    # Save to storage directory
    doc_dir = Path(settings.STORAGE_DIR) / "documents"
    doc_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex[:8]}_{original_name}"
    target_path = doc_dir / stored_filename
    target_path.write_bytes(file_bytes)

    # Process and index
    doc_record = await document_service.process_and_index_document(
        db=db,
        file_path=str(target_path.resolve()),
        original_filename=original_name,
        file_type=ext.replace(".", ""),
        file_size=file_size
    )

    return doc_record

@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List all uploaded reference documents."""
    query = select(DocumentModel).order_by(desc(DocumentModel.created_at))
    if status:
        query = query.where(DocumentModel.status == status)

    docs = (await db.execute(query)).scalars().all()
    return docs

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve document details by ID."""
    stmt = select(DocumentModel).where(DocumentModel.id == document_id)
    doc = (await db.execute(stmt)).scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/documents/{document_id}/chunks", response_model=List[DocumentChunkResponse])
async def get_document_chunks(document_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve all chunks belonging to a document."""
    stmt = select(DocumentChunkModel).where(DocumentChunkModel.document_id == document_id).order_by(DocumentChunkModel.chunk_index)
    chunks = (await db.execute(stmt)).scalars().all()
    return chunks

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """Delete document, its chunks, vectors, and local file."""
    stmt = select(DocumentModel).where(DocumentModel.id == document_id)
    doc = (await db.execute(stmt)).scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. Delete vector embeddings from Pinecone / local store
    pinecone_service.delete_document_chunks(document_id)

    # 2. Delete local storage file if exists
    try:
        if os.path.exists(doc.storage_path):
            os.remove(doc.storage_path)
    except Exception as e:
        logger.warning(f"Could not remove local file {doc.storage_path}: {e}")

    # 3. Delete database record
    await db.delete(doc)
    await db.commit()

    return {"message": "Document and associated vectors deleted successfully", "id": document_id}

@router.post("/documents/retrieve", response_model=DocumentQueryResponse)
async def retrieve_document_chunks(
    req: DocumentQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Test vector retrieval against indexed documents."""
    matches = await document_service.retrieve_context(
        query=req.query,
        selected_document_ids=req.document_ids,
        top_k=req.top_k or 4,
        db=db
    )

    query_results = [
        DocumentQueryResult(
            chunk_id=m["chunk_id"],
            document_id=m["document_id"] or "",
            filename=m["filename"],
            page_number=m.get("page_number"),
            score=round(m["score"], 4),
            content=m["content"]
        )
        for m in matches
    ]

    return DocumentQueryResponse(
        query=req.query,
        results=query_results
    )
