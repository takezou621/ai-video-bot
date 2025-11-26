"""
ElevenLabs Speech-to-Text Integration
Provides accurate subtitle timing by analyzing actual audio
"""
import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Tuple
from difflib import SequenceMatcher

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")


def transcribe_audio_with_elevenlabs(audio_path: Path) -> List[Dict]:
    """
    Transcribe audio using ElevenLabs STT API.

    Args:
        audio_path: Path to audio file

    Returns:
        List of transcription segments with accurate timing
    """
    if not ELEVENLABS_API_KEY:
        print("ElevenLabs API key not found, using fallback timing")
        return None

    try:
        url = "https://api.elevenlabs.io/v1/speech-to-text"

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY
        }

        with open(audio_path, "rb") as audio_file:
            files = {
                "audio": audio_file,
                "model_id": (None, "eleven_multilingual_v2")  # Supports Japanese
            }

            print(f"Transcribing audio with ElevenLabs STT...")
            response = requests.post(url, headers=headers, files=files, timeout=300)
            response.raise_for_status()

        data = response.json()

        # Extract segments with timing
        segments = []
        if "words" in data:
            for word in data["words"]:
                segments.append({
                    "text": word.get("text", ""),
                    "start": word.get("start", 0),
                    "end": word.get("end", 0)
                })

        print(f"  Transcribed {len(segments)} word segments")
        return segments

    except Exception as e:
        print(f"ElevenLabs STT failed: {e}")
        return None


def align_script_with_transcription(
    script_dialogues: List[Dict],
    transcription_segments: List[Dict]
) -> List[Dict]:
    """
    Match script text with transcribed audio to get accurate timing.
    This implements the article's approach: "台本テキストとSTT結果をマッチングさせて、
    完全に正確な字幕データを取得"

    Args:
        script_dialogues: Original dialogue script [{"speaker": "A/B", "text": "..."}]
        transcription_segments: STT results with timing

    Returns:
        Aligned timing data for each dialogue
    """
    if not transcription_segments:
        return None

    # Combine all transcribed text
    full_transcription = " ".join([s["text"] for s in transcription_segments])

    aligned_data = []
    current_segment_idx = 0

    for dialogue in script_dialogues:
        dialogue_text = dialogue["text"]

        # Find best match in transcription
        best_match_start = None
        best_match_end = None
        best_similarity = 0

        # Try to find this dialogue text in the transcription
        for i in range(current_segment_idx, len(transcription_segments)):
            # Build a window of text from segments
            window_text = ""
            window_start = transcription_segments[i]["start"]
            window_end = transcription_segments[i]["end"]

            for j in range(i, min(i + 100, len(transcription_segments))):
                window_text += transcription_segments[j]["text"]
                window_end = transcription_segments[j]["end"]

                # Calculate similarity
                similarity = SequenceMatcher(None, dialogue_text, window_text).ratio()

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_start = window_start
                    best_match_end = window_end

                    # If we found a good match, use it
                    if similarity > 0.7:
                        current_segment_idx = j + 1
                        break

            if best_similarity > 0.7:
                break

        if best_match_start is not None:
            aligned_data.append({
                "speaker": dialogue["speaker"],
                "text": dialogue["text"],
                "start": best_match_start,
                "end": best_match_end,
                "confidence": best_similarity
            })
        else:
            # Fallback: estimate based on previous timing
            if aligned_data:
                last_end = aligned_data[-1]["end"]
                duration = len(dialogue_text) / 7.0  # Rough estimate
                aligned_data.append({
                    "speaker": dialogue["speaker"],
                    "text": dialogue["text"],
                    "start": last_end + 0.3,
                    "end": last_end + 0.3 + duration,
                    "confidence": 0.0
                })
            else:
                # First dialogue, start from 0
                duration = len(dialogue_text) / 7.0
                aligned_data.append({
                    "speaker": dialogue["speaker"],
                    "text": dialogue["text"],
                    "start": 0,
                    "end": duration,
                    "confidence": 0.0
                })

    print(f"  Aligned {len(aligned_data)} dialogues")
    avg_confidence = sum(d["confidence"] for d in aligned_data) / len(aligned_data)
    print(f"  Average alignment confidence: {avg_confidence:.2%}")

    return aligned_data


def generate_accurate_subtitles(
    script_dialogues: List[Dict],
    audio_path: Path
) -> List[Dict]:
    """
    Generate highly accurate subtitles using ElevenLabs STT + script alignment.

    Args:
        script_dialogues: Original script
        audio_path: Path to generated audio

    Returns:
        Accurate timing data for subtitles
    """
    # Step 1: Transcribe audio with ElevenLabs
    transcription = transcribe_audio_with_elevenlabs(audio_path)

    if not transcription:
        print("Falling back to estimated timing")
        return None

    # Step 2: Align script with transcription
    aligned_timing = align_script_with_transcription(script_dialogues, transcription)

    return aligned_timing


if __name__ == "__main__":
    # Test with sample data
    test_dialogues = [
        {"speaker": "A", "text": "こんにちは、今日は経済について話しましょう。"},
        {"speaker": "B", "text": "はい、最近の円安について教えてください。"},
        {"speaker": "A", "text": "円安は輸出企業には有利ですが、輸入物価が上がります。"}
    ]

    print("ElevenLabs STT module loaded")
    print("To test: provide audio_path and run generate_accurate_subtitles()")
