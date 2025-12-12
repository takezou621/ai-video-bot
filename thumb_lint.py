#!/usr/bin/env python3
"""
Thumbnail QA Lint
Checks common YouTube thumbnail requirements:
- Resolution, aspect ratio, file size
- Brightness / contrast balance
- Palette simplicity (<= 6 dominant colors)
- 150px縮小時の視認性（極端なノイズ/暗さを検知）
"""
from __future__ import annotations

import argparse
import statistics
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageFilter


def _brightness_stats(image: Image.Image) -> Tuple[float, float, float]:
    gray = image.convert("L")
    pixels = list(gray.getdata())
    avg = statistics.fmean(pixels)
    bright_ratio = sum(1 for p in pixels if p >= 200) / len(pixels)
    dark_ratio = sum(1 for p in pixels if p <= 30) / len(pixels)
    return avg, bright_ratio, dark_ratio


def _palette_complexity(image: Image.Image, limit: int = 4) -> int:
    reduced = image.convert("P", palette=Image.ADAPTIVE, colors=limit)
    colors = reduced.getcolors(limit ** 2)
    return len(colors or [])


def _edge_strength(image: Image.Image) -> float:
    small = image.resize((150, int(150 * image.height / image.width)), Image.Resampling.LANCZOS)
    edges = small.filter(ImageFilter.FIND_EDGES).convert("L")
    return statistics.fmean(edges.getdata())


def _visual_busyness_score(image: Image.Image) -> float:
    sample = image.resize((48, int(48 * image.height / image.width)), Image.Resampling.BILINEAR).convert("L")
    data = sample.getdata()
    intense = sum(1 for p in data if p >= 230 or p <= 25)
    return intense / len(data)


def lint_thumbnail(path: Path, min_size_kb: int = 80, max_size_kb: int = 2000) -> List[str]:
    warnings: List[str] = []
    if not path.exists():
        return [f"File not found: {path}"]
    size_kb = path.stat().st_size / 1024
    with Image.open(path) as img:
        img = img.convert("RGB")
        width, height = img.size
        aspect = width / height

        if width < 1280 or height < 720:
            warnings.append(f"Resolution too small ({width}x{height})")
        if abs(aspect - (16 / 9)) > 0.03:
            warnings.append(f"Aspect ratio off: {aspect:.2f}")

        if size_kb < min_size_kb:
            warnings.append(f"File size too small ({size_kb:.0f}KB)")
        if size_kb > max_size_kb:
            warnings.append(f"File size too large ({size_kb:.0f}KB)")

        avg_brightness, bright_ratio, dark_ratio = _brightness_stats(img)
        if not 45 <= avg_brightness <= 195:
            warnings.append(f"Average brightness {avg_brightness:.1f} outside 45-195")
        if bright_ratio < 0.12:
            warnings.append(f"Bright pixel ratio low ({bright_ratio:.2%}) – text may be unreadable")
        if dark_ratio < 0.05:
            warnings.append(f"Shadow ratio low ({dark_ratio:.2%}) – insufficient depth")

        palette_size = _palette_complexity(img)
        if palette_size > 4:
            warnings.append(f"Too many dominant colors ({palette_size}) – limit palette to 3")

        edge_score = _edge_strength(img)
        if edge_score < 30:
            warnings.append("Edge contrast too low at 150px – text/subjects may blur")

        text_box = (
            int(width * 0.1),
            int(height * 0.4),
            int(width * 0.65),
            int(height * 0.75)
        )
        title_region = img.crop(text_box).convert("L")
        title_pixels = list(title_region.getdata())
        dark_ratio = sum(1 for p in title_pixels if p < 40) / len(title_pixels)
        bright_ratio = sum(1 for p in title_pixels if p > 200) / len(title_pixels)
        if dark_ratio > 0.15:
            warnings.append(f"Title backdrop too noisy (dark pixels {dark_ratio:.1%})")
        if bright_ratio < 0.25:
            warnings.append(f"Title text contrast low (bright pixels {bright_ratio:.1%})")

        busyness = _visual_busyness_score(img)
        if busyness > 0.45:
            warnings.append("Too many competing elements detected - simplify layout (busyness>{:.0%})".format(busyness))

    return warnings


def main():
    parser = argparse.ArgumentParser(description="Lint YouTube thumbnails for quality issues")
    parser.add_argument("images", nargs="+", help="Thumbnail image paths")
    parser.add_argument("--min-size-kb", type=int, default=80)
    parser.add_argument("--max-size-kb", type=int, default=2000)
    args = parser.parse_args()

    exit_code = 0
    for img_path in args.images:
        path = Path(img_path)
        warnings = lint_thumbnail(path, args.min_size_kb, args.max_size_kb)
        title = f"[{path}]"
        if warnings:
            print(f"{title} ⚠️  {len(warnings)} warning(s):")
            for w in warnings:
                print(f"   - {w}")
            exit_code = 1
        else:
            print(f"{title} ✅  PASS")

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
