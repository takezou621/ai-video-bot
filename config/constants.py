"""
Shared constants for AI Video Bot.

This module centralizes configuration values that were previously
duplicated across multiple files, reducing maintenance burden
and ensuring consistency.
"""


# =============================================================================
# Video Configuration
# =============================================================================
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
DEFAULT_VIDEO_CODEC = 'libx264'
DEFAULT_AUDIO_CODEC = 'aac'
DEFAULT_AUDIO_BITRATE = '192k'


# =============================================================================
# Subtitle Styling
# =============================================================================
FONT_SIZE = 52
SUBTITLE_MARGIN = 160
BOX_PADDING = 30
BOX_OPACITY = 200

# Male speaker: Blue accent
MALE_COLOR = (120, 200, 255)
MALE_COLOR_HEX = '#78C8FF'

# Female speaker: Pink accent
FEMALE_COLOR = (255, 150, 180)
FEMALE_COLOR_HEX = '#FF96B4'

# Legacy color names for backward compatibility
SPEAKER_A_COLOR = MALE_COLOR
SPEAKER_B_COLOR = FEMALE_COLOR
TEXT_COLOR = (255, 255, 255)
TEXT_COLOR_HEX = 'white'
BG_COLOR = 'rgba(20,20,30,0.85)'


# =============================================================================
# MoviePy Subtitle Configuration
# =============================================================================
# CRITICAL: These values were carefully tuned to prevent text cut-off issues.
# DO NOT modify without thorough testing with long Japanese text (26+ characters).

MAX_CHARS_PER_LINE = 26      # Max characters per line (Japanese text)
SUBTITLE_BOX_HEIGHT = 120    # Fixed height for subtitle text box
SUBTITLE_Y_POSITION = 680    # Fixed Y position - DO NOT LOWER without testing!
SUBTITLE_SAFE_BOTTOM = 800   # Text box bottom (Y + HEIGHT) must not exceed 900

# Bottom gradient settings
GRADIENT_HEIGHT_RATIO = 0.35  # Bottom 35% of the image
GRADIENT_OPACITY = 0.7  # Maximum opacity at the bottom


# =============================================================================
# API Configuration
# =============================================================================
DEFAULT_API_TIMEOUT = 180  # seconds
DEFAULT_MAX_RETRIES = 3
REQUEST_RETRY_DELAY = 1.0  # seconds


# =============================================================================
# TTS Configuration
# =============================================================================
DEFAULT_TTS_SAMPLE_RATE = 24000
DEFAULT_TTS_CHANNELS = 1
DEFAULT_TTS_FORMAT = 'pcm'


# =============================================================================
# Content Generation
# =============================================================================
DEFAULT_TEMPERATURE = 0.9
DEFAULT_MAX_OUTPUT_TOKENS = 8192
ANALYTICAL_TEMPERATURE = 0.4
CREATIVE_TEMPERATURE = 0.9

# Japanese text timing
CHARACTERS_PER_MINUTE = 300  # For natural Japanese speech
CHARACTERS_PER_SECOND = 7     # For Gemini TTS output
EXCHANGES_PER_MINUTE = 6      # Average dialogue exchanges


# =============================================================================
# File Paths
# =============================================================================
DEFAULT_BACKGROUND_FILENAME = 'background.png'
DEFAULT_VIDEO_FILENAME = 'video.mp4'
DEFAULT_AUDIO_FILENAME = 'dialogue.mp3'
DEFAULT_THUMBNAIL_FILENAME = 'thumbnail.jpg'
DEFAULT_SCRIPT_FILENAME = 'script.json'
DEFAULT_METADATA_FILENAME = 'metadata.json'
DEFAULT_COMMENTS_FILENAME = 'comments.json'
DEFAULT_TOPIC_FILENAME = 'topic.json'
DEFAULT_TIMING_FILENAME = 'timing.json'
DEFAULT_MANIFEST_FILENAME = 'manifest.json'


# =============================================================================
# Speaker Identifiers
# =============================================================================
SPEAKER_MALE = "男性"
SPEAKER_FEMALE = "女性"
SPEAKER_A = "A"  # Legacy
SPEAKER_B = "B"  # Legacy

MALE_SPEAKERS = [SPEAKER_MALE, SPEAKER_A]
FEMALE_SPEAKERS = [SPEAKER_FEMALE, SPEAKER_B]


# =============================================================================
# Validation Constants
# =============================================================================
MIN_VIDEO_DURATION_SECONDS = 60
MAX_VIDEO_DURATION_SECONDS = 3600
MIN_THUMBNAIL_SIZE_BYTES = 10000
MAX_THUMBNAIL_SIZE_BYTES = 2 * 1024 * 1024  # 2MB
MIN_THUMBNAIL_WIDTH = 1280
MIN_THUMBNAIL_HEIGHT = 720


# =============================================================================
# Helper Functions
# =============================================================================

def is_male_speaker(speaker: str) -> bool:
    """Check if speaker identifier refers to male speaker."""
    return speaker in MALE_SPEAKERS


def is_female_speaker(speaker: str) -> bool:
    """Check if speaker identifier refers to female speaker."""
    return speaker in FEMALE_SPEAKERS


def get_speaker_color(speaker: str, as_hex: bool = False) -> tuple | str:
    """
    Get color for speaker.

    Args:
        speaker: Speaker identifier (男性/女性/A/B)
        as_hex: If True, return hex color string, otherwise RGB tuple

    Returns:
        Color as RGB tuple or hex string
    """
    if is_male_speaker(speaker):
        return MALE_COLOR_HEX if as_hex else MALE_COLOR
    elif is_female_speaker(speaker):
        return FEMALE_COLOR_HEX if as_hex else FEMALE_COLOR
    else:
        # Default to male color
        return MALE_COLOR_HEX if as_hex else MALE_COLOR


def validate_subtitle_config() -> bool:
    """
    Validate subtitle configuration to prevent text cut-off issues.

    Returns:
        True if configuration is valid, False otherwise
    """
    text_bottom = SUBTITLE_Y_POSITION + SUBTITLE_BOX_HEIGHT
    max_safe_bottom = VIDEO_HEIGHT - 180  # Need at least 180px margin

    if text_bottom > max_safe_bottom:
        return False

    # Warn if text is significantly above gradient
    gradient_top = int(VIDEO_HEIGHT * (1 - GRADIENT_HEIGHT_RATIO))
    if SUBTITLE_Y_POSITION < gradient_top - 50:
        # This is a warning, not an error
        pass

    return True
