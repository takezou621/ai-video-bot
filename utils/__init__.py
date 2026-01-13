"""
Utilities module for AI Video Bot.

Exports common utility functions and error handling.
"""
from utils.error_handler import (
    # Custom exceptions
    VideoBotError,
    APIError,
    TTSError,
    VideoRenderingError,
    ContentGenerationError,
    ValidationError,
    # Error logging
    ErrorContext,
    log_error,
    log_api_error,
    log_and_return,
    # Decorators
    handle_errors,
    handle_api_errors,
    safe_execute,
    retry_on_failure,
    # Utilities
    create_error,
    is_recoverable_error,
    error_handler,
)

__all__ = [
    # Exceptions
    'VideoBotError',
    'APIError',
    'TTSError',
    'VideoRenderingError',
    'ContentGenerationError',
    'ValidationError',
    # Error logging
    'ErrorContext',
    'log_error',
    'log_api_error',
    'log_and_return',
    # Decorators
    'handle_errors',
    'handle_api_errors',
    'safe_execute',
    'retry_on_failure',
    # Utilities
    'create_error',
    'is_recoverable_error',
    'error_handler',
]
