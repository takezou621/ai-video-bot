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

import text_normalizer
from voicevox_client import is_available as check_voicevox_available
import voicevox_client

# TTS Priority Configuration
USE_VOICEVOX = os.getenv("USE_VOICEVOX", "true").lower() == "true"

# Gemini TTS control (separate from GEMINI_API_KEY to allow script generation but skip TTS)
USE_GEMINI_TTS = os.getenv("USE_GEMINI_TTS", "true").lower() == "true"

# Lazy evaluation - only check VOICEVOX when actually needed
_voicevox_available_cached = None
_voicevox_checked = False

def _check_voicevox_available() -> bool:
    """Check VOICEVOX availability lazily - only when needed."""
    global _voicevox_available_cached, _voicevox_checked

    if not USE_VOICEVOX:
        return False

    # Return cached value if already checked
    if _voicevox_checked:
        return _voicevox_available_cached

    try:
        _voicevox_available_cached = check_voicevox_available()
    except Exception:
        _voicevox_available_cached = False

    _voicevox_checked = True
    return _voicevox_available_cached

def get_voicevox_available() -> bool:
    """Get VOICEVOX availability status (cached after first check)."""
    return _check_voicevox_available()

# Don't call _check_voicevox_available() at import time - this causes blocking
# The check will be performed lazily when first needed

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

# Log TTS strategy (lazy check - only at function call time, not import)
# Note: We defer checking VOICEVOX availability until actually needed
if USE_VOICEVOX:
    print(f"[TTS] Primary: VOICEVOX (will check availability when needed)")
elif GEMINI_API_KEY and USE_GEMINI_TTS:
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
    if _check_voicevox_available():
        return _generate_with_voicevox(normalized_dialogues, output_path)
    elif GEMINI_API_KEY and USE_GEMINI_TTS:
        return _generate_with_gemini(normalized_dialogues, output_path)
    else:
        return _fallback_tts(normalized_dialogues, output_path)


