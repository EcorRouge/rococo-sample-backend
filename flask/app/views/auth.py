from flask_restx import Namespace, Resource
from flask import request
from app.helpers.response import get_success_response, get_failure_response, parse_request_body, validate_required_fields
from common.app_config import config
from common.services import AuthService, PersonService, OAuthClient

# Create the auth blueprint
auth_api = Namespace('auth', description="Auth related APIs")


@auth_api.route('/test')
class Test(Resource):
    def get(self):
        login_data = {
            "username": "test",
            "password": "test"
        }
        return get_success_response(**login_data)


@auth_api.route('/signup')
class Signup(Resource):
    @auth_api.expect(
        {'type': 'object', 'properties': {
            'first_name': {'type': 'string'},
            'last_name': {'type': 'string'},
            'email_address': {'type': 'string'}
        }}
    )
    def post(self):
        parsed_body = parse_request_body(request, ['first_name', 'last_name', 'email_address'])
        validate_required_fields(parsed_body)

        auth_service = AuthService(config)

        auth_service.signup(
            parsed_body['email_address'],
            parsed_body['first_name'],
            parsed_body['last_name']
        )
        return get_success_response(message="User signed up successfully and verification email is sent.")


@auth_api.route('/login')
class Login(Resource):
    @auth_api.expect(
        {'type': 'object', 'properties': {
            'email': {'type': 'string'},
            'password': {'type': 'string'}
        }}
    )
    def post(self):
        parsed_body = parse_request_body(request, ['email', 'password'])
        validate_required_fields(parsed_body)

        auth_service = AuthService(config)
        access_token, expiry = auth_service.login_user_by_email_password(
            parsed_body['email'], 
            parsed_body['password']
        )

        person_service = PersonService(config)
        person = person_service.get_person_by_email_address(email_address=parsed_body['email'])

        return get_success_response(person=person.as_dict(), access_token=access_token, expiry=expiry)


@auth_api.route('/forgot_password', doc=dict(description="Send reset password link"))
class ForgotPassword(Resource):
    @auth_api.expect(
        {'type': 'object', 'properties': {
            'email': {'type': 'string'}
        }}
    )
    def post(self):
        parsed_body = parse_request_body(request, ['email'])
        validate_required_fields(parsed_body)

        auth_service = AuthService(config)
        auth_service.trigger_forgot_password_email(parsed_body.get('email'))

        return get_success_response(message="Password reset email sent successfully.")


@auth_api.route(
    '/reset_password/<string:token>/<string:uidb64>',
    doc=dict(description="Update the password using reset password link")
)
class ResetPassword(Resource):
    @auth_api.expect(
        {'type': 'object', 'properties': {
            'password': {'type': 'string'}
        }}
    )
    def post(self, token, uidb64):
        parsed_body = parse_request_body(request, ['password'])
        validate_required_fields(parsed_body)

        auth_service = AuthService(config)
        access_token, expiry, person_obj = auth_service.reset_user_password(token, uidb64, parsed_body.get('password'))
        return get_success_response(
            message="Your password has been updated!", 
            access_token=access_token, 
            expiry=expiry,
            person=person_obj.as_dict()
        )


@auth_api.route('/<string:provider>/exchange')
class OAuthExchange(Resource):
    def post(self, provider):
        """
        Exchange OAuth authorization code for access token and user info
        
        Args:
            provider: OAuth provider (google, microsoft)
        """
        parsed_body = parse_request_body(
            request,
            ['code', 'redirect_uri', 'code_verifier']
        )
        validate_required_fields(parsed_body)

        oauth_client = OAuthClient(config)
        auth_service = AuthService(config)

        try:
            # Token exchange + user info retrieval
            if provider == "google":
                token_response = oauth_client.get_google_token(
                    parsed_body['code'],
                    parsed_body['redirect_uri'],
                    parsed_body['code_verifier']
                )
                user_info = oauth_client.get_google_user_info(token_response['access_token'])

            elif provider == "microsoft":
                token_response = oauth_client.get_microsoft_token(
                    parsed_body['code'],
                    parsed_body['redirect_uri'],
                    parsed_body['code_verifier']
                )
                user_info = oauth_client.get_microsoft_user_info(token_response['access_token'])

            else:
                return get_failure_response(message=f"Unsupported provider: {provider}")

            # Normalize name + email
            if provider == "google":
                email = user_info.get('email')
                name = user_info.get('name', '')

            elif provider == "microsoft":
                email = user_info.get('email')
                name = user_info.get('name', '')

            if not email:
                return get_failure_response(message=f"{provider.capitalize()} user info does not contain email.")

            name_parts = name.split(' ', 1)
            first_name, last_name = name_parts[0], name_parts[1] if len(name_parts) > 1 else ""

            # Login or create user
            access_token, expiry, person = auth_service.login_user_by_oauth(
                email, first_name, last_name,
                provider=provider,
                provider_data=user_info
            )

            return get_success_response(person=person.as_dict(), access_token=access_token, expiry=expiry)

        except Exception as e:
            return get_failure_response(message=f"OAuth authentication failed: {str(e)}")
