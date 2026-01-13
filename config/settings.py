"""
Configuration settings for AI Video Bot.

Centralizes environment variable access with sensible defaults.
Use this module instead of direct os.getenv() calls for consistency.
"""
import os
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class VideoSettings:
    """Video generation settings."""
    width: int
    height: int
    fps: int
    duration_minutes: int
    videos_per_day: int
    use_moviepy: bool

    @classmethod
    def from_env(cls) -> 'VideoSettings':
        return cls(
            width=int(os.getenv('VIDEO_WIDTH', '1920')),
            height=int(os.getenv('VIDEO_HEIGHT', '1080')),
            fps=int(os.getenv('FPS', '30')),
            duration_minutes=int(os.getenv('DURATION_MINUTES', '10')),
            videos_per_day=int(os.getenv('VIDEOS_PER_DAY', '1')),
            use_moviepy=_parse_bool(os.getenv('USE_MOVIEPY', 'true')),
        )


@dataclass
class GeminiSettings:
    """Gemini API settings."""
    api_key: Optional[str]
    model: str
    temperature: float
    max_output_tokens: int

    @classmethod
    def from_env(cls) -> 'GeminiSettings':
        return cls(
            api_key=os.getenv('GEMINI_API_KEY'),
            model=os.getenv('GEMINI_MODEL', 'gemini-3-flash-preview'),
            temperature=float(os.getenv('GEMINI_TEMPERATURE', '0.9')),
            max_output_tokens=int(os.getenv('GEMINI_MAX_TOKENS', '8192')),
        )


@dataclass
class GeminiTTSSettings:
    """Gemini TTS settings."""
    model: str
    male_voice: str
    female_voice: str

    @classmethod
    def from_env(cls) -> 'GeminiTTSSettings':
        return cls(
            model=os.getenv('GEMINI_TTS_MODEL', 'gemini-2.5-flash-preview-tts'),
            male_voice=os.getenv('GEMINI_TTS_MALE_VOICE', 'Zephyr'),
            female_voice=os.getenv('GEMINI_TTS_FEMALE_VOICE', 'Aoede'),
        )


@dataclass
class WhisperSettings:
    """Whisper STT settings."""
    enabled: bool
    model_size: str

    @classmethod
    def from_env(cls) -> 'WhisperSettings':
        return cls(
            enabled=_parse_bool(os.getenv('USE_WHISPER_STT', 'true')),
            model_size=os.getenv('WHISPER_MODEL_SIZE', 'base'),
        )


@dataclass
class ElevenLabsSettings:
    """ElevenLabs API settings."""
    api_key: Optional[str]
    use_for_stt: bool

    @classmethod
    def from_env(cls) -> 'ElevenLabsSettings':
        return cls(
            api_key=os.getenv('ELEVENLABS_API_KEY'),
            use_for_stt=_parse_bool(os.getenv('USE_ELEVENLABS_STT', 'false')),
        )


@dataclass
class WebSearchSettings:
    """Web search settings."""
    enabled: bool
    api_key: Optional[str]

    @classmethod
    def from_env(cls) -> 'WebSearchSettings':
        return cls(
            enabled=_parse_bool(os.getenv('USE_WEB_SEARCH', 'true')),
            api_key=os.getenv('SERPER_API_KEY'),
        )


@dataclass
class YouTubeSettings:
    """YouTube upload settings."""
    upload_enabled: bool
    privacy_status: str
    post_comments: bool
    playlist_id: Optional[str]

    @classmethod
    def from_env(cls) -> 'YouTubeSettings':
        return cls(
            upload_enabled=_parse_bool(os.getenv('YOUTUBE_UPLOAD_ENABLED', 'false')),
            privacy_status=os.getenv('YOUTUBE_PRIVACY_STATUS', 'private'),
            post_comments=_parse_bool(os.getenv('YOUTUBE_POST_COMMENTS', 'false')),
            playlist_id=os.getenv('YOUTUBE_PLAYLIST_ID'),
        )


@dataclass
class PodcastAPISettings:
    """Podcast API settings."""
    enabled: bool
    url: str

    @classmethod
    def from_env(cls) -> 'PodcastAPISettings':
        return cls(
            enabled=_parse_bool(os.getenv('PODCAST_API_ENABLED', 'false')),
            url=os.getenv('PODCAST_API_URL', 'https://pg-admin.takezou.com/api/podcasts'),
        )


@dataclass
class NotificationSettings:
    """Notification settings."""
    slack_webhook_url: Optional[str]

    @classmethod
    def from_env(cls) -> 'NotificationSettings':
        return cls(
            slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL'),
        )


@dataclass
class Settings:
    """Main settings container."""
    video: VideoSettings
    gemini: GeminiSettings
    gemini_tts: GeminiTTSSettings
    whisper: WhisperSettings
    elevenlabs: ElevenLabsSettings
    web_search: WebSearchSettings
    youtube: YouTubeSettings
    podcast_api: PodcastAPISettings
    notification: NotificationSettings
    topic_category: str

    @classmethod
    def load(cls) -> 'Settings':
        return cls(
            video=VideoSettings.from_env(),
            gemini=GeminiSettings.from_env(),
            gemini_tts=GeminiTTSSettings.from_env(),
            whisper=WhisperSettings.from_env(),
            elevenlabs=ElevenLabsSettings.from_env(),
            web_search=WebSearchSettings.from_env(),
            youtube=YouTubeSettings.from_env(),
            podcast_api=PodcastAPISettings.from_env(),
            notification=NotificationSettings.from_env(),
            topic_category=os.getenv('TOPIC_CATEGORY', 'economics'),
        )


def _parse_bool(value: str) -> bool:
    """
    Parse boolean from environment variable string.

    Accepts: true, yes, 1, t, y (case-insensitive)
    """
    return str(value).lower() in ('true', 'yes', '1', 't', 'y')


# Global settings instance (lazy loaded)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings.load()
    return _settings


if __name__ == "__main__":
    # Test settings loading
    settings = get_settings()
    print(f"Video: {settings.video.width}x{settings.video.height} @ {settings.video.fps}fps")
    print(f"Gemini Model: {settings.gemini.model}")
    print(f"Whisper STT: {'enabled' if settings.whisper.enabled else 'disabled'}")
    print(f"YouTube Upload: {'enabled' if settings.youtube.upload_enabled else 'disabled'}")
