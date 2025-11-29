"""
OpenAI Whisper (Local) Speech-to-Text Integration
Provides accurate subtitle timing by analyzing actual audio - 100% FREE
No API costs - runs locally using open source Whisper model
"""
import os
import json
import warnings
from pathlib import Path
from typing import List, Dict, Optional
from difflib import SequenceMatcher

# Suppress FP16 warning on CPU
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("[WARNING] OpenAI Whisper not installed. Install with: pip install openai-whisper")


def transcribe_audio_with_whisper(
    audio_path: Path,
    model_size: str = "base",
    language: str = "ja"
) -> Optional[List[Dict]]:
    """
    Transcribe audio using local Whisper model (100% FREE).

    Args:
        audio_path: Path to audio file
        model_size: Whisper model size (tiny, base, small, medium, large)
                   - tiny: fastest, lowest accuracy (~1GB RAM)
                   - base: good balance (~1GB RAM) - RECOMMENDED
                   - small: better accuracy (~2GB RAM)
                   - medium: high accuracy (~5GB RAM)
                   - large: best accuracy (~10GB RAM)
        language: Language code (ja for Japanese)

    Returns:
        List of word-level segments with accurate timing
    """
    if not WHISPER_AVAILABLE:
        print("Whisper not available, using fallback timing")
        return None

    if not audio_path.exists():
        print(f"Audio file not found: {audio_path}")
        return None

    try:
        print(f"Loading Whisper model '{model_size}' (this may take a moment on first run)...")
        model = whisper.load_model(model_size)

        print(f"Transcribing audio with Whisper (100% FREE, no API costs)...")

        # Transcribe with word-level timestamps
        result = model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True,
            verbose=False
        )

        # Extract word-level segments
        segments = []

        # Whisper returns segments with word-level timing
        for segment in result.get("segments", []):
            for word in segment.get("words", []):
                segments.append({
                    "text": word.get("word", "").strip(),
                    "start": word.get("start", 0),
                    "end": word.get("end", 0)
                })

        # If no word-level data, fall back to segment-level
        if not segments:
            for segment in result.get("segments", []):
                segments.append({
                    "text": segment.get("text", "").strip(),
                    "start": segment.get("start", 0),
                    "end": segment.get("end", 0)
                })

        print(f"✅ Transcribed {len(segments)} segments with Whisper")
        return segments

    except Exception as e:
        print(f"Whisper transcription failed: {e}")
        return None


