
import os
import json
from pathlib import Path

# Set environment variables BEFORE importing our modules
os.environ["VOICEVOX_URL"] = "http://localhost:50021"
os.environ["USE_VOICEVOX"] = "true"

from tts_generator import generate_dialogue_audio
from video_maker_ffmpeg import make_podcast_video
from PIL import Image
import text_normalizer

# Setup test directory
TEST_DIR = Path("outputs/test_run_full")
TEST_DIR.mkdir(parents=True, exist_ok=True)

# 1. Test Text Normalization (P0 check)
test_text = "This is a very long English sentence that should not be deleted by the new rules. OpenAI and Google are leading."
norm_text = text_normalizer.normalize_for_tts_advanced(test_text)
print(f"--- Normalization Test ---")
print(f"Original: {test_text}")
print(f"Normalized: {norm_text}")
if "sentence" in norm_text or "センチネル" in norm_text or "sentence" in norm_text.lower():
    print("✅ English preservation: PASSED")
else:
    print("❌ English preservation: FAILED (Text might have been deleted)")

# 2. Test TTS & Video Pipeline
script_dialogues = [
    {"speaker": "男性", "text": "こんにちは、本日はテックニュースをお届けします。"},
    {"speaker": "女性", "text": "AIの世界では、Large Language Modelsの進化が止まりませんね。"},
    {"speaker": "男性", "text": "はい。特にOpenAIの新しいモデルは驚異的です。"},
]

print(f"\n--- Pipeline Test ---")
audio_path = TEST_DIR / "dialogue"
bg_path = TEST_DIR / "background.png"

# Create dummy background
if not bg_path.exists():
    img = Image.new('RGB', (1920, 1080), color = (40, 44, 52))
    img.save(bg_path)

try:
    # Generate Audio
    print("Generating audio (VOICEVOX)...")
    audio_file, timing_data = generate_dialogue_audio(script_dialogues, audio_path)
    print(f"✅ Audio generated: {audio_file}")
    
    # Save timing for inspection
    with open(TEST_DIR / "timing.json", "w") as f:
        json.dump(timing_data, f, indent=2, ensure_ascii=False)
    
    # Generate Video
    print("Generating video (FFmpeg)...")
    video_path = TEST_DIR / "video.mp4"
    make_podcast_video(bg_path, timing_data, audio_file, video_path)
    
    if video_path.exists() and video_path.stat().st_size > 0:
        print(f"✅ Video generated: {video_path}")
        print(f"\n🚀 ALL TESTS PASSED!")
    else:
        print(f"❌ Video generation FAILED.")

except Exception as e:
    print(f"❌ Test FAILED with error: {e}")
    import traceback
    traceback.print_exc()
