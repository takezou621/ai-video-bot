"""
Video renderers module for AI Video Bot.

Exports the renderer abstraction layer and implementations.
"""
from renderers.base import (
    VideoRenderer,
    RendererFactory,
    render_video,
)

# Import implementations to register them
from renderers.ffmpeg_renderer import FFMpegRenderer
from renderers.moviepy_renderer import MoviePyRenderer

__all__ = [
    'VideoRenderer',
    'RendererFactory',
    'render_video',
    'FFMpegRenderer',
    'MoviePyRenderer',
]
