"""
Video Maker - Creates podcast-style videos with subtitles
"""
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict
from PIL import Image, ImageDraw, ImageFont
import os

# Video dimensions
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

# Subtitle styling
FONT_SIZE = 52
SUBTITLE_MARGIN = 160  # Increased to ensure 2-3 lines of text fit with padding (prevent bottom cutoff)
BOX_PADDING = 30
BOX_OPACITY = 200
# Male speaker: Blue accent
MALE_COLOR = (120, 200, 255)
# Female speaker: Pink accent
FEMALE_COLOR = (255, 150, 180)
# Legacy color names for backward compatibility
SPEAKER_A_COLOR = MALE_COLOR
SPEAKER_B_COLOR = FEMALE_COLOR
TEXT_COLOR = (255, 255, 255)


def get_japanese_font(size: int):
    """Get a font that supports Japanese"""
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
                return ImageFont.truetype(path, size)
            except:
                continue

    return ImageFont.load_default()


def wrap_text(text: str, font, max_width: int) -> List[str]:
    """Wrap text to fit width"""
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


def create_frame_with_subtitle(
    background: Image.Image,
    speaker: str,
    text: str,
    font
) -> Image.Image:
    """Create frame with subtitle overlay"""
    frame = background.copy().convert('RGBA')
    overlay = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Wrap text
    max_width = VIDEO_WIDTH - SUBTITLE_MARGIN * 4
    lines = wrap_text(text, font, max_width)

    # Calculate box dimensions
    line_height = FONT_SIZE + 12
    text_height = len(lines) * line_height
    box_height = text_height + BOX_PADDING * 2 + 20
    box_y = VIDEO_HEIGHT - box_height - SUBTITLE_MARGIN

    # Draw semi-transparent box
    draw.rounded_rectangle(
        [(SUBTITLE_MARGIN, box_y),
         (VIDEO_WIDTH - SUBTITLE_MARGIN, box_y + box_height)],
        radius=15,
        fill=(20, 20, 30, BOX_OPACITY)
    )

    # Draw speaker indicator bar
    # Support both new format (男性/女性) and legacy format (A/B)
    if speaker in ["男性", "A"]:
        bar_color = MALE_COLOR
    elif speaker in ["女性", "B"]:
        bar_color = FEMALE_COLOR
    else:
        bar_color = MALE_COLOR  # Default to male color

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
        x = (VIDEO_WIDTH - text_width) // 2

        # Draw shadow
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 180))
        # Draw text
        draw.text((x, y), line, font=font, fill=TEXT_COLOR + (255,))
        y += line_height

    return Image.alpha_composite(frame, overlay).convert('RGB')


def make_podcast_video(
    background_path: Path,
    timing_data: List[Dict],
    audio_path: Path,
    output_path: Path
) -> Path:
    """
    Create podcast-style video with subtitles.

    Args:
        background_path: Path to background image
        timing_data: List of {"speaker", "text", "start", "end"}
        audio_path: Path to audio file
        output_path: Output video path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create frames directory
    frames_dir = output_path.parent / "frames"
    frames_dir.mkdir(exist_ok=True)

    temp_video = None

    try:
        # Load background
        bg = Image.open(background_path).convert('RGBA')
        bg = bg.resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.Resampling.LANCZOS)

        font = get_japanese_font(FONT_SIZE)

        # Get total duration from audio
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "csv=p=0", str(audio_path)
        ], capture_output=True, text=True)

        try:
            audio_duration = float(result.stdout.strip())
        except:
            audio_duration = max(t["end"] for t in timing_data) if timing_data else 60

        total_frames = int(audio_duration * FPS)

        print(f"Generating {total_frames} frames for {audio_duration:.1f}s video...")

        # Generate frames
        for frame_num in range(total_frames):
            current_time = frame_num / FPS

            # Find current subtitle
            current_sub = None
            for t in timing_data:
                if t["start"] <= current_time < t["end"]:
                    current_sub = t
                    break

            if current_sub:
                frame = create_frame_with_subtitle(
                    bg, current_sub["speaker"], current_sub["text"], font
                )
            else:
                frame = bg.convert('RGB')

            frame.save(frames_dir / f"f_{frame_num:06d}.png", 'PNG')

            if frame_num % (FPS * 5) == 0:
                pct = (frame_num / total_frames) * 100
                print(f"  Frame generation: {pct:.0f}%")

        print("Encoding video...")

        # Create video from frames
        temp_video = output_path.parent / "temp_video.mp4"
        subprocess.run([
            "ffmpeg", "-y",
            "-framerate", str(FPS),
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
        # Cleanup: Always execute, even if error occurs
        print("Cleaning up...")
        if temp_video and temp_video.exists():
            temp_video.unlink()
        # Remove frames directory and all contents
        if frames_dir.exists():
            try:
                shutil.rmtree(frames_dir, ignore_errors=True)
                print(f"  Cleaned up frames directory")
            except Exception as e:
                print(f"  Warning: Could not remove frames directory: {e}")


# Keep old function for compatibility
def make_slideshow_video(images, durations, narration_path: Path, out_path: Path):
    """Legacy slideshow video maker"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    list_txt = out_path.parent / "images.txt"

    with open(list_txt, "w") as f:
        for img, dur in zip(images, durations):
            f.write(f"file '{img}'\n")
            f.write(f"duration {dur}\n")

    tmp = out_path.parent / "tmp.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_txt),
        "-vsync", "vfr", "-pix_fmt", "yuv420p", str(tmp)
    ], check=True)

    subprocess.run([
        "ffmpeg", "-y", "-i", str(tmp), "-i", str(narration_path),
        "-c:v", "copy", "-c:a", "aac", "-shortest", str(out_path)
    ], check=True)

    return out_path
