from common.repositories.factory import RepositoryFactory, RepoType
from common.models.task import Task
from common.tasks.send_message import MessageSender
from common.app_logger import logger


class TaskService:

    EMAIL_TRANSMITTER_QUEUE_NAME = "email_transmitter"

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.task_repo = self.repository_factory.get_repository(RepoType.TASK)
        self.message_sender = MessageSender()

        from common.services import PersonService, EmailService
        self.person_service = PersonService(config)
        self.email_service = EmailService(config)

    def create_task(self, person_id: str, title: str, description: str = None, due_date: str = None):
        """
        Create a new task

        Args:
            person_id: The ID of the person creating the task
            title: Task title
            description: Optional task description
            due_date: Optional due date

        Returns:
            Created Task object
        """
        task = Task(
            title=title,
            description=description,
            completed=False,
            due_date=due_date,
            person_id=person_id
        )
        task = self.task_repo.save(task)

        # Send task created email notification
        try:
            person = self.person_service.get_person_by_id(person_id)
            if person:
                email_obj = self.email_service.get_email_by_email_address(person.email)
                if email_obj:
                    message = {
                        "event": "TASK_CREATED",
                        "data": {
                            "recipient_name": f"{person.first_name} {person.last_name}".strip(),
                            "task_title": task.title,
                            "task_description": task.description or "",
                            "task_due_date": task.due_date or "",
                        },
                        "to_emails": [email_obj.email],
                    }
                    self.message_sender.send_message(self.EMAIL_TRANSMITTER_QUEUE_NAME, message)
        except Exception as e:
            logger.error(f"Failed to send task created email: {str(e)}")

        return task

    def get_task_by_id(self, task_id: str, person_id: str):
        """
        Get a task by ID with ownership verification

        Args:
            task_id: The task's entity_id
            person_id: The ID of the person requesting the task

        Returns:
            Task object if found and owned by person, None otherwise
        """
        task = self.task_repo.get_one({"entity_id": task_id})
        if task and task.person_id == person_id:
            return task
        return None

    def get_all_tasks_for_user(self, person_id: str, completed: bool = None):
        """
        Get all tasks for a user, optionally filtered by completion status

        Args:
            person_id: The person's entity_id
            completed: Optional filter - True for completed, False for pending, None for all

        Returns:
            List of Task objects
        """
        if completed is True:
            return self.task_repo.get_completed_tasks(person_id)
        elif completed is False:
            return self.task_repo.get_pending_tasks(person_id)
        else:
            return self.task_repo.get_tasks_by_person_id(person_id)

    def update_task(self, task_id: str, person_id: str, title: str = None,
                   description: str = None, completed: bool = None, due_date: str = None):
        """
        Update a task with ownership verification

        Args:
            task_id: The task's entity_id
            person_id: The ID of the person updating the task
            title: Optional new title
            description: Optional new description
            completed: Optional new completed status
            due_date: Optional new due date

        Returns:
            Updated Task object if successful, None if not found or not owned
        """
        task = self.get_task_by_id(task_id, person_id)
        if not task:
            return None

        # Update only provided fields
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if completed is not None:
            task.completed = completed
        if due_date is not None:
            task.due_date = due_date

        task = self.task_repo.save(task)
        return task

    def delete_task(self, task_id: str, person_id: str):
        """
        Delete a task with ownership verification

        Args:
            task_id: The task's entity_id
            person_id: The ID of the person deleting the task

        Returns:
            True if deleted successfully, False if not found or not owned
        """
        task = self.get_task_by_id(task_id, person_id)
        if not task:
            return False

        # Send task deleted email notification before deletion
        try:
            person = self.person_service.get_person_by_id(person_id)
            if person:
                email_obj = self.email_service.get_email_by_email_address(person.email)
                if email_obj:
                    message = {
                        "event": "TASK_DELETED",
                        "data": {
                            "recipient_name": f"{person.first_name} {person.last_name}".strip(),
                            "task_title": task.title,
                            "task_description": task.description or "",
                            "task_due_date": task.due_date or "",
                        },
                        "to_emails": [email_obj.email],
                    }
                    self.message_sender.send_message(self.EMAIL_TRANSMITTER_QUEUE_NAME, message)
        except Exception as e:
            logger.error(f"Failed to send task deleted email: {str(e)}")

        self.task_repo.delete(task)
        return True

    def mark_task_completed(self, task_id: str, person_id: str):
        """
        Mark a task as completed

        Args:
            task_id: The task's entity_id
            person_id: The ID of the person completing the task

        Returns:
            Updated Task object if successful, None if not found or not owned
        """
        task = self.update_task(task_id, person_id, completed=True)

        # Send task completed email notification
        if task:
            try:
                person = self.person_service.get_person_by_id(person_id)
                if person:
                    email_obj = self.email_service.get_email_by_email_address(person.email)
                    if email_obj:
                        message = {
                            "event": "TASK_COMPLETED",
                            "data": {
                                "recipient_name": f"{person.first_name} {person.last_name}".strip(),
                                "task_title": task.title,
                                "task_description": task.description or "",
                                "task_due_date": task.due_date or "",
                            },
                            "to_emails": [email_obj.email],
                        }
                        self.message_sender.send_message(self.EMAIL_TRANSMITTER_QUEUE_NAME, message)
            except Exception as e:
                logger.error(f"Failed to send task completed email: {str(e)}")

        return task
