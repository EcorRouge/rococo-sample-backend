"""
Comprehensive unit tests for adw_plan_build_test_iso.py

Tests cover:
1. Command-line argument handling
2. Main workflow orchestration (plan -> build -> test)
3. ADW ID extraction logic from state files
4. Error handling at each workflow step
5. Subprocess execution and exit codes
"""

import sys
import os
import json
import pytest
import importlib.util
from unittest.mock import MagicMock, patch, mock_open, call
from subprocess import CompletedProcess

# Load the target module from the parent repository
# This test file is at: trees/1308e31d/tests/adws/test_adw_plan_build_test_iso.py
# Target file is at: adws/adw_plan_build_test_iso.py
# So we need to go up 4 levels: ../../../.. from this file
PARENT_REPO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
ADWS_PATH = os.path.join(PARENT_REPO_PATH, 'adws')
TARGET_FILE = os.path.join(ADWS_PATH, 'adw_plan_build_test_iso.py')

# Import the module under test using importlib
# First, add the ADWS path to sys.path so adw_modules can be imported
sys.path.insert(0, ADWS_PATH)

spec = importlib.util.spec_from_file_location("adw_plan_build_test_iso", TARGET_FILE)
adw_plan_build_test_iso = importlib.util.module_from_spec(spec)
sys.modules['adw_plan_build_test_iso'] = adw_plan_build_test_iso
spec.loader.exec_module(adw_plan_build_test_iso)


class TestCommandLineArguments:
    """Test command-line argument parsing and validation."""

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    def test_missing_issue_number_exits_with_code_1(self, mock_print, mock_load_dotenv):
        """Test that missing issue number argument causes exit with code 1."""
        with patch.object(sys, 'argv', ['script.py']):
            with patch.object(sys, 'exit', side_effect=SystemExit(1)) as mock_exit:
                with pytest.raises(SystemExit):
                    adw_plan_build_test_iso.main()

                mock_print.assert_called_with("Usage: uv run adws/adw_plan_build_test_iso.py <issue-number> [adw-id]")
                mock_exit.assert_called_once_with(1)

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('subprocess.run')
    def test_valid_issue_number_proceeds_to_planning(self, mock_subprocess, mock_load_dotenv):
        """Test that valid issue number proceeds to planning step."""
        # Mock planning failure to exit early
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=1)

        with patch.object(sys, 'argv', ['script.py', '123']):
            with patch.object(sys, 'exit') as mock_exit:
                adw_plan_build_test_iso.main()

                # Verify subprocess was called (planning step)
                assert mock_subprocess.called
                mock_exit.assert_called_with(1)


class TestStep1Planning:
    """Test Step 1 (Planning) execution."""

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('subprocess.run')
    def test_planning_failure_exits_with_code_1(self, mock_subprocess, mock_print, mock_load_dotenv):
        """Test that planning failure exits with code 1."""
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=2)

        with patch.object(sys, 'argv', ['script.py', '123']):
            with patch.object(sys, 'exit') as mock_exit:
                adw_plan_build_test_iso.main()

                # Verify error message and exit
                calls = [call for call in mock_print.call_args_list if '❌ Planning failed' in str(call)]
                assert len(calls) > 0
                mock_exit.assert_called_with(1)

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_planning_success_proceeds_to_adw_id_extraction(self, mock_subprocess, mock_exists, mock_load_dotenv):
        """Test that successful planning proceeds to ADW ID extraction."""
        # Planning succeeds
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)
        # No agents directory (will fail at ADW ID extraction)
        mock_exists.return_value = False

        with patch.object(sys, 'argv', ['script.py', '123']):
            with patch.object(sys, 'exit') as mock_exit:
                adw_plan_build_test_iso.main()

                # Should exit with 1 due to missing ADW ID
                mock_exit.assert_called_with(1)

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('subprocess.run')
    def test_planning_command_without_adw_id(self, mock_subprocess, mock_load_dotenv):
        """Test planning command construction without ADW ID."""
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=1)

        with patch.object(sys, 'argv', ['script.py', '123']):
            with patch.object(sys, 'exit'):
                adw_plan_build_test_iso.main()

                # Check the first subprocess call (planning)
                first_call = mock_subprocess.call_args_list[0]
                args = first_call[0][0]

                assert args[0] == sys.executable
                assert 'adw_plan_iso.py' in args[1]
                assert args[2] == '123'
                assert len(args) == 3  # No ADW ID

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('subprocess.run')
    def test_planning_command_with_adw_id(self, mock_subprocess, mock_load_dotenv):
        """Test planning command construction with ADW ID."""
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=1)

        with patch.object(sys, 'argv', ['script.py', '123', 'test-adw-id']):
            with patch.object(sys, 'exit'):
                adw_plan_build_test_iso.main()

                # Check the first subprocess call (planning)
                first_call = mock_subprocess.call_args_list[0]
                args = first_call[0][0]

                assert args[0] == sys.executable
                assert 'adw_plan_iso.py' in args[1]
                assert args[2] == '123'
                assert args[3] == 'test-adw-id'


