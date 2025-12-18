"""
Test script for Whisper STT integration
Generates a short audio and tests Whisper transcription
"""
import os
from pathlib import Path
from tts_generator import generate_dialogue_audio

# Test dialogue (short for quick testing)
test_dialogues = [
    {"speaker": "男性", "text": "こんにちは、今日は経済について話しましょう。"},
    {"speaker": "女性", "text": "はい、最近の円安について教えてください。"},
    {"speaker": "男性", "text": "円安は輸出企業には有利ですが、輸入物価が上がります。"}
]

# Create test output directory
test_dir = Path("test_output")
test_dir.mkdir(exist_ok=True)

print("=" * 60)
print("Whisper STT Integration Test")
print("=" * 60)
print()

print("Test dialogues:")
for i, d in enumerate(test_dialogues, 1):
    print(f"{i}. [{d['speaker']}] {d['text']}")
print()

print("Generating audio with Gemini TTS...")
print()

try:
    audio_path, timing_data = generate_dialogue_audio(
        dialogues=test_dialogues,
        output_path=test_dir / "test_audio.mp3"
    )

    print()
    print("=" * 60)
    print("✅ Audio generation successful!")
    print("=" * 60)
    print()
    print(f"Audio file: {audio_path}")
    print(f"File size: {audio_path.stat().st_size / 1024:.1f} KB")
    print()

    print("Subtitle timing data:")
    print("-" * 60)
    for i, timing in enumerate(timing_data, 1):
        print(f"{i}. [{timing['speaker']}] {timing['start']:.2f}s - {timing['end']:.2f}s")
        print(f"   {timing['text']}")
        if 'confidence' in timing:
            print(f"   Confidence: {timing['confidence']:.1%}")
        print()

    # Calculate total duration
    total_duration = max(t['end'] for t in timing_data)
    print(f"Total duration: {total_duration:.2f} seconds")
    print()

    # Check if Whisper was used
    has_confidence = any('confidence' in t for t in timing_data)
    if has_confidence:
        avg_confidence = sum(t.get('confidence', 0) for t in timing_data) / len(timing_data)
        print(f"✅ Whisper STT was used!")
        print(f"   Average confidence: {avg_confidence:.1%}")
    else:
        print("⚠️  Timing estimation was used (Whisper may have failed)")

    print()
    print("=" * 60)
    print("Test completed successfully!")
    print("=" * 60)

except Exception as e:
    print()
    print("=" * 60)
    print("❌ Test failed!")
    print("=" * 60)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
