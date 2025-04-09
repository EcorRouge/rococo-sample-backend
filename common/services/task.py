from common.repositories.factory import RepositoryFactory, RepoType
from common.models.task import Task
from typing import List, Optional
from datetime import datetime


class TaskService:

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.task_repo = self.repository_factory.get_repository(RepoType.TASK)

    def save_task(self, task: Task):
        return self.task_repo.save(task)

    def get_task_by_id(self, task_id: str):
        return self.task_repo.get_one({"entity_id": task_id})

    def get_tasks_by_person_id(self, person_id: str, include_completed: bool = True):
        if include_completed:
            return self.task_repo.get_many({"person_id": person_id})
        else:
            return self.task_repo.get_many({"person_id": person_id, "is_completed": False})

    def get_completed_tasks_by_person_id(self, person_id: str):
        return self.task_repo.get_many({"person_id": person_id, "is_completed": True})

    def update_task_status(self, task_id: str, is_completed: bool) -> Optional[Task]:
        task = self.get_task_by_id(task_id)
        if task:
            task.is_completed = is_completed
            task.completed_at = datetime.now() if is_completed else None
            return self.save_task(task)
        return None

    def delete_task(self, task_id: str) -> bool:
        task = self.get_task_by_id(task_id)
        if not task:
            return False
        return self.task_repo.delete(task)