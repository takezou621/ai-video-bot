"""
VOICEVOX Client - Enhanced for 30-minute podcast production
Supports chunked synthesis, retry logic, caching, and metrics collection.
Optimized for Mac mini M4 16GB stability.
"""
import os
import json
import hashlib
import time
import requests
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

# Configuration
VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://voicevox:50021")

# =============================================================================
# SPEAKER CONFIGURATION - Role-based naming (not gender-based)
# =============================================================================
# Speaker roles are defined by番組の役割, not by perceived voice gender.
# This avoids confusion since some voices (like もち子さん) may not match
# the variable name's implied gender.
#
# Common VOICEVOX speakers:
#   0: 四国めたん（あまあま）    - 落ち着いた女性声
#   2: 四国めたん（ノーマル）    - はっきりした女性声
#   3: ずんだもん（ノーマル）    - 元気な声
#   8: 春日部つむぎ（ノーマル）  - 明るい女性声
#  13: 青山龍星（ノーマル）      - 落ち着いた男性声
#  20: もち子さん（ノーマル）    - 柔らかい声
#  54: 春歌ナナ                  - 明るい女性声
#
# Role definitions:
#   NARRATOR_MAIN: 進行役（落ち着き、メイン解説）
#   NARRATOR_SUB:  補足役（明るめ、相槌・質問）
# =============================================================================
NARRATOR_MAIN = int(os.getenv("VOICEVOX_NARRATOR_MAIN_ID", "20"))  # もち子さん - 落ち着いた進行
NARRATOR_SUB = int(os.getenv("VOICEVOX_NARRATOR_SUB_ID", "2"))     # 四国めたん - 明るい補足

# Narrator name → Speaker ID mapping for specific narrators
# Used when narrator names are detected in podcast scenarios
NARRATOR_SPEAKER_MAP = {
    "森下菜々": 9,   # 波音リツ
    "もりした なな": 9,  # 波音リツ
    "菜々": 9,          # 波音リツ
    "天野結衣": 2,     # 四国めたん
    "あまの ゆい": 2,  # 四国めたん（天野結衣の別名）
    "結衣": 2,         # 四国めたん（天野結衣の略称）
}

# Voice parameters
SPEED_SCALE = float(os.getenv("VOICEVOX_SPEED_SCALE", "1.15"))
PITCH_SCALE = float(os.getenv("VOICEVOX_PITCH_SCALE", "0.0"))
INTONATION_SCALE = float(os.getenv("VOICEVOX_INTONATION_SCALE", "1.0"))
VOLUME_SCALE = float(os.getenv("VOICEVOX_VOLUME_SCALE", "1.0"))

# Cache configuration
CACHE_DIR = Path(os.getenv("VOICEVOX_CACHE_DIR", "/tmp/voicevox_cache"))
CACHE_ENABLED = os.getenv("VOICEVOX_CACHE_ENABLED", "true").lower() == "true"


