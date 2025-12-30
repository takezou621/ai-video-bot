"""
MoviePy-based Video Maker - Higher quality subtitle rendering
Based on the Zenn article's approach using MoviePy
"""
from pathlib import Path
from typing import List, Dict
import os
import numpy as np

try:
    from moviepy import (
        ImageClip, AudioFileClip, TextClip, CompositeVideoClip,
        concatenate_videoclips, vfx
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("MoviePy not available, using fallback")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# Video settings
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

# Subtitle styling
FONT_SIZE = 52
# Male speaker: Blue accent
MALE_COLOR = '#78C8FF'
# Female speaker: Pink accent
FEMALE_COLOR = '#FF96B4'
# Legacy color names for backward compatibility
SPEAKER_A_COLOR = MALE_COLOR
SPEAKER_B_COLOR = FEMALE_COLOR
TEXT_COLOR = 'white'
BG_COLOR = 'rgba(20,20,30,0.85)'

# Bottom gradient settings
GRADIENT_HEIGHT_RATIO = 0.35  # Bottom 35% of the image
GRADIENT_OPACITY = 0.7  # Maximum opacity at the bottom


def _create_gradient_overlay(width: int, height: int, gradient_ratio: float = 0.4) -> np.ndarray:
    """
    Create a gradient overlay image that darkens the bottom portion.

    Args:
        width: Image width
        height: Image height
        gradient_ratio: Ratio of image height to apply gradient (0.4 = bottom 40%)

    Returns:
        RGBA numpy array with gradient
    """
    # Create gradient array
    gradient_height = int(height * gradient_ratio)
    gradient_start = height - gradient_height

    # Create RGBA array (transparent at top, black at bottom)
    overlay = np.zeros((height, width, 4), dtype=np.uint8)

    for y in range(gradient_start, height):
        # Calculate alpha (0 at gradient_start, max at bottom)
        progress = (y - gradient_start) / gradient_height
        # Use ease-in curve for smoother gradient
        alpha = int(200 * (progress ** 1.5))  # Max alpha 200 (out of 255)
        overlay[y, :, 3] = alpha  # Set alpha channel
        # RGB stays 0 (black)

    return overlay


def _apply_gradient_to_background(background_path: Path, output_path: Path) -> Path:
    """
    Apply a dark gradient to the bottom portion of the background image.

    Args:
        background_path: Original background image path
        output_path: Path to save the processed image

    Returns:
        Path to the processed image
    """
    if not PIL_AVAILABLE:
        return background_path

    try:
        with Image.open(background_path) as bg:
            bg = bg.convert('RGBA')
            width, height = bg.size

            # Create gradient overlay
            gradient = _create_gradient_overlay(width, height, GRADIENT_HEIGHT_RATIO)
            gradient_img = Image.fromarray(gradient, 'RGBA')

            # Composite gradient over background
            result = Image.alpha_composite(bg, gradient_img)

            # Save as RGB (no alpha needed for video)
            result = result.convert('RGB')
            result.save(output_path, 'PNG')

            return output_path
    except Exception as e:
        print(f"  Warning: Failed to apply gradient: {e}")
        return background_path


def make_podcast_video_moviepy(
    background_path: Path,
    timing_data: List[Dict],
    audio_path: Path,
    output_path: Path
) -> Path:
    """
    Create podcast-style video using MoviePy for higher quality.

    Args:
        background_path: Path to background image
        timing_data: List of {"speaker", "text", "start", "end"}
        audio_path: Path to audio file
        output_path: Output video path

    Returns:
        Path to created video
    """
    if not MOVIEPY_AVAILABLE:
        # Fallback to PIL-based video maker
        from video_maker import make_podcast_video
        return make_podcast_video(background_path, timing_data, audio_path, output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Creating video with MoviePy...")

    # Apply gradient to background for better subtitle readability
    gradient_bg_path = output_path.parent / "background_gradient.png"
    processed_bg = _apply_gradient_to_background(Path(background_path), gradient_bg_path)
    print(f"  Applied dark gradient to bottom {int(GRADIENT_HEIGHT_RATIO*100)}% of background")

    # Load audio
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration

    # Create background clip with gradient
    background = ImageClip(str(processed_bg)).with_duration(duration)
    background = background.resized((VIDEO_WIDTH, VIDEO_HEIGHT))

    # Create subtitle clips
    subtitle_clips = []

    for i, segment in enumerate(timing_data):
        speaker = segment["speaker"]
        text = segment["text"]
        start = segment["start"]
        end = segment["end"]
        seg_duration = end - start

        if seg_duration <= 0:
            continue

        # Choose color based on speaker
        # Support both new format (男性/女性) and legacy format (A/B)
        if speaker in ["男性", "A"]:
            color = MALE_COLOR
        elif speaker in ["女性", "B"]:
            color = FEMALE_COLOR
        else:
            color = MALE_COLOR  # Default to male color

        try:
            # Create text clip with MoviePy
            # Try to use Japanese font
            font = _find_japanese_font()

            txt_clip = TextClip(
                text=text,
                font_size=FONT_SIZE,
                color=TEXT_COLOR,
                font=font,
                size=(VIDEO_WIDTH - 200, None),
                method='caption',
                text_align='center',
                stroke_color=color,
                stroke_width=2
            )

            # Get the actual height of the text clip
            txt_height = txt_clip.h if hasattr(txt_clip, 'h') else 150

            # Position text so its BOTTOM edge is at a fixed distance from video bottom
            # This ensures multi-line text never gets cut off
            bottom_margin = 80  # Distance from bottom of video to bottom of text
            y_position = VIDEO_HEIGHT - bottom_margin - txt_height

            # Ensure y_position is within gradient area (bottom 35%)
            gradient_top = int(VIDEO_HEIGHT * (1 - GRADIENT_HEIGHT_RATIO))
            if y_position < gradient_top:
                y_position = gradient_top + 20  # Keep text in darkened area

            txt_clip = txt_clip.with_position(('center', y_position))
            txt_clip = txt_clip.with_start(start)
            txt_clip = txt_clip.with_duration(seg_duration)

            # Add fade effects for smoother transitions
            if seg_duration > 0.5:
                txt_clip = txt_clip.with_effects([
                    vfx.FadeIn(0.15),
                    vfx.FadeOut(0.15)
                ])

            subtitle_clips.append(txt_clip)

        except Exception as e:
            print(f"  Warning: Failed to create subtitle for segment {i}: {e}")
            # Create simple text clip as fallback
            try:
                txt_clip = TextClip(
                    text=text[:100],  # Limit length
                    font_size=FONT_SIZE,
                    color=TEXT_COLOR,
                    method='label'
                )
                # Use bottom-aligned positioning for fallback too
                txt_height = txt_clip.h if hasattr(txt_clip, 'h') else 80
                y_position = VIDEO_HEIGHT - 80 - txt_height
                txt_clip = txt_clip.with_position(('center', y_position))
                txt_clip = txt_clip.with_start(start)
                txt_clip = txt_clip.with_duration(min(seg_duration, 5))
                subtitle_clips.append(txt_clip)
            except:
                continue

    # Composite all clips
    print(f"  Compositing {len(subtitle_clips)} subtitle clips...")
    video = CompositeVideoClip(
        [background] + subtitle_clips,
        size=(VIDEO_WIDTH, VIDEO_HEIGHT)
    )

    # Set audio
    video = video.with_audio(audio)

    # Write video file
    print("  Rendering video (this may take a while)...")
    video.write_videofile(
        str(output_path),
        fps=FPS,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile=str(output_path.parent / 'temp-audio.m4a'),
        remove_temp=True,
        preset='medium',
        threads=4,
        logger=None  # Suppress verbose output
    )

    # Cleanup
    video.close()
    audio.close()

    print(f"Video created: {output_path}")
    return output_path


def _find_japanese_font() -> str:
    """Find a Japanese font for MoviePy"""
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
            return font

    # Return common font name as fallback
    return "Arial"


# For compatibility, keep the same function name
def make_podcast_video(
    background_path: Path,
    timing_data: List[Dict],
    audio_path: Path,
    output_path: Path,
    use_moviepy: bool = True
) -> Path:
    """
    Create podcast-style video with optional MoviePy rendering.

    Args:
        background_path: Path to background image
        timing_data: List of subtitle timing data
        audio_path: Path to audio file
        output_path: Output video path
        use_moviepy: Whether to use MoviePy (higher quality but slower)

    Returns:
        Path to created video
    """
    if use_moviepy and MOVIEPY_AVAILABLE:
        return make_podcast_video_moviepy(
            background_path, timing_data, audio_path, output_path
        )
    else:
        # Use original PIL-based method
        from video_maker import make_podcast_video as make_video_pil
        return make_video_pil(
            background_path, timing_data, audio_path, output_path
        )


if __name__ == "__main__":
    if MOVIEPY_AVAILABLE:
        print("MoviePy is available")
    else:
        print("MoviePy is not available - install with: pip install moviepy")
