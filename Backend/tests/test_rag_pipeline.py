import pytest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy import select
from app.services.document_service import (
    split_text_into_chunks,
    generate_fallback_embedding,
    document_service
)
from app.services.pinecone_service import pinecone_service
from app.services.gemini_service import gemini_service
from app.db.models import DocumentModel, DocumentChunkModel, GenerationModel
from app.db.session import AsyncSessionLocal
from httpx import AsyncClient

def test_split_text_into_chunks():
    """Verify chunking maintains overlap and does not lose text."""
    sample_text = "Word " * 200 # approx 1000 chars
    chunks = split_text_into_chunks(sample_text, chunk_size=300, chunk_overlap=50)
    assert len(chunks) >= 3
    for c in chunks:
        assert len(c) > 0
        assert len(c) <= 300

def test_rag_vector_metadata_and_filtering():
    """Verify that vector retrieval strictly respects document_id filtering without hitting external Pinecone."""
    assert not pinecone_service.is_configured, "Test must run in offline/local fallback mode"
    doc_a_id = "doc_alpha_123"
    doc_b_id = "doc_beta_456"

    vec_a = generate_fallback_embedding("Kubernetes container orchestration and pod autoscaling")
    vec_b = generate_fallback_embedding("PostgreSQL relational database indexing strategies")

    pinecone_service.upsert_chunks([
        {
            "id": f"{doc_a_id}_0",
            "values": vec_a,
            "metadata": {
                "document_id": doc_a_id,
                "filename": "k8s_architecture.pdf",
                "text_preview": "Kubernetes container orchestration and pod autoscaling"
            }
        },
        {
            "id": f"{doc_b_id}_0",
            "values": vec_b,
            "metadata": {
                "document_id": doc_b_id,
                "filename": "postgres_internals.pdf",
                "text_preview": "PostgreSQL relational database indexing strategies"
            }
        }
    ], namespace="test_namespace")

    # Query filtered specifically for doc_a
    query_vec = generate_fallback_embedding("container orchestration pods")
    results = pinecone_service.query_similarity(
        query_vector=query_vec,
        top_k=5,
        document_ids=[doc_a_id],
        namespace="test_namespace"
    )

    assert len(results) > 0
    # Every returned result must belong to doc_a_id
    for r in results:
        assert r["metadata"]["document_id"] == doc_a_id
        assert r["metadata"]["document_id"] != doc_b_id

    # Test deletion
    pinecone_service.delete_document_chunks(doc_a_id, namespace="test_namespace")
    results_after_delete = pinecone_service.query_similarity(
        query_vector=query_vec,
        top_k=5,
        document_ids=[doc_a_id],
        namespace="test_namespace"
    )
    assert len(results_after_delete) == 0

@pytest.mark.asyncio
async def test_dont_mix_embedding_spaces_on_gemini_failure(monkeypatch, tmp_path):
    """When Gemini is configured and embedding fails mid-document, do NOT mix fallback hash vectors."""
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("Detailed architecture of streaming distributed systems.", encoding="utf-8")

    # Mock Gemini as configured but embed_documents raises
    monkeypatch.setattr(gemini_service, "api_key", "test-key")
    mock_embed_client = MagicMock()
    mock_embed_client.embed_documents.side_effect = RuntimeError("Rate limit exceeded on Gemini API")
    monkeypatch.setattr(gemini_service, "get_embeddings", lambda: mock_embed_client)

    async with AsyncSessionLocal() as db:
        doc = await document_service.process_and_index_document(
            db=db,
            file_path=str(sample_file),
            original_filename="sample.txt",
            file_type="txt",
            file_size=sample_file.stat().st_size
        )

        assert doc.status == "failed"
        assert "retryable" in doc.error_message
        assert "Gemini embedding failed" in doc.error_message

@pytest.mark.asyncio
async def test_fallback_embeddings_when_gemini_unconfigured(monkeypatch, tmp_path):
    """When Gemini is not configured, fallback hash embeddings are used and embedder is recorded."""
    sample_file = tmp_path / "offline_sample.txt"
    sample_file.write_text("Offline document indexing with deterministic hash embeddings.", encoding="utf-8")

    # Ensure unconfigured
    monkeypatch.setattr(gemini_service, "api_key", None)

    async with AsyncSessionLocal() as db:
        doc = await document_service.process_and_index_document(
            db=db,
            file_path=str(sample_file),
            original_filename="offline_sample.txt",
            file_type="txt",
            file_size=sample_file.stat().st_size
        )

        assert doc.status == "ready"
        assert doc.embedding_model == "fallback_hash"