class TestADWIDExtraction:
    """Test ADW ID extraction logic from state files."""

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('subprocess.run')
    def test_adw_id_provided_skips_extraction(self, mock_subprocess, mock_load_dotenv):
        """Test that provided ADW ID skips extraction logic."""
        # Mock all three subprocess calls to succeed
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        with patch.object(sys, 'argv', ['script.py', '123', 'provided-adw-id']):
            adw_plan_build_test_iso.main()

            # Should have 3 subprocess calls (plan, build, test)
            assert mock_subprocess.call_count == 3

            # Check build command has the provided ADW ID
            build_call = mock_subprocess.call_args_list[1]
            build_args = build_call[0][0]
            assert 'provided-adw-id' in build_args

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_no_agents_directory_exits_with_error(self, mock_subprocess, mock_exists, mock_print, mock_load_dotenv):
        """Test that missing agents directory causes error."""
        # Planning succeeds
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)
        # No agents directory
        mock_exists.return_value = False

        with patch.object(sys, 'argv', ['script.py', '123']):
            with patch.object(sys, 'exit') as mock_exit:
                adw_plan_build_test_iso.main()

                # Should print error and exit
                calls = [call for call in mock_print.call_args_list if '❌ Error: Could not find ADW ID' in str(call)]
                assert len(calls) > 0
                mock_exit.assert_called_with(1)

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('subprocess.run')
    def test_empty_agents_directory_exits_with_error(self, mock_subprocess, mock_listdir, mock_exists, mock_print, mock_load_dotenv):
        """Test that empty agents directory causes error."""
        # Planning succeeds
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)
        # Empty agents directory
        mock_exists.return_value = True
        mock_listdir.return_value = []

        with patch.object(sys, 'argv', ['script.py', '123']):
            with patch.object(sys, 'exit') as mock_exit:
                adw_plan_build_test_iso.main()

                # Should print error and exit
                calls = [call for call in mock_print.call_args_list if '❌ Error: Could not find ADW ID' in str(call)]
                assert len(calls) > 0
                mock_exit.assert_called_with(1)

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('os.path.getmtime')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('subprocess.run')
    def test_adw_id_extracted_from_matching_state_file(self, mock_subprocess, mock_json_load, mock_file, mock_getmtime, mock_listdir, mock_exists, mock_print, mock_load_dotenv):
        """Test successful ADW ID extraction from state file with matching issue number."""
        # Planning succeeds
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        # Mock file system
        mock_exists.side_effect = lambda path: True  # All paths exist
        mock_listdir.return_value = ['adw-123']
        mock_getmtime.return_value = 1234567890

        # Mock state file content
        mock_json_load.return_value = {"issue_number": "123", "adw_id": "adw-123"}

        with patch.object(sys, 'argv', ['script.py', '123']):
            adw_plan_build_test_iso.main()

            # Should print found message
            calls = [call for call in mock_print.call_args_list if 'Found ADW ID from Step 1: adw-123' in str(call)]
            assert len(calls) > 0

            # Should have 3 subprocess calls (plan, build, test)
            assert mock_subprocess.call_count == 3

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('os.path.getmtime')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('subprocess.run')
    def test_non_matching_issue_number_continues_search(self, mock_subprocess, mock_json_load, mock_file, mock_getmtime, mock_listdir, mock_exists, mock_print, mock_load_dotenv):
        """Test that non-matching issue number continues search."""
        # Planning succeeds
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        # Mock file system
        mock_exists.side_effect = lambda path: True
        mock_listdir.return_value = ['adw-456']
        mock_getmtime.return_value = 1234567890

        # Mock state file with different issue number
        mock_json_load.return_value = {"issue_number": "456", "adw_id": "adw-456"}

        with patch.object(sys, 'argv', ['script.py', '123']):
            with patch.object(sys, 'exit') as mock_exit:
                adw_plan_build_test_iso.main()

                # Should exit with error (no matching ADW ID found)
                mock_exit.assert_called_with(1)

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('os.path.getmtime')
    @patch('builtins.open')
    @patch('subprocess.run')
    def test_multiple_state_files_uses_most_recent(self, mock_subprocess, mock_file, mock_getmtime, mock_listdir, mock_exists, mock_print, mock_load_dotenv):
        """Test that most recent state file is checked first."""
        # Planning succeeds
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        # Mock file system with multiple agent directories
        mock_exists.side_effect = lambda path: True
        mock_listdir.return_value = ['adw-old', 'adw-new']

        # Mock modification times (adw-new is newer)
        def getmtime_side_effect(path):
            if 'adw-new' in path:
                return 2000000000
            return 1000000000
        mock_getmtime.side_effect = getmtime_side_effect

        # Mock file opening and json loading
        def open_side_effect(path, mode='r'):
            mock_file_obj = MagicMock()
            mock_file_obj.name = path
            mock_file_obj.__enter__ = MagicMock(return_value=mock_file_obj)
            mock_file_obj.__exit__ = MagicMock(return_value=False)

            if 'adw-new' in path:
                mock_file_obj.read.return_value = '{"issue_number": "123", "adw_id": "adw-new"}'
            else:
                mock_file_obj.read.return_value = '{"issue_number": "456", "adw_id": "adw-old"}'
            return mock_file_obj

        mock_file.side_effect = open_side_effect

        with patch.object(sys, 'argv', ['script.py', '123']):
            adw_plan_build_test_iso.main()

            # Should find the newer ADW ID
            calls = [call for call in mock_print.call_args_list if 'Found ADW ID from Step 1: adw-new' in str(call)]
            assert len(calls) > 0

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('os.path.getmtime')
    @patch('builtins.open')
    @patch('subprocess.run')
    def test_malformed_json_continues_search(self, mock_subprocess, mock_file, mock_getmtime, mock_listdir, mock_exists, mock_print, mock_load_dotenv):
        """Test that malformed JSON in state file is handled gracefully."""
        # Planning succeeds
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        # Mock file system
        mock_exists.side_effect = lambda path: True
        mock_listdir.return_value = ['adw-bad', 'adw-good']

        # Mock modification times (adw-bad is newer but has malformed JSON)
        def getmtime_side_effect(path):
            if 'adw-bad' in path:
                return 2000000000
            return 1000000000
        mock_getmtime.side_effect = getmtime_side_effect

        # Mock file opening - first file raises JSONDecodeError, second succeeds
        call_count = [0]
        def open_side_effect(path, mode='r'):
            mock_file_obj = MagicMock()
            mock_file_obj.name = path
            mock_file_obj.__enter__ = MagicMock(return_value=mock_file_obj)
            mock_file_obj.__exit__ = MagicMock(return_value=False)

            if 'adw-bad' in path:
                # First call returns invalid JSON that will cause json.load to raise
                mock_file_obj.read.return_value = '{invalid json'
            else:
                mock_file_obj.read.return_value = '{"issue_number": "123", "adw_id": "adw-good"}'
            return mock_file_obj

        mock_file.side_effect = open_side_effect

        with patch.object(sys, 'argv', ['script.py', '123']):
            adw_plan_build_test_iso.main()

            # Should find the good ADW ID
            calls = [call for call in mock_print.call_args_list if 'Found ADW ID from Step 1: adw-good' in str(call)]
            assert len(calls) > 0

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('os.path.getmtime')
    @patch('builtins.open')
    @patch('subprocess.run')
    def test_os_error_reading_file_continues_search(self, mock_subprocess, mock_file, mock_getmtime, mock_listdir, mock_exists, mock_print, mock_load_dotenv):
        """Test that OS error reading state file is handled gracefully."""
        # Planning succeeds
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        # Mock file system
        mock_exists.side_effect = lambda path: True
        mock_listdir.return_value = ['adw-error']
        mock_getmtime.return_value = 1234567890

        # Mock file open to raise OSError
        mock_file.side_effect = OSError("Cannot read file")

        with patch.object(sys, 'argv', ['script.py', '123']):
            with patch.object(sys, 'exit') as mock_exit:
                adw_plan_build_test_iso.main()

                # Should exit with error (no valid state file found)
                mock_exit.assert_called_with(1)

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('os.path.getmtime')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('subprocess.run')
    def test_missing_issue_number_in_state_continues_search(self, mock_subprocess, mock_json_load, mock_file, mock_getmtime, mock_listdir, mock_exists, mock_print, mock_load_dotenv):
        """Test that missing issue_number field in state is handled gracefully."""
        # Planning succeeds
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        # Mock file system
        mock_exists.side_effect = lambda path: True
        mock_listdir.return_value = ['adw-incomplete']
        mock_getmtime.return_value = 1234567890

        # Mock state file without issue_number field
        mock_json_load.return_value = {"adw_id": "adw-incomplete"}

        with patch.object(sys, 'argv', ['script.py', '123']):
            with patch.object(sys, 'exit') as mock_exit:
                adw_plan_build_test_iso.main()

                # Should exit with error (no valid state file found)
                mock_exit.assert_called_with(1)


