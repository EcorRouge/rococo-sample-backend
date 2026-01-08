from common.repositories.base import BaseRepository
from common.models.task import Task


class TaskRepository(BaseRepository):
    MODEL = Task

    def get_tasks_by_person_id(self, person_id: str):
        """
        Get all tasks for a specific person

        Args:
            person_id: The person's entity_id

        Returns:
            List of Task objects
        """
        return self.get_all({"person_id": person_id})

    def get_completed_tasks(self, person_id: str):
        """
        Get all completed tasks for a specific person

        Args:
            person_id: The person's entity_id

        Returns:
            List of completed Task objects
        """
        return self.get_all({"person_id": person_id, "completed": True})

    def get_pending_tasks(self, person_id: str):
        """
        Get all pending (not completed) tasks for a specific person

        Args:
            person_id: The person's entity_id

        Returns:
            List of pending Task objects
        """
        return self.get_all({"person_id": person_id, "completed": False})
