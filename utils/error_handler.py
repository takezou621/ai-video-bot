"""
Standardized error handling for AI Video Bot.

Provides consistent error handling patterns across all modules:
- Custom exceptions
- Error logging utilities
- Decorators for error handling
- Fallback result management
"""
import logging
import sys
import traceback
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Type
from dataclasses import dataclass

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from config.constants import DEFAULT_API_TIMEOUT

logger = logging.getLogger(__name__)

# Type variables for generic decorators
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


# =============================================================================
# Custom Exceptions
# =============================================================================

class VideoBotError(Exception):
    """Base exception for all AI Video Bot errors."""

    def __init__(self, message: str, module: str = "", context: Optional[dict] = None):
        super().__init__(message)
        self.module = module
        self.context = context or {}

    def __str__(self):
        if self.module:
            return f"[{self.module}] {super().__str__()}"
        return super().__str__()


class APIError(VideoBotError):
    """Exception raised for API-related errors."""

    def __init__(
        self,
        message: str,
        service: str = "",
        status_code: Optional[int] = None,
        is_rate_limit: bool = False
    ):
        super().__init__(message, module=service or "API")
        self.status_code = status_code
        self.is_rate_limit = is_rate_limit


class TTSError(VideoBotError):
    """Exception raised for TTS-related errors."""

    def __init__(self, message: str, engine: str = ""):
        super().__init__(message, module=engine or "TTS")
        self.engine = engine


class VideoRenderingError(VideoBotError):
    """Exception raised for video rendering errors."""

    def __init__(self, message: str, stage: str = ""):
        super().__init__(message, module=stage or "VideoRendering")
        self.stage = stage


class ContentGenerationError(VideoBotError):
    """Exception raised for content generation errors."""

    def __init__(self, message: str, generator: str = ""):
        super().__init__(message, module=generator or "ContentGeneration")
        self.generator = generator


class ValidationError(VideoBotError):
    """Exception raised for validation errors."""

    def __init__(self, message: str, field: str = ""):
        super().__init__(message, module="Validation")
        self.field = field


# =============================================================================
# Error Logging Utilities
# =============================================================================

@dataclass
class ErrorContext:
    """Context information for error logging."""
    module: str
    function: str
    error: Exception
    traceback_str: Optional[str] = None
    extra_info: Optional[dict] = None


def log_error(error: Exception, level: int = logging.ERROR) -> ErrorContext:
    """
    Log an error with context information.

    Args:
        error: The exception to log
        level: Logging level (default: ERROR)

    Returns:
        ErrorContext with details about the error
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()

    context = ErrorContext(
        module=getattr(error, 'module', 'Unknown'),
        function=_get_function_name(),
        error=error,
        traceback_str=''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)) if exc_traceback else None,
        extra_info=getattr(error, 'context', None)
    )

    logger.log(
        level,
        f"[{context.module}] {type(error).__name__}: {str(error)}",
        exc_info=exc_traceback is not None
    )

    return context


def log_api_error(service: str, error: Exception, is_rate_limit: bool = False) -> None:
    """
    Log API-specific error.

    Args:
        service: Service name (e.g., "GEMINI", "ELEVENLABS")
        error: The exception
        is_rate_limit: Whether this is a rate limit error
    """
    prefix = "RATE LIMIT" if is_rate_limit else "API ERROR"
    logger.error(f"[{service}] {prefix}: {str(error)}")


def log_and_return(
    error: Exception,
    fallback_value: Any = None,
    log_level: int = logging.ERROR
) -> Any:
    """
    Log an error and return a fallback value.

    Args:
        error: The exception to log
        fallback_value: Value to return after logging
        log_level: Logging level

    Returns:
        The fallback value
    """
    log_error(error, log_level)
    return fallback_value


# =============================================================================
# Error Handling Decorators
# =============================================================================

def handle_errors(
    fallback_value: Any = None,
    exceptions: tuple = (Exception,),
    log_level: int = logging.ERROR,
    reraise: bool = False
) -> Callable[[F], F]:
    """
    Decorator to handle exceptions in functions.

    Args:
        fallback_value: Value to return if exception occurs
        exceptions: Tuple of exceptions to catch
        log_level: Logging level
        reraise: If True, re-raise the exception after logging

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                module = func.__module__
                logger.log(
                    log_level,
                    f"[{module}] Error in {func.__name__}: {str(e)}"
                )
                if reraise:
                    raise
                return fallback_value
        return wrapper
    return decorator


