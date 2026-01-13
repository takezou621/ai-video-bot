"""
Pytest configuration and fixtures for AI Video Bot tests.
"""
import os
import sys
from pathlib import Path

# Import pytest fixtures and configuration
import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests"
    )


@pytest.fixture
def test_env_vars():
    """Fixture providing test environment variables."""
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ.update({
        'VIDEO_WIDTH': '1920',
        'VIDEO_HEIGHT': '1080',
        'FPS': '30',
        'DURATION_MINUTES': '10',
        'VIDEOS_PER_DAY': '1',
        'USE_MOVIEPY': 'false',
        'USE_WHISPER_STT': 'true',
        'WHISPER_MODEL_SIZE': 'base',
        'GEMINI_MODEL': 'gemini-3-flash-preview',
        'GEMINI_TEMPERATURE': '0.9',
        'GEMINI_MAX_TOKENS': '8192',
    })

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
