"""
Audio Mastering - Combine TTS chunks into final podcast audio
Handles: Concatenation, crossfade, silence trimming, volume normalization (LUFS)

Optimized for 30-minute podcast production.
"""
import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Configuration
CROSSFADE_MS = int(os.getenv("AUDIO_CROSSFADE_MS", "200"))  # 200-400ms recommended
SILENCE_THRESHOLD_DB = float(os.getenv("AUDIO_SILENCE_THRESHOLD_DB", "-40"))
TARGET_LUFS = float(os.getenv("AUDIO_TARGET_LUFS", "-16"))  # Podcast standard
SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "24000"))
OUTPUT_BITRATE = os.getenv("AUDIO_OUTPUT_BITRATE", "192k")


@dataclass
class AudioSegment:
    """Represents an audio segment with timing info."""
    path: Path
    duration: float
    start_time: float
    end_time: float
    speaker: str
    text: str


def get_audio_duration(audio_path: Path) -> float:
    """Get duration of audio file in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(audio_path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def trim_silence(
    input_path: Path,
    output_path: Path,
    threshold_db: float = SILENCE_THRESHOLD_DB,
) -> Path:
    """
    Trim silence from beginning and end of audio.

    Args:
        input_path: Input audio file.
        output_path: Output audio file.
        threshold_db: Silence threshold in dB.

    Returns:
        Path to trimmed audio.
    """
    try:
        # Use silenceremove filter to trim start and end
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-af", f"silenceremove=start_periods=1:start_silence=0.1:start_threshold={threshold_db}dB,"
                       f"areverse,silenceremove=start_periods=1:start_silence=0.1:start_threshold={threshold_db}dB,areverse",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return output_path
    except Exception as e:
        print(f"[Mastering] Silence trim failed: {e}, using original")
        return input_path


def normalize_volume(
    input_path: Path,
    output_path: Path,
    target_lufs: float = TARGET_LUFS,
) -> Path:
    """
    Normalize audio volume to target LUFS.

    Args:
        input_path: Input audio file.
        output_path: Output audio file.
        target_lufs: Target loudness in LUFS (default: -16 for podcasts).

    Returns:
        Path to normalized audio.
    """
    try:
        # Two-pass loudness normalization
        # Pass 1: Analyze
        analyze_result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:print_format=json",
                "-f", "null", "-",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Parse loudness stats from stderr
        stderr = analyze_result.stderr
        json_start = stderr.rfind("{")
        json_end = stderr.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            stats = json.loads(stderr[json_start:json_end])
            input_i = stats.get("input_i", "-24")
            input_tp = stats.get("input_tp", "-1")
            input_lra = stats.get("input_lra", "11")
            input_thresh = stats.get("input_thresh", "-34")

            # Pass 2: Apply normalization
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(input_path),
                    "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:"
                           f"measured_I={input_i}:measured_TP={input_tp}:"
                           f"measured_LRA={input_lra}:measured_thresh={input_thresh}:"
                           f"linear=true",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                timeout=120,
            )
            return output_path

        # Fallback: simple volume adjustment
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
        return output_path

    except Exception as e:
        print(f"[Mastering] Volume normalization failed: {e}, using original")
        return input_path


def concatenate_with_crossfade(
    chunk_paths: List[Path],
    output_path: Path,
    crossfade_ms: int = CROSSFADE_MS,
) -> Path:
    """
    Concatenate audio chunks with crossfade transitions.

    Args:
        chunk_paths: List of audio chunk paths (in order).
        output_path: Output audio file.
        crossfade_ms: Crossfade duration in milliseconds.

    Returns:
        Path to concatenated audio.
    """
    if not chunk_paths:
        raise ValueError("No chunks to concatenate")

    if len(chunk_paths) == 1:
        # Single file, just copy
        import shutil
        shutil.copy(chunk_paths[0], output_path)
        return output_path

    try:
        # Build complex filter for crossfade
        crossfade_sec = crossfade_ms / 1000.0

        # For many chunks, use concat demuxer (simpler, no crossfade)
        # Crossfade is complex filter and can be slow for many files
        if len(chunk_paths) > 50 or crossfade_ms == 0:
            return _concatenate_simple(chunk_paths, output_path)

        # Build crossfade filter chain
        inputs = []
        filter_parts = []

        for i, path in enumerate(chunk_paths):
            inputs.extend(["-i", str(path)])

        # Build filter graph
        # [0][1]acrossfade=d=0.2[a01]; [a01][2]acrossfade=d=0.2[a02]; ...
        current_label = "[0]"

        for i in range(1, len(chunk_paths)):
            next_label = f"[a{i:02d}]"
            filter_parts.append(
                f"{current_label}[{i}]acrossfade=d={crossfade_sec}:c1=tri:c2=tri{next_label}"
            )
            current_label = next_label

        filter_complex = ";".join(filter_parts)

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", current_label,
            "-c:a", "pcm_s16le",
            str(output_path),
        ]

        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        return output_path

    except Exception as e:
        print(f"[Mastering] Crossfade concat failed: {e}, using simple concat")
        return _concatenate_simple(chunk_paths, output_path)


def _concatenate_simple(chunk_paths: List[Path], output_path: Path) -> Path:
    """Simple concatenation using concat demuxer."""
    # Create concat file
    concat_file = output_path.parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for path in chunk_paths:
            # Escape single quotes in path
            safe_path = str(path).replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "pcm_s16le",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            timeout=300,
        )
    finally:
        concat_file.unlink(missing_ok=True)

    return output_path


def convert_to_mp3(
    input_path: Path,
    output_path: Path,
    bitrate: str = OUTPUT_BITRATE,
) -> Path:
    """
    Convert audio to MP3 format.

    Args:
        input_path: Input audio file.
        output_path: Output MP3 file.
        bitrate: Output bitrate (default: 192k).

    Returns:
        Path to MP3 file.
    """
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-c:a", "libmp3lame",
            "-b:a", bitrate,
            str(output_path),
        ],
        check=True,
        capture_output=True,
        timeout=120,
    )
    return output_path


def master_episode(
    chunk_paths: List[Path],
    chunks_metadata: List[Dict],
    output_dir: Path,
    episode_id: int,
    normalize: bool = True,
    crossfade: bool = True,
) -> Tuple[Path, List[Dict]]:
    """
    Master a complete episode from chunks.

    This is the main entry point for audio mastering.

    Args:
        chunk_paths: List of audio chunk files (in order).
        chunks_metadata: Metadata for each chunk (speaker, text).
        output_dir: Directory to save output files.
        episode_id: Episode identifier for naming.
        normalize: Apply volume normalization.
        crossfade: Apply crossfade between chunks.

    Returns:
        Tuple of (final MP3 path, timing data).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Mastering] Processing {len(chunk_paths)} chunks...")

    # Step 1: Calculate timing data from chunk durations
    timing_data = []
    current_time = 0.0

    chunk_durations = []
    for i, (path, meta) in enumerate(zip(chunk_paths, chunks_metadata)):
        duration = get_audio_duration(path)
        chunk_durations.append(duration)

        timing_data.append({
            "speaker": meta.get("speaker", "男性"),
            "text": meta.get("text", ""),
            "start": current_time,
            "end": current_time + duration,
            "chunk_id": meta.get("chunk_id", i),
        })

        # Account for crossfade overlap (chunks will overlap slightly)
        if crossfade and i < len(chunk_paths) - 1:
            current_time += duration - (CROSSFADE_MS / 1000.0)
        else:
            current_time += duration

    print(f"[Mastering]   Total duration (pre-master): {current_time:.1f}s")

    # Step 2: Concatenate chunks
    concat_wav = output_dir / f"episode_{episode_id:04d}_concat.wav"

    if crossfade:
        print("[Mastering]   Concatenating with crossfade...")
        concatenate_with_crossfade(chunk_paths, concat_wav, CROSSFADE_MS)
    else:
        print("[Mastering]   Simple concatenation...")
        _concatenate_simple(chunk_paths, concat_wav)

    # Step 3: Trim silence
    trimmed_wav = output_dir / f"episode_{episode_id:04d}_trimmed.wav"
    print("[Mastering]   Trimming silence...")
    trim_silence(concat_wav, trimmed_wav)

    # Step 4: Normalize volume
    if normalize:
        normalized_wav = output_dir / f"episode_{episode_id:04d}_normalized.wav"
        print(f"[Mastering]   Normalizing to {TARGET_LUFS} LUFS...")
        normalize_volume(trimmed_wav, normalized_wav, TARGET_LUFS)
    else:
        normalized_wav = trimmed_wav

    # Step 5: Convert to MP3
    final_mp3 = output_dir / f"dialogue.mp3"
    print("[Mastering]   Converting to MP3...")
    convert_to_mp3(normalized_wav, final_mp3, OUTPUT_BITRATE)

    # Get final duration
    final_duration = get_audio_duration(final_mp3)
    print(f"[Mastering]   Final duration: {final_duration:.1f}s ({final_duration/60:.1f} min)")

    # Adjust timing data to match actual duration
    # P0 Fix: Do NOT linearly scale timing. This causes drift if silence was only removed from edges.
    # Instead, just clamp the last segment to the final duration.
    if timing_data and final_duration > 0:
        # Calculate the shift caused by silence trimming at the start
        # (Heuristic: simple diff if duration mismatch is small)
        original_end = timing_data[-1]["end"]
        if abs(final_duration - original_end) > 1.0:
            print(f"[Mastering] Warning: Large duration mismatch (Exp: {original_end:.1f}s, Act: {final_duration:.1f}s)")
        
        # Clamp only the very last end time
        if timing_data[-1]["end"] > final_duration:
            timing_data[-1]["end"] = final_duration

    # Cleanup intermediate files
    for temp_file in [concat_wav, trimmed_wav]:
        if temp_file.exists() and temp_file != normalized_wav:
            temp_file.unlink(missing_ok=True)
    if normalize and normalized_wav.exists() and normalized_wav != final_mp3:
        normalized_wav.unlink(missing_ok=True)

    return final_mp3, timing_data


