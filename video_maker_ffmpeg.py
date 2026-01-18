"""
FFmpeg-based Video Maker - High performance video generation
Replaces MoviePy with direct FFmpeg commands for better stability and speed.
"""
import subprocess
import os
import shutil
from pathlib import Path
from typing import List, Dict
from PIL import Image, ImageDraw

try:
    from subtitle_generator import generate_ass_subtitles
except ImportError:
    # Fallback/Local import
    import sys
    sys.path.append(str(Path(__file__).parent))
    from subtitle_generator import generate_ass_subtitles

# Video settings
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
GRADIENT_HEIGHT_RATIO = 0.35


def _get_ffmpeg_path() -> str:
    """
    Get FFmpeg path, preferring ffmpeg-full which has libass support.

    Returns:
        Path to FFmpeg executable
    """
    # Priority order for FFmpeg
    paths_to_try = [
        "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",  # Has libass support
        "/opt/homebrew/bin/ffmpeg",  # Regular ffmpeg
        "/usr/local/bin/ffmpeg",
    ]

    for path in paths_to_try:
        if Path(path).exists():
            return path

    # Fallback to system path
    result = shutil.which("ffmpeg")
    return result if result else "ffmpeg"

def _apply_gradient_to_background(background_path: Path, output_path: Path) -> Path:
    """Apply gradient to background image using pure PIL (no numpy)"""
    try:
        with Image.open(background_path) as bg:
            bg = bg.convert('RGBA')
            bg = bg.resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.Resampling.LANCZOS)
            width, height = bg.size
            
            # Create gradient overlay
            # Height of the gradient area
            gradient_height = int(height * GRADIENT_HEIGHT_RATIO)
            gradient_start = height - gradient_height
            
            # Create a new transparent image for the gradient
            gradient_img = Image.new('RGBA', (width, height), (0,0,0,0))
            draw = ImageDraw.Draw(gradient_img)
            
            # Draw lines with increasing opacity
            for y in range(gradient_height):
                # Alpha goes from 0 to 200
                progress = y / gradient_height
                alpha = int(200 * (progress ** 1.5))
                # Draw a horizontal line
                draw.line(
                    [(0, gradient_start + y), (width, gradient_start + y)], 
                    fill=(0, 0, 0, alpha)
                )
            
            # Composite
            result = Image.alpha_composite(bg, gradient_img)
            result = result.convert('RGB')
            result.save(output_path, 'PNG')
            
            return output_path
    except Exception as e:
        print(f"[VideoMaker] Gradient application failed: {e}")
        return background_path

def make_podcast_video_ffmpeg(
    background_path: Path,
    timing_data: List[Dict],
    audio_path: Path,
    output_path: Path
) -> Path:
    """
    Create video using direct FFmpeg commands.
    
    Args:
        background_path: Path to background image
        timing_data: List of subtitle timing data
        audio_path: Path to audio file
        output_path: Output video path
        
    Returns:
        Path to created video
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("[VideoMaker] Using FFmpeg for rendering...")
    
    # 1. Prepare Background (Resize + Gradient)
    bg_processed = output_path.parent / "bg_processed.png"
    _apply_gradient_to_background(background_path, bg_processed)
    
    # 2. Generate Subtitles (.ass)
    ass_path = output_path.parent / "subtitles.ass"
    generate_ass_subtitles(timing_data, ass_path)
    print(f"[VideoMaker] Generated subtitles at {ass_path}")
    
    # 3. Render Video with FFmpeg
    # Inputs:
    # - loop 1: Loop the image
    # - i bg: Background image
    # - i audio: Audio file
    # Filters:
    # - subtitles: Burn in subtitles
    # - shortest: Stop when audio ends

    # Escape subtitle path for FFmpeg subtitles filter
    # Use filename= prefix to avoid path parsing issues
    ass_escaped = str(ass_path).replace(":", r"\:").replace("'", r"\'")

    cmd = [
        _get_ffmpeg_path(), "-y",
        "-loop", "1",
        "-i", str(bg_processed),
        "-i", str(audio_path),
        "-vf", f"subtitles=filename='{ass_escaped}'",
        "-c:v", "libx264",
        "-preset", "medium",
        "-tune", "stillimage",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    
    print(f"[VideoMaker] Running FFmpeg command...")
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"[VideoMaker] Video created successfully: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg failed: {e.stderr.decode()}")
        raise RuntimeError("Video rendering failed")
        
    return output_path

# Compatibility wrapper
def make_podcast_video(
    background_path: Path,
    timing_data: List[Dict],
    audio_path: Path,
    output_path: Path,
    use_moviepy: bool = False # Ignored, always uses FFmpeg in this module
) -> Path:
    return make_podcast_video_ffmpeg(
        background_path, timing_data, audio_path, output_path
    )

if __name__ == "__main__":
    print("FFmpeg Video Maker Module Loaded")