def _generate_with_voicevox(dialogues: List[Dict], output_path: Path) -> Tuple[Path, List[Dict]]:
    """Generate audio using VOICEVOX with persistent chunking."""
    print("[TTS] Using VOICEVOX for synthesis...")

    chunk_paths = []
    chunks_metadata = []
    timing_data = []
    successful_dialogues = []
    current_time = 0.0

    # P0 Fix: Use persistent chunks directory for idempotency
    chunks_dir = output_path.parent / "chunks"
    chunks_dir.mkdir(exist_ok=True)

    for idx, dialogue in enumerate(dialogues):
        text = dialogue.get("text", "").strip()
        speaker = dialogue.get("speaker", "男性")
        
        # Create a hash of the text to ensure audio matches content
        import hashlib
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:8]
        
        # Role-based mapping (Main/Sub)
        speaker_role = "sub" if speaker in ["女性", "B", "Female", "Sub"] else "main"

        # Consistent naming for idempotency
        # Include hash in filename or use sidecar file to verify
        chunk_filename = f"chunk_{idx:04d}.wav"
        chunk_path = chunks_dir / chunk_filename
        hash_path = chunks_dir / f"chunk_{idx:04d}.hash"

        # Idempotency: Check if chunk already exists AND matches the text hash
        is_valid_cache = False
        if chunk_path.exists() and chunk_path.stat().st_size > 0 and hash_path.exists():
            with open(hash_path, "r") as f:
                cached_hash = f.read().strip()
                if cached_hash == text_hash:
                    is_valid_cache = True

        if is_valid_cache:
            # print(f"[TTS] Reusing valid chunk {idx}")
            result = chunk_path
        else:
            # print(f"[TTS] Generating fresh chunk {idx}")
            result = voicevox_client.generate_voice(
                text,
                chunk_path,
                speaker_role=speaker_role,
            )
            # Save the hash for future verification
            if result:
                with open(hash_path, "w") as f:
                    f.write(text_hash)

        if result:
            duration = voicevox_client.get_audio_duration(chunk_path)
            # Metadata for this successful chunk
            chunk_meta = {
                "chunk_id": chunk_filename,
                "speaker": speaker,
                "text": dialogue.get("original_text", text),
                "start": current_time,
                "end": current_time + duration,
            }
            chunks_metadata.append(chunk_meta)
            timing_data.append(chunk_meta)
            
            # For Whisper alignment, we need the ORIGINAL text for subtitles,
            # but we also need to keep the normalized text for audio matching if needed.
            # Whisper alignment uses 'text' field for the final subtitle content.
            successful_dialogues.append({
                "speaker": speaker,
                "text": dialogue.get("original_text", text),
            })
            
            current_time += duration
            chunk_paths.append(chunk_path)
        else:
            print(f"[TTS] Warning: Failed to generate chunk {idx} - SKIPPING")

    if not chunk_paths:
        print("[TTS] No chunks generated, falling back to gTTS")
        return _fallback_tts(dialogues, output_path)

    # Concatenate chunks using audio_mastering
    from audio_mastering import master_episode

    final_mp3, adjusted_timing = master_episode(
        chunk_paths=chunk_paths,
        chunks_metadata=chunks_metadata,
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
    
    # Get accurate timing using Whisper STT (or fallback to calculated timing)
    # This fixes sync issues caused by crossfading/mastering duration changes
    print("[TTS] Aligning subtitles with final audio...")
    if USE_WHISPER_STT or USE_ELEVENLABS_STT:
        # VOICEVOX produces human-like voices, so is_synthetic=False
        timing_result = _get_accurate_timing(successful_dialogues, final_mp3, adjusted_timing, is_synthetic=False)
    else:
        print("[TTS] Using calculated timing (Whisper disabled)")
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

    # CRITICAL FIX: Adjust timing to match actual concatenated audio duration
    actual_duration = _get_audio_duration(final_path)
    estimated_end = timing_data[-1]["end"] if timing_data else 0

    if abs(actual_duration - estimated_end) > 1.0:  # More than 1 second difference
        scale_factor = actual_duration / estimated_end
        print(f"[TTS] Adjusting timing: estimated={estimated_end:.2f}s, actual={actual_duration:.2f}s, scale={scale_factor:.3f}")

        # Scale all timing to match actual audio duration
        current_time = 0.0
        for segment in timing_data:
            duration = (segment["end"] - segment["start"]) * scale_factor
            segment["start"] = current_time
            segment["end"] = current_time + duration
            current_time += duration

    # Get accurate timing (Whisper may still help with word-level timing)
    # Gemini TTS produces synthetic speech, so is_synthetic=True
    timing_result = _get_accurate_timing(dialogues, final_path, timing_data, is_synthetic=True)

    return final_path, timing_result


def _fallback_tts(dialogues: List[Dict], output_path: Path) -> Tuple[Path, List[Dict]]:
    """Fallback to gTTS (Google Text-to-Speech)."""
    from gtts import gTTS

    print("[TTS] Using gTTS (Google Text-to-Speech)...")

    temp_files = []
    timing_data = []
    current_time = 0.0
    chunks_dir = output_path.parent / "tts_chunks"
    chunks_dir.mkdir(exist_ok=True)

    for i, d in enumerate(dialogues):
        text = d.get("text", "")
        if not text.strip():
            continue

        temp_path = chunks_dir / f"chunk_{i}.mp3"
        speaker = d.get("speaker", "男性")

        try:
            tts = gTTS(text=text, lang="ja")
            tts.save(str(temp_path))

            temp_files.append(temp_path)

            duration = _get_audio_duration(temp_path)
            timing_data.append({
                "speaker": speaker,
                "text": d.get("original_text", text),
                "start": current_time,
                "end": current_time + duration,
            })
            current_time += duration

        except Exception as e:
            print(f"[TTS] gTTS failed for segment {i}: {e}")

    final_path = output_path.with_suffix(".mp3")

    if temp_files:
        # Concatenate with overall speed factor
        _concatenate_chunks(temp_files, final_path, speed_factor=SPEED_FACTOR)
        # Clean up chunks
        for tf in temp_files:
            tf.unlink(missing_ok=True)
        # Use shutil to remove directory even if not empty (handles edge cases)
        import shutil
        shutil.rmtree(chunks_dir, ignore_errors=True)
    else:
        _create_empty_audio(final_path)

    # CRITICAL FIX: Adjust timing to match actual concatenated audio duration
    actual_duration = _get_audio_duration(final_path)
    estimated_end = timing_data[-1]["end"] if timing_data else 0

    if abs(actual_duration - estimated_end) > 1.0:  # More than 1 second difference
        scale_factor = actual_duration / estimated_end
        print(f"[TTS] Adjusting timing: estimated={estimated_end:.2f}s, actual={actual_duration:.2f}s, scale={scale_factor:.3f}")

        # Scale all timing to match actual audio duration
        current_time = 0.0
        for segment in timing_data:
            duration = (segment["end"] - segment["start"]) * scale_factor
            segment["start"] = current_time
            segment["end"] = current_time + duration
            current_time += duration

    return final_path, timing_data


def _get_accurate_timing(
    dialogues: List[Dict],
    audio_path: Path,
    estimated_timing: List[Dict],
    is_synthetic: bool = False,
) -> List[Dict]:
    """
    Get accurate subtitle timing using Whisper or ElevenLabs STT.

    Args:
        dialogues: List of dialogue segments
        audio_path: Path to the audio file
        estimated_timing: Estimated timing data
        is_synthetic: True if using gTTS/Gemini TTS (synthetic voices)
                     False if using VOICEVOX (human-like voices)
    """

    # Check if we're using gTTS (synthetic voice) - Whisper struggles with synthetic speech
    # For gTTS, use simple estimated timing (more accurate than Whisper for synthetic speech)
    using_gtts = _should_use_estimated_timing(dialogues, estimated_timing, is_synthetic)

    if using_gtts:
        synth_type = "Gemini TTS" if is_synthetic else "gTTS"
        print(f"[TTS] Using estimated timing for synthetic speech ({synth_type})")
        # Don't modify timing - keep it as-is for best sync
        return estimated_timing

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


def _should_use_estimated_timing(
    dialogues: List[Dict],
    estimated_timing: List[Dict],
    is_synthetic: bool = False,
) -> bool:
    """
    Determine if we should use estimated timing instead of Whisper.
    Returns True for gTTS (synthetic speech) where Whisper struggles.

    Args:
        dialogues: List of dialogue segments
        estimated_timing: Timing data with start/end times
        is_synthetic: True if using gTTS/Gemini TTS (synthetic voices)
                     False if using VOICEVOX (human-like voices)
    """
    # For synthetic speech (gTTS, Gemini TTS), always use estimated timing
    # Whisper struggles with synthetic voices due to robotic patterns
    if is_synthetic:
        return True

    # For human-like voices (VOICEVOX), use the segment count heuristic
    # Only skip Whisper if we have many short segments (unlikely for VOICEVOX)
    if len(estimated_timing) > 15:
        avg_duration = sum(
            t["end"] - t["start"] for t in estimated_timing
        ) / len(estimated_timing)
        # Synthetic speech typically has shorter, more regular segments
        if avg_duration < 5.0:
            return True
    return False


def _improve_estimated_timing(
    audio_path: Path,
    timing_data: List[Dict],
) -> List[Dict]:
    """
    Improve estimated timing by using actual audio duration and adding gaps.
    """
    import subprocess

    # Get actual audio duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True,
        text=True
    )

    try:
        actual_duration = float(result.stdout.strip())
    except (ValueError, AttributeError):
        actual_duration = None

    if actual_duration is None:
        return timing_data

    # Calculate total estimated duration
    total_estimated = sum(t["end"] - t["start"] for t in timing_data)
    last_end = timing_data[-1]["end"] if timing_data else 0

    # Scale timing if mismatch
    if actual_duration > last_end * 1.1:  # More than 10% difference
        scale_factor = actual_duration / last_end

        # Apply scaling with gaps between segments
        improved_timing = []
        current_time = 0.0
        gap = 0.15  # Small gap between speakers

        for i, segment in enumerate(timing_data):
            duration = (segment["end"] - segment["start"]) * scale_factor

            # Add gap before new speaker (except first)
            if i > 0:
                prev_speaker = timing_data[i - 1]["speaker"]
                curr_speaker = segment["speaker"]
                if prev_speaker != curr_speaker:
                    current_time += gap

            improved_timing.append({
                **segment,
                "start": current_time,
                "end": current_time + duration
            })
            current_time += duration

        return improved_timing

    return timing_data


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
    import os
    concat_file = output_path.parent / "tts_concat.txt"

    # Use relative paths from the concat file directory to avoid path duplication
    output_dir = output_path.parent
    with open(concat_file, "w", encoding="utf-8") as f:
        for chunk in chunk_paths:
            # Use relative path or just filename if in same directory
            try:
                rel_path = os.path.relpath(chunk, output_dir)
                f.write(f"file '{rel_path}'\n")
            except ValueError:
                # On Windows or different drives, use absolute path
                f.write(f"file '{chunk}'\n")

    filter_args = []
    if speed_factor != 1.0:
        filter_args = ["-filter:a", f"atempo={speed_factor}"]

    # Run FFmpeg from the output directory to handle relative paths correctly
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "tts_concat.txt",
        *filter_args,
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path.name)
    ], check=True, capture_output=True, cwd=str(output_dir))

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

    print(f"VOICEVOX available: {_check_voicevox_available()}")
    print(f"Gemini API key: {'Yes' if GEMINI_API_KEY else 'No'}")

    result_path, timing = generate_dialogue_audio(test_dialogues, test_output)

    print(f"\nOutput: {result_path}")
    print(f"Duration: {_get_audio_duration(result_path):.1f}s")
    print(f"Timing entries: {len(timing)}")

    for t in timing:
        print(f"  [{t['start']:.1f}-{t['end']:.1f}] {t['speaker']}: {t['text'][:30]}...")