# Retry configuration
MAX_RETRIES = int(os.getenv("VOICEVOX_MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("VOICEVOX_RETRY_DELAY", "2.0"))

# Request timeout (seconds)
AUDIO_QUERY_TIMEOUT = int(os.getenv("VOICEVOX_QUERY_TIMEOUT", "30"))
SYNTHESIS_TIMEOUT = int(os.getenv("VOICEVOX_SYNTHESIS_TIMEOUT", "120"))


@dataclass
class TTSMetrics:
    """Metrics for TTS generation performance tracking."""
    total_chunks: int = 0
    successful_chunks: int = 0
    failed_chunks: int = 0
    cache_hits: int = 0
    total_generation_time: float = 0.0
    generation_times: List[float] = field(default_factory=list)
    normalized_words: List[str] = field(default_factory=list)

    @property
    def p50(self) -> float:
        if not self.generation_times:
            return 0.0
        sorted_times = sorted(self.generation_times)
        idx = len(sorted_times) // 2
        return sorted_times[idx]

    @property
    def p95(self) -> float:
        if not self.generation_times:
            return 0.0
        sorted_times = sorted(self.generation_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    def to_dict(self) -> Dict:
        return {
            "total_chunks": self.total_chunks,
            "successful_chunks": self.successful_chunks,
            "failed_chunks": self.failed_chunks,
            "cache_hits": self.cache_hits,
            "total_generation_time_sec": round(self.total_generation_time, 2),
            "p50_ms": round(self.p50 * 1000, 1),
            "p95_ms": round(self.p95 * 1000, 1),
            "normalized_words_count": len(self.normalized_words),
        }


# Global metrics instance (reset per episode)
_metrics = TTSMetrics()


def get_metrics() -> TTSMetrics:
    """Get current metrics instance."""
    return _metrics


def reset_metrics() -> None:
    """Reset metrics for a new episode."""
    global _metrics
    _metrics = TTSMetrics()


def is_available() -> bool:
    """Check if VOICEVOX engine is reachable and initialize dictionary."""
    try:
        response = requests.get(f"{VOICEVOX_URL}/speakers", timeout=5)
        if response.status_code == 200:
            # Initialize user dictionary for proper pronunciation
            try:
                from voicevox_dictionary import ensure_dictionary_initialized
                ensure_dictionary_initialized()
            except Exception as e:
                print(f"[VOICEVOX] Dictionary init warning: {e}")
            return True
        return False
    except Exception:
        return False


def get_speakers() -> List[Dict]:
    """Get list of available speakers from VOICEVOX."""
    try:
        response = requests.get(f"{VOICEVOX_URL}/speakers", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"[VOICEVOX] Failed to get speakers: {e}")
    return []


def _get_cache_key(
    text: str,
    speaker_id: int,
    speed: float = SPEED_SCALE,
    pitch: float = PITCH_SCALE,
    intonation: float = INTONATION_SCALE,
) -> str:
    """Generate cache key from synthesis parameters."""
    key_data = f"{text}|{speaker_id}|{speed}|{pitch}|{intonation}"
    return hashlib.sha256(key_data.encode()).hexdigest()[:16]


def _get_cache_path(cache_key: str) -> Path:
    """Get file path for cached audio."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{cache_key}.wav"


def _check_cache(cache_key: str) -> Optional[Path]:
    """Check if cached audio exists and return path if valid."""
    if not CACHE_ENABLED:
        return None
    cache_path = _get_cache_path(cache_key)
    if cache_path.exists() and cache_path.stat().st_size > 0:
        return cache_path
    return None


def generate_voice(
    text: str,
    output_path: Path,
    speaker_role: str = "main",  # Changed from speaker_type="male"
    speed_scale: float = SPEED_SCALE,
    pitch_scale: float = PITCH_SCALE,
    intonation_scale: float = INTONATION_SCALE,
    volume_scale: float = VOLUME_SCALE,
    # Backward compatibility for named arguments
    speaker_type: str = None, 
) -> Optional[Path]:
    """
    Generate speech using VOICEVOX engine with retry and caching.

    Args:
        text: Text to synthesize.
        output_path: Path to save the wav file.
        speaker_role: 'main' (Narrator A) or 'sub' (Narrator B).
                      Also accepts 'male'/'female' for legacy compatibility.
        speed_scale: Speech speed (1.0 = normal).
        pitch_scale: Pitch adjustment.
        intonation_scale: Intonation adjustment.
        volume_scale: Volume adjustment.

    Returns:
        Path to the generated file or None if failed.
    """
    global _metrics
    _metrics.total_chunks += 1

    # Handle legacy argument
    if speaker_type:
        speaker_role = speaker_type

    # Map roles/types to IDs
    # Normalized to lowercase for comparison
    role = str(speaker_role).lower()
    
    if role in ["sub", "b", "female", "woman", "女性", "assistant"]:
        speaker_id = NARRATOR_SUB
    else:
        # Default to MAIN for "main", "a", "male", "man", "男性", or unknown
        speaker_id = NARRATOR_MAIN

    # Check cache first
    cache_key = _get_cache_key(text, speaker_id, speed_scale, pitch_scale, intonation_scale)
    cached_path = _check_cache(cache_key)
    if cached_path:
        # Copy from cache to output path
        import shutil
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(cached_path, output_path)
        _metrics.cache_hits += 1
        _metrics.successful_chunks += 1
        print(f"[VOICEVOX] Cache hit for '{text[:20]}...'")
        return output_path

    # Generate with retry
    start_time = time.time()

    for attempt in range(MAX_RETRIES):
        try:
            result = _synthesize(
                text=text,
                output_path=output_path,
                speaker_id=speaker_id,
                speed_scale=speed_scale,
                pitch_scale=pitch_scale,
                intonation_scale=intonation_scale,
                volume_scale=volume_scale,
            )

            if result:
                gen_time = time.time() - start_time
                _metrics.generation_times.append(gen_time)
                _metrics.total_generation_time += gen_time
                _metrics.successful_chunks += 1

                # Save to cache
                if CACHE_ENABLED:
                    import shutil
                    cache_path = _get_cache_path(cache_key)
                    shutil.copy(output_path, cache_path)

                return result

        except Exception as e:
            print(f"[VOICEVOX] Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))

    _metrics.failed_chunks += 1
    print(f"[VOICEVOX] Failed after {MAX_RETRIES} attempts: '{text[:30]}...'")
    return None


def _synthesize(
    text: str,
    output_path: Path,
    speaker_id: int,
    speed_scale: float,
    pitch_scale: float,
    intonation_scale: float,
    volume_scale: float,
) -> Optional[Path]:
    """Internal synthesis function without retry logic."""
    # Step 1: Create Audio Query
    params = {"text": text, "speaker": speaker_id}
    query_response = requests.post(
        f"{VOICEVOX_URL}/audio_query",
        params=params,
        timeout=AUDIO_QUERY_TIMEOUT,
    )

    if query_response.status_code != 200:
        raise RuntimeError(f"audio_query failed: {query_response.text}")

    query_data = query_response.json()

    # Apply voice parameters
    query_data["speedScale"] = speed_scale
    query_data["pitchScale"] = pitch_scale
    query_data["intonationScale"] = intonation_scale
    query_data["volumeScale"] = volume_scale

    # Step 2: Synthesis
    synthesis_response = requests.post(
        f"{VOICEVOX_URL}/synthesis",
        params={"speaker": speaker_id},
        json=query_data,
        timeout=SYNTHESIS_TIMEOUT,
    )

    if synthesis_response.status_code != 200:
        raise RuntimeError(f"synthesis failed: {synthesis_response.text}")

    # Step 3: Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(synthesis_response.content)

    print(f"[VOICEVOX] Generated: {output_path.name} (speaker={speaker_id})")
    return output_path


def generate_dialogue_chunks(
    dialogues: List[Dict],
    output_dir: Path,
    on_progress: Optional[callable] = None,
) -> Tuple[List[Path], List[Dict]]:
    """
    Generate audio chunks for dialogue segments.

    Args:
        dialogues: List of {"speaker": "男性/女性", "text": "...", "chunk_id": int}
        output_dir: Directory to save chunk files.
        on_progress: Optional callback(chunk_idx, total, status).

    Returns:
        Tuple of (list of chunk paths, list of failed chunk info).
    """
    reset_metrics()
    output_dir.mkdir(parents=True, exist_ok=True)

    chunk_paths = []
    failed_chunks = []

    total = len(dialogues)

    for idx, dialogue in enumerate(dialogues):
        text = dialogue.get("text", "").strip()
        if not text:
            continue

        speaker = dialogue.get("speaker", "男性")
        # Map speaker label to role
        speaker_role = "sub" if speaker in ["女性", "B", "Female", "Sub"] else "main"
        chunk_id = dialogue.get("chunk_id", idx)

        chunk_path = output_dir / f"chunk_{chunk_id:04d}.wav"

        if on_progress:
            on_progress(idx, total, "generating")

        result = generate_voice(text, chunk_path, speaker_role=speaker_role)

        if result:
            chunk_paths.append(result)
        else:
            failed_chunks.append({
                "chunk_id": chunk_id,
                "speaker": speaker,
                "text": text,
                "error": "synthesis_failed",
            })

    if on_progress:
        on_progress(total, total, "complete")

    return chunk_paths, failed_chunks


def get_audio_duration(audio_path: Path) -> float:
    """Get duration of audio file in seconds using ffprobe."""
    import subprocess

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


def clear_cache(max_age_hours: int = 24) -> int:
    """
    Clear old cache files.

    Args:
        max_age_hours: Delete files older than this (default: 24 hours).

    Returns:
        Number of files deleted.
    """
    if not CACHE_DIR.exists():
        return 0

    deleted = 0
    cutoff_time = time.time() - (max_age_hours * 3600)

    for cache_file in CACHE_DIR.glob("*.wav"):
        try:
            if cache_file.stat().st_mtime < cutoff_time:
                cache_file.unlink()
                deleted += 1
        except Exception:
            pass

    print(f"[VOICEVOX] Cleared {deleted} cache files older than {max_age_hours}h")
    return deleted


# ============================================
# Pre-generated common phrases (jingles, intros)
# ============================================

COMMON_PHRASES = {
    "intro_male": "お聴きいただきありがとうございます。",
    "intro_female": "本日もよろしくお願いします。",
    "outro_male": "ご視聴ありがとうございました。",
    "outro_female": "また次回お会いしましょう。",
    "transition": "続いてのトピックです。",
}


def pregenerate_common_phrases(output_dir: Path) -> Dict[str, Path]:
    """
    Pre-generate common phrases used in every episode.
    These can be reused without regeneration.

    Args:
        output_dir: Directory to save pre-generated files.

    Returns:
        Dict mapping phrase key to file path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    for key, text in COMMON_PHRASES.items():
        speaker_role = "main" if "male" in key else "sub"
        output_path = output_dir / f"common_{key}.wav"

        if not output_path.exists():
            result = generate_voice(text, output_path, speaker_role=speaker_role)
            if result:
                paths[key] = result
        else:
            paths[key] = output_path

    return paths


if __name__ == "__main__":
    print("=== VOICEVOX Client Test ===\n")

    if is_available():
        print(f"VOICEVOX engine available at {VOICEVOX_URL}")

        # Show available speakers
        speakers = get_speakers()
        print(f"\nAvailable speakers ({len(speakers)} total):")
        for speaker in speakers[:5]:
            print(f"  - {speaker.get('name')}: {[s.get('id') for s in speaker.get('styles', [])]}")

        # Test generation
        test_dir = Path("/tmp/voicevox_test")
        test_dir.mkdir(exist_ok=True)

        print("\nTesting voice generation...")

        # Main voice (formerly male/Mochiko)
        male_result = generate_voice(
            "こんにちは、テストです。本日は晴れですね。",
            test_dir / "test_main.wav",
            speaker_role="main",
        )
        print(f"Main voice: {male_result}")

        # Sub voice (formerly female/Metan)
        female_result = generate_voice(
            "はい、素晴らしい天気ですね。",
            test_dir / "test_sub.wav",
            speaker_role="sub",
        )
        print(f"Sub voice: {female_result}")

        # Show metrics
        metrics = get_metrics()
        print(f"\nMetrics: {json.dumps(metrics.to_dict(), indent=2)}")

    else:
        print(f"VOICEVOX engine not available at {VOICEVOX_URL}")
        print("Start VOICEVOX with: docker compose up voicevox")


def get_speaker_id_for_narrator(narrator: Optional[str], speaker_role: str = "main") -> int:
    """
    ナレーター名に応じたVOICEVOXスピーカーIDを返す

    Args:
        narrator: ナレーター名（例: "森下菜々", "天野結衣"）
        speaker_role: 役割（main/sub）

    Returns:
        スピーカーID
    """
    # 優先順: ナレーター名マッチ → 役割ベース → デフォルト
    if narrator and narrator.strip():
        narrator = narrator.strip()
        if narrator in NARRATOR_SPEAKER_MAP:
            speaker_id = NARRATOR_SPEAKER_MAP[narrator]
            print(f"[VOICEVOX] Narrator '{narrator}' -> speaker ID {speaker_id}")
            return speaker_id

    # 役割ベースの選択
    role = str(speaker_role).lower()
    if role in ["sub", "b", "female", "woman", "女性", "assistant"]:
        print(f"[VOICEVOX] Role '{speaker_role}' -> NARRATOR_SUB (ID={NARRATOR_SUB})")
        return NARRATOR_SUB
    else:
        # Default to MAIN for "main", "a", "male", "man", "男性", or unknown
        print(f"[VOICEVOX] Role '{speaker_role}' -> NARRATOR_MAIN (ID={NARRATOR_MAIN})")
        return NARRATOR_MAIN

