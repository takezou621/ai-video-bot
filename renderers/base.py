"""
Video renderer abstraction layer for AI Video Bot.

Provides a unified interface for different video rendering backends:
- FFmpeg (fast, PIL-based)
- MoviePy (high quality, with fade effects)

This allows easy switching between backends and adding new ones.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, FPS,
    FONT_SIZE, MALE_COLOR, FEMALE_COLOR,
    SPEAKER_MALE, SPEAKER_FEMALE
)


class VideoRenderer(ABC):
    """
    Abstract base class for video renderers.

    All renderer implementations must inherit from this class
    and implement the required methods.
    """

    def __init__(
        self,
        width: int = VIDEO_WIDTH,
        height: int = VIDEO_HEIGHT,
        fps: int = FPS
    ):
        """
        Initialize the renderer.

        Args:
            width: Video width in pixels
            height: Video height in pixels
            fps: Frames per second
        """
        self.width = width
        self.height = height
        self.fps = fps

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the renderer is available (dependencies installed).

        Returns:
            True if renderer can be used
        """
        pass

    @abstractmethod
    def render(
        self,
        background_path: Path,
        timing_data: List[Dict[str, Any]],
        audio_path: Path,
        output_path: Path
    ) -> Path:
        """
        Render a podcast-style video with subtitles.

        Args:
            background_path: Path to background image
            timing_data: List of {"speaker", "text", "start", "end"}
            audio_path: Path to audio file
            output_path: Output video path

        Returns:
            Path to created video
        """
        pass

    def get_speaker_color(self, speaker: str) -> Any:
        """
        Get color for speaker.

        Args:
            speaker: Speaker identifier

        Returns:
            Color in the format expected by the renderer
        """
        if speaker in [SPEAKER_MALE, "A"]:
            return self._format_color(MALE_COLOR)
        elif speaker in [SPEAKER_FEMALE, "B"]:
            return self._format_color(FEMALE_COLOR)
        return self._format_color(MALE_COLOR)  # Default

    @abstractmethod
    def _format_color(self, color: Any) -> Any:
        """
        Format color for the specific renderer.

        Args:
            color: Color in some format

        Returns:
            Color in renderer-specific format
        """
        pass


class RendererFactory:
    """Factory for creating video renderers."""

    _renderers: Dict[str, type] = {}
    _default_renderer: Optional[str] = None

    @classmethod
    def register(cls, name: str, renderer_class: type) -> None:
        """
        Register a renderer.

        Args:
            name: Renderer name
            renderer_class: Renderer class (must inherit from VideoRenderer)
        """
        if not issubclass(renderer_class, VideoRenderer):
            raise ValueError(f"{renderer_class} must inherit from VideoRenderer")
        cls._renderers[name] = renderer_class

    @classmethod
    def create(cls, backend: str = "auto", **kwargs) -> VideoRenderer:
        """
        Create a renderer instance.

        Args:
            backend: Renderer name ("auto", "ffmpeg", "moviepy")
            **kwargs: Additional arguments for renderer

        Returns:
            VideoRenderer instance
        """
        if backend == "auto":
            backend = cls._get_best_available()

        if backend not in cls._renderers:
            available = ", ".join(cls._renderers.keys())
            raise ValueError(
                f"Unknown renderer: {backend}. Available: {available}"
            )

        renderer = cls._renderers[backend](**kwargs)

        if not renderer.is_available():
            # Fallback to next best
            if backend != "ffmpeg":
                return cls.create("ffmpeg", **kwargs)
            raise RuntimeError(f"Renderer '{backend}' is not available and no fallback")

        return renderer

    @classmethod
    def _get_best_available(cls) -> str:
        """
        Get the best available renderer.

        Returns:
            Name of the best available renderer
        """
        # Priority: moviepy > ffmpeg
        for name in ["moviepy", "ffmpeg"]:
            if name in cls._renderers:
                renderer = cls._renderers[name]()
                if renderer.is_available():
                    return name

        raise RuntimeError("No video renderer available")

    @classmethod
    def set_default(cls, renderer: str) -> None:
        """Set the default renderer."""
        cls._default_renderer = renderer

    @classmethod
    def list_available(cls) -> List[str]:
        """
        List all available renderers.

        Returns:
            List of renderer names that are available
        """
        available = []
        for name, renderer_class in cls._renderers.items():
            renderer = renderer_class()
            if renderer.is_available():
                available.append(name)
        return available


def render_video(
    background_path: Path,
    timing_data: List[Dict[str, Any]],
    audio_path: Path,
    output_path: Path,
    backend: str = "auto",
    **kwargs
) -> Path:
    """
    Convenience function to render a video.

    Args:
        background_path: Path to background image
        timing_data: List of {"speaker", "text", "start", "end"}
        audio_path: Path to audio file
        output_path: Output video path
        backend: Renderer to use ("auto", "ffmpeg", "moviepy")
        **kwargs: Additional arguments for renderer

    Returns:
        Path to created video
    """
    renderer = RendererFactory.create(backend, **kwargs)
    return renderer.render(background_path, timing_data, audio_path, output_path)


if __name__ == "__main__":
    # Test renderer factory
    print(f"Available renderers: {RendererFactory.list_available()}")
