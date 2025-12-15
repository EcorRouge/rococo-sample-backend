"""
Unit tests for flask/app/helpers/decorators.py
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from functools import wraps


class TestLoginRequired:
    """Tests for login_required decorator."""

    @patch('app.helpers.decorators.parse_access_token')
    @patch('app.helpers.decorators.create_person_from_token')
    @patch('app.helpers.decorators.create_email_from_token')
    @patch('app.helpers.decorators.request')
    @patch('app.helpers.decorators.g')
    def test_login_required_success(
        self, mock_g, mock_request, mock_create_email, mock_create_person, mock_parse_token
    ):
        """Test successful login with valid token."""
        from app.helpers.decorators import login_required

        # Setup mocks
        mock_request.headers = {'Authorization': 'Bearer valid-token'}
        mock_parse_token.return_value = {'sub': 'user-id'}
        mock_person = MagicMock()
        mock_person.entity_id = 'person-123'
        mock_create_person.return_value = mock_person
        mock_email = MagicMock()
        mock_create_email.return_value = mock_email

        # Create decorated function
        @login_required()
        def test_func(self):
            return "success"

        # Create mock self
        mock_self = MagicMock()
        result = test_func(mock_self)

        assert result == "success"
        mock_parse_token.assert_called_once_with('valid-token')

    @patch('app.helpers.decorators.request')
    @patch('app.helpers.decorators.get_failure_response')
    def test_login_required_no_auth_header(self, mock_failure_response, mock_request):
        """Test login_required with missing Authorization header."""
        from app.helpers.decorators import login_required

        mock_request.headers = {}
        mock_failure_response.return_value = "auth error"

        @login_required()
        def test_func(self):
            return "success"

        mock_self = MagicMock()
        result = test_func(mock_self)

        assert result == "auth error"
        mock_failure_response.assert_called_once_with(
            message="Authorization header not present", status_code=401
        )

    @patch('app.helpers.decorators.parse_access_token')
    @patch('app.helpers.decorators.request')
    @patch('app.helpers.decorators.get_failure_response')
    def test_login_required_invalid_token(
        self, mock_failure_response, mock_request, mock_parse_token
    ):
        """Test login_required with invalid token."""
        from app.helpers.decorators import login_required

        mock_request.headers = {'Authorization': 'Bearer invalid-token'}
        mock_parse_token.return_value = None
        mock_failure_response.return_value = "invalid token error"

        @login_required()
        def test_func(self):
            return "success"

        mock_self = MagicMock()
        result = test_func(mock_self)

        assert result == "invalid token error"
        mock_failure_response.assert_called_once_with(
            message='Access token is invalid', status_code=401
        )

    @patch('app.helpers.decorators.parse_access_token')
    @patch('app.helpers.decorators.request')
    @patch('app.helpers.decorators.abort')
    @patch('app.helpers.decorators.logger')
    def test_login_required_exception(
        self, mock_logger, mock_abort, mock_request, mock_parse_token
    ):
        """Test login_required handles exceptions."""
        from app.helpers.decorators import login_required

        mock_request.headers = {'Authorization': 'Bearer valid-token'}
        mock_parse_token.side_effect = Exception("Token parsing error")

        @login_required()
        def test_func(self):
            return "success"

        mock_self = MagicMock()
        test_func(mock_self)

        mock_abort.assert_called_once_with(500)

    @patch('app.helpers.decorators.parse_access_token')
    @patch('app.helpers.decorators.create_person_from_token')
    @patch('app.helpers.decorators.create_email_from_token')
    @patch('app.helpers.decorators.request')
    @patch('app.helpers.decorators.g')
    def test_login_required_injects_person_and_email(
        self, mock_g, mock_request, mock_create_email, mock_create_person, mock_parse_token
    ):
        """Test that person and email are injected when function parameters exist."""
        from app.helpers.decorators import login_required

        mock_request.headers = {'Authorization': 'Bearer valid-token'}
        mock_parse_token.return_value = {'sub': 'user-id'}
        mock_person = MagicMock()
        mock_person.entity_id = 'person-123'
        mock_create_person.return_value = mock_person
        mock_email = MagicMock()
        mock_create_email.return_value = mock_email

        received_args = {}

        @login_required()
        def test_func(self, person=None, email=None):
            received_args['person'] = person
            received_args['email'] = email
            return "success"

        mock_self = MagicMock()
        result = test_func(mock_self)

        assert result == "success"
        assert received_args['person'] == mock_person
        assert received_args['email'] == mock_email


class TestOrganizationRequired:
    """Tests for organization_required decorator."""

    @patch('app.helpers.decorators.OrganizationService')
    @patch('app.helpers.decorators.PersonOrganizationRoleService')
    @patch('app.helpers.decorators.request')
    @patch('app.helpers.decorators.g')
    @patch('app.helpers.decorators.config')
    def test_organization_required_success(
        self, mock_config, mock_g, mock_request, mock_por_service, mock_org_service
    ):
        """Test successful organization validation."""
        from app.helpers.decorators import organization_required

        mock_person = MagicMock()
        mock_person.entity_id = 'person-123'
        mock_g.person = mock_person
        type(mock_g).person = PropertyMock(return_value=mock_person)

        mock_request.headers = {'x-organization-id': 'org-123'}

        mock_org = MagicMock()
        mock_org.entity_id = 'org-123'
        mock_org_service.return_value.get_organization_by_id.return_value = mock_org

        mock_role = MagicMock()
        mock_role.role = 'member'
        mock_por_service.return_value.get_role_of_person_in_organization.return_value = mock_role

        @organization_required()
        def test_func(self):
            return "success"

        mock_self = MagicMock()
        result = test_func(mock_self)

        assert result == "success"

    @patch('app.helpers.decorators.request')
    @patch('app.helpers.decorators.get_failure_response')
    def test_organization_required_no_header(self, mock_failure_response, mock_request):
        """Test organization_required with missing x-organization-id header."""
        from app.helpers.decorators import organization_required

        mock_request.headers = {}
        mock_failure_response.return_value = "header missing error"

        @organization_required()
        def test_func(self):
            return "success"

        mock_self = MagicMock()
        result = test_func(mock_self)

        assert result == "header missing error"
        mock_failure_response.assert_called_once_with(
            message="x-organization-id header is not present", status_code=401
        )

    @patch('app.helpers.decorators.request')
    @patch('app.helpers.decorators.g')
    def test_organization_required_no_person(self, mock_g, mock_request):
        """Test organization_required without person raises RuntimeError."""
        from app.helpers.decorators import organization_required

        mock_request.headers = {'x-organization-id': 'org-123'}

        # Simulate getattr returning None for person
        def mock_getattr(obj, name, default=None):
            if name == 'person':
                return None
            return default

        with patch('app.helpers.decorators.getattr', mock_getattr):
            @organization_required()
            def test_func(self):
                return "success"

            mock_self = MagicMock()
            with pytest.raises(RuntimeError) as exc_info:
                test_func(mock_self)

            assert "login_required decorator" in str(exc_info.value)

    @patch('app.helpers.decorators.OrganizationService')
    @patch('app.helpers.decorators.PersonOrganizationRoleService')
    @patch('app.helpers.decorators.request')
    @patch('app.helpers.decorators.g')
    @patch('app.helpers.decorators.config')
    @patch('app.helpers.decorators.get_failure_response')
    def test_organization_required_invalid_org(
        self, mock_failure_response, mock_config, mock_g, mock_request, mock_por_service, mock_org_service
    ):
        """Test organization_required with invalid organization."""
        from app.helpers.decorators import organization_required

        mock_person = MagicMock()
        mock_person.entity_id = 'person-123'
        mock_g.person = mock_person
        type(mock_g).person = PropertyMock(return_value=mock_person)

        mock_request.headers = {'x-organization-id': 'invalid-org'}
        mock_org_service.return_value.get_organization_by_id.return_value = None
        mock_failure_response.return_value = "invalid org error"

        @organization_required()
        def test_func(self):
            return "success"

        mock_self = MagicMock()
        result = test_func(mock_self)

        assert result == "invalid org error"
        mock_failure_response.assert_called_once_with(
            message='Organization ID is invalid', status_code=403
        )

    @patch('app.helpers.decorators.OrganizationService')
    @patch('app.helpers.decorators.PersonOrganizationRoleService')
    @patch('app.helpers.decorators.request')
    @patch('app.helpers.decorators.g')
    @patch('app.helpers.decorators.config')
    @patch('app.helpers.decorators.get_failure_response')
    def test_organization_required_user_not_in_org(
        self, mock_failure_response, mock_config, mock_g, mock_request, mock_por_service, mock_org_service
    ):
        """Test organization_required when user is not in organization."""
        from app.helpers.decorators import organization_required

        mock_person = MagicMock()
        mock_person.entity_id = 'person-123'
        mock_g.person = mock_person
        type(mock_g).person = PropertyMock(return_value=mock_person)

        mock_request.headers = {'x-organization-id': 'org-123'}

        mock_org = MagicMock()
        mock_org.entity_id = 'org-123'
        mock_org_service.return_value.get_organization_by_id.return_value = mock_org

        mock_por_service.return_value.get_role_of_person_in_organization.return_value = None
        mock_failure_response.return_value = "not authorized error"

        @organization_required()
        def test_func(self):
            return "success"

        mock_self = MagicMock()
        result = test_func(mock_self)

        assert result == "not authorized error"
        mock_failure_response.assert_called_once_with(
            message="User is not authorized to use this organization.", status_code=401
        )

    @patch('app.helpers.decorators.OrganizationService')
    @patch('app.helpers.decorators.PersonOrganizationRoleService')
    @patch('app.helpers.decorators.request')
    @patch('app.helpers.decorators.g')
    @patch('app.helpers.decorators.config')
    @patch('app.helpers.decorators.get_failure_response')
    def test_organization_required_with_roles_unauthorized(
        self, mock_failure_response, mock_config, mock_g, mock_request, mock_por_service, mock_org_service
    ):
        """Test organization_required with specific roles - user unauthorized."""
        from app.helpers.decorators import organization_required

        mock_person = MagicMock()
        mock_person.entity_id = 'person-123'
        mock_g.person = mock_person
        type(mock_g).person = PropertyMock(return_value=mock_person)

        mock_request.headers = {'x-organization-id': 'org-123'}

        mock_org = MagicMock()
        mock_org.entity_id = 'org-123'
        mock_org_service.return_value.get_organization_by_id.return_value = mock_org

        mock_role = MagicMock()
        mock_role.role = 'member'
        mock_por_service.return_value.get_role_of_person_in_organization.return_value = mock_role

        mock_failure_response.return_value = "role unauthorized error"

        @organization_required(with_roles=['admin', 'owner'])
        def test_func(self):
            return "success"

        mock_self = MagicMock()
        result = test_func(mock_self)

        assert result == "role unauthorized error"

    @patch('app.helpers.decorators.OrganizationService')
    @patch('app.helpers.decorators.PersonOrganizationRoleService')
    @patch('app.helpers.decorators.request')
    @patch('app.helpers.decorators.g')
    @patch('app.helpers.decorators.config')
    def test_organization_required_injects_role_and_org(
        self, mock_config, mock_g, mock_request, mock_por_service, mock_org_service
    ):
        """Test that role and organization are injected when function parameters exist."""
        from app.helpers.decorators import organization_required

        mock_person = MagicMock()
        mock_person.entity_id = 'person-123'
        mock_g.person = mock_person
        type(mock_g).person = PropertyMock(return_value=mock_person)

        mock_request.headers = {'x-organization-id': 'org-123'}

        mock_org = MagicMock()
        mock_org.entity_id = 'org-123'
        mock_org_service.return_value.get_organization_by_id.return_value = mock_org

        mock_role = MagicMock()
        mock_role.role = 'admin'
        mock_por_service.return_value.get_role_of_person_in_organization.return_value = mock_role

        received_args = {}

        @organization_required()
        def test_func(self, role=None, organization=None):
            received_args['role'] = role
            received_args['organization'] = organization
            return "success"

        mock_self = MagicMock()
        result = test_func(mock_self)

        assert result == "success"
        assert received_args['role'] == mock_role
        assert received_args['organization'] == mock_org
