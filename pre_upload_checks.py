"""Pre-upload validation to ensure media assets are ready for YouTube."""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def _file_exists_with_min_size(path: Path, min_bytes: int) -> bool:
    return path.exists() and path.stat().st_size >= min_bytes


def _is_sorted_timestamps(timestamps: List[Dict[str, Any]]) -> bool:
    times = [ts.get("time", 0) for ts in timestamps]
    return times == sorted(times)


def _has_unique_labels(timestamps: List[Dict[str, Any]], min_unique: int) -> bool:
    labels = {ts.get("label") for ts in timestamps if ts.get("label")}
    return len(labels) >= min_unique


def run_pre_upload_checks(
    video_path: Path,
    thumbnail_path: Path,
    metadata: Dict[str, Any],
    timestamps: List[Dict[str, Any]],
    script: Dict[str, Any],
    timing_data: List[Dict[str, Any]],
    expected_duration_seconds: float,
) -> Dict[str, Any]:
    """Run a set of validations and return aggregated results."""
    checks: List[CheckResult] = []

    video_ok = _file_exists_with_min_size(video_path, min_bytes=2 * 1024 * 1024)
    checks.append(CheckResult(
        "video_file",
        video_ok,
        f"Video exists ({video_path.name})" if video_ok else "Video file missing or too small"
    ))

    thumb_ok = _file_exists_with_min_size(thumbnail_path, min_bytes=50 * 1024)
    checks.append(CheckResult(
        "thumbnail_file",
        thumb_ok,
        f"Thumbnail ready ({thumbnail_path.name})" if thumb_ok else "Thumbnail missing or too small"
    ))

    title = metadata.get("youtube_title", "")
    title_ok = bool(title) and 10 <= len(title) <= 90
    checks.append(CheckResult(
        "title_length",
        title_ok,
        "Title length OK" if title_ok else f"Title length invalid ({len(title)} chars)"
    ))

    if title:
        first_token = title.split()[0]
        entity_ok = first_token.isascii() or len(first_token) >= 1
    else:
        entity_ok = False
    checks.append(CheckResult(
        "title_entity",
        entity_ok,
        "Title starts with entity" if entity_ok else "Title may be missing named entity prefix"
    ))

    ts_ok = bool(timestamps) and _is_sorted_timestamps(timestamps) and _has_unique_labels(timestamps, 3)
    checks.append(CheckResult(
        "timestamps",
        ts_ok,
        "Timestamps look valid" if ts_ok else "Timestamps missing / unsorted / low variety"
    ))

    script_ok = len(script.get("dialogues", [])) >= 10
    checks.append(CheckResult(
        "script_dialogues",
        script_ok,
        "Dialogue count OK" if script_ok else "Dialogue count too low"
    ))

    duration_diff = abs(expected_duration_seconds - timing_data[-1].get("end", 0) if timing_data else 0)
    duration_ok = duration_diff <= 60  # Allow up to 60s difference for TTS estimation variance
    checks.append(CheckResult(
        "duration_match",
        duration_ok,
        "Duration matches timing data" if duration_ok else "Duration mismatch vs timing data"
    ))

    passed = all(c.passed for c in checks)
    return {
        "passed": passed,
        "checks": checks,
    }
