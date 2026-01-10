"""Data types for GitHub API responses and Claude Code agent."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Literal, ClassVar
from rococo.models import BaseModel
from enum import Enum


# Retry codes for Claude Code execution errors
class RetryCode(str, Enum):
    """Codes indicating different types of errors that may be retryable."""

    CLAUDE_CODE_ERROR = "claude_code_error"  # General Claude Code CLI error
    TIMEOUT_ERROR = "timeout_error"  # Command timed out
    EXECUTION_ERROR = "execution_error"  # Error during execution
    ERROR_DURING_EXECUTION = "error_during_execution"  # Agent encountered an error
    NONE = "none"  # No retry needed


# Supported slash commands for issue classification
IssueClassSlashCommand = Literal["/chore", "/bug", "/feature"]

# Model set types for ADW workflows
ModelSet = Literal["base", "heavy"]

# ADW workflow types (all isolated now)
ADWWorkflow = Literal[
    "adw_plan_iso",  # Planning only
    "adw_patch_iso",  # Direct patch from issue
    "adw_build_iso",  # Building only (dependent workflow)
    "adw_test_iso",  # Testing only (dependent workflow)
    "adw_review_iso",  # Review only (dependent workflow)
    "adw_document_iso",  # Documentation only (dependent workflow)
    "adw_ship_iso",  # Ship/deployment workflow
    "adw_sdlc_ZTE_iso",  # Zero Touch Execution - full SDLC with auto-merge
    "adw_plan_build_iso",  # Plan + Build
    "adw_plan_build_test_iso",  # Plan + Build + Test
    "adw_plan_build_test_review_iso",  # Plan + Build + Test + Review
    "adw_plan_build_document_iso",  # Plan + Build + Document
    "adw_plan_build_review_iso",  # Plan + Build + Review
    "adw_sdlc_iso",  # Complete SDLC: Plan + Build + Test + Review + Document
]

# All slash commands used in the ADW system
SlashCommand = Literal[
    # Issue classification commands
    "/chore",
    "/bug",
    "/feature",
    # ADW workflow commands
    "/classify_issue",
    "/classify_adw",
    "/generate_branch_name",
    "/commit",
    "/pull_request",
    "/implement",
    "/test",
    "/resolve_failed_test",
    "/test_e2e",
    "/resolve_failed_e2e_test",
    "/review",
    "/patch",
    "/document",
    "/track_agentic_kpis",
    # Installation/setup commands
    "/install_worktree",
]


@dataclass(kw_only=True)
class GitHubUser(BaseModel):
    """GitHub user model."""
    
    allow_extra: ClassVar[bool] = True  # Allow extra fields from GitHub API

    login: str
    id: Optional[str] = None
    name: Optional[str] = None
    is_bot: bool = field(default=False, metadata={'alias': 'isBot'})


@dataclass(kw_only=True)
class GitHubLabel(BaseModel):
    """GitHub label model."""

    id: str
    name: str
    color: str
    description: Optional[str] = None


@dataclass(kw_only=True)
class GitHubMilestone(BaseModel):
    """GitHub milestone model."""

    id: str
    number: int
    title: str
    state: str
    description: Optional[str] = None


@dataclass(kw_only=True)
class GitHubComment(BaseModel):
    """GitHub comment model."""
    
    allow_extra: ClassVar[bool] = True  # Allow extra fields from GitHub API

    id: str
    author: GitHubUser = field(metadata={'model': GitHubUser})
    body: str
    created_at: datetime = field(metadata={'alias': 'createdAt'})
    updated_at: Optional[datetime] = field(default=None, metadata={'alias': 'updatedAt'})


@dataclass(kw_only=True)
class GitHubIssueListItem(BaseModel):
    """GitHub issue model for list responses (simplified)."""
    
    allow_extra: ClassVar[bool] = True  # Allow extra fields from GitHub API

    number: int
    title: str
    body: str
    created_at: datetime = field(metadata={'alias': 'createdAt'})
    updated_at: datetime = field(metadata={'alias': 'updatedAt'})
    labels: List[GitHubLabel] = field(default_factory=list, metadata={'model': GitHubLabel})


@dataclass(kw_only=True)
class GitHubIssue(BaseModel):
    """GitHub issue model."""
    
    allow_extra: ClassVar[bool] = True  # Allow extra fields from GitHub API

    number: int
    title: str
    body: str
    state: str
    author: GitHubUser = field(metadata={'model': GitHubUser})
    url: str
    created_at: datetime = field(metadata={'alias': 'createdAt'})
    updated_at: datetime = field(metadata={'alias': 'updatedAt'})
    assignees: List[GitHubUser] = field(default_factory=list, metadata={'model': GitHubUser})
    labels: List[GitHubLabel] = field(default_factory=list, metadata={'model': GitHubLabel})
    comments: List[GitHubComment] = field(default_factory=list, metadata={'model': GitHubComment})
    milestone: Optional[GitHubMilestone] = field(default=None, metadata={'model': GitHubMilestone})
    closed_at: Optional[datetime] = field(default=None, metadata={'alias': 'closedAt'})


@dataclass(kw_only=True)
class AgentPromptRequest(BaseModel):
    """Claude Code agent prompt configuration."""

    prompt: str
    adw_id: str
    output_file: str
    agent_name: str = "ops"
    model: Literal["sonnet", "opus"] = "sonnet"
    dangerously_skip_permissions: bool = False
    working_dir: Optional[str] = None


@dataclass(kw_only=True)
class AgentPromptResponse(BaseModel):
    """Claude Code agent response."""

    output: str
    success: bool
    session_id: Optional[str] = None
    retry_code: RetryCode = RetryCode.NONE


@dataclass(kw_only=True)
class AgentTemplateRequest(BaseModel):
    """Claude Code agent template execution request."""

    agent_name: str
    slash_command: SlashCommand
    args: List[str]
    adw_id: str
    model: Literal["sonnet", "opus"] = "sonnet"
    working_dir: Optional[str] = None


@dataclass(kw_only=True)
class ClaudeCodeResultMessage(BaseModel):
    """Claude Code JSONL result message (last line)."""

    type: str
    subtype: str
    is_error: bool
    duration_ms: int
    duration_api_ms: int
    num_turns: int
    result: str
    session_id: str
    total_cost_usd: float


@dataclass(kw_only=True)
class TestResult(BaseModel):
    """Individual test result from test suite execution."""

    test_name: str
    passed: bool
    execution_command: str
    test_purpose: str
    error: Optional[str] = None


@dataclass(kw_only=True)
class E2ETestResult(BaseModel):
    """Individual E2E test result from browser automation."""

    test_name: str
    status: Literal["passed", "failed"]
    test_path: str
    screenshots: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        """Check if test passed."""
        return self.status == "passed"


@dataclass(kw_only=True)
class ADWStateData(BaseModel):
    """Minimal persistent state for ADW workflow.

    Stored in agents/{adw_id}/adw_state.json
    Contains only essential identifiers to connect workflow steps.
    """

    adw_id: str
    issue_number: Optional[str] = None
    branch_name: Optional[str] = None
    plan_file: Optional[str] = None
    issue_class: Optional[IssueClassSlashCommand] = None
    worktree_path: Optional[str] = None
    backend_port: Optional[int] = None
    model_set: Optional[ModelSet] = "base"
    all_adws: List[str] = field(default_factory=list)


@dataclass(kw_only=True)
class ReviewIssue(BaseModel):
    """Individual review issue found during spec verification."""

    review_issue_number: int
    screenshot_path: str
    issue_description: str
    issue_resolution: str
    issue_severity: Literal["skippable", "tech_debt", "blocker"]
    screenshot_url: Optional[str] = None


@dataclass(kw_only=True)
class ReviewResult(BaseModel):
    """Result from reviewing implementation against specification."""

    success: bool
    review_summary: str
    review_issues: List[ReviewIssue] = field(default_factory=list, metadata={'model': ReviewIssue})
    screenshots: List[str] = field(default_factory=list)
    screenshot_urls: List[str] = field(default_factory=list)


@dataclass(kw_only=True)
class DocumentationResult(BaseModel):
    """Result from documentation generation workflow."""

    success: bool
    documentation_created: bool
    documentation_path: Optional[str] = None
    error_message: Optional[str] = None


@dataclass(kw_only=True)
class ADWExtractionResult(BaseModel):
    """Result from extracting ADW information from text."""
    
    workflow_command: Optional[str] = None
    adw_id: Optional[str] = None
    model_set: Optional[ModelSet] = "base"
    
    @property
    def has_workflow(self) -> bool:
        """Check if a workflow command was extracted."""
        return self.workflow_command is not None

