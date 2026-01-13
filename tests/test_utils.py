"""
Unit tests for utility modules.

Tests cover:
- Error handling
- Custom exceptions
- Decorators
"""
import pytest

from utils.error_handler import (
    VideoBotError,
    APIError,
    TTSError,
    VideoRenderingError,
    ContentGenerationError,
    ValidationError,
    handle_errors,
    safe_execute,
    is_recoverable_error,
    create_error,
)


def test_video_bot_error():
    """Test base VideoBotError exception."""
    error = VideoBotError("Test error", module="TestModule")
    assert str(error) == "[TestModule] Test error"
    assert error.module == "TestModule"
    assert error.context == {}


def test_video_bot_error_with_context():
    """Test VideoBotError with context information."""
    error = VideoBotError("Test error", module="TestModule", context={"key": "value"})
    assert error.context == {"key": "value"}


def test_api_error():
    """Test APIError exception."""
    error = APIError("API failed", service="GEMINI", status_code=429, is_rate_limit=True)
    assert error.module == "GEMINI"
    assert error.status_code == 429
    assert error.is_rate_limit is True


def test_tts_error():
    """Test TTSError exception."""
    error = TTSError("TTS failed", engine="gTTS")
    assert error.module == "gTTS"
    assert error.engine == "gTTS"


def test_video_rendering_error():
    """Test VideoRenderingError exception."""
    error = VideoRenderingError("Render failed", stage="encoding")
    assert error.module == "encoding"
    assert error.stage == "encoding"


def test_content_generation_error():
    """Test ContentGenerationError exception."""
    error = ContentGenerationError("Generation failed", generator="Gemini")
    assert error.module == "Gemini"
    assert error.generator == "Gemini"


def test_validation_error():
    """Test ValidationError exception."""
    error = ValidationError("Invalid value", field="email")
    assert error.module == "Validation"
    assert error.field == "email"


def test_handle_errors_decorator():
    """Test handle_errors decorator with fallback value."""
    @handle_errors(fallback_value="fallback", exceptions=(ValueError,))
    def test_function(x: int) -> str:
        if x < 0:
            raise ValueError("Negative value")
        return f"Success: {x}"

    # Success case
    assert test_function(10) == "Success: 10"

    # Error case - should return fallback
    assert test_function(-1) == "fallback"


def test_handle_errors_decorator_reraise():
    """Test handle_errors decorator with reraise=True."""
    @handle_errors(fallback_value="fallback", exceptions=(ValueError,), reraise=True)
    def test_function(x: int) -> str:
        if x < 0:
            raise ValueError("Negative value")
        return f"Success: {x}"

    # Should raise exception
    with pytest.raises(ValueError):
        test_function(-1)


def test_safe_execute_decorator():
    """Test safe_execute decorator."""
    @safe_execute(default_return="default", log_errors=False)
    def test_function(x: int) -> str:
        if x < 0:
            raise RuntimeError("Error")
        return f"Success: {x}"

    # Success case
    assert test_function(10) == "Success: 10"

    # Error case - should return default
    assert test_function(-1) == "default"


def test_create_error():
    """Test create_error factory function."""
    error = create_error(APIError, "Test API error", service="TEST", status_code=500)

    assert isinstance(error, APIError)
    assert str(error) == "[TEST] Test API error"
    assert error.status_code == 500


def test_is_recoverable_error():
    """Test is_recoverable_error function."""
    # APIError with rate limit should be recoverable
    rate_limit_error = APIError("Rate limited", is_rate_limit=True)
    assert is_recoverable_error(rate_limit_error) is True

    # Regular APIError without rate limit should not be recoverable
    normal_error = APIError("Normal error", is_rate_limit=False)
    assert is_recoverable_error(normal_error) is False

    # VideoBotError should not be recoverable by default
    bot_error = VideoBotError("Bot error")
    assert is_recoverable_error(bot_error) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
