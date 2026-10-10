from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class GenerationCreateRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500, description="The primary topic or title idea for the blog")
    audience: Optional[str] = Field(default="Developers & Technical Practitioners", description="Target reader persona")
    tone: Optional[str] = Field(default="Technical and Engaging", description="Writing style and tone")
    blog_kind: Optional[str] = Field(default="explainer", description="Format: explainer, tutorial, comparison, etc.")
    target_word_count: Optional[int] = Field(default=1500, ge=300, le=5000, description="Target total word count")
    enable_research: Optional[bool] = Field(default=True, description="Enable Tavily web research")
    enable_hitl: Optional[bool] = Field(default=False, description="Enable human approval checkpoint")
    selected_document_ids: Optional[List[str]] = Field(default_factory=list, description="IDs of uploaded reference documents for RAG")

class GenerationUpdateRequest(BaseModel):
    blog_title: Optional[str] = None
    final_markdown: Optional[str] = None

class ResumeRequest(BaseModel):
    decision: Any = Field(default=True, description="Approval boolean or updated plan object")

class GenerationSummary(BaseModel):
    id: str
    thread_id: str
    topic: str
    blog_title: Optional[str] = None
    blog_kind: str
    status: str
    current_stage: str
    created_at: datetime
    updated_at: datetime
    image_count: int = 0
    source_count: int = 0

class GenerationResponse(BaseModel):
    id: str
    thread_id: str
    topic: str
    blog_title: Optional[str] = None
    audience: str
    tone: str
    blog_kind: str
    target_word_count: int
    enable_research: bool
    enable_hitl: bool
    status: str
    current_stage: str
    stage_statuses: Dict[str, str] = Field(default_factory=dict)
    selected_document_ids: List[str] = Field(default_factory=list)
    plan: Optional[Dict[str, Any]] = None
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    final_markdown: Optional[str] = None
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    document_chunks_used: List[Dict[str, Any]] = Field(default_factory=list)
    image_specs: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
