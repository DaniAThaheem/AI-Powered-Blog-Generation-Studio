import datetime
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict, MutableList
from app.db.session import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class GenerationModel(Base):
    __tablename__ = "generations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    thread_id = Column(String(64), nullable=False, unique=True, index=True)
    topic = Column(String(500), nullable=False)
    blog_title = Column(String(500), nullable=True)
    audience = Column(String(100), default="Developers & Technical Practitioners")
    tone = Column(String(100), default="Technical and Engaging")
    blog_kind = Column(String(50), default="explainer")
    target_word_count = Column(Integer, default=1500)
    enable_research = Column(Boolean, default=True)
    enable_hitl = Column(Boolean, default=False)
    
    status = Column(String(50), default="queued", index=True)  # queued, running, interrupted, completed, failed, cancelled
    current_stage = Column(String(100), default="queued")
    stage_statuses = Column(MutableDict.as_mutable(JSON), default=dict)  # {"router": "completed", ...}
    
    selected_document_ids = Column(MutableList.as_mutable(JSON), default=list)
    plan = Column(MutableDict.as_mutable(JSON), nullable=True)
    sections = Column(MutableList.as_mutable(JSON), default=list)
    final_markdown = Column(Text, nullable=True)
    evidence = Column(MutableList.as_mutable(JSON), default=list)
    document_chunks_used = Column(MutableList.as_mutable(JSON), default=list)
    image_specs = Column(MutableList.as_mutable(JSON), default=list)
    warnings = Column(MutableList.as_mutable(JSON), default=list)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    media_assets = relationship("MediaAssetModel", back_populates="generation", cascade="all, delete-orphan")

class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, default=0)
    storage_path = Column(String(500), nullable=False)
    cloudinary_url = Column(String(500), nullable=True)
    cloudinary_public_id = Column(String(255), nullable=True)
    
    status = Column(String(50), default="uploaded", index=True) # uploaded, extracting, chunking, indexing, ready, failed
    embedding_model = Column(String(100), nullable=True, default="fallback_hash")
    chunk_count = Column(Integer, default=0)
    extracted_text_preview = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    chunks = relationship("DocumentChunkModel", back_populates="document", cascade="all, delete-orphan")

class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"

    id = Column(String(64), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    text_content = Column(Text, nullable=False)
    metadata_json = Column(MutableDict.as_mutable(JSON), default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("DocumentModel", back_populates="chunks")

class MediaAssetModel(Base):
    __tablename__ = "media_assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    generation_id = Column(String(36), ForeignKey("generations.id", ondelete="SET NULL"), nullable=True, index=True)
    placeholder = Column(String(50), nullable=True)
    filename = Column(String(255), nullable=False)
    alt_text = Column(String(500), nullable=True)
    caption = Column(Text, nullable=True)
    prompt = Column(Text, nullable=False)
    cloudinary_url = Column(String(1000), nullable=False)
    cloudinary_public_id = Column(String(255), nullable=True)
    local_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    generation = relationship("GenerationModel", back_populates="media_assets")
