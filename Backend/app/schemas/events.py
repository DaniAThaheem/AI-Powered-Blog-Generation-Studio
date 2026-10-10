from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel
import datetime

StageType = Literal[
    "analyze_topic",
    "research",
    "plan",
    "write_sections",
    "merge",
    "plan_images",
    "generate_images",
    "save"
]

StageStatus = Literal["pending", "running", "completed", "skipped", "failed"]

class WorkflowEvent(BaseModel):
    event_type: Literal["stage", "warning", "interrupted", "completed", "failed", "ping"]
    generation_id: str
    stage: Optional[StageType] = None
    stage_status: Optional[StageStatus] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: str = None

    def __init__(self, **data):
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = datetime.datetime.utcnow().isoformat()
        super().__init__(**data)