def handle_api_errors(
    service: str,
    fallback_value: Any = None,
    reraise: bool = False
) -> Callable[[F], F]:
    """
    Decorator specifically for API call errors.

    Args:
        service: Service name for logging
        fallback_value: Value to return if exception occurs
        reraise: If True, re-raise the exception

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                is_rate_limit = getattr(e, 'is_rate_limit', False)
                log_api_error(service, e, is_rate_limit)
                if reraise:
                    raise
                return fallback_value
            except Exception as e:
                if REQUESTS_AVAILABLE and isinstance(e, requests.exceptions.RequestException):
                    is_rate_limit = getattr(e, 'is_rate_limit', False)
                    log_api_error(service, e, is_rate_limit)
                else:
                    logger.error(f"[{service}] Unexpected error in {func.__name__}: {str(e)}")
                if reraise:
                    raise
                return fallback_value
        return wrapper
    return decorator


def safe_execute(
    default_return: Any = None,
    log_errors: bool = True
) -> Callable[[F], F]:
    """
    Decorator that safely executes a function, catching all exceptions.

    Args:
        default_return: Value to return on exception
        log_errors: Whether to log errors

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.warning(f"[{func.__module__}] {func.__name__} failed: {str(e)}")
                return default_return
        return wrapper
    return decorator


# =============================================================================
# Retry Logic
# =============================================================================

def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
) -> Callable[[F], F]:
    """
    Decorator to retry a function on failure.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Callback function called on each retry

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        if on_retry:
                            on_retry(attempt + 1, e)
                        logger.warning(
                            f"[{func.__module__}] {func.__name__} failed "
                            f"(attempt {attempt + 1}/{max_attempts}), retrying in {current_delay}s"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"[{func.__module__}] {func.__name__} failed "
                            f"after {max_attempts} attempts"
                        )

            # All retries exhausted
            raise last_exception if last_exception else Exception("Retry failed")

        return wrapper
    return decorator


# =============================================================================
# Utility Functions
# =============================================================================

def _get_function_name() -> str:
    """Get the name of the calling function."""
    return sys._getframe(2).f_code.co_name if sys._getframe(2) else "unknown"


def create_error(
    error_class: Type[VideoBotError],
    message: str,
    **kwargs
) -> VideoBotError:
    """
    Factory function to create custom errors.

    Args:
        error_class: Error class to instantiate
        message: Error message
        **kwargs: Additional arguments for the error class

    Returns:
        Instance of the error class
    """
    return error_class(message, **kwargs)


def is_recoverable_error(error: Exception) -> bool:
    """
    Check if an error is recoverable (should retry).

    Args:
        error: The exception to check

    Returns:
        True if error is recoverable
    """
    if REQUESTS_AVAILABLE and isinstance(error, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return True
    if isinstance(error, APIError) and getattr(error, 'is_rate_limit', False):
        return True
    return False


# =============================================================================
# Context Manager for Error Handling
# =============================================================================

from contextlib import contextmanager


@contextmanager
def error_handler(
    module: str,
    fallback_value: Any = None,
    reraise: bool = False,
    on_error: Optional[Callable[[Exception], Any]] = None
):
    """
    Context manager for error handling.

    Args:
        module: Module name for logging
        fallback_value: Value to yield on error
        reraise: Whether to re-raise exceptions
        on_error: Callback function when error occurs

    Yields:
        Either the result or fallback_value
    """
    try:
        yield
    except Exception as e:
        logger.error(f"[{module}] Error: {str(e)}")
        if on_error:
            on_error(e)
        if reraise:
            raise
        yield fallback_value


if __name__ == "__main__":
    # Test error handling
    logging.basicConfig(level=logging.INFO)

    # Test custom exception
    try:
        raise APIError("Test API error", service="GEMINI", status_code=429, is_rate_limit=True)
    except APIError as e:
        log_error(e)
        print(f"Is rate limit: {e.is_rate_limit}")

    # Test decorator
    @handle_errors(fallback_value="fallback", exceptions=(ValueError,))
    def test_function(x: int) -> str:
        if x < 0:
            raise ValueError("Negative value")
        return f"Success: {x}"

    print(test_function(10))  # Success
    print(test_function(-1))  # Fallback