class TestStep2Building:
    """Test Step 2 (Building) execution."""

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('subprocess.run')
    def test_building_failure_exits_with_code_1(self, mock_subprocess, mock_print, mock_load_dotenv):
        """Test that building failure exits with code 1."""
        # Planning succeeds, building fails
        def subprocess_side_effect(cmd):
            if 'adw_plan_iso.py' in cmd[1]:
                return CompletedProcess(args=[], returncode=0)
            elif 'adw_build_iso.py' in cmd[1]:
                return CompletedProcess(args=[], returncode=3)
            return CompletedProcess(args=[], returncode=0)

        mock_subprocess.side_effect = subprocess_side_effect

        with patch.object(sys, 'argv', ['script.py', '123', 'test-adw-id']):
            with patch.object(sys, 'exit') as mock_exit:
                adw_plan_build_test_iso.main()

                # Verify error message and exit
                calls = [call for call in mock_print.call_args_list if '❌ Building failed' in str(call)]
                assert len(calls) > 0
                mock_exit.assert_called_with(1)

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('subprocess.run')
    def test_building_success_proceeds_to_testing(self, mock_subprocess, mock_load_dotenv):
        """Test that successful building proceeds to testing."""
        # All steps succeed
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        with patch.object(sys, 'argv', ['script.py', '123', 'test-adw-id']):
            adw_plan_build_test_iso.main()

            # Should have 3 subprocess calls (plan, build, test)
            assert mock_subprocess.call_count == 3

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('subprocess.run')
    def test_building_command_construction(self, mock_subprocess, mock_load_dotenv):
        """Test building command construction with issue number and ADW ID."""
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        with patch.object(sys, 'argv', ['script.py', '123', 'test-adw-id']):
            adw_plan_build_test_iso.main()

            # Check the second subprocess call (building)
            build_call = mock_subprocess.call_args_list[1]
            args = build_call[0][0]

            assert args[0] == sys.executable
            assert 'adw_build_iso.py' in args[1]
            assert args[2] == '123'
            assert args[3] == 'test-adw-id'


