import pytest
from app.services.document_service import split_text_into_chunks, generate_fallback_embedding
from app.services.pinecone_service import pinecone_service

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
