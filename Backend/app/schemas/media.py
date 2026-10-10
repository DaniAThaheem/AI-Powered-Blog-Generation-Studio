from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class MediaAssetResponse(BaseModel):
    id: str
    generation_id: Optional[str] = None
    placeholder: Optional[str] = None
    filename: str
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    prompt: str
    cloudinary_url: str
    cloudinary_public_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
