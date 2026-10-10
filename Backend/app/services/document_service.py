from typing import List, Dict, Any, Optional, Tuple
import os
import uuid
import hashlib
from pathlib import Path
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.core.logging import logger
from app.db.models import DocumentModel, DocumentChunkModel
from app.services.gemini_service import gemini_service
from app.services.pinecone_service import pinecone_service
from app.services.cloudinary_service import cloudinary_service

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}

def split_text_into_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> List[str]:
    """Simple robust character splitter with overlap."""
    if not text:
        return []
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start += (chunk_size - chunk_overlap)
    return chunks

def generate_fallback_embedding(text: str, dim: int = 768) -> List[float]:
    """Deterministically generate unit-normalized vector for testing/offline mode."""
    h = hashlib.sha256(text.encode("utf-8")).digest()
    vals = [((b / 255.0) * 2.0 - 1.0) for b in h]
    # expand to dim
    expanded = (vals * (dim // len(vals) + 1))[:dim]
    norm = sum(x * x for x in expanded) ** 0.5 or 1.0
    return [x / norm for x in expanded]

class DocumentService:
    async def process_and_index_document(
        self,
        db: AsyncSession,
        file_path: str,
        original_filename: str,
        file_type: str,
        file_size: int
    ) -> DocumentModel:
        """Extract text, chunk, embed, and index document."""
        doc_id = str(uuid.uuid4())
        
        # 1. Create document record in DB
        doc_record = DocumentModel(
            id=doc_id,
            filename=Path(file_path).name,
            original_name=original_filename,
            file_type=file_type,
            file_size=file_size,
            storage_path=file_path,
            status="extracting"
        )
        db.add(doc_record)
        await db.commit()
        await db.refresh(doc_record)

        # 2. Upload to Cloudinary (optional)
        try:
            cloud_url, pub_id = cloudinary_service.upload_file(file_path)
            doc_record.cloudinary_url = cloud_url
            doc_record.cloudinary_public_id = pub_id
            await db.commit()
        except Exception as e:
            logger.warning(f"Could not upload file to Cloudinary: {e}")

        # 3. Extract text
        extracted_pages: List[Tuple[Optional[int], str]] = []
        try:
            if file_type.lower() == "pdf":
                reader = PdfReader(file_path)
                for page_idx, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        extracted_pages.append((page_idx + 1, page_text))
            else:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    full_text = f.read()
                extracted_pages.append((1, full_text))
        except Exception as e:
            logger.error(f"Failed to extract text from {original_filename}: {e}")
            doc_record.status = "failed"
            doc_record.error_message = f"Text extraction failed: {str(e)}"
            await db.commit()
            return doc_record

        # 4. Chunk text
        doc_record.status = "chunking"
        await db.commit()

        chunk_records = []
        raw_chunks: List[Dict[str, Any]] = []
        chunk_idx = 0
        all_text_preview = ""

        for page_num, page_content in extracted_pages:
            page_chunks = split_text_into_chunks(page_content, chunk_size=600, chunk_overlap=100)
            for chunk_text in page_chunks:
                chunk_id = f"{doc_id}_{chunk_idx}"
                metadata = {
                    "document_id": doc_id,
                    "filename": original_filename,
                    "chunk_index": chunk_idx,
                    "page_number": page_num,
                    "text_preview": chunk_text[:150]
                }
                
                chunk_rec = DocumentChunkModel(
                    id=chunk_id,
                    document_id=doc_id,
                    chunk_index=chunk_idx,
                    page_number=page_num,
                    text_content=chunk_text,
                    metadata_json=metadata
                )
                chunk_records.append(chunk_rec)
                raw_chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": metadata
                })
                chunk_idx += 1
                if len(all_text_preview) < 500:
                    all_text_preview += chunk_text + "\n"

        doc_record.chunk_count = len(chunk_records)
        doc_record.extracted_text_preview = all_text_preview[:500]
        for c in chunk_records:
            db.add(c)
        await db.commit()

        # 5. Embed and Index into Pinecone / local store
        doc_record.status = "indexing"
        await db.commit()

        try:
            # Generate embeddings without mixing spaces
            vectors_to_upsert = []
            if gemini_service.is_configured:
                embed_client = gemini_service.get_embeddings()
                texts = [rc["text"] for rc in raw_chunks]
                try:
                    embeddings = embed_client.embed_documents(texts)
                    doc_record.embedding_model = settings.GEMINI_EMBEDDING_MODEL
                except Exception as embed_err:
                    logger.error(f"Gemini embedding failed for document {doc_id}: {embed_err}")
                    doc_record.status = "failed"
                    doc_record.error_message = f"Gemini embedding failed: {str(embed_err)} (retryable)"
                    await db.commit()
                    return doc_record
            else:
                embeddings = [generate_fallback_embedding(rc["text"]) for rc in raw_chunks]
                doc_record.embedding_model = "fallback_hash"

            for rc, emb in zip(raw_chunks, embeddings):
                vectors_to_upsert.append({
                    "id": rc["id"],
                    "values": emb,
                    "metadata": rc["metadata"]
                })

            pinecone_service.upsert_chunks(vectors_to_upsert)
            doc_record.status = "ready"
            await db.commit()
            logger.info(f"Document {original_filename} ({doc_id}) indexed successfully with {len(raw_chunks)} chunks using {doc_record.embedding_model}")
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            doc_record.status = "failed"
            doc_record.error_message = f"Indexing failed: {str(e)}"
            await db.commit()

        await db.refresh(doc_record)
        return doc_record

    async def retrieve_context(
        self,
        query: str,
        selected_document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve most relevant chunks for a given query."""
        if not query or not query.strip():
            return []

        # 1. Get query embedding
        if gemini_service.is_configured:
            try:
                emb = gemini_service.get_embeddings().embed_query(query)
            except Exception:
                emb = generate_fallback_embedding(query)
        else:
            emb = generate_fallback_embedding(query)

        # 2. Query vector store
        matches = pinecone_service.query_similarity(
            query_vector=emb,
            top_k=top_k,
            document_ids=selected_document_ids
        )

        results = []
        if not matches:
            return results

        # Single batch query to avoid N+1 queries
        chunk_text_map: Dict[str, str] = {}
        if db:
            matched_ids = [m["id"] for m in matches]
            stmt = select(DocumentChunkModel).where(DocumentChunkModel.id.in_(matched_ids))
            chunk_rows = (await db.execute(stmt)).scalars().all()
            chunk_text_map = {row.id: row.text_content for row in chunk_rows}

        for m in matches:
            chunk_id = m["id"]
            meta = m.get("metadata", {})
            score = m.get("score", 0.0)
            text_content = chunk_text_map.get(chunk_id, meta.get("text_preview", ""))

            results.append({
                "chunk_id": chunk_id,
                "document_id": meta.get("document_id"),
                "filename": meta.get("filename", "Unknown Document"),
                "page_number": meta.get("page_number"),
                "score": score,
                "content": text_content
            })

        return results

    async def reindex_all_documents(self):
        """Re-index chunks for ready documents into in-memory vector store on startup."""
        if pinecone_service.is_configured:
            return  # Remote Pinecone already persists vectors

        try:
            from app.db.session import AsyncSessionLocal
            logger.info("Starting background re-indexing of documents into local vector store...")
            async with AsyncSessionLocal() as db:
                stmt = select(DocumentModel).where(DocumentModel.status == "ready")
                ready_docs = (await db.execute(stmt)).scalars().all()
                if not ready_docs:
                    logger.info("No ready documents to re-index")
                    return

                doc_map = {doc.id: doc for doc in ready_docs}
                chunk_stmt = select(DocumentChunkModel).where(DocumentChunkModel.document_id.in_(list(doc_map.keys())))
                chunks = (await db.execute(chunk_stmt)).scalars().all()

                if not chunks:
                    return

                vectors_to_upsert = []
                for chunk in chunks:
                    doc = doc_map.get(chunk.document_id)
                    embedder = getattr(doc, "embedding_model", None)
                    if gemini_service.is_configured and embedder and embedder != "fallback_hash":
                        try:
                            emb = gemini_service.get_embeddings().embed_query(chunk.text_content)
                        except Exception:
                            emb = generate_fallback_embedding(chunk.text_content)
                    else:
                        emb = generate_fallback_embedding(chunk.text_content)

                    vectors_to_upsert.append({
                        "id": chunk.id,
                        "values": emb,
                        "metadata": chunk.metadata_json or {
                            "document_id": chunk.document_id,
                            "filename": getattr(doc, "filename", "document"),
                            "chunk_index": chunk.chunk_index,
                            "page_number": chunk.page_number,
                            "text_preview": chunk.text_content[:150]
                        }
                    })

                pinecone_service.upsert_chunks(vectors_to_upsert)
                logger.info(f"Re-indexed {len(vectors_to_upsert)} chunks from {len(ready_docs)} ready document(s) in background.")
        except Exception as e:
            logger.error(f"Error during background re-indexing: {e}")

document_service = DocumentService()
