"""
Unit tests for video renderer modules.

Tests cover:
- Renderer factory
- FFmpeg renderer
- MoviePy renderer (when available)
"""
import os
from pathlib import Path

# Set test environment before importing renderers
os.environ['USE_MOVIEPY'] = 'false'


def test_renderer_factory_list_available():
    """Test that RendererFactory can list available renderers."""
    from renderers import RendererFactory

    available = RendererFactory.list_available()
    assert isinstance(available, list)
    assert len(available) > 0
    # FFmpeg should always be available in the Docker environment
    assert 'ffmpeg' in available


def test_renderer_factory_create_auto():
    """Test creating a renderer with 'auto' backend."""
    from renderers import RendererFactory

    renderer = RendererFactory.create('auto')
    assert renderer is not None
    assert renderer.is_available() is True


def test_renderer_factory_create_ffmpeg():
    """Test creating FFmpeg renderer explicitly."""
    from renderers import RendererFactory

    renderer = RendererFactory.create('ffmpeg')
    assert renderer is not None
    assert renderer.is_available() is True
    assert renderer.width == 1920
    assert renderer.height == 1080
    assert renderer.fps == 30


def test_ffmpeg_renderer_get_speaker_color():
    """Test FFmpeg renderer speaker color selection."""
    from renderers import RendererFactory

    renderer = RendererFactory.create('ffmpeg')

    # Test male speakers
    male_color = renderer.get_speaker_color("男性", as_hex=False)
    assert male_color == (120, 200, 255)

    male_color_a = renderer.get_speaker_color("A", as_hex=False)
    assert male_color_a == (120, 200, 255)

    # Test female speakers
    female_color = renderer.get_speaker_color("女性", as_hex=False)
    assert female_color == (255, 150, 180)

    female_color_b = renderer.get_speaker_color("B", as_hex=False)
    assert female_color_b == (255, 150, 180)

    # Test default (unknown speaker)
    default_color = renderer.get_speaker_color("Unknown", as_hex=False)
    assert default_color == (120, 200, 255)  # Defaults to male


def test_render_video_import():
    """Test that render_video convenience function is importable."""
    from renderers import render_video

    assert callable(render_video)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
