from dataclasses import dataclass, field
from rococo.models.versioned_model import VersionedModel
from typing import ClassVar, Optional


@dataclass
class Task(VersionedModel):
    use_type_checking: ClassVar[bool] = True
    
    # Define fields explicitly so VersionedModel recognizes them
    person_id: Optional[str] = None
    title: Optional[str] = None
    completed: bool = False
    
    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)

