"""Standardized error handling for ADW workflows.

Provides consistent error handling patterns across all ADW workflows,
including error reporting, GitHub comments, and graceful exits.
"""

import sys
import logging
import traceback
from typing import Optional, Callable, Any
from enum import Enum

from adw_modules.github import make_issue_comment
from adw_modules.workflow_ops import format_issue_message


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"  # Workflow must stop immediately
    ERROR = "error"  # Workflow should stop, but can be retried
    WARNING = "warning"  # Workflow can continue with degraded functionality
    INFO = "info"  # Informational message


class ADWError(Exception):
    """Base exception for ADW workflows with standardized error handling."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        issue_number: Optional[str] = None,
        adw_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        should_comment: bool = True,
        should_exit: bool = True,
        exit_code: int = 1,
    ):
        """Initialize ADW error.
        
        Args:
            message: Error message
            severity: Error severity level
            issue_number: GitHub issue number (for commenting)
            adw_id: ADW ID (for logging context)
            agent_name: Agent name (for GitHub comment formatting)
            should_comment: Whether to post GitHub comment
            should_exit: Whether to exit the process
            exit_code: Exit code to use if should_exit is True
        """
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.issue_number = issue_number
        self.adw_id = adw_id
        self.agent_name = agent_name or "ops"
        self.should_comment = should_comment
        self.should_exit = should_exit
        self.exit_code = exit_code


def handle_error(
    error: Exception,
    logger: logging.Logger,
    issue_number: Optional[str] = None,
    adw_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    context: Optional[str] = None,
) -> None:
    """Handle an error with standardized logging and GitHub comments.
    
    Args:
        error: The exception that occurred
        logger: Logger instance
        issue_number: GitHub issue number (for commenting)
        adw_id: ADW ID (for context)
        agent_name: Agent name (for GitHub comment formatting)
        context: Additional context about where the error occurred
    """
    # Determine error details
    if isinstance(error, ADWError):
        message = error.message
        severity = error.severity
        issue_number = issue_number or error.issue_number
        adw_id = adw_id or error.adw_id
        agent_name = agent_name or error.agent_name
        should_comment = error.should_comment
        should_exit = error.should_exit
        exit_code = error.exit_code
    else:
        message = str(error)
        severity = ErrorSeverity.ERROR
        should_comment = True
        should_exit = True
        exit_code = 1
    
    # Build full error message
    full_message = message
    if context:
        full_message = f"{context}: {message}"
    
    # Log based on severity
    if severity == ErrorSeverity.CRITICAL:
        logger.critical(full_message)
        logger.debug(traceback.format_exc())
    elif severity == ErrorSeverity.ERROR:
        logger.error(full_message)
        logger.debug(traceback.format_exc())
    elif severity == ErrorSeverity.WARNING:
        logger.warning(full_message)
    else:
        logger.info(full_message)
    
    # Post GitHub comment if applicable
    if should_comment and issue_number:
        try:
            emoji = "❌" if severity in [ErrorSeverity.CRITICAL, ErrorSeverity.ERROR] else "⚠️"
            comment_message = format_issue_message(
                adw_id or "unknown",
                agent_name,
                f"{emoji} {full_message}"
            )
            make_issue_comment(issue_number, comment_message)
        except Exception as comment_error:
            logger.warning(f"Failed to post GitHub comment: {comment_error}")
    
    # Exit if needed
    if should_exit:
        sys.exit(exit_code)


def safe_execute(
    func: Callable[[], Any],
    logger: logging.Logger,
    error_message: str,
    issue_number: Optional[str] = None,
    adw_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    context: Optional[str] = None,
    reraise: bool = False,
) -> Any:
    """Execute a function with standardized error handling.
    
    Args:
        func: Function to execute
        logger: Logger instance
        error_message: Error message if function fails
        issue_number: GitHub issue number (for commenting)
        adw_id: ADW ID (for context)
        agent_name: Agent name (for GitHub comment formatting)
        context: Additional context about where the error occurred
        reraise: If True, re-raise the exception instead of exiting
        
    Returns:
        Result of func() if successful
        
    Raises:
        Exception: If reraise is True and an error occurs
    """
    try:
        return func()
    except ADWError as e:
        # ADWError handles its own reporting
        if reraise:
            raise
        handle_error(e, logger, issue_number, adw_id, agent_name, context)
        return None
    except Exception as e:
        # Wrap in ADWError for consistent handling
        adw_error = ADWError(
            message=f"{error_message}: {str(e)}",
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name=agent_name,
        )
        if reraise:
            raise adw_error
        handle_error(adw_error, logger, issue_number, adw_id, agent_name, context)
        return None


def validate_result(
    result: Any,
    success_condition: Callable[[Any], bool],
    error_message: str,
    logger: logging.Logger,
    issue_number: Optional[str] = None,
    adw_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    context: Optional[str] = None,
) -> None:
    """Validate a result and handle failure with standardized error handling.
    
    Args:
        result: Result to validate
        success_condition: Function that returns True if result is valid
        error_message: Error message if validation fails
        logger: Logger instance
        issue_number: GitHub issue number (for commenting)
        adw_id: ADW ID (for context)
        agent_name: Agent name (for GitHub comment formatting)
        context: Additional context about where the error occurred
    """
    if not success_condition(result):
        error = ADWError(
            message=error_message,
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name=agent_name,
        )
        handle_error(error, logger, issue_number, adw_id, agent_name, context)


def validate_tuple_result(
    result: tuple,
    error_message: str,
    logger: logging.Logger,
    issue_number: Optional[str] = None,
    adw_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    context: Optional[str] = None,
) -> Any:
    """Validate a (result, error) tuple pattern and handle errors.
    
    This is a common pattern in ADW workflows where functions return (result, error).
    
    Args:
        result: Tuple of (result, error) or (success, error)
        error_message: Base error message if error is present
        logger: Logger instance
        issue_number: GitHub issue number (for commenting)
        adw_id: ADW ID (for context)
        agent_name: Agent name (for GitHub comment formatting)
        context: Additional context about where the error occurred
        
    Returns:
        The result value if successful
        
    Raises:
        ADWError: If error is present in tuple
    """
    if len(result) != 2:
        raise ValueError("validate_tuple_result expects a 2-tuple (result, error)")
    
    value, error = result
    
    if error:
        full_message = f"{error_message}: {error}"
        raise ADWError(
            message=full_message,
            issue_number=issue_number,
            adw_id=adw_id,
            agent_name=agent_name,
        )
    
    return value

