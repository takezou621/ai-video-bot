"""
VOICEVOX TTS Gateway - Central orchestrator for podcast audio generation
Handles: Script parsing → Normalization → Chunking → Queue control → TTS → Output

Designed for 30-minute podcast production on Mac mini M4 16GB.
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

import voicevox_client
import text_normalizer
from podcast_api import parse_podcast_scenario, fetch_podcasts

# Configuration
MAX_CHUNK_CHARS = int(os.getenv("VOICEVOX_MAX_CHUNK_CHARS", "80"))
MIN_CHUNK_CHARS = int(os.getenv("VOICEVOX_MIN_CHUNK_CHARS", "20"))
CONCURRENT_LIMIT = int(os.getenv("VOICEVOX_CONCURRENT_LIMIT", "1"))  # Keep at 1 for M4 stability

# Output directories
DEFAULT_OUTPUT_DIR = Path(os.getenv("VOICEVOX_OUTPUT_DIR", "outputs"))


@dataclass
class RenderResult:
    """Result of an episode render."""
    episode_id: int
    mp3_path: Optional[Path]
    duration_seconds: float
    chunk_count: int
    failed_chunks: List[Dict]
    metrics: Dict
    timing_data: List[Dict]
    render_time_seconds: float
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["mp3_path"] = str(d["mp3_path"]) if d["mp3_path"] else None
        return d


@dataclass
class LineRenderResult:
    """Result of a single line render."""
    wav_path: Optional[Path]
    duration_seconds: float
    success: bool
    error: Optional[str] = None


def normalize_scenario_to_lines(scenario_text: str) -> List[Dict]:
    """
    Parse scenario text and convert to normalized line format.

    Args:
        scenario_text: Raw podcast scenario text.

    Returns:
        List of {"speaker": "男性/女性", "text": "...", "original_text": "..."}
    """
    # Parse using existing podcast_api parser
    dialogues = parse_podcast_scenario(scenario_text)

    normalized_lines = []
    for dialogue in dialogues:
        original_text = dialogue.get("text", "")
        if not original_text.strip():
            continue

        # Apply advanced normalization (numbers, dates, etc.)
        normalized_text = text_normalizer.normalize_for_tts_advanced(original_text)

        # Apply English to Katakana conversion
        normalized_text = text_normalizer.normalize_text_for_tts(normalized_text)

        normalized_lines.append({
            "speaker": dialogue.get("speaker", "男性"),
            "text": normalized_text,
            "original_text": original_text,
        })

    return normalized_lines


def chunk_lines(lines: List[Dict], max_chars: int = MAX_CHUNK_CHARS) -> List[Dict]:
    """
    Split long lines into smaller chunks for TTS processing.

    Args:
        lines: List of normalized lines.
        max_chars: Maximum characters per chunk.

    Returns:
        List of chunks with chunk_id assigned.
    """
    chunks = []
    chunk_id = 0

    for line in lines:
        text = line.get("text", "")
        speaker = line.get("speaker", "男性")

        # Split text into chunks
        text_chunks = text_normalizer.split_into_chunks(text, max_chars=max_chars)

        for chunk_text in text_chunks:
            if chunk_text.strip():
                chunks.append({
                    "chunk_id": chunk_id,
                    "speaker": speaker,
                    "text": chunk_text,
                })
                chunk_id += 1

    return chunks


def render_episode(
    episode_id: int,
    scenario_text: str,
    output_dir: Optional[Path] = None,
    title: str = "",
) -> RenderResult:
    """
    Render a complete episode from scenario text.

    This is the main entry point for episode rendering.

    Args:
        episode_id: Unique episode identifier.
        scenario_text: Full podcast scenario text.
        output_dir: Output directory (default: outputs/YYYY-MM-DD/episode_{id}/).
        title: Optional episode title for logging.

    Returns:
        RenderResult with all generation details.
    """
    start_time = time.time()

    # Setup output directory
    if output_dir is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = DEFAULT_OUTPUT_DIR / date_str / f"episode_{episode_id:04d}"

    output_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir = output_dir / "chunks"
    chunks_dir.mkdir(exist_ok=True)

    print(f"[Gateway] Starting episode {episode_id}: {title[:50]}...")

    try:
        # Step 1: Parse and normalize scenario
        print("[Gateway] Step 1: Parsing and normalizing scenario...")
        lines = normalize_scenario_to_lines(scenario_text)
        print(f"[Gateway]   Extracted {len(lines)} dialogue lines")

        if not lines:
            return RenderResult(
                episode_id=episode_id,
                mp3_path=None,
                duration_seconds=0,
                chunk_count=0,
                failed_chunks=[],
                metrics={},
                timing_data=[],
                render_time_seconds=time.time() - start_time,
                success=False,
                error="No valid dialogue lines found in scenario",
            )

        # Step 2: Chunk long lines
        print("[Gateway] Step 2: Chunking lines for TTS...")
        chunks = chunk_lines(lines, max_chars=MAX_CHUNK_CHARS)
        print(f"[Gateway]   Created {len(chunks)} chunks")

        # Save chunks for debugging/resume
        chunks_file = output_dir / "chunks.json"
        with open(chunks_file, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        # Step 3: Generate audio chunks
        print("[Gateway] Step 3: Generating audio chunks...")
        chunk_paths, failed_chunks = voicevox_client.generate_dialogue_chunks(
            chunks,
            chunks_dir,
            on_progress=_print_progress,
        )

        if not chunk_paths:
            return RenderResult(
                episode_id=episode_id,
                mp3_path=None,
                duration_seconds=0,
                chunk_count=0,
                failed_chunks=failed_chunks,
                metrics=voicevox_client.get_metrics().to_dict(),
                timing_data=[],
                render_time_seconds=time.time() - start_time,
                success=False,
                error="No audio chunks generated",
            )

        # Step 4: Concatenate and master audio
        print("[Gateway] Step 4: Mastering audio...")
        from audio_mastering import master_episode

        final_mp3, timing_data = master_episode(
            chunk_paths=chunk_paths,
            chunks_metadata=chunks,
            output_dir=output_dir,
            episode_id=episode_id,
        )

        # Calculate total duration
        total_duration = sum(t.get("end", 0) for t in timing_data[-1:]) if timing_data else 0

        # Save timing data
        timing_file = output_dir / "timing.json"
        with open(timing_file, "w", encoding="utf-8") as f:
            json.dump(timing_data, f, ensure_ascii=False, indent=2)

        # Get metrics
        metrics = voicevox_client.get_metrics().to_dict()

        # Save render manifest
        manifest = {
            "episode_id": episode_id,
            "title": title,
            "rendered_at": datetime.now().isoformat(),
            "mp3_path": str(final_mp3),
            "duration_seconds": total_duration,
            "chunk_count": len(chunk_paths),
            "failed_chunks": len(failed_chunks),
            "metrics": metrics,
        }
        manifest_file = output_dir / "manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        render_time = time.time() - start_time
        print(f"[Gateway] Episode {episode_id} complete!")
        print(f"[Gateway]   Duration: {total_duration:.1f}s ({total_duration/60:.1f} min)")
        print(f"[Gateway]   Render time: {render_time:.1f}s")
        print(f"[Gateway]   Output: {final_mp3}")

        return RenderResult(
            episode_id=episode_id,
            mp3_path=final_mp3,
            duration_seconds=total_duration,
            chunk_count=len(chunk_paths),
            failed_chunks=failed_chunks,
            metrics=metrics,
            timing_data=timing_data,
            render_time_seconds=render_time,
            success=True,
        )

    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[Gateway] Error rendering episode {episode_id}: {error_msg}")
        traceback.print_exc()

        return RenderResult(
            episode_id=episode_id,
            mp3_path=None,
            duration_seconds=0,
            chunk_count=0,
            failed_chunks=[],
            metrics=voicevox_client.get_metrics().to_dict(),
            timing_data=[],
            render_time_seconds=time.time() - start_time,
            success=False,
            error=error_msg,
        )


def render_line(
    speaker: str,
    text: str,
    output_path: Optional[Path] = None,
) -> LineRenderResult:
    """
    Render a single line of dialogue.

    Useful for testing or generating individual segments.

    Args:
        speaker: "男性" or "女性".
        text: Text to synthesize.
        output_path: Output WAV path (default: temp file).

    Returns:
        LineRenderResult with generation details.
    """
    if output_path is None:
        output_path = Path(f"/tmp/voicevox_line_{int(time.time())}.wav")

    # Normalize text
    normalized = text_normalizer.normalize_for_tts_advanced(text)
    normalized = text_normalizer.normalize_text_for_tts(normalized)

    # Determine speaker type
    speaker_type = "female" if speaker in ["女性", "B", "Female"] else "male"

    # Generate
    result = voicevox_client.generate_voice(
        normalized,
        output_path,
        speaker_type=speaker_type,
    )

    if result:
        duration = voicevox_client.get_audio_duration(result)
        return LineRenderResult(
            wav_path=result,
            duration_seconds=duration,
            success=True,
        )
    else:
        return LineRenderResult(
            wav_path=None,
            duration_seconds=0,
            success=False,
            error="VOICEVOX synthesis failed",
        )


def render_from_api(
    episode_id: Optional[int] = None,
    date_filter: Optional[str] = None,
) -> RenderResult:
    """
    Fetch episode from Podcast API and render.

    Args:
        episode_id: Specific episode ID to render.
        date_filter: Filter by date (YYYY-MM-DD).

    Returns:
        RenderResult with all generation details.
    """
    print("[Gateway] Fetching episode from Podcast API...")

    try:
        podcasts = fetch_podcasts(limit=5)

        if not podcasts:
            return RenderResult(
                episode_id=episode_id or 0,
                mp3_path=None,
                duration_seconds=0,
                chunk_count=0,
                failed_chunks=[],
                metrics={},
                timing_data=[],
                render_time_seconds=0,
                success=False,
                error="No podcasts found in API",
            )

        # Find matching podcast
        podcast = None
        for p in podcasts:
            if episode_id and p.get("id") == episode_id:
                podcast = p
                break
            if date_filter and p.get("date", "").startswith(date_filter):
                podcast = p
                break

        # Default to latest
        if podcast is None:
            podcast = podcasts[0]

        scenario = podcast.get("podcast_scenario", "")
        title = podcast.get("youtube_title", "")
        ep_id = podcast.get("id", 0)

        print(f"[Gateway] Found episode {ep_id}: {title[:50]}...")

        return render_episode(
            episode_id=ep_id,
            scenario_text=scenario,
            title=title,
        )

    except Exception as e:
        import traceback
        error_msg = f"API fetch failed: {str(e)}"
        traceback.print_exc()

        return RenderResult(
            episode_id=episode_id or 0,
            mp3_path=None,
            duration_seconds=0,
            chunk_count=0,
            failed_chunks=[],
            metrics={},
            timing_data=[],
            render_time_seconds=0,
            success=False,
            error=error_msg,
        )


def health_check() -> Dict[str, Any]:
    """
    Check gateway and dependencies health.

    Returns:
        Health status dict.
    """
    voicevox_ok = voicevox_client.is_available()

    return {
        "status": "healthy" if voicevox_ok else "degraded",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "voicevox": {
                "status": "ok" if voicevox_ok else "unavailable",
                "url": voicevox_client.VOICEVOX_URL,
            },
            "cache": {
                "enabled": voicevox_client.CACHE_ENABLED,
                "directory": str(voicevox_client.CACHE_DIR),
            },
        },
        "config": {
            "max_chunk_chars": MAX_CHUNK_CHARS,
            "concurrent_limit": CONCURRENT_LIMIT,
            "speaker_male_id": voicevox_client.SPEAKER_MALE,
            "speaker_female_id": voicevox_client.SPEAKER_FEMALE,
        },
    }


def resume_episode(
    output_dir: Path,
    episode_id: int,
) -> RenderResult:
    """
    Resume a partially completed episode render.

    Checks for existing chunk files and only regenerates missing ones.

    Args:
        output_dir: Directory containing partial render.
        episode_id: Episode ID to resume.

    Returns:
        RenderResult with all generation details.
    """
    chunks_file = output_dir / "chunks.json"
    if not chunks_file.exists():
        return RenderResult(
            episode_id=episode_id,
            mp3_path=None,
            duration_seconds=0,
            chunk_count=0,
            failed_chunks=[],
            metrics={},
            timing_data=[],
            render_time_seconds=0,
            success=False,
            error="No chunks.json found - cannot resume",
        )

    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    chunks_dir = output_dir / "chunks"
    chunks_dir.mkdir(exist_ok=True)

    # Find missing chunks
    missing_chunks = []
    existing_paths = []

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", 0)
        chunk_path = chunks_dir / f"chunk_{chunk_id:04d}.wav"

        if chunk_path.exists() and chunk_path.stat().st_size > 0:
            existing_paths.append(chunk_path)
        else:
            missing_chunks.append(chunk)

    print(f"[Gateway] Resume: {len(existing_paths)} existing, {len(missing_chunks)} to generate")

    if missing_chunks:
        # Generate missing chunks
        new_paths, failed = voicevox_client.generate_dialogue_chunks(
            missing_chunks,
            chunks_dir,
        )
        existing_paths.extend(new_paths)
    else:
        failed = []

    # Sort by chunk_id
    existing_paths.sort(key=lambda p: int(p.stem.split("_")[1]))

    # Master audio
    from audio_mastering import master_episode

    final_mp3, timing_data = master_episode(
        chunk_paths=existing_paths,
        chunks_metadata=chunks,
        output_dir=output_dir,
        episode_id=episode_id,
    )

    total_duration = sum(t.get("end", 0) for t in timing_data[-1:]) if timing_data else 0

    return RenderResult(
        episode_id=episode_id,
        mp3_path=final_mp3,
        duration_seconds=total_duration,
        chunk_count=len(existing_paths),
        failed_chunks=failed,
        metrics=voicevox_client.get_metrics().to_dict(),
        timing_data=timing_data,
        render_time_seconds=0,
        success=True,
    )


def _print_progress(current: int, total: int, status: str) -> None:
    """Print progress callback."""
    pct = (current / total * 100) if total > 0 else 0
    print(f"[Gateway]   Progress: {current}/{total} ({pct:.0f}%) - {status}")


# ============================================
# CLI Interface
# ============================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="VOICEVOX TTS Gateway")
    parser.add_argument("--health", action="store_true", help="Check health status")
    parser.add_argument("--render-api", action="store_true", help="Render latest from API")
    parser.add_argument("--episode-id", type=int, help="Specific episode ID to render")
    parser.add_argument("--date", type=str, help="Date filter (YYYY-MM-DD)")
    parser.add_argument("--line", type=str, help="Render single line")
    parser.add_argument("--speaker", type=str, default="男性", help="Speaker for --line")
    parser.add_argument("--resume", type=str, help="Resume from directory")

    args = parser.parse_args()

    if args.health:
        status = health_check()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif args.render_api:
        result = render_from_api(
            episode_id=args.episode_id,
            date_filter=args.date,
        )
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))

    elif args.line:
        result = render_line(args.speaker, args.line)
        print(f"Success: {result.success}")
        print(f"Path: {result.wav_path}")
        print(f"Duration: {result.duration_seconds:.2f}s")

    elif args.resume:
        result = resume_episode(Path(args.resume), args.episode_id or 0)
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))

    else:
        # Default: show health and test
        print("=== VOICEVOX Gateway Test ===\n")

        status = health_check()
        print(f"Status: {status['status']}")
        print(f"VOICEVOX: {status['components']['voicevox']['status']}")

        if status["components"]["voicevox"]["status"] == "ok":
            print("\nTesting single line render...")
            result = render_line("男性", "こんにちは、テストです。")
            print(f"  Result: {result.success}, Duration: {result.duration_seconds:.2f}s")
        else:
            print("\nVOICEVOX not available. Start with: docker compose up voicevox")