class TestStep3Testing:
    """Test Step 3 (Testing) execution."""

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('subprocess.run')
    def test_testing_failure_prints_warning_no_exit(self, mock_subprocess, mock_print, mock_load_dotenv):
        """Test that testing failure prints warning but does not exit."""
        # Planning and building succeed, testing fails
        def subprocess_side_effect(cmd):
            if 'adw_test_iso.py' in cmd[1]:
                return CompletedProcess(args=[], returncode=5)
            return CompletedProcess(args=[], returncode=0)

        mock_subprocess.side_effect = subprocess_side_effect

        with patch.object(sys, 'argv', ['script.py', '123', 'test-adw-id']):
            adw_plan_build_test_iso.main()

            # Should print warning (not error)
            calls = [call for call in mock_print.call_args_list if '⚠️  Testing completed with some failures' in str(call)]
            assert len(calls) > 0

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('subprocess.run')
    def test_testing_success_prints_success_message(self, mock_subprocess, mock_print, mock_load_dotenv):
        """Test that testing success prints success message."""
        # All steps succeed
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        with patch.object(sys, 'argv', ['script.py', '123', 'test-adw-id']):
            adw_plan_build_test_iso.main()

            # Should print success message
            calls = [call for call in mock_print.call_args_list if '✅ All steps completed successfully!' in str(call)]
            assert len(calls) > 0

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('subprocess.run')
    def test_testing_command_construction(self, mock_subprocess, mock_load_dotenv):
        """Test testing command construction with issue number and ADW ID."""
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        with patch.object(sys, 'argv', ['script.py', '123', 'test-adw-id']):
            adw_plan_build_test_iso.main()

            # Check the third subprocess call (testing)
            test_call = mock_subprocess.call_args_list[2]
            args = test_call[0][0]

            assert args[0] == sys.executable
            assert 'adw_test_iso.py' in args[1]
            assert args[2] == '123'
            assert args[3] == 'test-adw-id'


