from flask_restx import Namespace, Resource
from flask import request, g
from app.helpers.response import get_success_response, get_failure_response, parse_request_body, validate_required_fields
from app.helpers.decorators import login_required
from common.app_config import config
from common.services.task import TaskService
from common.models.task import Task
from datetime import datetime

task_api = Namespace('tasks', description="Task management APIs")

@task_api.route('/')
class Tasks(Resource):
    
    @login_required()
    def get(self, person):
        """Get all tasks for the logged-in user"""
        task_service = TaskService(config)
        
        # Get filter parameter
        filter_param = request.args.get('filter', 'all')
        
        if filter_param == 'completed':
            tasks = task_service.get_completed_tasks_by_person_id(person.entity_id)
        elif filter_param == 'incomplete':
            tasks = task_service.get_tasks_by_person_id(person.entity_id, include_completed=False)
        else:  # 'all' is default
            tasks = task_service.get_tasks_by_person_id(person.entity_id)
            
        tasks_list = [task.as_dict() for task in tasks]
        return get_success_response(tasks=tasks_list)
    
    @login_required()
    def post(self, person):
        """Create a new task"""
        parsed_body = parse_request_body(request, ['title', 'description', 'due_date', 'priority'])
        validate_required_fields({'title': parsed_body.get('title')})
        
        task_service = TaskService(config)
        
        # Convert due_date string to datetime if provided
        due_date = None
        if parsed_body.get('due_date'):
            try:
                due_date = datetime.fromisoformat(parsed_body.get('due_date'))
            except ValueError:
                return get_failure_response("Invalid date format for due_date. Use ISO format (YYYY-MM-DDTHH:MM:SS).")
        
        task = Task(
            person_id=person.entity_id,
            title=parsed_body.get('title'),
            description=parsed_body.get('description'),
            due_date=due_date,
            priority=int(parsed_body.get('priority', 0))
        )
        
        task = task_service.save_task(task)
        return get_success_response(task=task.as_dict())

@task_api.route('/<string:task_id>')
class TaskItem(Resource):
    
    @login_required()
    def get(self, task_id, person):
        """Get a specific task"""
        task_service = TaskService(config)
        task = task_service.get_task_by_id(task_id)
        
        if not task:
            return get_failure_response("Task not found", 404)
            
        # Verify the task belongs to the logged-in user
        if task.person_id != person.entity_id:
            return get_failure_response("Access denied", 403)
            
        return get_success_response(task=task.as_dict())
    
    @login_required()
    def put(self, task_id, person):
        """Update a task"""
        task_service = TaskService(config)
        task = task_service.get_task_by_id(task_id)
        
        if not task:
            return get_failure_response("Task not found", 404)
            
        # Verify the task belongs to the logged-in user
        if task.person_id != person.entity_id:
            return get_failure_response("Access denied", 403)
        
        parsed_body = parse_request_body(request, ['title', 'description', 'is_completed', 'due_date', 'priority'])
        
        # Update task fields if provided
        if 'title' in parsed_body:
            task.title = parsed_body.get('title')
        if 'description' in parsed_body:
            task.description = parsed_body.get('description')
        if 'is_completed' in parsed_body:
            is_completed = parsed_body.get('is_completed')
            if isinstance(is_completed, str):
                is_completed = is_completed.lower() == 'true'
            task.is_completed = is_completed
            task.completed_at = datetime.now() if is_completed else None
        if 'due_date' in parsed_body:
            due_date_str = parsed_body.get('due_date')
            if due_date_str:
                try:
                    task.due_date = datetime.fromisoformat(due_date_str)
                except ValueError:
                    return get_failure_response("Invalid date format for due_date. Use ISO format (YYYY-MM-DDTHH:MM:SS).")
            else:
                task.due_date = None
        if 'priority' in parsed_body:
            task.priority = int(parsed_body.get('priority', 0))
        
        task = task_service.save_task(task)
        return get_success_response(task=task.as_dict())
    
    @login_required()
    def delete(self, task_id, person):
        """Delete a task"""
        task_service = TaskService(config)
        task = task_service.get_task_by_id(task_id)
        
        if not task:
            return get_failure_response("Task not found", 404)
            
        # Verify the task belongs to the logged-in user
        if task.person_id != person.entity_id:
            return get_failure_response("Access denied", 403)
            
        if task_service.delete_task(task_id):
            return get_success_response(message="Task deleted successfully")
        else:
            return get_failure_response("Failed to delete task")

@task_api.route('/<string:task_id>/toggle')
class TaskToggle(Resource):
    
    @login_required()
    def post(self, task_id, person):
        """Toggle task completion status"""
        task_service = TaskService(config)
        task = task_service.get_task_by_id(task_id)
        
        if not task:
            return get_failure_response("Task not found", 404)
            
        # Verify the task belongs to the logged-in user
        if task.person_id != person.entity_id:
            return get_failure_response("Access denied", 403)
            
        # Toggle completion status
        updated_task = task_service.update_task_status(task_id, not task.is_completed)
        return get_success_response(task=updated_task.as_dict())