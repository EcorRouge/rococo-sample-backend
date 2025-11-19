from common.repositories.factory import RepositoryFactory, RepoType
from common.models.task import Task


class TaskService:

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.task_repo = self.repository_factory.get_repository(RepoType.TASK)

    def save_task(self, task: Task):
        return self.task_repo.save(task)

    def get_tasks_by_person_id(self, person_id: str, completed: bool = None):
        filters = {"person_id": person_id, "active": True}
        if completed is not None:
            filters["completed"] = completed
        return self.task_repo.get_many(filters)

    def get_task_by_id(self, task_id: str, person_id: str):
        task = self.task_repo.get_one({"entity_id": task_id, "person_id": person_id, "active": True})
        return task

    def delete_task(self, task: Task):
        self.task_repo.delete(task)

