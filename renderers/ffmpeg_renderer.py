"""
FFmpeg-based video renderer.

Fast PIL-based renderer for generating podcast-style videos.
"""
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image, ImageDraw, ImageFont
import os

from renderers.base import VideoRenderer, RendererFactory
from config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, FPS,
    FONT_SIZE, SUBTITLE_MARGIN, BOX_PADDING,
    MALE_COLOR, FEMALE_COLOR, TEXT_COLOR, BOX_OPACITY,
    SPEAKER_MALE, SPEAKER_FEMALE
)


class FFMpegRenderer(VideoRenderer):
    """
    FFmpeg-based video renderer using PIL for subtitle rendering.

    Fast rendering by:
    1. Pre-rendering all frames with PIL
    2. Using FFmpeg to encode frames to video
    3. Adding audio track

    Pros:
    - Fast rendering
    - No MoviePy dependency
    - Reliable frame-by-frame rendering

    Cons:
    - No fade effects
    - Higher memory usage (frames stored on disk)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_cache = None

    def is_available(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def render(
        self,
        background_path: Path,
        timing_data: List[Dict[str, Any]],
        audio_path: Path,
        output_path: Path
    ) -> Path:
        """
        Render video with FFmpeg.

        Args:
            background_path: Path to background image
            timing_data: List of subtitle timing data
            audio_path: Path to audio file
            output_path: Output video path

        Returns:
            Path to created video
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        frames_dir = output_path.parent / "frames"
        frames_dir.mkdir(exist_ok=True)

        temp_video = None

        try:
            # Load and resize background
            bg = Image.open(background_path).convert('RGBA')
            bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)

            font = self._get_japanese_font()

            # Get audio duration
            audio_duration = self._get_audio_duration(audio_path)
            total_frames = int(audio_duration * self.fps)

            print(f"Generating {total_frames} frames for {audio_duration:.1f}s video...")

            # Generate frames
            for frame_num in range(total_frames):
                current_time = frame_num / self.fps
                current_sub = self._find_subtitle_at_time(timing_data, current_time)

                if current_sub:
                    frame = self._create_frame_with_subtitle(
                        bg, current_sub["speaker"], current_sub["text"], font
                    )
                else:
                    frame = bg.convert('RGB')

                frame.save(frames_dir / f"f_{frame_num:06d}.png", 'PNG')

                if frame_num % (self.fps * 1) == 0:
                    pct = (frame_num / total_frames) * 100
                    print(f"  Frame generation: {pct:.0f}%")

            print("Encoding video...")

            # Create video from frames
            temp_video = output_path.parent / "temp_video.mp4"
            subprocess.run([
                "ffmpeg", "-y",
                "-framerate", str(self.fps),
                "-i", str(frames_dir / "f_%06d.png"),
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "20",
                "-pix_fmt", "yuv420p",
                str(temp_video)
            ], check=True, capture_output=True)

            # Add audio
            print("Adding audio...")
            subprocess.run([
                "ffmpeg", "-y",
                "-i", str(temp_video),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(output_path)
            ], check=True, capture_output=True)

            print(f"Video created: {output_path}")
            return output_path

        finally:
            print("Cleaning up...")
            if temp_video and temp_video.exists():
                temp_video.unlink()
            if frames_dir.exists():
                try:
                    shutil.rmtree(frames_dir, ignore_errors=True)
                    print(f"  Cleaned up frames directory")
                except Exception as e:
                    print(f"  Warning: Could not remove frames directory: {e}")

    def _format_color(self, color: Any) -> Any:
        """FFmpeg renderer uses tuples."""
        return color if isinstance(color, tuple) else tuple(color)

    def _get_japanese_font(self):
        """Get a font that supports Japanese."""
        if self.font_cache:
            return self.font_cache

        font_paths = [
            # Linux (Docker)
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/google-noto-cjk/NotoSansCJKjp-Regular.otf",
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
            # macOS
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            # Windows
            "C:\\Windows\\Fonts\\msgothic.ttc",
        ]

        for path in font_paths:
            if os.path.exists(path):
                try:
                    self.font_cache = ImageFont.truetype(path, FONT_SIZE)
                    return self.font_cache
                except:
                    continue

        self.font_cache = ImageFont.load_default()
        return self.font_cache

    def _wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """Wrap text to fit width."""
        lines = []
        current = ""

        for char in text:
            test = current + char
            bbox = font.getbbox(test)
            if bbox[2] - bbox[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = char

        if current:
            lines.append(current)

        return lines or [""]

    def _create_frame_with_subtitle(
        self,
        background: Image.Image,
        speaker: str,
        text: str,
        font
    ) -> Image.Image:
        """Create frame with subtitle overlay."""
        frame = background.copy().convert('RGBA')
        overlay = Image.new('RGBA', frame.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Wrap text
        max_width = self.width - SUBTITLE_MARGIN * 4
        lines = self._wrap_text(text, font, max_width)

        # Calculate box dimensions
        line_height = FONT_SIZE + 12
        text_height = len(lines) * line_height
        box_height = text_height + BOX_PADDING * 2 + 20
        box_y = self.height - box_height - SUBTITLE_MARGIN

        # Draw semi-transparent box
        draw.rounded_rectangle(
            [(SUBTITLE_MARGIN, box_y),
             (self.width - SUBTITLE_MARGIN, box_y + box_height)],
            radius=15,
            fill=(20, 20, 30, BOX_OPACITY)
        )

        # Draw speaker indicator bar
        bar_color = self.get_speaker_color(speaker)
        draw.rectangle(
            [(SUBTITLE_MARGIN, box_y),
             (SUBTITLE_MARGIN + 8, box_y + box_height)],
            fill=bar_color + (255,)
        )

        # Draw text
        y = box_y + BOX_PADDING + 10
        for line in lines:
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2

            # Draw shadow
            draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 180))
            # Draw text
            draw.text((x, y), line, font=font, fill=TEXT_COLOR + (255,))
            y += line_height

        return Image.alpha_composite(frame, overlay).convert('RGB')

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio file duration."""
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "csv=p=0", str(audio_path)
        ], capture_output=True, text=True)

        try:
            return float(result.stdout.strip())
        except:
            # Fallback to default
            return 600.0

    def _find_subtitle_at_time(self, timing_data: List[Dict], current_time: float) -> Dict:
        """Find the subtitle that should be displayed at current_time."""
        for t in timing_data:
            if t["start"] <= current_time < t["end"]:
                return t
        return None


# Register the renderer
RendererFactory.register("ffmpeg", FFMpegRenderer)
