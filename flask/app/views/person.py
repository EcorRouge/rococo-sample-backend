from flask_restx import Namespace, Resource
from flask import request
from app.helpers.response import get_success_response, get_failure_response, parse_request_body, validate_required_fields
from app.helpers.decorators import login_required
from common.app_config import config
from common.services import PersonService

# Create the person blueprint
person_api = Namespace('person', description="Person-related APIs")


@person_api.route('/me')
class Me(Resource):
    
    @login_required()
    def get(self, person):
        return get_success_response(person=person)
        
    @login_required()
    def put(self, person):
        parsed_body = parse_request_body(request, ['first_name', 'last_name'])
        
        # Validate required fields
        if not parsed_body.get('first_name') and not parsed_body.get('last_name'):
            return get_failure_response("At least one field (first_name or last_name) must be provided", 400)
        
        # Initialize person service
        person_service = PersonService(config)
        
        # Update only the fields that were provided
        if 'first_name' in parsed_body:
            person.first_name = parsed_body['first_name']
        
        if 'last_name' in parsed_body:
            person.last_name = parsed_body['last_name']
        
        # Save the updated person
        updated_person = person_service.save_person(person)
        
        return get_success_response(
            message="Profile updated successfully", 
            person=updated_person
        )