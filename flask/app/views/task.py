from flask_restx import Namespace, Resource
from flask import request
from app.helpers.response import get_success_response, get_failure_response, parse_request_body, validate_required_fields
from app.helpers.decorators import login_required
from common.app_config import config
from common.services import TaskService

# Create the task blueprint
task_api = Namespace('task', description="Task-related APIs")


@task_api.route('')
class TaskList(Resource):

    @login_required()
    def get(self, person):
        """Get all tasks for the authenticated user"""
        task_service = TaskService(config)

        # Get optional completed filter from query params
        completed_param = request.args.get('completed')
        completed_filter = None
        if completed_param is not None:
            if completed_param.lower() == 'true':
                completed_filter = True
            elif completed_param.lower() == 'false':
                completed_filter = False

        tasks = task_service.get_all_tasks_for_user(person.entity_id, completed=completed_filter)
        tasks_data = [task.as_dict() for task in tasks]

        return get_success_response(tasks=tasks_data)

    @login_required()
    @task_api.expect(
        {'type': 'object', 'properties': {
            'title': {'type': 'string'},
            'description': {'type': 'string'},
            'due_date': {'type': 'string'}
        }}
    )
    def post(self, person):
        """Create a new task"""
        parsed_body = parse_request_body(request, ['title', 'description', 'due_date'])
        validate_required_fields({'title': parsed_body['title']})

        task_service = TaskService(config)
        task = task_service.create_task(
            person_id=person.entity_id,
            title=parsed_body['title'],
            description=parsed_body['description'],
            due_date=parsed_body['due_date']
        )

        return get_success_response(task=task.as_dict(), message="Task created successfully")


@task_api.route('/<string:task_id>')
class TaskDetail(Resource):

    @login_required()
    def get(self, person, task_id):
        """Get a specific task by ID"""
        task_service = TaskService(config)
        task = task_service.get_task_by_id(task_id, person.entity_id)

        if not task:
            return get_failure_response(message="Task not found or access denied", status_code=404)

        return get_success_response(task=task.as_dict())

    @login_required()
    @task_api.expect(
        {'type': 'object', 'properties': {
            'title': {'type': 'string'},
            'description': {'type': 'string'},
            'completed': {'type': 'boolean'},
            'due_date': {'type': 'string'}
        }}
    )
    def put(self, person, task_id):
        """Update a task"""
        parsed_body = parse_request_body(request, ['title', 'description', 'completed', 'due_date'])

        task_service = TaskService(config)
        task = task_service.update_task(
            task_id=task_id,
            person_id=person.entity_id,
            title=parsed_body['title'],
            description=parsed_body['description'],
            completed=parsed_body['completed'],
            due_date=parsed_body['due_date']
        )

        if not task:
            return get_failure_response(message="Task not found or access denied", status_code=404)

        return get_success_response(task=task.as_dict(), message="Task updated successfully")

    @login_required()
    def delete(self, person, task_id):
        """Delete a task"""
        task_service = TaskService(config)
        success = task_service.delete_task(task_id, person.entity_id)

        if not success:
            return get_failure_response(message="Task not found or access denied", status_code=404)

        return get_success_response(message="Task deleted successfully")
