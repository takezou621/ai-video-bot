"""
Gemini TTS Generator - Podcast-style dialogue audio generation
Enhanced with ElevenLabs STT for accurate subtitle timing
"""
import os
import json
import base64
import requests
import voicevox_client
import text_normalizer
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from api_key_manager import get_api_key, report_api_success, report_api_failure

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Gemini TTS Model Selection (December 2025 - latest models)
GEMINI_TTS_MODEL = os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")

# Audio Speed Factor (1.0 = normal, 1.3 = 30% faster)
SPEED_FACTOR = 1.3

# Local TTS (VoiceVox) - prioritized if enabled
USE_VOICEVOX = os.getenv("USE_VOICEVOX", "true").lower() == "true" and voicevox_client.is_available()

# Whisper STT (local, free) - prioritized over ElevenLabs
USE_WHISPER_STT = os.getenv("USE_WHISPER_STT", "true").lower() == "true"
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")  # tiny, base, small, medium, large

# ElevenLabs STT (paid API) - fallback if Whisper disabled
USE_ELEVENLABS_STT_ENV = os.getenv("USE_ELEVENLABS_STT", "false").lower() == "true"
USE_ELEVENLABS_STT = USE_ELEVENLABS_STT_ENV and bool(ELEVENLABS_API_KEY)

# Log TTS and subtitle timing strategy
if USE_VOICEVOX:
    print(f"[INFO] Using VOICEVOX (local, FREE) for high-quality Japanese speech")
else:
    print(f"[INFO] Using Gemini TTS model: {GEMINI_TTS_MODEL}")

if USE_WHISPER_STT:
    print(f"[INFO] Using Whisper STT (local, FREE) for accurate subtitles - model: {WHISPER_MODEL_SIZE}")
elif USE_ELEVENLABS_STT:
    print("[INFO] Using ElevenLabs STT (paid API) for accurate subtitles")
else:
    print("[INFO] Using timing estimation for subtitles (less accurate)")