class TestMainWorkflow:
    """Test complete workflow execution paths."""

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('subprocess.run')
    def test_complete_workflow_all_steps_succeed(self, mock_subprocess, mock_print, mock_load_dotenv):
        """Test complete workflow with all steps succeeding."""
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        with patch.object(sys, 'argv', ['script.py', '123', 'test-adw-id']):
            adw_plan_build_test_iso.main()

            # Verify all 3 steps were called
            assert mock_subprocess.call_count == 3

            # Verify step headers were printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any('STEP 1: Planning' in call for call in print_calls)
            assert any('STEP 2: Building' in call for call in print_calls)
            assert any('STEP 3: Testing' in call for call in print_calls)

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('os.path.getmtime')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('subprocess.run')
    def test_complete_workflow_with_adw_id_extraction(self, mock_subprocess, mock_json_load, mock_file, mock_getmtime, mock_listdir, mock_exists, mock_load_dotenv):
        """Test complete workflow with ADW ID extraction."""
        # All subprocess calls succeed
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        # Mock ADW ID extraction
        mock_exists.side_effect = lambda path: True
        mock_listdir.return_value = ['extracted-adw-id']
        mock_getmtime.return_value = 1234567890
        mock_json_load.return_value = {"issue_number": "123", "adw_id": "extracted-adw-id"}

        with patch.object(sys, 'argv', ['script.py', '123']):
            adw_plan_build_test_iso.main()

            # Should have 3 subprocess calls
            assert mock_subprocess.call_count == 3

            # Verify build command uses extracted ADW ID
            build_call = mock_subprocess.call_args_list[1]
            build_args = build_call[0][0]
            assert 'extracted-adw-id' in build_args

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('subprocess.run')
    def test_workflow_with_different_issue_number(self, mock_subprocess, mock_print, mock_load_dotenv):
        """Test workflow with different issue number."""
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        with patch.object(sys, 'argv', ['script.py', '456', 'workflow-adw-id']):
            adw_plan_build_test_iso.main()

            # Verify all commands use the correct issue number
            for call_item in mock_subprocess.call_args_list:
                args = call_item[0][0]
                assert '456' in args

    @patch('adw_plan_build_test_iso.load_dotenv')
    def test_load_dotenv_called_at_start(self, mock_load_dotenv):
        """Test that load_dotenv is called at the start of main."""
        with patch.object(sys, 'argv', ['script.py']):
            with patch.object(sys, 'exit', side_effect=SystemExit(1)):
                try:
                    adw_plan_build_test_iso.main()
                except SystemExit:
                    pass

        mock_load_dotenv.assert_called_once()


