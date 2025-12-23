from flask_restx import Namespace, Resource
from app.helpers.response import get_success_response, get_failure_response, parse_request_body
from app.helpers.decorators import login_required

from common.app_config import config
from common.services import PersonService
from common.helpers.exceptions import APIException
from flask import request

# Create the person blueprint
person_api = Namespace('person', description="Person-related APIs")


# API schema definition for updating profile name
UPDATE_PROFILE_SCHEMA = {
    'type': 'object',
    'properties': {
        'first_name': {'type': 'string'},
        'last_name': {'type': 'string'}
    }
}

@person_api.route('/me')
class Me(Resource):
    
    @login_required()
    def get(self, person):
        return get_success_response(person=person.as_dict())

    @login_required()
    @person_api.expect(UPDATE_PROFILE_SCHEMA)
    def put(self, person):
        """Update person's first and last name"""
        try:
            name_fields = ['first_name', 'last_name']
            parsed_body = parse_request_body(request, name_fields)

            person_service = PersonService(config)
            
            # Update fields if provided and not empty
            updated = False
            if parsed_body.get('first_name'):
                person.first_name = parsed_body['first_name'].strip()
                updated = True
            if parsed_body.get('last_name'):
                person.last_name = parsed_body['last_name'].strip()
                updated = True
            
            if not updated:
                return get_failure_response(
                    message="At least one of 'first_name' or 'last_name' must be provided.",
                    status_code=400
                )
            
            person = person_service.save_person(person)
            return get_success_response(
                message="Profile name updated successfully.",
                person=person.as_dict()
            )
            
        except APIException as e:
            return get_failure_response(message=str(e), status_code=400)
        except Exception as e:
            from common.app_logger import logger
            import traceback
            logger.error(f"Error updating person profile: {str(e)}\n{traceback.format_exc()}")
            return get_failure_response(
                message="An error occurred while updating your profile.",
                status_code=500
            )