def generate_dialogue_audio(
    dialogues: List[Dict], 
    output_path: Path,
    section_indices: List[int] = None
) -> Tuple[Path, List[Dict]]:
    """
    Generate podcast-style dialogue audio.

    Args:
        dialogues: List of {"speaker": "A/B/男性/女性", "text": "..."}
        output_path: Path to save the audio file
        section_indices: Optional list of dialogue indices where a new section starts

    Returns:
        Tuple of (audio_path, timing_data for subtitles)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    section_indices = section_indices or []

    if not USE_VOICEVOX and not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is required when VoiceVox is disabled")

    chunk_paths = []
    estimated_timing = []
    current_time = 0.0

    try:
        for idx, dialogue in enumerate(dialogues):
            # Topic change pause
            if idx in section_indices and idx > 0:
                print(f"  [TTS] Adding topic change pause at dialogue {idx}")
                # Add 1.5s pause (unscaled, so it becomes ~1.1s at 1.3x)
                pause_path = output_path.parent / f"pause_{idx}.wav"
                _create_silence(pause_path, 1.5)
                chunk_paths.append(pause_path)
                current_time += 1.5 / SPEED_FACTOR

            text = dialogue.get("text", "")
            if not text.strip():
                continue
            
            # Normalize text for proper reading (English -> Katakana)
            text = text_normalizer.normalize_text_for_tts(text)
            
            chunk_path = output_path.parent / f"chunk_{idx}.wav"
            
            if USE_VOICEVOX:
                # Map speaker for VoiceVox
                speaker_type = "female" if dialogue.get("speaker") in ["女性", "B", "Female"] else "male"
                voicevox_client.generate_voice(text, chunk_path, speaker_type=speaker_type)
            else:
                # Gemini TTS
                voice = _determine_voice(dialogue.get("speaker"))
                audio_bytes, mime_type = _request_gemini_tts(text, voice)
                _write_audio_chunk(audio_bytes, mime_type, chunk_path)
            
            # Calculate duration accounting for future speedup
            raw_duration = _get_audio_duration(chunk_path)
            duration = raw_duration / SPEED_FACTOR
            
            estimated_timing.append({
                "speaker": dialogue.get("speaker"),
                "text": text,
                "start": current_time,
                "end": current_time + duration
            })
            current_time += duration
            chunk_paths.append(chunk_path)

        if not chunk_paths:
            print("No audio chunks generated, using fallback")
            return _fallback_tts(dialogues, output_path)

        final_path = output_path.with_suffix(".mp3")
        concat_file = output_path.parent / "tts_concat.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for chunk in chunk_paths:
                f.write(f"file '{chunk}'\n")

        import subprocess
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-filter:a", f"atempo={SPEED_FACTOR}",
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(final_path)
        ], check=True, capture_output=True)

        # Cleanup chunks
        concat_file.unlink(missing_ok=True)
        for chunk in chunk_paths:
            chunk.unlink(missing_ok=True)

        timing_data = None

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

        if USE_ELEVENLABS_STT and not timing_data:
            try:
                from elevenlabs_stt import generate_accurate_subtitles
                timing_data = generate_accurate_subtitles(dialogues, final_path)
                if timing_data:
                    print("  Using ElevenLabs STT for accurate timing (paid API)")
                    return final_path, timing_data
            except Exception as e:
                print(f"  ElevenLabs STT failed: {e}, using estimation")

        print("  Using estimated timing (pre-TTS durations adjusted for speed)")
        return final_path, estimated_timing

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
        if not d.get("text") or not d["text"].strip():
            print(f"  [TTS] Skipping empty dialogue segment {i}")
            continue
            
        temp_path = output_path.parent / f"temp_{i}.mp3"

        # Note: gTTS doesn't support different voices for male/female,
        # but we maintain the speaker label for subtitle rendering
        tts = gTTS(text=d["text"], lang="ja")
        tts.save(str(temp_path))
        temp_files.append(temp_path)

        # Measure actual duration and adjust for speedup
        # (gTTS produces slow speech, so we must measure the original and divide)
        raw_duration = _get_audio_duration(temp_path)
        duration = raw_duration / SPEED_FACTOR
        
        timing_data.append({
            "speaker": d["speaker"],  # Preserve original speaker label (男性/女性 or A/B)
            "text": d["text"],
            "start": current_time,
            "end": current_time + duration
        })
        current_time += duration

    final_path = output_path.with_suffix(".mp3")
    
    # Concatenate audio files with speedup
    if len(temp_files) > 1:
        list_file = output_path.parent / "audio_list.txt"
        with open(list_file, "w") as f:
            for tf in temp_files:
                f.write(f"file '{tf}'\n")

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-filter:a", f"atempo={SPEED_FACTOR}",
            "-c:a", "libmp3lame", "-b:a", "192k",
            str(final_path)
        ], check=True, capture_output=True)

        # Cleanup
        for tf in temp_files:
            tf.unlink()
        list_file.unlink()
    else:
        # Process single file with speedup
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(temp_files[0]),
            "-filter:a", f"atempo={SPEED_FACTOR}",
            "-c:a", "libmp3lame", "-b:a", "192k",
            str(final_path)
        ], check=True, capture_output=True)
        temp_files[0].unlink()

    return final_path, timing_data


def _determine_voice(speaker: Optional[str]) -> str:
    if speaker in ["女性", "B", "Female"]:
        return FEMALE_VOICE_NAME
    # Default to male voice for "男性", "A", "Male", or unknown
    return MALE_VOICE_NAME


def _request_gemini_tts(text: str, voice_name: str) -> Tuple[bytes, str]:
    """
    Request Gemini TTS with API key rotation support.
    Implements the blog's strategy of multiple API keys for rate limit handling.
    """
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            # Get next available API key
            api_key = get_api_key("GEMINI")

            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{GEMINI_TTS_MODEL}:generateContent?key={api_key}"
            )
            payload = {
                "contents": [{"parts": [{"text": text}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": voice_name
                            }
                        }
                    }
                }
            }

            r = requests.post(url, json=payload, timeout=120)

            # Check for rate limiting
            if r.status_code == 429:
                report_api_failure("GEMINI", api_key, is_rate_limit=True)
                if attempt < max_retries - 1:
                    print(f"  [TTS] Rate limit hit (attempt {attempt + 1}/{max_retries}), trying next key...")
                    continue
                raise RuntimeError("Rate limit exceeded")

            r.raise_for_status()
            data = r.json()

            if "error" in data:
                error_msg = str(data["error"])
                is_rate_limit = "quota" in error_msg.lower() or "rate" in error_msg.lower()
                report_api_failure("GEMINI", api_key, is_rate_limit=is_rate_limit)

                if is_rate_limit and attempt < max_retries - 1:
                    print(f"  [TTS] Quota error (attempt {attempt + 1}/{max_retries}), trying next key...")
                    continue
                raise RuntimeError(error_msg)

            for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                if "inlineData" in part:
                    audio = base64.b64decode(part["inlineData"]["data"])
                    mime = part["inlineData"].get("mimeType", "audio/L16")

                    # Success!
                    report_api_success("GEMINI", api_key)
                    return audio, mime

            # No audio data found
            report_api_failure("GEMINI", api_key)
            raise RuntimeError("Gemini TTS response missing inlineData")

        except requests.exceptions.RequestException as e:
            last_error = e
            if 'api_key' in locals():
                is_rate_limit = "429" in str(e) or "quota" in str(e).lower()
                report_api_failure("GEMINI", api_key, is_rate_limit=is_rate_limit)

            if attempt < max_retries - 1:
                print(f"  [TTS] Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                continue
            raise

    # All retries exhausted
    raise RuntimeError(f"Gemini TTS failed after {max_retries} attempts: {last_error}")


def _write_audio_chunk(audio_bytes: bytes, mime_type: str, output_path: Path):
    raw_path = output_path.with_suffix(".raw")
    with open(raw_path, "wb") as f:
        f.write(audio_bytes)

    import subprocess
    if "L16" in mime_type or "pcm" in mime_type.lower():
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "s16le",
            "-ar", "24000",
            "-ac", "1",
            "-i", str(raw_path),
            str(output_path)
        ], check=True, capture_output=True)
    elif "wav" in mime_type.lower():
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(raw_path),
            str(output_path)
        ], check=True, capture_output=True)
    else:
        output_path.write_bytes(audio_bytes)

    raw_path.unlink(missing_ok=True)


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
MALE_VOICE_NAME = os.getenv("GEMINI_TTS_MALE_VOICE", "Fenrir")
FEMALE_VOICE_NAME = os.getenv("GEMINI_TTS_FEMALE_VOICE", "Aoede")

def _create_silence(path: Path, duration: float):
    """Create a silent WAV file using ffmpeg"""
    import subprocess
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
        "-t", str(duration),
        str(path)
    ], check=True, capture_output=True)