def align_script_with_whisper_transcription(
    script_dialogues: List[Dict],
    whisper_segments: List[Dict]
) -> Optional[List[Dict]]:
    """
    Match script text with Whisper transcription to get accurate timing.

    Args:
        script_dialogues: Original dialogue script [{"speaker": "A/B/男性/女性", "text": "..."}]
        whisper_segments: Whisper STT results with word-level timing

    Returns:
        Aligned timing data for each dialogue segment
    """
    if not whisper_segments:
        return None

    # Combine all transcribed text for analysis
    full_transcription = "".join([s["text"] for s in whisper_segments])

    aligned_data = []
    current_segment_idx = 0

    print(f"  Aligning {len(script_dialogues)} dialogues with Whisper transcription...")

    for i, dialogue in enumerate(script_dialogues):
        dialogue_text = dialogue["text"].replace(" ", "").replace("　", "")

        # Find best match in transcription
        best_match_start = None
        best_match_end = None
        best_similarity = 0
        best_idx = current_segment_idx

        # Search through segments to find this dialogue
        for j in range(current_segment_idx, len(whisper_segments)):
            # Build a window of text from segments
            window_text = ""
            window_start = whisper_segments[j]["start"]
            window_end = whisper_segments[j]["end"]

            # Look ahead to build enough text
            for k in range(j, min(j + 200, len(whisper_segments))):
                window_text += whisper_segments[k]["text"].replace(" ", "")
                window_end = whisper_segments[k]["end"]

                # Calculate similarity (ignore whitespace)
                similarity = SequenceMatcher(
                    None,
                    dialogue_text,
                    window_text
                ).ratio()

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_start = window_start
                    best_match_end = window_end
                    best_idx = k

                    # If excellent match, stop searching
                    if similarity > 0.85:
                        break

                # Stop if window is much longer than dialogue
                if len(window_text) > len(dialogue_text) * 2:
                    break

            # If good match found, move to next dialogue
            if best_similarity > 0.65:
                current_segment_idx = best_idx + 1
                break

        if best_match_start is not None and best_similarity > 0.5:
            aligned_data.append({
                "speaker": dialogue["speaker"],
                "text": dialogue["text"],
                "start": best_match_start,
                "end": best_match_end,
                "confidence": best_similarity
            })
        else:
            # Fallback: estimate based on previous timing
            if aligned_data:
                last_end = aligned_data[-1]["end"]
                duration = len(dialogue_text) / 7.0
                aligned_data.append({
                    "speaker": dialogue["speaker"],
                    "text": dialogue["text"],
                    "start": last_end + 0.2,
                    "end": last_end + 0.2 + duration,
                    "confidence": 0.0
                })
            else:
                # First dialogue, start from 0
                duration = len(dialogue_text) / 7.0
                aligned_data.append({
                    "speaker": dialogue["speaker"],
                    "text": dialogue["text"],
                    "start": 0,
                    "end": duration,
                    "confidence": 0.0
                })

    if aligned_data:
        avg_confidence = sum(d["confidence"] for d in aligned_data) / len(aligned_data)
        print(f"✅ Aligned {len(aligned_data)} dialogues (avg confidence: {avg_confidence:.1%})")

        # Warn if low confidence
        low_confidence = [d for d in aligned_data if d["confidence"] < 0.5]
        if low_confidence:
            print(f"  ⚠️  {len(low_confidence)} dialogues had low confidence alignment")

    return aligned_data


def generate_accurate_subtitles_with_whisper(
    script_dialogues: List[Dict],
    audio_path: Path,
    model_size: str = "base"
) -> Optional[List[Dict]]:
    """
    Generate highly accurate subtitles using local Whisper + script alignment.
    100% FREE - no API costs.

    Args:
        script_dialogues: Original script
        audio_path: Path to generated audio
        model_size: Whisper model size (base recommended for speed/accuracy balance)

    Returns:
        Accurate timing data for subtitles, or None if transcription fails
    """
    # Step 1: Transcribe audio with Whisper (local, free)
    transcription = transcribe_audio_with_whisper(
        audio_path,
        model_size=model_size,
        language="ja"
    )

    if not transcription:
        print("⚠️  Whisper transcription failed, falling back to estimated timing")
        return None

    # Step 2: Align script with transcription for perfect timing
    aligned_timing = align_script_with_whisper_transcription(
        script_dialogues,
        transcription
    )

    return aligned_timing


# Export main function
generate_accurate_subtitles = generate_accurate_subtitles_with_whisper


if __name__ == "__main__":
    # Test availability
    if WHISPER_AVAILABLE:
        print("✅ Whisper is available")
        print("\nAvailable model sizes:")
        print("  - tiny:   ~39M params, ~1GB RAM, fastest")
        print("  - base:   ~74M params, ~1GB RAM, recommended balance")
        print("  - small:  ~244M params, ~2GB RAM, better accuracy")
        print("  - medium: ~769M params, ~5GB RAM, high accuracy")
        print("  - large:  ~1550M params, ~10GB RAM, best accuracy")
        print("\nTo test transcription:")
        print("  result = transcribe_audio_with_whisper('audio.mp3', model_size='base')")
    else:
        print("❌ Whisper not installed")
        print("\nInstall with:")
        print("  pip install openai-whisper")
        print("\nSystem requirements:")
        print("  - Python 3.8+")
        print("  - ffmpeg")
        print("  - 1-10GB RAM depending on model size")
