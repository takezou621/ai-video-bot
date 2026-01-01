
import os
from pathlib import Path
from video_maker_ffmpeg import make_podcast_video
from PIL import Image

# Setup test paths
TEST_DIR = Path("test_step2_output")
TEST_DIR.mkdir(exist_ok=True)
BG_PATH = TEST_DIR / "bg.png"
AUDIO_PATH = TEST_DIR / "audio.mp3"
VIDEO_PATH = TEST_DIR / "output.mp4"

# Create dummy background
img = Image.new('RGB', (1920, 1080), color = (73, 109, 137))
img.save(BG_PATH)

# Create dummy audio (1 second silence)
os.system(f"ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=stereo -t 5 -q:a 9 -acodec libmp3lame {AUDIO_PATH} > /dev/null 2>&1")

# Dummy timing data
timing_data = [
    {"speaker": "Main", "text": "Step 2 Test: FFmpeg Rendering", "start": 0.5, "end": 2.5},
    {"speaker": "Sub", "text": "Subtitles should appear here.", "start": 3.0, "end": 4.5}
]

print("Starting FFmpeg render test...")
try:
    make_podcast_video(BG_PATH, timing_data, AUDIO_PATH, VIDEO_PATH)
    if VIDEO_PATH.exists() and VIDEO_PATH.stat().st_size > 0:
        print("\n✅ Step 2 Test PASSED: Video created successfully.")
        print(f"Output: {VIDEO_PATH}")
    else:
        print("\n❌ Step 2 Test FAILED: Output file missing or empty.")
except Exception as e:
    print(f"\n❌ Step 2 Test FAILED with error: {e}")
