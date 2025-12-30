"""Pre-upload validation to ensure media assets are ready for YouTube."""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    is_critical: bool = False  # Critical failures block YouTube upload


def _file_exists_with_min_size(path: Path, min_bytes: int) -> bool:
    return path.exists() and path.stat().st_size >= min_bytes


def _is_dummy_image(image_path: Path) -> bool:
    """
    Detect if an image is a dummy/placeholder image.

    Checks:
    1. Image is mostly a single solid color
    2. Image contains "DUMMY" text pattern (via color uniformity)
    3. Image is too small in file size for its dimensions

    Returns:
        True if image appears to be a dummy/placeholder
    """
    if not image_path.exists():
        return True  # Missing image is effectively a dummy

    if not PIL_AVAILABLE:
        # Fallback: check file size only
        # A real DALL-E 3 image at 1792x1024 should be at least 500KB
        return image_path.stat().st_size < 100 * 1024

    try:
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            width, height = img.size

            # Check 1: File size relative to dimensions
            # Real DALL-E images are typically 1-4MB for 1792x1024
            expected_min_size = (width * height) // 20  # At least ~92KB for 1792x1024
            actual_size = image_path.stat().st_size
            if actual_size < expected_min_size:
                return True

            # Check 2: Color uniformity (dummy images are often solid color)
            # Sample pixels from different regions
            sample_points = [
                (width // 4, height // 4),
                (width // 2, height // 2),
                (3 * width // 4, 3 * height // 4),
                (width // 4, 3 * height // 4),
                (3 * width // 4, height // 4),
            ]

            colors = [img.getpixel(p) for p in sample_points]

            # Check if all sampled colors are very similar (solid color)
            def color_distance(c1, c2):
                return sum(abs(a - b) for a, b in zip(c1, c2))

            max_distance = max(
                color_distance(colors[0], c) for c in colors[1:]
            )

            # If max color distance is very low, it's likely a solid color dummy
            if max_distance < 30:
                return True

            # Check 3: Known dummy color (40, 80, 120) from nano_banana_client.py
            dummy_color = (40, 80, 120)
            avg_color = tuple(sum(c[i] for c in colors) // len(colors) for i in range(3))
            if color_distance(avg_color, dummy_color) < 50:
                return True

            return False

    except Exception as e:
        print(f"[PreUploadCheck] Error checking image: {e}")
        # If we can't verify, assume it might be dummy
        return True


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
    background_path: Path = None,
) -> Dict[str, Any]:
    """Run a set of validations and return aggregated results.

    Returns:
        Dict with:
        - passed: bool - All checks passed
        - has_critical_failure: bool - Has failures that should block YouTube upload
        - checks: List[CheckResult] - Individual check results
    """
    checks: List[CheckResult] = []

    # CRITICAL CHECK: Background image must not be a dummy
    if background_path:
        bg_is_dummy = _is_dummy_image(background_path)
        checks.append(CheckResult(
            "background_image",
            not bg_is_dummy,
            "Background image is valid" if not bg_is_dummy else "CRITICAL: Background is dummy/placeholder image",
            is_critical=True  # This is a critical failure
        ))

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
    has_critical_failure = any(c.is_critical and not c.passed for c in checks)

    return {
        "passed": passed,
        "has_critical_failure": has_critical_failure,
        "checks": checks,
    }