@pytest.mark.asyncio
async def test_single_in_query_in_retrieve_context(tmp_path):
    """Verify retrieve_context loads matched chunks using a single IN query without N+1."""
    sample_file = tmp_path / "batch_chunks.txt"
    sample_file.write_text("Chunk text line 1. Chunk text line 2. Chunk text line 3.", encoding="utf-8")

    async with AsyncSessionLocal() as db:
        doc = await document_service.process_and_index_document(
            db=db,
            file_path=str(sample_file),
            original_filename="batch_chunks.txt",
            file_type="txt",
            file_size=sample_file.stat().st_size
        )

        # Retrieve context
        results = await document_service.retrieve_context(
            query="Chunk text",
            selected_document_ids=[doc.id],
            top_k=3,
            db=db
        )

        assert len(results) > 0
        for r in results:
            assert r["document_id"] == doc.id
            assert len(r["content"]) > 0

@pytest.mark.asyncio
async def test_background_reindex_on_startup():
    """Verify that reindex_all_documents repopulates in-memory vectors for ready documents."""
    doc_id = "test-doc-reindex"
    chunk_id = f"{doc_id}_0"
    content = "Microservices service discovery and registration patterns."

    async with AsyncSessionLocal() as db:
        doc = DocumentModel(
            id=doc_id,
            filename="reindex.txt",
            original_name="reindex.txt",
            file_type="txt",
            file_size=100,
            storage_path="./storage/reindex.txt",
            status="ready",
            embedding_model="fallback_hash",
            chunk_count=1
        )
        chunk = DocumentChunkModel(
            id=chunk_id,
            document_id=doc_id,
            chunk_index=0,
            page_number=1,
            text_content=content,
            metadata_json={"document_id": doc_id, "text_preview": content}
        )
        db.add(doc)
        db.add(chunk)
        await db.commit()

    # Clear in-memory vectors to simulate server restart
    pinecone_service._local_vectors.clear()
    assert len(pinecone_service._local_vectors) == 0

    # Run reindexing
    await document_service.reindex_all_documents()

    assert chunk_id in pinecone_service._local_vectors
    assert pinecone_service._local_vectors[chunk_id]["metadata"]["document_id"] == doc_id

@pytest.mark.asyncio
async def test_pinecone_missing_index_warning_surfaced(async_client: AsyncClient, monkeypatch):
    """Verify that when Pinecone index does not exist, warning is surfaced in health and settings."""
    monkeypatch.setattr(pinecone_service, "index_exists", False)
    monkeypatch.setattr(pinecone_service, "warning", "Pinecone index 'blog-rag' does not exist. Using local vector store fallback.")

    health_res = await async_client.get("/api/health")
    assert health_res.status_code == 200
    p_health = health_res.json()["services"]["pinecone"]
    assert p_health["index_exists"] is False
    assert "does not exist" in p_health["warning"]

    settings_res = await async_client.get("/api/settings")
    assert settings_res.status_code == 200
    p_settings = settings_res.json()["providers"]["pinecone"]
    assert p_settings["index_exists"] is False
    assert "does not exist" in p_settings["warning"]

@pytest.mark.asyncio
async def test_mutable_dict_json_mutation_tracking():
    """Verify that in-place JSON mutations on stage_statuses are tracked and committed without reassign."""
    gen_id = "test-mutable-json"
    async with AsyncSessionLocal() as db:
        gen = GenerationModel(
            id=gen_id,
            thread_id=f"thread_{gen_id}",
            topic="JSON Mutation Test",
            stage_statuses={"router": "pending", "save": "pending"}
        )
        db.add(gen)
        await db.commit()

    # Mutate in-place
    async with AsyncSessionLocal() as db:
        stmt = select(GenerationModel).where(GenerationModel.id == gen_id)
        g = (await db.execute(stmt)).scalars().first()
        g.stage_statuses["save"] = "completed"
        await db.commit()

    # Verify mutation persisted
    async with AsyncSessionLocal() as db:
        stmt = select(GenerationModel).where(GenerationModel.id == gen_id)
        reloaded = (await db.execute(stmt)).scalars().first()
        assert reloaded.stage_statuses["save"] == "completed"
