from typing import List, Dict, Any, Optional
import os
import math
from app.config import settings
from app.core.logging import logger

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

class PineconeService:
    def __init__(self):
        self.api_key = settings.PINECONE_API_KEY or os.environ.get("PINECONE_API_KEY")
        self.index_name = settings.PINECONE_INDEX_NAME
        self.namespace_prefix = settings.PINECONE_NAMESPACE_PREFIX
        self._index = None
        self._configured = False
        self.index_exists: Optional[bool] = None
        self.warning: Optional[str] = None
        
        # In-memory vector store fallback
        self._local_vectors: Dict[str, Dict[str, Any]] = {}
        self._init_pinecone()

    def _init_pinecone(self):
        if self.api_key and self.api_key.strip():
            try:
                from pinecone import Pinecone
                pc = Pinecone(api_key=self.api_key)
                
                # Check if index exists
                existing_indexes = [idx.name for idx in pc.list_indexes()]
                if self.index_name in existing_indexes:
                    self._index = pc.Index(self.index_name)
                    self._configured = True
                    self.index_exists = True
                    self.warning = None
                    logger.info(f"Connected to Pinecone index: {self.index_name}")
                else:
                    self.index_exists = False
                    self._configured = False
                    self.warning = f"Pinecone index '{self.index_name}' does not exist. Using local vector store fallback."
                    logger.warning(self.warning)
            except Exception as e:
                self.index_exists = False
                self._configured = False
                self.warning = f"Failed to connect to Pinecone ({e}). Using local vector store fallback."
                logger.warning(self.warning)
        else:
            self.index_exists = None
            self._configured = False
            self.warning = None

    @property
    def is_configured(self) -> bool:
        return self._configured

    def upsert_chunks(
        self,
        vectors: List[Dict[str, Any]],
        namespace: Optional[str] = None
    ) -> bool:
        """Upsert chunk vectors: each item has {'id': str, 'values': List[float], 'metadata': dict}"""
        ns = namespace or self.namespace_prefix

        # Always update local vectors for fallback
        for vec in vectors:
            self._local_vectors[vec["id"]] = {
                "values": vec["values"],
                "metadata": vec.get("metadata", {}),
                "namespace": ns
            }

        if self.is_configured and self._index is not None:
            try:
                # Upsert in batches of 100
                batch_size = 100
                for i in range(0, len(vectors), batch_size):
                    batch = vectors[i:i + batch_size]
                    self._index.upsert(vectors=batch, namespace=ns)
                logger.info(f"Upserted {len(vectors)} vectors to Pinecone namespace '{ns}'")
                return True
            except Exception as e:
                logger.error(f"Pinecone upsert failed ({e}). Stored in local fallback.")
                return False

        logger.info(f"Stored {len(vectors)} vectors in local vector store (namespace: {ns})")
        return True

    def query_similarity(
        self,
        query_vector: List[float],
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        namespace: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query top_k similar chunks, optionally filtered by document_ids."""
        ns = namespace or self.namespace_prefix

        if self.is_configured and self._index is not None:
            try:
                filter_dict = None
                if document_ids:
                    filter_dict = {"document_id": {"$in": document_ids}}

                response = self._index.query(
                    vector=query_vector,
                    top_k=top_k,
                    namespace=ns,
                    filter=filter_dict,
                    include_metadata=True
                )
                
                results = []
                for match in response.get("matches", []):
                    results.append({
                        "id": match["id"],
                        "score": match.get("score", 0.0),
                        "metadata": match.get("metadata", {})
                    })
                return results
            except Exception as e:
                logger.warning(f"Pinecone query failed ({e}). Falling back to local vector search.")

        # Local fallback search with cosine similarity and metadata filtering
        scored_items = []
        for vec_id, data in self._local_vectors.items():
            if ns and data.get("namespace") != ns:
                continue
            meta = data.get("metadata", {})
            if document_ids and meta.get("document_id") not in document_ids:
                continue

            score = cosine_similarity(query_vector, data["values"])
            scored_items.append({
                "id": vec_id,
                "score": score,
                "metadata": meta
            })

        scored_items.sort(key=lambda x: x["score"], reverse=True)
        return scored_items[:top_k]

    def delete_document_chunks(self, document_id: str, namespace: Optional[str] = None) -> bool:
        """Delete chunks belonging to a document."""
        ns = namespace or self.namespace_prefix
        
        # Remove from local vectors
        ids_to_del = [
            vid for vid, v in self._local_vectors.items()
            if v.get("metadata", {}).get("document_id") == document_id
        ]
        for vid in ids_to_del:
            del self._local_vectors[vid]

        if self.is_configured and self._index is not None:
            try:
                self._index.delete(filter={"document_id": document_id}, namespace=ns)
                logger.info(f"Deleted Pinecone chunks for doc {document_id}")
                return True
            except Exception as e:
                logger.warning(f"Pinecone delete failed: {e}")
                return False

        return True

pinecone_service = PineconeService()
