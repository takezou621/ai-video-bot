"""
Gemini TTS Generator - Podcast-style dialogue audio generation
Enhanced with ElevenLabs STT for accurate subtitle timing
"""
import os
import json
import base64
import requests
from pathlib import Path
from typing import List, Dict, Tuple

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Whisper STT (local, free) - prioritized over ElevenLabs
USE_WHISPER_STT = os.getenv("USE_WHISPER_STT", "true").lower() == "true"
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")  # tiny, base, small, medium, large

# ElevenLabs STT (paid API) - fallback if Whisper disabled
USE_ELEVENLABS_STT_ENV = os.getenv("USE_ELEVENLABS_STT", "false").lower() == "true"
USE_ELEVENLABS_STT = USE_ELEVENLABS_STT_ENV and bool(ELEVENLABS_API_KEY)

# Log subtitle timing strategy
if USE_WHISPER_STT:
    print(f"[INFO] Using Whisper STT (local, FREE) for accurate subtitles - model: {WHISPER_MODEL_SIZE}")
elif USE_ELEVENLABS_STT:
    print("[INFO] Using ElevenLabs STT (paid API) for accurate subtitles")
else:
    print("[INFO] Using timing estimation for subtitles (less accurate)")

def generate_dialogue_audio(dialogues: List[Dict], output_path: Path) -> Tuple[Path, List[Dict]]:
    """
    Generate podcast-style dialogue audio using Gemini TTS.

    Args:
        dialogues: List of {"speaker": "A/B/男性/女性", "text": "..."}
        output_path: Path to save the audio file

    Returns:
        Tuple of (audio_path, timing_data for subtitles)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is required")

    # Combine dialogues into a script format for Gemini
    script_parts = []
    for d in dialogues:
        # Support both new format (男性/女性) and legacy format (A/B)
        speaker_label = d["speaker"]
        if speaker_label in ["A", "男性"]:
            speaker = "Speaker 1"
        elif speaker_label in ["B", "女性"]:
            speaker = "Speaker 2"
        else:
            speaker = "Speaker 1"  # Default
        script_parts.append(f"{speaker}: {d['text']}")

    full_script = "\n".join(script_parts)

    # Use Gemini's TTS capability
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{
            "parts": [{"text": full_script}]
        }],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": "Zephyr"
                    }
                }
            }
        }
    }

    try:
        r = requests.post(url, json=payload, timeout=300)
        data = r.json()

        if "error" in data:
            print(f"Gemini TTS Error: {data['error']}")
            return _fallback_tts(dialogues, output_path)

        # Extract audio from response
        for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            if "inlineData" in part:
                audio_data = base64.b64decode(part["inlineData"]["data"])
                mime_type = part["inlineData"].get("mimeType", "audio/L16")
                print(f"  Gemini TTS returned: {mime_type} ({len(audio_data)} bytes)")

                # Save raw audio first
                raw_path = output_path.parent / "raw_audio.pcm"
                with open(raw_path, "wb") as f:
                    f.write(audio_data)

                # Convert to MP3 based on mime type
                final_path = output_path.with_suffix(".mp3")
                import subprocess

                if "L16" in mime_type or "pcm" in mime_type.lower():
                    # Raw PCM audio - Gemini typically returns 24kHz, 16-bit, mono
                    subprocess.run([
                        "ffmpeg", "-y",
                        "-f", "s16le",          # Signed 16-bit little endian
                        "-ar", "24000",         # 24kHz sample rate
                        "-ac", "1",             # Mono
                        "-i", str(raw_path),
                        "-c:a", "libmp3lame",
                        "-b:a", "192k",
                        str(final_path)
                    ], check=True, capture_output=True)
                elif "wav" in mime_type.lower():
                    # WAV format - convert to MP3
                    wav_path = output_path.with_suffix(".wav")
                    with open(wav_path, "wb") as f:
                        f.write(audio_data)
                    subprocess.run([
                        "ffmpeg", "-y",
                        "-i", str(wav_path),
                        "-c:a", "libmp3lame",
                        "-b:a", "192k",
                        str(final_path)
                    ], check=True, capture_output=True)
                    wav_path.unlink()
                else:
                    # Assume MP3 or other format
                    with open(final_path, "wb") as f:
                        f.write(audio_data)

                raw_path.unlink()

                # Get accurate timing - priority order:
                # 1. Whisper (local, free, accurate)
                # 2. ElevenLabs STT (paid API, accurate)
                # 3. Estimation (free, less accurate)

                timing_data = None

                # Try Whisper first (100% FREE, local processing)
                if USE_WHISPER_STT and not timing_data:
                    try:
                        from whisper_stt import generate_accurate_subtitles_with_whisper
                        timing_data = generate_accurate_subtitles_with_whisper(
                            dialogues,
                            final_path,
                            model_size=WHISPER_MODEL_SIZE
                        )
                        if timing_data:
                            print("✅ Using Whisper STT for accurate timing (100% FREE)")
                            return final_path, timing_data
                    except Exception as e:
                        print(f"  Whisper STT failed: {e}, trying fallback...")

                # Try ElevenLabs if Whisper failed
                if USE_ELEVENLABS_STT and not timing_data:
                    try:
                        from elevenlabs_stt import generate_accurate_subtitles
                        timing_data = generate_accurate_subtitles(dialogues, final_path)
                        if timing_data:
                            print("  Using ElevenLabs STT for accurate timing (paid API)")
                            return final_path, timing_data
                    except Exception as e:
                        print(f"  ElevenLabs STT failed: {e}, using estimation")

                # Fallback to timing estimation
                actual_duration = _get_audio_duration(final_path)
                timing_data = _estimate_timing_scaled(dialogues, actual_duration)
                print("  Using timing estimation (fallback)")
                return final_path, timing_data

        print("No audio in Gemini response, using fallback")
        return _fallback_tts(dialogues, output_path)

    except Exception as e:
        print(f"Gemini TTS failed: {e}, using fallback")
        return _fallback_tts(dialogues, output_path)


def _fallback_tts(dialogues: List[Dict], output_path: Path) -> Tuple[Path, List[Dict]]:
    """Fallback to gTTS if Gemini TTS fails"""
    from gtts import gTTS
    import subprocess

    # Generate audio for each dialogue segment
    temp_files = []
    timing_data = []
    current_time = 0.0

    for i, d in enumerate(dialogues):
        temp_path = output_path.parent / f"temp_{i}.mp3"

        # Note: gTTS doesn't support different voices for male/female,
        # but we maintain the speaker label for subtitle rendering
        tts = gTTS(text=d["text"], lang="ja")
        tts.save(str(temp_path))
        temp_files.append(temp_path)

        # Estimate duration (rough: 150 chars per minute for Japanese)
        duration = max(2.0, len(d["text"]) / 5.0)
        timing_data.append({
            "speaker": d["speaker"],  # Preserve original speaker label (男性/女性 or A/B)
            "text": d["text"],
            "start": current_time,
            "end": current_time + duration
        })
        current_time += duration

    # Concatenate audio files
    if len(temp_files) > 1:
        list_file = output_path.parent / "audio_list.txt"
        with open(list_file, "w") as f:
            for tf in temp_files:
                f.write(f"file '{tf}'\n")

        final_path = output_path.with_suffix(".mp3")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file), "-c", "copy", str(final_path)
        ], check=True, capture_output=True)

        # Cleanup
        for tf in temp_files:
            tf.unlink()
        list_file.unlink()
    else:
        final_path = output_path.with_suffix(".mp3")
        temp_files[0].rename(final_path)

    return final_path, timing_data


def _get_audio_duration(audio_path: Path) -> float:
    """Get actual audio duration using ffprobe"""
    import subprocess
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "csv=p=0", str(audio_path)
        ], capture_output=True, text=True)
        return float(result.stdout.strip())
    except:
        return 60.0  # Default fallback


def _estimate_timing_scaled(dialogues: List[Dict], actual_duration: float) -> List[Dict]:
    """
    Estimate timing for subtitles and scale to match actual audio duration.

    This calculates relative timing based on text length, then scales
    everything to fit the actual audio duration.
    """
    if not dialogues:
        return []

    # Calculate relative weights based on text length
    weights = []
    for d in dialogues:
        # Weight based on character count (Japanese chars take longer)
        weight = len(d["text"])
        weights.append(weight)

    total_weight = sum(weights)
    if total_weight == 0:
        total_weight = 1

    # Leave minimal gaps between segments for natural flow
    pause_time = 0.1  # Reduced pause between speakers (was 0.2)
    total_pause_time = pause_time * (len(dialogues) - 1)
    available_speech_time = actual_duration - total_pause_time

    if available_speech_time < 0:
        available_speech_time = actual_duration * 0.98  # Use more time (was 0.95)
        pause_time = (actual_duration * 0.02) / max(1, len(dialogues) - 1)

    # Generate timing data with slight early offset for better sync
    timing_data = []
    current_time = 0.0
    offset = 0.1  # Start subtitles slightly early for better perception

    for i, d in enumerate(dialogues):
        # Calculate duration proportional to text length
        duration = (weights[i] / total_weight) * available_speech_time
        duration = max(0.5, duration)  # Minimum 0.5 second per segment (was 1.0)

        # Apply offset only to non-first segments for natural flow
        segment_offset = 0 if i == 0 else offset

        timing_data.append({
            "speaker": d["speaker"],
            "text": d["text"],
            "start": max(0, current_time - segment_offset),
            "end": current_time + duration
        })

        current_time += duration
        if i < len(dialogues) - 1:
            current_time += pause_time

    print(f"  Timing scaled to {actual_duration:.1f}s audio duration")
    return timing_data


def _estimate_timing(dialogues: List[Dict]) -> List[Dict]:
    """Estimate timing for subtitles based on text length (legacy)"""
    timing_data = []
    current_time = 0.0

    for d in dialogues:
        # Rough estimate: Japanese speech ~7 chars/second (faster for Gemini TTS)
        duration = max(2.0, len(d["text"]) / 7.0)
        timing_data.append({
            "speaker": d["speaker"],
            "text": d["text"],
            "start": current_time,
            "end": current_time + duration
        })
        current_time += duration + 0.3  # Small pause between speakers

    return timing_data
