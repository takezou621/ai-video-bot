"""
Unit tests for configuration modules.

Tests cover:
- Constants module
- Settings module with value validation
- Helper functions
"""
import os
import pytest

# Set test environment variables before importing config
os.environ.update({
    'VIDEO_WIDTH': '1920',
    'VIDEO_HEIGHT': '1080',
    'FPS': '30',
    'USE_MOVIEPY': 'true',
})


def test_constants_export():
    """Test that constants are properly exported from config module."""
    from config import (
        VIDEO_WIDTH, VIDEO_HEIGHT, FPS,
        DEFAULT_API_TIMEOUT, DEFAULT_MAX_RETRIES,
        MALE_COLOR, FEMALE_COLOR,
        SPEAKER_MALE, SPEAKER_FEMALE,
    )
    assert VIDEO_WIDTH == 1920
    assert VIDEO_HEIGHT == 1080
    assert FPS == 30
    assert DEFAULT_API_TIMEOUT == 180
    assert DEFAULT_MAX_RETRIES == 3
    assert MALE_COLOR == (120, 200, 255)
    assert FEMALE_COLOR == (255, 150, 180)
    assert SPEAKER_MALE == "男性"
    assert SPEAKER_FEMALE == "女性"


def test_is_male_speaker():
    """Test speaker identification helper functions."""
    from config import is_male_speaker, is_female_speaker

    assert is_male_speaker("男性") is True
    assert is_male_speaker("A") is True
    assert is_male_speaker("女性") is False
    assert is_male_speaker("B") is False

    assert is_female_speaker("女性") is True
    assert is_female_speaker("B") is True
    assert is_female_speaker("男性") is False
    assert is_female_speaker("A") is False


def test_get_speaker_color():
    """Test get_speaker_color returns correct colors."""
    from config import get_speaker_color, MALE_COLOR, FEMALE_COLOR

    # Test RGB tuple (default)
    assert get_speaker_color("男性", as_hex=False) == MALE_COLOR
    assert get_speaker_color("女性", as_hex=False) == FEMALE_COLOR
    assert get_speaker_color("A", as_hex=False) == MALE_COLOR
    assert get_speaker_color("B", as_hex=False) == FEMALE_COLOR

    # Test hex string
    assert get_speaker_color("男性", as_hex=True) == '#78C8FF'
    assert get_speaker_color("女性", as_hex=True) == '#FF96B4'


def test_validate_subtitle_config():
    """Test subtitle configuration validation."""
    from config import validate_subtitle_config

    # Current configuration should be valid
    assert validate_subtitle_config() is True


def test_settings_video_settings():
    """Test VideoSettings creation."""
    from config.settings import VideoSettings

    settings = VideoSettings(
        width=1920,
        height=1080,
        fps=30,
        duration_minutes=10,
        videos_per_day=1,
        use_moviepy=True
    )

    assert settings.width == 1920
    assert settings.height == 1080
    assert settings.fps == 30
    assert settings.duration_minutes == 10
    assert settings.videos_per_day == 1
    assert settings.use_moviepy is True


def test_settings_parse_int_valid():
    """Test _parse_int with valid values."""
    from config.settings import _parse_int

    assert _parse_int("1920", 1280) == 1920
    assert _parse_int("0", 1280) == 0
    assert _parse_int("-1", 1280) == -1


def test_settings_parse_int_invalid():
    """Test _parse_int with invalid values returns default."""
    from config.settings import _parse_int

    assert _parse_int("", 1280) == 1280
    assert _parse_int("abc", 1280) == 1280
    assert _parse_int(None, 1280) == 1280
    assert _parse_float("12.5.5", 10.0) == 10.0


def test_settings_parse_float_valid():
    """Test _parse_float with valid values."""
    from config.settings import _parse_float

    assert _parse_float("0.9", 0.5) == 0.9
    assert _parse_float("1.5", 1.0) == 1.5
    assert _parse_float("0", 1.0) == 0.0


def test_settings_parse_float_invalid():
    """Test _parse_float with invalid values returns default."""
    from config.settings import _parse_float

    assert _parse_float("", 0.7) == 0.7
    assert _parse_float("abc", 0.7) == 0.7
    assert _parse_float(None, 0.7) == 0.7


def test_settings_parse_bool():
    """Test _parse_bool with various values."""
    from config.settings import _parse_bool

    # True values
    assert _parse_bool("true") is True
    assert _parse_bool("TRUE") is True
    assert _parse_bool("yes") is True
    assert _parse_bool("1") is True
    assert _parse_bool("t") is True
    assert _parse_bool("y") is True

    # False values
    assert _parse_bool("false") is False
    assert _parse_bool("no") is False
    assert _parse_bool("0") is False
    assert _parse_bool("f") is False
    assert _parse_bool("n") is False
    assert _parse_bool("anything") is False


def test_settings_from_env_with_invalid_values():
    """Test Settings.from_env with invalid environment variables."""
    import os
    from config.settings import get_settings, reload_settings

    # Set invalid values
    os.environ['VIDEO_WIDTH'] = 'invalid'
    os.environ['FPS'] = 'not_a_number'

    # Reload settings should use defaults for invalid values
    reload_settings()
    settings = get_settings()

    # Should use defaults instead of crashing
    assert settings.video.width > 0  # Should use default 1920
    assert settings.video.fps > 0     # Should use default 30

    # Reset to valid values
    os.environ['VIDEO_WIDTH'] = '1920'
    os.environ['FPS'] = '30'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
