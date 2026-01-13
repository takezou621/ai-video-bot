"""
Configuration module for AI Video Bot.

Exports common constants and settings for easy import.
"""
from config.constants import (
    # Video
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    FPS,
    DEFAULT_VIDEO_CODEC,
    DEFAULT_AUDIO_CODEC,
    DEFAULT_AUDIO_BITRATE,
    # Subtitle colors
    MALE_COLOR,
    MALE_COLOR_HEX,
    FEMALE_COLOR,
    FEMALE_COLOR_HEX,
    TEXT_COLOR,
    TEXT_COLOR_HEX,
    # Subtitle configuration
    FONT_SIZE,
    SUBTITLE_MARGIN,
    BOX_PADDING,
    BOX_OPACITY,
    SUBTITLE_BOX_HEIGHT,
    SUBTITLE_Y_POSITION,
    MAX_CHARS_PER_LINE,
    GRADIENT_HEIGHT_RATIO,
    GRADIENT_OPACITY,
    BG_COLOR,
    # API
    DEFAULT_API_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    # Speakers
    SPEAKER_MALE,
    SPEAKER_FEMALE,
    MALE_SPEAKERS,
    FEMALE_SPEAKERS,
    # Helper functions
    is_male_speaker,
    is_female_speaker,
    get_speaker_color,
    validate_subtitle_config,
)

from config.settings import (
    Settings,
    VideoSettings,
    GeminiSettings,
    GeminiTTSSettings,
    WhisperSettings,
    ElevenLabsSettings,
    WebSearchSettings,
    YouTubeSettings,
    PodcastAPISettings,
    NotificationSettings,
    get_settings,
    reload_settings,
)

__all__ = [
    # Constants
    'VIDEO_WIDTH',
    'VIDEO_HEIGHT',
    'FPS',
    'DEFAULT_VIDEO_CODEC',
    'DEFAULT_AUDIO_CODEC',
    'DEFAULT_AUDIO_BITRATE',
    'MALE_COLOR',
    'MALE_COLOR_HEX',
    'FEMALE_COLOR',
    'FEMALE_COLOR_HEX',
    'TEXT_COLOR',
    'TEXT_COLOR_HEX',
    'FONT_SIZE',
    'SUBTITLE_MARGIN',
    'BOX_PADDING',
    'BOX_OPACITY',
    'SUBTITLE_BOX_HEIGHT',
    'SUBTITLE_Y_POSITION',
    'MAX_CHARS_PER_LINE',
    'GRADIENT_HEIGHT_RATIO',
    'GRADIENT_OPACITY',
    'BG_COLOR',
    'DEFAULT_API_TIMEOUT',
    'DEFAULT_MAX_RETRIES',
    'SPEAKER_MALE',
    'SPEAKER_FEMALE',
    'MALE_SPEAKERS',
    'FEMALE_SPEAKERS',
    # Helper functions
    'is_male_speaker',
    'is_female_speaker',
    'get_speaker_color',
    'validate_subtitle_config',
    # Settings
    'Settings',
    'VideoSettings',
    'GeminiSettings',
    'GeminiTTSSettings',
    'WhisperSettings',
    'ElevenLabsSettings',
    'WebSearchSettings',
    'YouTubeSettings',
    'PodcastAPISettings',
    'NotificationSettings',
    'get_settings',
    'reload_settings',
]
