from flask_restx import Namespace, Resource
from flask import request
from app.helpers.response import get_success_response, get_failure_response, parse_request_body, validate_required_fields
from app.helpers.decorators import login_required
from common.app_config import config
from common.services import TaskService
from common.models.task import Task

task_api = Namespace('tasks', description="Task-related APIs")


@task_api.route('')
class Tasks(Resource):
    @login_required()
    def get(self, person):
        # Get filter query param: ?filter=all|active|completed
        filter_type = request.args.get('filter', 'all')
        task_service = TaskService(config)
        
        completed = None
        if filter_type == 'active':
            completed = False
        elif filter_type == 'completed':
            completed = True
        
        tasks = task_service.get_tasks_by_person_id(person.entity_id, completed)
        return get_success_response(tasks=[task.as_dict() for task in tasks])
    
    @login_required()
    def post(self, person):
        try:
            parsed_body = parse_request_body(request, ['title'])
            validate_required_fields(parsed_body)
            
            task_service = TaskService(config)
            # Create task with keyword arguments (now that it's a dataclass)
            task = Task(
                person_id=person.entity_id,
                title=parsed_body['title'],
                completed=False
            )
            task = task_service.save_task(task)
            return get_success_response(task=task.as_dict(), message="Task created successfully.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            return get_failure_response(message=f"Error creating task: {str(e)}")


@task_api.route('/<string:task_id>')
class TaskDetail(Resource):
    @login_required()
    def put(self, person, task_id):
        parsed_body = parse_request_body(request, ['title'])
        validate_required_fields(parsed_body)
        
        task_service = TaskService(config)
        task = task_service.get_task_by_id(task_id, person.entity_id)
        if not task:
            return get_failure_response(message="Task not found.")
        
        task.title = parsed_body['title']
        task = task_service.save_task(task)
        return get_success_response(task=task.as_dict(), message="Task updated successfully.")
    
    @login_required()
    def delete(self, person, task_id):
        task_service = TaskService(config)
        task = task_service.get_task_by_id(task_id, person.entity_id)
        if not task:
            return get_failure_response(message="Task not found.")
        
        task_service.delete_task(task)
        return get_success_response(message="Task deleted successfully.")


@task_api.route('/<string:task_id>/complete')
class TaskComplete(Resource):
    @login_required()
    def patch(self, person, task_id):
        parsed_body = parse_request_body(request, ['completed'])
        validate_required_fields(parsed_body)
        
        task_service = TaskService(config)
        task = task_service.get_task_by_id(task_id, person.entity_id)
        if not task:
            return get_failure_response(message="Task not found.")
        
        task.completed = parsed_body['completed']
        task = task_service.save_task(task)
        return get_success_response(task=task.as_dict(), message="Task updated successfully.")