class TestEnvironmentAndPaths:
    """Test environment setup and path construction."""

    def test_script_dir_constant(self):
        """Test that SCRIPT_DIR is correctly set."""
        # SCRIPT_DIR should point to the directory containing the script
        assert hasattr(adw_plan_build_test_iso, 'SCRIPT_DIR')
        script_dir = adw_plan_build_test_iso.SCRIPT_DIR
        assert isinstance(script_dir, str)
        assert os.path.isabs(script_dir)

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('subprocess.run')
    def test_subprocess_uses_sys_executable(self, mock_subprocess, mock_load_dotenv):
        """Test that subprocess commands use sys.executable for Python."""
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        with patch.object(sys, 'argv', ['script.py', '123', 'test-adw-id']):
            adw_plan_build_test_iso.main()

            # Verify all subprocess calls use sys.executable
            for call_item in mock_subprocess.call_args_list:
                args = call_item[0][0]
                assert args[0] == sys.executable


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('subprocess.run')
    def test_extra_arguments_ignored(self, mock_subprocess, mock_load_dotenv):
        """Test that extra arguments beyond issue number and ADW ID are ignored."""
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        with patch.object(sys, 'argv', ['script.py', '123', 'adw-id', 'extra', 'args']):
            adw_plan_build_test_iso.main()

            # Should complete successfully
            assert mock_subprocess.call_count == 3

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('os.path.getmtime')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('subprocess.run')
    def test_state_file_path_not_exists_skipped(self, mock_subprocess, mock_json_load, mock_file, mock_getmtime, mock_listdir, mock_exists, mock_load_dotenv):
        """Test that non-existent state file path is skipped."""
        # Planning succeeds
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        # Mock file system - agents dir exists, but state file doesn't
        def exists_side_effect(path):
            if 'agents' in path and 'adw_state.json' not in path:
                return True
            return False
        mock_exists.side_effect = exists_side_effect

        mock_listdir.return_value = ['adw-no-state']

        with patch.object(sys, 'argv', ['script.py', '123']):
            with patch.object(sys, 'exit') as mock_exit:
                adw_plan_build_test_iso.main()

                # Should exit due to no valid state file
                # This is caught by the empty state_files list
                mock_exit.assert_called_with(1)

    @patch('adw_plan_build_test_iso.load_dotenv')
    @patch('builtins.print')
    @patch('subprocess.run')
    def test_print_step_headers(self, mock_subprocess, mock_print, mock_load_dotenv):
        """Test that step headers are printed correctly."""
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)

        with patch.object(sys, 'argv', ['script.py', '123', 'test-adw-id']):
            adw_plan_build_test_iso.main()

            # Verify step headers with separators
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any('=' * 60 in call for call in print_calls)
            assert any('STEP 1: Planning' in call for call in print_calls)
            assert any('STEP 2: Building' in call for call in print_calls)
            assert any('STEP 3: Testing' in call for call in print_calls)
