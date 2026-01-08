from rococo.models import VersionedModel
from rococo.models.versioned_model import ModelValidationError
from typing import ClassVar


class Task(VersionedModel):
    use_type_checking: ClassVar[bool] = True

    TABLE_NAME = "task"

    def __init__(
        self,
        title: str = None,
        description: str = None,
        completed: bool = False,
        due_date: str = None,
        person_id: str = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title = title
        self.description = description
        self.completed = completed if completed is not None else False
        self.due_date = due_date
        self.person_id = person_id

    def validate(self):
        """Validate task fields"""
        errors = []

        # Validate title is required
        if not self.title:
            errors.append("Title is required.")

        # Validate title is a string
        if self.title and not isinstance(self.title, str):
            errors.append("Title must be a string.")

        # Validate title length (max 255 characters)
        if self.title and len(self.title) > 255:
            errors.append("Title exceeds maximum length of 255 characters.")

        # Validate person_id is required
        if not self.person_id:
            errors.append("Person ID is required.")

        # Validate person_id is a string
        if self.person_id and not isinstance(self.person_id, str):
            errors.append("Person ID must be a string.")

        # Validate completed is a boolean
        if self.completed is not None and not isinstance(self.completed, bool):
            errors.append("Completed must be a boolean.")

        # Validate description is a string if provided
        if self.description is not None and not isinstance(self.description, str):
            errors.append("Description must be a string.")

        if errors:
            raise ModelValidationError(errors)
