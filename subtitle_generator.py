"""
Subtitle Generator - Creates subtitle frames for video
"""
from pathlib import Path
from typing import List, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont
import subprocess
import os

# Video dimensions (16:9)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

# Subtitle styling
SUBTITLE_FONT_SIZE = 48
SUBTITLE_PADDING = 40
SUBTITLE_BG_COLOR = (0, 0, 0, 180)  # Semi-transparent black
SUBTITLE_TEXT_COLOR = (255, 255, 255)
SPEAKER_A_COLOR = (100, 200, 255)  # Light blue
SPEAKER_B_COLOR = (255, 180, 100)  # Light orange


def get_font(size: int) -> ImageFont.FreeTypeFont:
    """Get a font that supports Japanese characters"""
    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "C:\\Windows\\Fonts\\msgothic.ttc",
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue

    # Fallback to default font
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """Wrap text to fit within max_width"""
    lines = []
    current_line = ""

    for char in text:
        test_line = current_line + char
        bbox = font.getbbox(test_line)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char

    if current_line:
        lines.append(current_line)

    return lines


def create_subtitle_frame(
    background: Image.Image,
    speaker: str,
    text: str,
    font: ImageFont.FreeTypeFont
) -> Image.Image:
    """Create a single frame with subtitle overlay"""
    frame = background.copy()
    draw = ImageDraw.Draw(frame, 'RGBA')

    # Calculate subtitle area
    max_text_width = VIDEO_WIDTH - (SUBTITLE_PADDING * 4)
    lines = wrap_text(text, font, max_text_width)

    # Calculate total height needed
    line_height = font.size + 10
    total_text_height = len(lines) * line_height
    box_height = total_text_height + SUBTITLE_PADDING * 2

    # Draw subtitle background box at bottom
    box_y = VIDEO_HEIGHT - box_height - 50
    draw.rectangle(
        [(SUBTITLE_PADDING, box_y),
         (VIDEO_WIDTH - SUBTITLE_PADDING, box_y + box_height)],
        fill=SUBTITLE_BG_COLOR
    )

    # Draw speaker indicator
    speaker_color = SPEAKER_A_COLOR if speaker == "A" else SPEAKER_B_COLOR
    speaker_text = "▶ " if speaker == "A" else "◀ "
    draw.text(
        (SUBTITLE_PADDING * 2, box_y + SUBTITLE_PADDING // 2),
        speaker_text,
        font=font,
        fill=speaker_color
    )

    # Draw text lines
    y = box_y + SUBTITLE_PADDING
    for line in lines:
        # Center the text
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        draw.text((x, y), line, font=font, fill=SUBTITLE_TEXT_COLOR)
        y += line_height

    return frame


def generate_subtitle_video(
    background_path: Path,
    timing_data: List[Dict],
    output_path: Path,
    fps: int = 30
) -> Path:
    """
    Generate video with animated subtitles.

    Args:
        background_path: Path to background image
        timing_data: List of {"speaker", "text", "start", "end"}
        output_path: Output video path
        fps: Frames per second

    Returns:
        Path to generated video
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load and resize background
    background = Image.open(background_path).convert('RGBA')
    background = background.resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.Resampling.LANCZOS)

    font = get_font(SUBTITLE_FONT_SIZE)

    # Calculate total duration
    total_duration = max(t["end"] for t in timing_data) if timing_data else 10
    total_frames = int(total_duration * fps)

    # Create frames directory
    frames_dir = output_path.parent / "frames"
    frames_dir.mkdir(exist_ok=True)

    print(f"Generating {total_frames} frames...")

    # Generate frames
    current_subtitle_idx = 0
    for frame_num in range(total_frames):
        current_time = frame_num / fps

        # Find current subtitle
        current_subtitle = None
        for t in timing_data:
            if t["start"] <= current_time < t["end"]:
                current_subtitle = t
                break

        if current_subtitle:
            frame = create_subtitle_frame(
                background,
                current_subtitle["speaker"],
                current_subtitle["text"],
                font
            )
        else:
            frame = background.copy()

        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:06d}.png"
        frame.convert('RGB').save(frame_path, 'PNG')

        # Progress indicator
        if frame_num % (fps * 10) == 0:
            print(f"  Progress: {frame_num}/{total_frames} frames")

    # Combine frames into video using ffmpeg
    print("Combining frames into video...")
    video_path = output_path.with_suffix('.mp4')

    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%06d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        str(video_path)
    ], check=True, capture_output=True)

    # Cleanup frames
    print("Cleaning up frames...")
    for f in frames_dir.glob("*.png"):
        f.unlink()
    frames_dir.rmdir()

    return video_path


def add_audio_to_video(video_path: Path, audio_path: Path, output_path: Path) -> Path:
    """Combine video with audio"""
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output_path)
    ], check=True, capture_output=True)

    return output_path
