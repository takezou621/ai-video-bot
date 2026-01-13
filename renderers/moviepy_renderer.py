"""
MoviePy-based video renderer.

High-quality renderer with fade effects for smooth transitions.
"""
from pathlib import Path
from typing import List, Dict, Any
import os

try:
    from moviepy import (
        ImageClip, AudioFileClip, TextClip, CompositeVideoClip,
        vfx
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

try:
    from PIL import Image
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from renderers.base import VideoRenderer, RendererFactory
from config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, FPS,
    FONT_SIZE, MALE_COLOR_HEX, FEMALE_COLOR_HEX,
    TEXT_COLOR_HEX, BG_COLOR,
    SUBTITLE_BOX_HEIGHT, SUBTITLE_Y_POSITION,
    MAX_CHARS_PER_LINE, GRADIENT_HEIGHT_RATIO,
    SPEAKER_MALE, SPEAKER_FEMALE
)


class MoviePyRenderer(VideoRenderer):
    """
    MoviePy-based video renderer with high-quality output.

    Features:
    - Fade effects for smooth subtitle transitions
    - Gradient overlay for better text readability
    - Single-line subtitle display
    - Professional quality output

    Pros:
    - High-quality rendering
    - Smooth fade effects
    - Better text rendering

    Cons:
    - Slower than FFmpeg renderer
    - Requires MoviePy dependency
    - More complex rendering pipeline
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_cache = None

    def is_available(self) -> bool:
        """Check if MoviePy is available."""
        return MOVIEPY_AVAILABLE and PIL_AVAILABLE

    def render(
        self,
        background_path: Path,
        timing_data: List[Dict[str, Any]],
        audio_path: Path,
        output_path: Path
    ) -> Path:
        """
        Render video with MoviePy.

        Args:
            background_path: Path to background image
            timing_data: List of subtitle timing data
            audio_path: Path to audio file
            output_path: Output video path

        Returns:
            Path to created video
        """
        if not self.is_available():
            raise RuntimeError("MoviePy is not available")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        print("Creating video with MoviePy...")

        # Apply gradient to background
        gradient_bg_path = output_path.parent / "background_gradient.png"
        processed_bg = self._apply_gradient_to_background(background_path, gradient_bg_path)
        print(f"  Applied dark gradient to bottom {int(GRADIENT_HEIGHT_RATIO*100)}% of background")

        # Load audio
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration

        # Create background clip
        background = ImageClip(str(processed_bg)).with_duration(duration)
        background = background.resized((self.width, self.height))

        # Create subtitle clips
        subtitle_clips = []
        font = self._find_japanese_font()

        for i, segment in enumerate(timing_data):
            speaker = segment["speaker"]
            text = segment["text"]
            start = segment["start"]
            end = segment["end"]
            seg_duration = end - start

            if seg_duration <= 0:
                continue

            color = self.get_speaker_color(speaker)

            # Split text into lines
            lines = self._split_text_into_lines(text)
            num_lines = len(lines)

            # Distribute time across lines
            line_duration = seg_duration / num_lines
            current_time = start

            for line_idx, line_text in enumerate(lines):
                line_start = current_time
                line_end = current_time + line_duration
                current_time = line_end

                # Ensure last line ends at segment end
                if line_idx == num_lines - 1:
                    line_end = end
                    line_duration = line_end - line_start

                if line_duration <= 0:
                    continue

                try:
                    txt_clip = TextClip(
                        text=line_text,
                        font_size=FONT_SIZE,
                        color=TEXT_COLOR_HEX,
                        font=font,
                        method='caption',
                        size=(self.width - 100, SUBTITLE_BOX_HEIGHT),
                        text_align='center',
                        stroke_color=color,
                        stroke_width=3,
                    )

                    txt_clip = txt_clip.with_position(('center', SUBTITLE_Y_POSITION))
                    txt_clip = txt_clip.with_start(line_start)
                    txt_clip = txt_clip.with_duration(line_duration)

                    # Add fade effects
                    if line_duration > 0.3:
                        fade_time = min(0.1, line_duration * 0.15)
                        txt_clip = txt_clip.with_effects([
                            vfx.FadeIn(fade_time),
                            vfx.FadeOut(fade_time)
                        ])

                    subtitle_clips.append(txt_clip)

                except Exception as e:
                    print(f"  Warning: Failed to create subtitle for segment {i}, line {line_idx}: {e}")
                    # Try fallback
                    try:
                        txt_clip = TextClip(
                            text=line_text[:40],
                            font_size=FONT_SIZE,
                            color=TEXT_COLOR_HEX,
                            method='caption',
                            size=(self.width - 100, SUBTITLE_BOX_HEIGHT),
                            text_align='center',
                        )
                        txt_clip = txt_clip.with_position(('center', SUBTITLE_Y_POSITION))
                        txt_clip = txt_clip.with_start(line_start)
                        txt_clip = txt_clip.with_duration(line_duration)
                        subtitle_clips.append(txt_clip)
                    except:
                        continue

        # Composite all clips
        bg_clips = [background]
        print(f"  Compositing {len(bg_clips)} background clips and {len(subtitle_clips)} subtitle clips...")
        video = CompositeVideoClip(
            bg_clips + subtitle_clips,
            size=(self.width, self.height)
        )

        # Set audio
        video = video.with_audio(audio)

        # Write video file
        print("  Rendering video (this may take a while)...")
        video.write_videofile(
            str(output_path),
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=str(output_path.parent / 'temp-audio.m4a'),
            remove_temp=True,
            preset='medium',
            threads=4,
            logger=None
        )

        # Cleanup
        video.close()
        audio.close()

        print(f"Video created: {output_path}")
        return output_path

    def _format_color(self, color: Any) -> str:
        """MoviePy renderer uses hex strings."""
        if isinstance(color, tuple):
            return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        return color

    def _split_text_into_lines(self, text: str, max_chars: int = MAX_CHARS_PER_LINE) -> List[str]:
        """Split text into lines for subtitle display."""
        if len(text) <= max_chars:
            return [text]

        lines = []
        remaining = text

        # Japanese break points
        break_chars = '。、！？）」』】・'
        no_start_chars = 'はがのをにでとへもやかな'

        while remaining:
            if len(remaining) <= max_chars:
                lines.append(remaining)
                break

            # Find best break point
            best_break = max_chars

            # Look for punctuation
            for i in range(max_chars - 1, max_chars // 2, -1):
                if remaining[i] in break_chars:
                    best_break = i + 1
                    break
            else:
                # Avoid breaking before particles
                for i in range(max_chars - 1, max_chars // 2, -1):
                    if remaining[i] not in no_start_chars:
                        best_break = i
                        break

            lines.append(remaining[:best_break])
            remaining = remaining[best_break:]

        return lines

    def _create_gradient_overlay(self, width: int, height: int, gradient_ratio: float = 0.4):
        """Create gradient overlay array."""
        if not PIL_AVAILABLE:
            return None

        gradient_height = int(height * gradient_ratio)
        gradient_start = height - gradient_height

        overlay = np.zeros((height, width, 4), dtype=np.uint8)

        for y in range(gradient_start, height):
            progress = (y - gradient_start) / gradient_height
            alpha = int(200 * (progress ** 1.5))
            overlay[y, :, 3] = alpha

        return overlay

    def _apply_gradient_to_background(
        self,
        background_path: Path,
        output_path: Path
    ) -> Path:
        """Apply gradient to background image."""
        if not PIL_AVAILABLE:
            return background_path

        try:
            with Image.open(background_path) as bg:
                bg = bg.convert('RGBA')
                width, height = bg.size

                gradient = self._create_gradient_overlay(width, height, GRADIENT_HEIGHT_RATIO)
                if gradient is None:
                    return background_path

                gradient_img = Image.fromarray(gradient, 'RGBA')
                result = Image.alpha_composite(bg, gradient_img)
                result = result.convert('RGB')
                result.save(output_path, 'PNG')

                return output_path
        except Exception as e:
            print(f"  Warning: Failed to apply gradient: {e}")
            return background_path

    def _find_japanese_font(self) -> str:
        """Find a Japanese font for MoviePy."""
        if self.font_cache:
            return self.font_cache

        font_paths = [
            # Linux (Docker)
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            # macOS
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
            "Hiragino-Sans-GB",
            # Windows
            "msgothic",
            # Fallback
            "Arial-Unicode-MS"
        ]

        for font in font_paths:
            if os.path.exists(font):
                self.font_cache = font
                return font

        self.font_cache = "Arial"
        return self.font_cache


# Register the renderer
if MOVIEPY_AVAILABLE:
    RendererFactory.register("moviepy", MoviePyRenderer)
