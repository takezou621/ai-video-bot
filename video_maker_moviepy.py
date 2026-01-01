"""
MoviePy-based Video Maker - Higher quality subtitle rendering
Based on the Zenn article's approach using MoviePy
Enhanced with subtitle optimization for better readability
"""
from pathlib import Path
from typing import List, Dict, Any
import os
from subtitle_optimizer import SubtitleOptimizer

try:
    from moviepy import (
        ImageClip, AudioFileClip, TextClip, CompositeVideoClip,
        concatenate_videoclips, vfx
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("MoviePy not available, using fallback")


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


def make_podcast_video_moviepy(
    backgrounds: Any, # Can be Path or List[Dict[str, Any]]
    timing_data: List[Dict],
    audio_path: Path,
    output_path: Path
) -> Path:
    """
    Create podcast-style video using MoviePy for higher quality.

    Args:
        backgrounds: Path to background image OR List of {"path": Path, "start": float}
        timing_data: List of {"speaker", "text", "start", "end"}
        audio_path: Path to audio file
        output_path: Output video path

    Returns:
        Path to created video
    """
    if not MOVIEPY_AVAILABLE:
        # Fallback to PIL-based video maker (doesn't support multiple backgrounds yet)
        from video_maker import make_podcast_video
        bg_path = backgrounds if isinstance(backgrounds, (Path, str)) else backgrounds[0]["path"]
        return make_podcast_video(bg_path, timing_data, audio_path, output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Creating video with MoviePy...")

    # Optimize subtitles for better readability
    print("  Optimizing subtitles...")
    optimizer = SubtitleOptimizer()
    timing_data = optimizer.optimize_timing_data(timing_data)

    # Validate subtitle quality
    validation = optimizer.validate_subtitle_quality(timing_data)
    if not validation["passed"]:
        print(f"  ⚠️  Subtitle quality issues detected:")
        for issue in validation["issues"][:5]:  # Show first 5 issues
            print(f"    - {issue}")
    print(f"  Avg reading speed: {validation['stats']['avg_reading_speed']:.1f} chars/sec")

    # Load audio
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration

    # Create background clips
    bg_clips = []
    if isinstance(backgrounds, (Path, str)):
        # Single background
        bg_clips.append(
            ImageClip(str(backgrounds)).with_duration(duration).resized((VIDEO_WIDTH, VIDEO_HEIGHT))
        )
    else:
        # Multiple backgrounds
        # Sort by start time
        sorted_bgs = sorted(backgrounds, key=lambda x: x["start"])
        for i, bg_info in enumerate(sorted_bgs):
            bg_path = bg_info["path"]
            start_time = bg_info["start"]
            
            # End time is either next background's start or video duration
            if i + 1 < len(sorted_bgs):
                end_time = sorted_bgs[i+1]["start"]
            else:
                end_time = duration
                
            bg_duration = end_time - start_time
            if bg_duration <= 0:
                continue
                
            clip = ImageClip(str(bg_path)).with_duration(bg_duration).resized((VIDEO_WIDTH, VIDEO_HEIGHT))
            clip = clip.with_start(start_time)
            
            # Optional: Add cross-fade between backgrounds
            if i > 0:
                clip = clip.with_effects([vfx.CrossFadeIn(0.5)])
                
            bg_clips.append(clip)

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
                stroke_width=3
            )

            # Position with sufficient bottom margin to prevent cut-off
            # Ensures 2-3 lines of text with stroke fit safely within the frame
            # Y position is the TOP of the text clip, so we need extra margin
            # for text height (~100-120px) + stroke width + internal padding
            # Setting to 400px to ensure complete visibility with safety margin
            bottom_margin = 400
            txt_clip = txt_clip.with_position(
                ('center', VIDEO_HEIGHT - bottom_margin)
            )
            txt_clip = txt_clip.with_start(start)
            txt_clip = txt_clip.with_duration(seg_duration)

            # Add fade effects for smoother transitions
            if seg_duration > 0.5:
                txt_clip = txt_clip.with_effects([
                    vfx.FadeIn(0.2),
                    vfx.FadeOut(0.2)
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
                bottom_margin = 400
                txt_clip = txt_clip.with_position(
                    ('center', VIDEO_HEIGHT - bottom_margin)
                )
                txt_clip = txt_clip.with_start(start)
                txt_clip = txt_clip.with_duration(min(seg_duration, 5))
                subtitle_clips.append(txt_clip)
            except:
                continue

    # Composite all clips
    print(f"  Compositing {len(bg_clips)} background clips and {len(subtitle_clips)} subtitle clips...")
    video = CompositeVideoClip(
        bg_clips + subtitle_clips,
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
    background_path: Any, # Path or List[Dict]
    timing_data: List[Dict],
    audio_path: Path,
    output_path: Path,
    use_moviepy: bool = True
) -> Path:
    """
    Create podcast-style video with optional MoviePy rendering.

    Args:
        background_path: Path to background image or List of background segments
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
        # Use original PIL-based method (Fallback)
        # Handle list input by taking the first background
        if isinstance(background_path, list):
            # Assuming list of dicts with 'path' key
            try:
                real_bg_path = background_path[0]["path"]
            except (IndexError, KeyError, TypeError):
                 # Fallback if list structure is unexpected
                real_bg_path = background_path
        else:
            real_bg_path = background_path
            
        from video_maker import make_podcast_video as make_video_pil
        return make_video_pil(
            real_bg_path, timing_data, audio_path, output_path
        )


if __name__ == "__main__":
    if MOVIEPY_AVAILABLE:
        print("MoviePy is available")
    else:
        print("MoviePy is not available - install with: pip install moviepy")
