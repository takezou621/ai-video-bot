"""
Audio Quality Validator - Automated audio quality checks
Ensures high-quality audio output before video generation
"""
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class AudioQualityValidator:
    """
    Validates audio quality using ffprobe and other analysis tools.

    Checks:
    - Audio duration
    - Volume levels (peak, RMS)
    - Silence detection
    - Audio format compliance
    """

    # Quality thresholds
    MIN_PEAK_LEVEL_DB = -6.0  # Minimum peak level (dB)
    MAX_PEAK_LEVEL_DB = -1.0  # Maximum peak level (to avoid clipping)
    MIN_RMS_LEVEL_DB = -30.0  # Minimum RMS level
    MAX_SILENCE_DURATION = 3.0  # Maximum allowed silence (seconds)
    MIN_DURATION = 10.0  # Minimum audio duration (seconds)

    @staticmethod
    def validate_audio_file(audio_path: Path) -> Dict:
        """
        Comprehensive audio quality validation.

        Args:
            audio_path: Path to audio file

        Returns:
            Validation report
        """
        if not audio_path.exists():
            return {
                "passed": False,
                "errors": [f"Audio file not found: {audio_path}"],
                "warnings": [],
                "stats": {}
            }

        errors = []
        warnings = []
        stats = {}

        # Check 1: Audio duration
        duration = AudioQualityValidator._get_audio_duration(audio_path)
        stats["duration"] = duration

        if duration < AudioQualityValidator.MIN_DURATION:
            errors.append(f"Audio too short: {duration:.1f}s (minimum: {AudioQualityValidator.MIN_DURATION}s)")

        # Check 2: Audio format
        format_info = AudioQualityValidator._get_audio_format(audio_path)
        stats["format"] = format_info

        # Check 3: Volume levels
        volume_stats = AudioQualityValidator._analyze_volume(audio_path)
        stats["volume"] = volume_stats

        if volume_stats.get("peak_level"):
            peak = volume_stats["peak_level"]
            if peak < AudioQualityValidator.MIN_PEAK_LEVEL_DB:
                warnings.append(f"Audio level low: peak {peak:.1f}dB (recommended: > {AudioQualityValidator.MIN_PEAK_LEVEL_DB}dB)")
            elif peak > AudioQualityValidator.MAX_PEAK_LEVEL_DB:
                warnings.append(f"Audio level high: peak {peak:.1f}dB (may clip, recommended: < {AudioQualityValidator.MAX_PEAK_LEVEL_DB}dB)")

        if volume_stats.get("mean_level"):
            mean = volume_stats["mean_level"]
            if mean < AudioQualityValidator.MIN_RMS_LEVEL_DB:
                warnings.append(f"Audio RMS low: {mean:.1f}dB (recommended: > {AudioQualityValidator.MIN_RMS_LEVEL_DB}dB)")

        # Check 4: Silence detection
        silence_periods = AudioQualityValidator._detect_silence(audio_path)
        stats["silence_periods"] = len(silence_periods)

        long_silences = [s for s in silence_periods if s["duration"] > AudioQualityValidator.MAX_SILENCE_DURATION]
        if long_silences:
            warnings.append(f"Long silence detected: {len(long_silences)} period(s) > {AudioQualityValidator.MAX_SILENCE_DURATION}s")
            stats["long_silences"] = long_silences

        # Generate report
        report = {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "stats": stats
        }

        return report

    @staticmethod
    def validate_audio_subtitle_sync(
        audio_path: Path,
        timing_data: List[Dict],
        tolerance: float = 0.5
    ) -> Dict:
        """
        Validate that subtitles are properly synced with audio.

        Args:
            audio_path: Path to audio file
            timing_data: Subtitle timing data
            tolerance: Acceptable timing difference (seconds)

        Returns:
            Validation report
        """
        audio_duration = AudioQualityValidator._get_audio_duration(audio_path)

        errors = []
        warnings = []

        if not timing_data:
            errors.append("No subtitle timing data")
            return {
                "passed": False,
                "errors": errors,
                "warnings": warnings
            }

        # Check subtitle coverage
        last_subtitle_end = max(seg["end"] for seg in timing_data)

        if abs(last_subtitle_end - audio_duration) > tolerance:
            diff = abs(last_subtitle_end - audio_duration)
            warnings.append(
                f"Subtitle duration mismatch: subtitles end at {last_subtitle_end:.1f}s, "
                f"audio ends at {audio_duration:.1f}s (diff: {diff:.1f}s)"
            )

        # Check for subtitle gaps
        gaps = []
        for i in range(len(timing_data) - 1):
            current_end = timing_data[i]["end"]
            next_start = timing_data[i + 1]["start"]
            gap = next_start - current_end

            if gap > 2.0:  # Gap > 2 seconds
                gaps.append({
                    "index": i,
                    "gap_duration": gap,
                    "time": current_end
                })

        if gaps:
            warnings.append(f"Large gaps between subtitles: {len(gaps)} gap(s) > 2s")

        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "subtitle_coverage": (last_subtitle_end / audio_duration) * 100 if audio_duration > 0 else 0,
            "gaps": gaps
        }

    @staticmethod
    def _get_audio_duration(audio_path: Path) -> float:
        """Get audio duration using ffprobe."""
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(audio_path)
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except Exception as e:
            print(f"Failed to get audio duration: {e}")

        return 0.0

    @staticmethod
    def _get_audio_format(audio_path: Path) -> Dict:
        """Get audio format information."""
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error",
                "-show_format", "-show_streams",
                "-of", "json",
                str(audio_path)
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                data = json.loads(result.stdout)
                format_info = data.get("format", {})
                stream_info = data.get("streams", [{}])[0]

                return {
                    "format_name": format_info.get("format_name", "unknown"),
                    "codec": stream_info.get("codec_name", "unknown"),
                    "sample_rate": stream_info.get("sample_rate", "unknown"),
                    "channels": stream_info.get("channels", "unknown"),
                    "bit_rate": format_info.get("bit_rate", "unknown")
                }
        except Exception as e:
            print(f"Failed to get audio format: {e}")

        return {}

    @staticmethod
    def _analyze_volume(audio_path: Path) -> Dict:
        """Analyze audio volume levels."""
        try:
            result = subprocess.run([
                "ffmpeg", "-i", str(audio_path),
                "-af", "volumedetect",
                "-f", "null", "-"
            ], capture_output=True, text=True, timeout=60)

            # Parse volumedetect output
            output = result.stderr

            stats = {}

            # Extract peak level
            if "max_volume:" in output:
                for line in output.split("\n"):
                    if "max_volume:" in line:
                        parts = line.split("max_volume:")
                        if len(parts) > 1:
                            stats["peak_level"] = float(parts[1].strip().split()[0])

            # Extract mean level
            if "mean_volume:" in output:
                for line in output.split("\n"):
                    if "mean_volume:" in line:
                        parts = line.split("mean_volume:")
                        if len(parts) > 1:
                            stats["mean_level"] = float(parts[1].strip().split()[0])

            return stats

        except Exception as e:
            print(f"Failed to analyze volume: {e}")
            return {}

    @staticmethod
    def _detect_silence(audio_path: Path, noise_threshold: float = -50.0, duration: float = 1.0) -> List[Dict]:
        """
        Detect silence periods in audio.

        Args:
            audio_path: Path to audio
            noise_threshold: Silence threshold in dB
            duration: Minimum silence duration (seconds)

        Returns:
            List of silence periods
        """
        try:
            result = subprocess.run([
                "ffmpeg", "-i", str(audio_path),
                "-af", f"silencedetect=n={noise_threshold}dB:d={duration}",
                "-f", "null", "-"
            ], capture_output=True, text=True, timeout=60)

            output = result.stderr
            silences = []

            # Parse silence detect output
            silence_start = None
            for line in output.split("\n"):
                if "silence_start:" in line:
                    parts = line.split("silence_start:")
                    if len(parts) > 1:
                        silence_start = float(parts[1].strip().split()[0])

                elif "silence_end:" in line and silence_start is not None:
                    parts = line.split("silence_end:")
                    if len(parts) > 1:
                        silence_end = float(parts[1].strip().split()[0])
                        silences.append({
                            "start": silence_start,
                            "end": silence_end,
                            "duration": silence_end - silence_start
                        })
                        silence_start = None

            return silences

        except Exception as e:
            print(f"Failed to detect silence: {e}")
            return []


