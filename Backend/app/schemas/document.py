from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class DocumentChunkResponse(BaseModel):
    id: str
    chunk_index: int
    page_number: Optional[int] = None
    text_content: str
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    storage_path: str
    cloudinary_url: Optional[str] = None
    status: str
    embedding_model: Optional[str] = None
    chunk_count: int
    extracted_text_preview: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query text to search across documents")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional document filter IDs")
    top_k: Optional[int] = Field(default=4, ge=1, le=20)

class DocumentQueryResult(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: Optional[int] = None
    score: float
    content: str

class DocumentQueryResponse(BaseModel):
    query: str
    results: List[DocumentQueryResult]
