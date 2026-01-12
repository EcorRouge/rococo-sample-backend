# /test - Generate Tests for Uncovered Code

Generate comprehensive test cases for code that lacks test coverage.

## Usage

```
/test
```

## Behavior

**CRITICAL - Coverage Data Usage:**
- **If coverage data is provided as an argument, you MUST use ONLY the files listed in that coverage data**
- **DO NOT scan the codebase or look at any other files when coverage data is provided**
- **The coverage data already contains only application code from `flask/` and `common/` directories - use it as-is**

- Don't change application code just produce tests, and if there is a bug in the application code mention that.

1. **DO NOT generate tests for files in `adws/` directory** - only generate tests for application code
2. **If coverage data is provided as an argument, use ONLY the files in that coverage data to identify uncovered files and lines**
3. **Otherwise** (only if no coverage data is provided), analyze the codebase to identify files and functions without test coverage (excluding adws/)
4. Generate pytest test cases for uncovered code, prioritizing files with the lowest coverage
5. Place test files in the `tests/` directory following existing test patterns
6. Ensure tests follow the existing test structure (using pytest, fixtures from conftest.py, etc.)

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

**CRITICAL: Return ONLY a JSON array of test results. Do NOT include any markdown, explanations, or other text. The output must be valid JSON that can be parsed directly.**

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

**IMPORTANT**: 
- Output ONLY the JSON array, nothing else
- Do NOT include markdown formatting, explanations, or summaries
- Do NOT wrap the JSON in code blocks
- The output must start with `[` and end with `]`

## Guidelines

- Use pytest as the testing framework
- Follow existing test patterns in `tests/` directory
- Use fixtures from `tests/conftest.py` when available
- Test both success and error cases
- Aim for 100% code coverage
- Place tests in appropriate test files matching the source structure
- Use descriptive test names following the pattern `test_<module>_<function>_<scenario>`

**CRITICAL - Patch Path Rules:**
When using `@patch` to mock dependencies, patch them at their **actual module location**, not where they're imported:
- ✅ CORRECT: `@patch('common.services.email.EmailService')` - patches EmailService where it's defined
- ❌ WRONG: `@patch('common.services.person.EmailService')` - this won't work because EmailService is not in person.py
- ✅ CORRECT: `@patch('common.services.auth.EmailService')` - works because AuthService imports it at module level
- ✅ CORRECT: `@patch('common.services.person.RepositoryFactory')` - works because RepositoryFactory is imported in person.py

**Service Dependency Mapping:**
- `EmailService` → Always patch as `'common.services.email.EmailService'`
- `PersonService` → Always patch as `'common.services.person.PersonService'`  
- `LoginMethodService` → Always patch as `'common.services.login_method.LoginMethodService'`
- `OrganizationService` → Always patch as `'common.services.organization.OrganizationService'`
- `RepositoryFactory` → Patch where it's used: `'common.services.<module>.RepositoryFactory'`
- Check the actual file location (`common/services/<name>.py`) to determine the correct patch path

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