def add_bgm(
    voice_path: Path,
    bgm_path: Path,
    output_path: Path,
    bgm_volume: float = 0.1,
    fade_in_sec: float = 3.0,
    fade_out_sec: float = 5.0,
) -> Path:
    """
    Add background music to voice audio.

    Args:
        voice_path: Path to voice audio.
        bgm_path: Path to BGM audio.
        output_path: Output path.
        bgm_volume: BGM volume (0.0-1.0, default: 0.1 = 10%).
        fade_in_sec: BGM fade in duration.
        fade_out_sec: BGM fade out duration.

    Returns:
        Path to mixed audio.
    """
    voice_duration = get_audio_duration(voice_path)

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(voice_path),
                "-stream_loop", "-1", "-i", str(bgm_path),
                "-filter_complex",
                f"[1:a]volume={bgm_volume},"
                f"afade=t=in:st=0:d={fade_in_sec},"
                f"afade=t=out:st={voice_duration - fade_out_sec}:d={fade_out_sec},"
                f"atrim=0:{voice_duration}[bgm];"
                f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2",
                "-c:a", "libmp3lame",
                "-b:a", OUTPUT_BITRATE,
                str(output_path),
            ],
            check=True,
            capture_output=True,
            timeout=300,
        )
        return output_path
    except Exception as e:
        print(f"[Mastering] BGM mixing failed: {e}")
        return voice_path