if __name__ == "__main__":
    # Test
    import tempfile
    import shutil

    # Create a test audio file (1 second of silence)
    test_dir = Path(tempfile.mkdtemp())
    test_audio = test_dir / "test.mp3"

    try:
        # Generate test audio using ffmpeg
        subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", "5", "-q:a", "9", "-acodec", "libmp3lame",
            str(test_audio)
        ], check=True, capture_output=True)

        print("Testing audio quality validation...\n")

        validator = AudioQualityValidator()

        # Test 1: Audio file validation
        print("1. Audio file validation:")
        report = validator.validate_audio_file(test_audio)
        print(f"   Passed: {report['passed']}")
        print(f"   Errors: {len(report['errors'])}")
        print(f"   Warnings: {len(report['warnings'])}")
        print(f"   Duration: {report['stats'].get('duration', 0):.1f}s")

        # Test 2: Audio-subtitle sync validation
        print("\n2. Audio-subtitle sync validation:")
        test_timing = [
            {"speaker": "A", "text": "Test", "start": 0.0, "end": 2.0},
            {"speaker": "B", "text": "Test", "start": 2.0, "end": 4.0}
        ]
        sync_report = validator.validate_audio_subtitle_sync(test_audio, test_timing)
        print(f"   Passed: {sync_report['passed']}")
        print(f"   Subtitle coverage: {sync_report.get('subtitle_coverage', 0):.1f}%")

        print("\n✓ Test complete")

    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)
