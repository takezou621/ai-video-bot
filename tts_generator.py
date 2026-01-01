"""
TTS Generator - Podcast-style dialogue audio generation
Primary: VOICEVOX (local, free, high-quality Japanese)
Fallback: Gemini TTS (API, paid) → gTTS (basic fallback)

Enhanced with accurate subtitle timing via Whisper STT.
"""
import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from api_key_manager import get_api_key, report_api_success, report_api_failure

import voicevox_client
import text_normalizer

# TTS Priority Configuration
USE_VOICEVOX = os.getenv("USE_VOICEVOX", "true").lower() == "true"
VOICEVOX_AVAILABLE = voicevox_client.is_available() if USE_VOICEVOX else False

# Gemini TTS (fallback)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_TTS_MODEL = os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
MALE_VOICE_NAME = os.getenv("GEMINI_TTS_MALE_VOICE", "Fenrir")
FEMALE_VOICE_NAME = os.getenv("GEMINI_TTS_FEMALE_VOICE", "Aoede")

# Audio Speed Factor (1.0 = normal, 1.3 = 30% faster)
SPEED_FACTOR = float(os.getenv("TTS_SPEED_FACTOR", "1.0"))  # VOICEVOX handles speed internally

# Whisper STT (local, free) - for subtitle timing
USE_WHISPER_STT = os.getenv("USE_WHISPER_STT", "true").lower() == "true"
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

# ElevenLabs STT (paid API) - fallback for subtitle timing
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
USE_ELEVENLABS_STT = os.getenv("USE_ELEVENLABS_STT", "false").lower() == "true" and bool(ELEVENLABS_API_KEY)

# Log TTS strategy
if VOICEVOX_AVAILABLE:
    print(f"[TTS] Primary: VOICEVOX (local, FREE)")
elif GEMINI_API_KEY:
    print(f"[TTS] Primary: Gemini TTS ({GEMINI_TTS_MODEL})")
else:
    print("[TTS] Primary: gTTS (basic fallback)")

if USE_WHISPER_STT:
    print(f"[TTS] Subtitle timing: Whisper STT (local, FREE) - model: {WHISPER_MODEL_SIZE}")
elif USE_ELEVENLABS_STT:
    print("[TTS] Subtitle timing: ElevenLabs STT (paid API)")
else:
    print("[TTS] Subtitle timing: Duration estimation")


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

    # Normalize all dialogues first
    normalized_dialogues = []
    for d in dialogues:
        text = d.get("text", "").strip()
        if not text:
            continue

        # Apply normalization
        text = text_normalizer.normalize_for_tts_advanced(text)
        text = text_normalizer.normalize_text_for_tts(text)

        normalized_dialogues.append({
            "speaker": d.get("speaker", "男性"),
            "text": text,
            "original_text": d.get("text", ""),
        })

    if not normalized_dialogues:
        print("[TTS] No valid dialogues to process")
        return _create_empty_audio(output_path), []

    # Choose TTS engine
    if VOICEVOX_AVAILABLE:
        return _generate_with_voicevox(normalized_dialogues, output_path)
    elif GEMINI_API_KEY:
        return _generate_with_gemini(normalized_dialogues, output_path)
    else:
        return _fallback_tts(normalized_dialogues, output_path)


