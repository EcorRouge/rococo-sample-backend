# /test - Generate Tests for Uncovered Code

Generate comprehensive test cases for code that lacks test coverage.

## Usage

```
/test
```

## Behavior

1. If coverage data is provided as an argument, use it to identify uncovered files and lines
2. Otherwise, analyze the codebase to identify files and functions without test coverage
3. Generate pytest test cases for uncovered code, prioritizing files with the lowest coverage
4. Place test files in the `tests/` directory following existing test patterns
5. Ensure tests follow the existing test structure (using pytest, fixtures from conftest.py, etc.)

## Arguments

- Optional: JSON string containing SonarQube coverage data with structure:
  ```json
  {
    "total_uncovered_files": 5,
    "files": [
      {
        "path": "common/models/person.py",
        "coverage_percentage": 75.5,
        "uncovered_lines": [42, 43, 67, 89],
        "total_uncovered_lines": 4,
        "lines_to_cover": 16
      }
    ]
  }
  ```

## Output Format

Return a JSON array of test results:

```json
[
  {
    "test_name": "test_person_repository_create",
    "passed": true,
    "execution_command": "pytest tests/test_person_repository.py::test_person_repository_create -v",
    "test_purpose": "Test creating a new person in the repository",
    "error": null
  }
]
```

## Guidelines

- Use pytest as the testing framework
- Follow existing test patterns in `tests/` directory
- Use fixtures from `tests/conftest.py` when available
- Test both success and error cases
- Aim for 100% code coverage
- Place tests in appropriate test files matching the source structure
- Use descriptive test names following the pattern `test_<module>_<function>_<scenario>`

## Example Test Structure

```python
import pytest
from unittest.mock import MagicMock, patch

class TestPersonRepository:
    """Tests for PersonRepository."""
    
    def test_create_person_success(self, mock_repository):
        """Test creating a person successfully."""
        # Test implementation
        pass
    
    def test_create_person_validation_error(self, mock_repository):
        """Test creating a person with invalid data."""
        # Test implementation
        pass

        
```

