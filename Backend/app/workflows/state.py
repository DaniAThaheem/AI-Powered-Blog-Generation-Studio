from __future__ import annotations
from typing import Annotated, List, TypedDict, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
import operator

class Task(BaseModel):
    id: int
    title: str
    goal: str = Field(..., description="One line to describe what the reader should understand after reading this section")
    bullets: List[str] = Field(..., min_length=2, max_length=6, description="2-6 concrete, non-overlapping subpoints to cover in this topic")
    brief: str = Field(..., description="What to cover")
    target_word: int = Field(default=300, description="Target word count for this section (120-600)")
    tags: List[str] = Field(default_factory=list)
    requires_research: bool = False
    requires_citation: bool = False
    requires_code: bool = False

class Plan(BaseModel):
    blog_title: str
    audience: str
    tone: str
    blog_kind: Literal["explainer", "tutorial", "new_roundup", "comparison", "system_design"] = "explainer"
    constraint: List[str] = Field(default_factory=list)
    tasks: List[Task]

class EvidenceItem(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None
    snippet: Optional[str] = None
    source: Optional[str] = None

class EvidencePack(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)

class RouterDecision(BaseModel):
    needs_research: bool
    mode: Literal["open_book", "hybrid", "closed_book"]
    queries: List[str] = Field(default_factory=list)

class ImageSpec(BaseModel):
    placeholder: str = Field(..., description="e.g. [[IMAGE_1]]")
    filename: str = Field(..., description="Save filename, e.g. architecture-flow.png")
    alt: str
    caption: str
    prompt: str = Field(..., description="Prompt to send to the image generation model")
    size: Literal["1024x1024", "1024x1536", "1536x1024"] = "1024x1024"
    quality: Literal["low", "medium", "high"] = "medium"
    url: Optional[str] = None

class GlobalImagePlan(BaseModel):
    md_with_placeholders: str
    images: List[ImageSpec] = Field(default_factory=list)

class SectionResult(BaseModel):
    id: int
    title: str
    content: str

class WorkflowState(TypedDict):
    topic: str
    audience: str
    tone: str
    blog_kind: str
    target_word_count: int
    enable_research: bool
    enable_hitl: bool
    selected_document_ids: List[str]
    document_chunks: List[Dict[str, Any]]

    mode: str
    needs_research: bool
    queries: List[str]
    evidence: List[Dict[str, Any]]
    plan: Optional[Dict[str, Any]]
    
    # Reducer fix: clean list of section results merged with operator.add
    sections: Annotated[List[Dict[str, Any]], operator.add]

    merged_md: str
    md_with_placeholders: str
    image_specs: List[Dict[str, Any]]
    final: str
    output_path: str
    warnings: Annotated[List[str], operator.add]
    error: Optional[str]