def add_jingle(
    main_audio: Path,
    jingle_path: Path,
    output_path: Path,
    position: str = "start",  # "start" or "end"
    crossfade_sec: float = 1.0,
) -> Path:
    """
    Add jingle at start or end of audio.

    Args:
        main_audio: Path to main audio.
        jingle_path: Path to jingle audio.
        output_path: Output path.
        position: "start" or "end".
        crossfade_sec: Crossfade duration.

    Returns:
        Path to output audio.
    """
    try:
        if position == "start":
            # Jingle first, then main
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(jingle_path),
                    "-i", str(main_audio),
                    "-filter_complex",
                    f"[0][1]acrossfade=d={crossfade_sec}:c1=tri:c2=tri",
                    "-c:a", "libmp3lame",
                    "-b:a", OUTPUT_BITRATE,
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                timeout=120,
            )
        else:
            # Main first, then jingle
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(main_audio),
                    "-i", str(jingle_path),
                    "-filter_complex",
                    f"[0][1]acrossfade=d={crossfade_sec}:c1=tri:c2=tri",
                    "-c:a", "libmp3lame",
                    "-b:a", OUTPUT_BITRATE,
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                timeout=120,
            )
        return output_path
    except Exception as e:
        print(f"[Mastering] Jingle addition failed: {e}")
        return main_audio


if __name__ == "__main__":
    print("=== Audio Mastering Test ===\n")

    # Test with sample files
    test_dir = Path("/tmp/audio_mastering_test")
    test_dir.mkdir(exist_ok=True)

    # Create test WAV files using ffmpeg
    print("Creating test audio files...")

    for i, text in enumerate(["テスト音声1", "テスト音声2", "テスト音声3"]):
        wav_path = test_dir / f"test_{i}.wav"
        # Generate silence as placeholder
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"sine=frequency=440:duration=2",
                str(wav_path),
            ],
            capture_output=True,
        )
        print(f"  Created: {wav_path}")

    # Test concatenation
    chunk_paths = list(test_dir.glob("test_*.wav"))
    chunks_meta = [{"speaker": "男性", "text": f"chunk {i}"} for i in range(len(chunk_paths))]

    print("\nTesting master_episode...")
    try:
        mp3_path, timing = master_episode(
            chunk_paths=chunk_paths,
            chunks_metadata=chunks_meta,
            output_dir=test_dir,
            episode_id=9999,
        )
        print(f"Output: {mp3_path}")
        print(f"Duration: {get_audio_duration(mp3_path):.1f}s")
        print(f"Timing entries: {len(timing)}")
    except Exception as e:
        print(f"Error: {e}")
