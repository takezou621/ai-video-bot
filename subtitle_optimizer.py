"""
Subtitle Optimizer - Improve subtitle readability and quality
Based on best practices for YouTube subtitles
"""
from typing import List, Dict, Tuple
import re


class SubtitleOptimizer:
    """
    Optimizes subtitles for better readability and viewer experience.

    Features:
    - Ensures minimum display duration
    - Splits long text into multiple segments
    - Validates reading speed
    - Adds optimal line breaks
    """

    # Optimal reading speed: 15-21 characters per second (Japanese)
    MIN_CHARS_PER_SECOND = 15
    MAX_CHARS_PER_SECOND = 25  # Increased from 21 for faster speech

    # Display timing
    MIN_DISPLAY_DURATION = 1.0  # Minimum 1 second per subtitle
    MAX_DISPLAY_DURATION = 7.0  # Maximum 7 seconds per subtitle

    # Text length constraints
    MAX_CHARS_PER_SUBTITLE = 80  # Maximum characters per subtitle
    MAX_CHARS_PER_LINE = 40      # Maximum characters per line
    MAX_LINES = 2                # Maximum lines per subtitle

    @staticmethod
    def optimize_timing_data(timing_data: List[Dict]) -> List[Dict]:
        """
        Optimize subtitle timing and split long texts.

        Args:
            timing_data: Original timing data

        Returns:
            Optimized timing data
        """
        optimized = []

        for segment in timing_data:
            speaker = segment["speaker"]
            text = segment["text"]
            start = segment["start"]
            end = segment["end"]
            duration = end - start

            # Check if text is too long
            if len(text) > SubtitleOptimizer.MAX_CHARS_PER_SUBTITLE:
                # Split into multiple segments
                split_segments = SubtitleOptimizer._split_long_subtitle(
                    text, speaker, start, end
                )
                optimized.extend(split_segments)
            else:
                # Check if duration is too short
                if duration < SubtitleOptimizer.MIN_DISPLAY_DURATION:
                    # Extend duration slightly
                    duration = SubtitleOptimizer.MIN_DISPLAY_DURATION
                    end = start + duration

                # Check if reading speed is too fast
                chars_per_sec = len(text) / max(duration, 0.1)
                if chars_per_sec > SubtitleOptimizer.MAX_CHARS_PER_SECOND:
                    # Too fast to read comfortably - extend duration
                    min_duration = len(text) / SubtitleOptimizer.MAX_CHARS_PER_SECOND
                    if min_duration > duration:
                        end = start + min_duration

                optimized.append({
                    "speaker": speaker,
                    "text": text,
                    "start": start,
                    "end": end,
                    "reading_speed": len(text) / max(end - start, 0.1)
                })

        # Adjust overlaps
        optimized = SubtitleOptimizer._fix_overlaps(optimized)

        return optimized

    @staticmethod
    def _split_long_subtitle(
        text: str,
        speaker: str,
        start: float,
        end: float
    ) -> List[Dict]:
        """Split long subtitle into multiple segments."""
        segments = []
        duration = end - start

        # Try to split at sentence boundaries
        sentences = re.split(r'([。！？\.\!\?])', text)

        # Reconstruct sentences with punctuation
        current_text = ""
        split_points = []

        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punct = sentences[i + 1] if i + 1 < len(sentences) else ""

            if len(current_text) + len(sentence) + len(punct) > SubtitleOptimizer.MAX_CHARS_PER_SUBTITLE:
                if current_text:
                    split_points.append(current_text)
                current_text = sentence + punct
            else:
                current_text += sentence + punct

        if current_text:
            split_points.append(current_text)

        # If no sentence splits, split by character count
        if len(split_points) <= 1:
            split_points = []
            for i in range(0, len(text), SubtitleOptimizer.MAX_CHARS_PER_SUBTITLE):
                split_points.append(text[i:i + SubtitleOptimizer.MAX_CHARS_PER_SUBTITLE])

        # Calculate timing for each segment
        total_chars = sum(len(s) for s in split_points)
        current_time = start

        for segment_text in split_points:
            # Proportional timing based on character count
            segment_duration = (len(segment_text) / total_chars) * duration
            segment_duration = max(segment_duration, SubtitleOptimizer.MIN_DISPLAY_DURATION)

            segments.append({
                "speaker": speaker,
                "text": segment_text,
                "start": current_time,
                "end": current_time + segment_duration,
                "reading_speed": len(segment_text) / segment_duration
            })

            current_time += segment_duration

        return segments

    @staticmethod
    def _fix_overlaps(timing_data: List[Dict]) -> List[Dict]:
        """Fix overlapping subtitles by adjusting end times."""
        if not timing_data:
            return []

        fixed = []
        for i, segment in enumerate(timing_data):
            if i > 0:
                # Check if this segment overlaps with previous
                prev_end = fixed[-1]["end"]
                if segment["start"] < prev_end:
                    # Add small gap between subtitles
                    segment["start"] = prev_end + 0.1

                # Ensure minimum duration
                if segment["end"] <= segment["start"]:
                    segment["end"] = segment["start"] + SubtitleOptimizer.MIN_DISPLAY_DURATION

            fixed.append(segment)

        return fixed

    @staticmethod
    def add_line_breaks(text: str) -> str:
        """
        Add optimal line breaks for readability.

        Args:
            text: Subtitle text

        Returns:
            Text with line breaks
        """
        if len(text) <= SubtitleOptimizer.MAX_CHARS_PER_LINE:
            return text

        # Try to split at natural boundaries
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= SubtitleOptimizer.MAX_CHARS_PER_LINE:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        # Limit to MAX_LINES
        if len(lines) > SubtitleOptimizer.MAX_LINES:
            lines = lines[:SubtitleOptimizer.MAX_LINES]
            lines[-1] += "..."

        return "\n".join(lines)

    @staticmethod
    def validate_subtitle_quality(timing_data: List[Dict]) -> Dict:
        """
        Validate subtitle quality and generate report.

        Args:
            timing_data: Timing data to validate

        Returns:
            Validation report
        """
        issues = []
        warnings = []
        stats = {
            "total_segments": len(timing_data),
            "too_fast": 0,
            "too_slow": 0,
            "too_short": 0,
            "too_long": 0,
            "avg_reading_speed": 0,
            "avg_duration": 0
        }

        total_duration = 0
        total_speed = 0

        for i, segment in enumerate(timing_data):
            duration = segment["end"] - segment["start"]
            chars = len(segment["text"])
            reading_speed = chars / max(duration, 0.1)

            total_duration += duration
            total_speed += reading_speed

            # Check reading speed
            if reading_speed > SubtitleOptimizer.MAX_CHARS_PER_SECOND:
                stats["too_fast"] += 1
                issues.append(f"Segment {i}: Too fast ({reading_speed:.1f} chars/sec)")
            elif reading_speed < SubtitleOptimizer.MIN_CHARS_PER_SECOND:
                stats["too_slow"] += 1
                warnings.append(f"Segment {i}: Too slow ({reading_speed:.1f} chars/sec)")

            # Check duration
            if duration < SubtitleOptimizer.MIN_DISPLAY_DURATION:
                stats["too_short"] += 1
                issues.append(f"Segment {i}: Too short ({duration:.1f}s)")
            elif duration > SubtitleOptimizer.MAX_DISPLAY_DURATION:
                stats["too_long"] += 1
                warnings.append(f"Segment {i}: Too long ({duration:.1f}s)")

            # Check text length
            if chars > SubtitleOptimizer.MAX_CHARS_PER_SUBTITLE:
                issues.append(f"Segment {i}: Text too long ({chars} chars)")

        # Calculate averages
        if stats["total_segments"] > 0:
            stats["avg_reading_speed"] = total_speed / stats["total_segments"]
            stats["avg_duration"] = total_duration / stats["total_segments"]

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "stats": stats
        }


if __name__ == "__main__":
    # Test
    test_timing = [
        {
            "speaker": "A",
            "text": "これは非常に長いテキストの例で、一つの字幕には長すぎるので、複数の字幕に分割されるべきです。さらに続けて、もっと長くします。",
            "start": 0.0,
            "end": 3.0
        },
        {
            "speaker": "B",
            "text": "短い",
            "start": 3.0,
            "end": 3.2
        }
    ]

    optimizer = SubtitleOptimizer()

    print("Original timing:")
    for seg in test_timing:
        print(f"  {seg['start']:.1f}-{seg['end']:.1f}: {seg['text'][:30]}...")

    print("\nOptimized timing:")
    optimized = optimizer.optimize_timing_data(test_timing)
    for seg in optimized:
        print(f"  {seg['start']:.1f}-{seg['end']:.1f}: {seg['text'][:30]}...")

    print("\nValidation:")
    report = optimizer.validate_subtitle_quality(optimized)
    print(f"  Passed: {report['passed']}")
    print(f"  Issues: {len(report['issues'])}")
    print(f"  Warnings: {len(report['warnings'])}")
    print(f"  Avg reading speed: {report['stats']['avg_reading_speed']:.1f} chars/sec")
