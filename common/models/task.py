from rococo.models import VersionedModel
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class Task(VersionedModel):
    person_id: str = field(default="")
    title: str = field(default="")
    description: Optional[str] = None
    is_completed: bool = False
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    priority: int = 0  # 0 = normal, 1 = high, etc.