def _generate_with_voicevox(dialogues: List[Dict], output_path: Path) -> Tuple[Path, List[Dict]]:
    """Generate audio using VOICEVOX with persistent chunking."""
    print("[TTS] Using VOICEVOX for synthesis...")

    chunk_paths = []
    timing_data = []
    current_time = 0.0

    # P0 Fix: Use persistent chunks directory for idempotency
    chunks_dir = output_path.parent / "chunks"
    chunks_dir.mkdir(exist_ok=True)

    for idx, dialogue in enumerate(dialogues):
        text = dialogue.get("text", "").strip()
        speaker = dialogue.get("speaker", "男性")

        # Role-based mapping (Main/Sub)
        speaker_role = "sub" if speaker in ["女性", "B", "Female", "Sub"] else "main"

        # Consistent naming for idempotency
        chunk_filename = f"chunk_{idx:04d}.wav"
        chunk_path = chunks_dir / chunk_filename

        # Idempotency: Check if chunk already exists
        if chunk_path.exists() and chunk_path.stat().st_size > 0:
            # print(f"[TTS] Skipping existing chunk {idx}")
            result = chunk_path
        else:
            result = voicevox_client.generate_voice(
                text,
                chunk_path,
                speaker_role=speaker_role,
            )

        if result:
            duration = voicevox_client.get_audio_duration(chunk_path)
            timing_data.append({
                "chunk_id": chunk_filename,  # P0 Fix: Link chunk ID
                "speaker": speaker,
                "text": dialogue.get("original_text", text),
                "start": current_time,
                "end": current_time + duration,
            })
            current_time += duration
            chunk_paths.append(chunk_path)
        else:
            print(f"[TTS] Warning: Failed to generate chunk {idx}")

    if not chunk_paths:
        print("[TTS] No chunks generated, falling back to gTTS")
        return _fallback_tts(dialogues, output_path)

    # Concatenate chunks using audio_mastering
    from audio_mastering import master_episode

    final_mp3, adjusted_timing = master_episode(
        chunk_paths=chunk_paths,
        chunks_metadata=[{"speaker": d["speaker"], "text": d.get("original_text", d["text"])} for d in dialogues],
        output_dir=output_path.parent,
        episode_id=0,
        normalize=True,
        crossfade=True,
    )

    # Move/rename to expected output path
    if final_mp3 != output_path.with_suffix(".mp3"):
        import shutil
        target = output_path.with_suffix(".mp3")
        shutil.move(str(final_mp3), str(target))
        final_mp3 = target

    # P0 Fix: DO NOT delete chunks. Keep them for retry/debugging.
    
    # P0 Fix: Skip global Whisper alignment to avoid cumulative drift for long videos.
    # We now trust the precise timing from audio_mastering (derived from chunk durations).
    # timing_result = _get_accurate_timing(dialogues, final_mp3, adjusted_timing)
    print("[TTS] Skipping global Whisper alignment to prevent drift (using precise chunk timing)")
    timing_result = adjusted_timing
    
    # Add chunk_ids back to timing result if lost during mastering adjustment
    # (Assuming simple 1:1 mapping for now, though mastering might shift things)
    if len(timing_result) == len(timing_data):
        for t_res, t_orig in zip(timing_result, timing_data):
            t_res["chunk_id"] = t_orig.get("chunk_id")

    print(f"[TTS] VOICEVOX generation complete: {final_mp3}")
    return final_mp3, timing_result


def _generate_with_gemini(dialogues: List[Dict], output_path: Path) -> Tuple[Path, List[Dict]]:
    """Generate audio using Gemini TTS API."""
    import base64
    import requests
    import time as time_module

    print("[TTS] Using Gemini TTS for synthesis...")

    chunk_paths = []
    timing_data = []
    current_time = 0.0

    for idx, dialogue in enumerate(dialogues):
        text = dialogue.get("text", "")
        speaker = dialogue.get("speaker", "男性")
        voice = FEMALE_VOICE_NAME if speaker in ["女性", "B", "Female"] else MALE_VOICE_NAME

        chunk_path = output_path.parent / f"chunk_{idx}.wav"

        # Rate limiting for Gemini API
        max_retries = 3
        for retry in range(max_retries):
            try:
                audio_bytes, mime_type = _request_gemini_tts(text, voice)
                _write_audio_chunk(audio_bytes, mime_type, chunk_path)

                duration = _get_audio_duration(chunk_path)
                if SPEED_FACTOR != 1.0:
                    duration = duration / SPEED_FACTOR

                timing_data.append({
                    "speaker": speaker,
                    "text": dialogue.get("original_text", text),
                    "start": current_time,
                    "end": current_time + duration,
                })
                current_time += duration
                chunk_paths.append(chunk_path)

                # Rate limit: wait between requests
                if idx < len(dialogues) - 1:
                    time_module.sleep(21)  # 3 req/min limit
                break

            except RuntimeError as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    wait_time = 25 * (retry + 1)
                    print(f"[TTS] Rate limited, waiting {wait_time}s...")
                    time_module.sleep(wait_time)
                    if retry == max_retries - 1:
                        print(f"[TTS] Failed after {max_retries} retries")
                else:
                    raise

    if not chunk_paths:
        return _fallback_tts(dialogues, output_path)

    # Concatenate and convert
    final_path = output_path.with_suffix(".mp3")
    _concatenate_chunks(chunk_paths, final_path)

    # Cleanup
    for chunk in chunk_paths:
        chunk.unlink(missing_ok=True)

    # Get accurate timing
    timing_result = _get_accurate_timing(dialogues, final_path, timing_data)

    return final_path, timing_result


