"""
MoviePy-based Video Maker - Higher quality subtitle rendering
Based on the Zenn article's approach using MoviePy
"""
from pathlib import Path
from typing import List, Dict
import os

try:
    from moviepy.editor import (
        ImageClip, AudioFileClip, TextClip, CompositeVideoClip,
        concatenate_videoclips
    )
    from moviepy.video.fx import fadein, fadeout
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("MoviePy not available, using fallback")


# Video settings
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

# Subtitle styling
FONT_SIZE = 56
SPEAKER_A_COLOR = '#78C8FF'
SPEAKER_B_COLOR = '#FFC878'
TEXT_COLOR = 'white'
BG_COLOR = 'rgba(20,20,30,0.85)'


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

    # Load audio
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration

    # Create background clip
    background = ImageClip(str(background_path)).set_duration(duration)
    background = background.resize((VIDEO_WIDTH, VIDEO_HEIGHT))

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
        color = SPEAKER_A_COLOR if speaker == "A" else SPEAKER_B_COLOR

        try:
            # Create text clip with MoviePy
            # Try to use Japanese font
            font = _find_japanese_font()

            txt_clip = TextClip(
                text,
                fontsize=FONT_SIZE,
                color=TEXT_COLOR,
                font=font,
                size=(VIDEO_WIDTH - 200, None),
                method='caption',
                align='center',
                stroke_color=color,
                stroke_width=3
            )

            # Position at bottom
            txt_clip = txt_clip.set_position(('center', VIDEO_HEIGHT - 200))
            txt_clip = txt_clip.set_start(start)
            txt_clip = txt_clip.set_duration(seg_duration)

            # Add fade effects for smoother transitions
            if seg_duration > 0.5:
                txt_clip = fadein(txt_clip, 0.2)
                txt_clip = fadeout(txt_clip, 0.2)

            subtitle_clips.append(txt_clip)

        except Exception as e:
            print(f"  Warning: Failed to create subtitle for segment {i}: {e}")
            # Create simple text clip as fallback
            try:
                txt_clip = TextClip(
                    text[:100],  # Limit length
                    fontsize=FONT_SIZE,
                    color=TEXT_COLOR,
                    method='label'
                )
                txt_clip = txt_clip.set_position(('center', VIDEO_HEIGHT - 200))
                txt_clip = txt_clip.set_start(start)
                txt_clip = txt_clip.set_duration(min(seg_duration, 5))
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
    video = video.set_audio(audio)

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
