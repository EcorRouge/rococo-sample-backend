"""
Unit tests for common/utils/version.py
"""
import pytest
from unittest.mock import patch, mock_open, MagicMock
import io


class TestVersionFunctions:
    """Tests for version.py functions."""

    def test_get_service_version(self):
        """Test get_service_version returns correct version."""
        from common.utils.version import get_service_version
        
        result = get_service_version()
        
        # Should return a string version
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_project_name(self):
        """Test get_project_name returns title-cased project name."""
        from common.utils.version import get_project_name
        
        result = get_project_name()
        
        # Should return a string project name
        assert isinstance(result, str)
        assert len(result) > 0
        # Should be title case
        assert result == result.title()

    @patch('builtins.print')
    def test_main_function(self, mock_print):
        """Test main function prints version info."""
        from common.utils.version import main, get_project_name, get_service_version
        
        main()
        
        # Verify print was called with version info
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert get_project_name() in call_args
        assert get_service_version() in call_args


class TestVersionModuleLoading:
    """Tests for version.py module loading behavior."""

    def test_pyproject_data_loaded(self):
        """Test that pyproject_data is loaded correctly."""
        from common.utils.version import pyproject_data
        
        # Should have tool.poetry section
        assert 'tool' in pyproject_data
        assert 'poetry' in pyproject_data['tool']
        assert 'version' in pyproject_data['tool']['poetry']
        assert 'name' in pyproject_data['tool']['poetry']

    def test_flask_toml_path_exists(self):
        """Test that FLASK_TOML path is constructed correctly."""
        from common.utils.version import FLASK_TOML, BASE_DIR
        import os
        
        # BASE_DIR should be the repo root
        assert os.path.isdir(BASE_DIR)
        # FLASK_TOML should point to flask/pyproject.toml
        assert FLASK_TOML.endswith('flask/pyproject.toml') or FLASK_TOML.endswith('flask\\pyproject.toml')