def _fallback_tts(dialogues: List[Dict], output_path: Path) -> Tuple[Path, List[Dict]]:
    """Fallback to gTTS if other engines fail."""
    from gtts import gTTS

    print("[TTS] Using gTTS fallback...")

    temp_files = []
    timing_data = []
    current_time = 0.0

    for i, d in enumerate(dialogues):
        text = d.get("text", "")
        if not text.strip():
            continue

        temp_path = output_path.parent / f"temp_{i}.mp3"

        try:
            tts = gTTS(text=text, lang="ja")
            tts.save(str(temp_path))
            temp_files.append(temp_path)

            duration = _get_audio_duration(temp_path)
            if SPEED_FACTOR != 1.0:
                duration = duration / SPEED_FACTOR

            timing_data.append({
                "speaker": d.get("speaker", "男性"),
                "text": d.get("original_text", text),
                "start": current_time,
                "end": current_time + duration,
            })
            current_time += duration

        except Exception as e:
            print(f"[TTS] gTTS failed for segment {i}: {e}")

    final_path = output_path.with_suffix(".mp3")

    if temp_files:
        _concatenate_chunks(temp_files, final_path, speed_factor=SPEED_FACTOR)
        for tf in temp_files:
            tf.unlink(missing_ok=True)
    else:
        _create_empty_audio(final_path)

    return final_path, timing_data


def _get_accurate_timing(
    dialogues: List[Dict],
    audio_path: Path,
    estimated_timing: List[Dict],
) -> List[Dict]:
    """Get accurate subtitle timing using Whisper or ElevenLabs STT."""

    if USE_WHISPER_STT:
        try:
            from whisper_stt import generate_accurate_subtitles_with_whisper
            timing = generate_accurate_subtitles_with_whisper(
                dialogues,
                audio_path,
                model_size=WHISPER_MODEL_SIZE,
            )
            if timing:
                print("[TTS] Using Whisper STT for accurate timing (100% FREE)")
                return timing
        except Exception as e:
            print(f"[TTS] Whisper STT failed: {e}")

    if USE_ELEVENLABS_STT:
        try:
            from elevenlabs_stt import generate_accurate_subtitles
            timing = generate_accurate_subtitles(dialogues, audio_path)
            if timing:
                print("[TTS] Using ElevenLabs STT for accurate timing")
                return timing
        except Exception as e:
            print(f"[TTS] ElevenLabs STT failed: {e}")

    print("[TTS] Using estimated timing")
    return estimated_timing


def _request_gemini_tts(text: str, voice_name: str) -> Tuple[bytes, str]:
    """Request audio from Gemini TTS API."""
    import base64
    import requests

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_TTS_MODEL}:generateContent?key={GEMINI_API_KEY}"
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
    data = r.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            audio = base64.b64decode(part["inlineData"]["data"])
            mime = part["inlineData"].get("mimeType", "audio/L16")
            return audio, mime

    raise RuntimeError("Gemini TTS response missing inlineData")


def _write_audio_chunk(audio_bytes: bytes, mime_type: str, output_path: Path):
    """Write raw audio bytes to WAV file."""
    raw_path = output_path.with_suffix(".raw")
    with open(raw_path, "wb") as f:
        f.write(audio_bytes)

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


def _concatenate_chunks(chunk_paths: List[Path], output_path: Path, speed_factor: float = 1.0):
    """Concatenate audio chunks into single file."""
    concat_file = output_path.parent / "tts_concat.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for chunk in chunk_paths:
            f.write(f"file '{chunk}'\n")

    filter_args = []
    if speed_factor != 1.0:
        filter_args = ["-filter:a", f"atempo={speed_factor}"]

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        *filter_args,
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path)
    ], check=True, capture_output=True)

    concat_file.unlink(missing_ok=True)


def _get_audio_duration(audio_path: Path) -> float:
    """Get audio duration using ffprobe."""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(audio_path)
        ], capture_output=True, text=True, timeout=10)
        return float(result.stdout.strip())
    except:
        return 60.0


def _create_empty_audio(output_path: Path) -> Path:
    """Create a short silent audio file."""
    final_path = output_path.with_suffix(".mp3")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=24000:cl=mono",
        "-t", "1",
        "-c:a", "libmp3lame",
        str(final_path)
    ], capture_output=True)
    return final_path


if __name__ == "__main__":
    print("=== TTS Generator Test ===\n")

    # Test dialogues
    test_dialogues = [
        {"speaker": "男性", "text": "こんにちは、本日のニュースをお届けします。"},
        {"speaker": "女性", "text": "AIの進化が加速していますね。"},
        {"speaker": "男性", "text": "OpenAIのGPT-5が発表されました。"},
    ]

    test_output = Path("/tmp/tts_test/dialogue.mp3")

    print(f"VOICEVOX available: {VOICEVOX_AVAILABLE}")
    print(f"Gemini API key: {'Yes' if GEMINI_API_KEY else 'No'}")

    result_path, timing = generate_dialogue_audio(test_dialogues, test_output)

    print(f"\nOutput: {result_path}")
    print(f"Duration: {_get_audio_duration(result_path):.1f}s")
    print(f"Timing entries: {len(timing)}")

    for t in timing:
        print(f"  [{t['start']:.1f}-{t['end']:.1f}] {t['speaker']}: {t['text'][:30]}...")
