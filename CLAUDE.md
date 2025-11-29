# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Video Bot is an automated YouTube video generation system that creates podcast-style dialogue videos using multiple AI services. The project is based on a successful YouTube monetization case study documented in a [Zenn article](https://zenn.dev/xtm_blog/articles/da1eba90525f91).

**Core Value Proposition**: Generates complete, publish-ready videos with minimal human intervention - from topic discovery through final video with thumbnails, metadata, and engagement comments.

## Recent Quality Improvements

The system has been enhanced with high-quality features based on the Zenn article's successful approach:

1. **Whisper STT Integration** (`whisper_stt.py`): **100% FREE** accurate subtitle synchronization using OpenAI Whisper (local execution, no API costs)
2. **ElevenLabs STT Integration** (`elevenlabs_stt.py`): Optional paid alternative for subtitle synchronization (99%+ accuracy)
3. **Enhanced Claude Prompts** (`claude_generator.py`): Optimized for engagement, storytelling, and SEO
4. **MoviePy Rendering** (`video_maker_moviepy.py`): Higher quality subtitle rendering with fade effects
5. **Character-based Comments**: 5 distinct personas for authentic engagement
6. **YouTube SEO Optimization**: CTR-focused titles and search-optimized metadata

See `QUALITY_IMPROVEMENTS.md` for detailed information about these enhancements.

## Development Commands

### Running Video Generation

```bash
# Simple generation (legacy, fixed nostalgic topics)
docker compose run --rm ai-video-bot python daily_video_job.py

# Advanced generation (recommended, with all features)
docker compose run --rm ai-video-bot python advanced_video_pipeline.py

# Test individual modules
docker compose run --rm ai-video-bot python web_search.py
docker compose run --rm ai-video-bot python claude_generator.py
docker compose run --rm ai-video-bot python thumbnail_generator.py
```

### Environment Setup

```bash
# Copy and configure environment variables
cp .env.sample .env
# Edit .env with API keys

# Build Docker image
docker compose build
```

### Configuration via .env

**Basic Settings:**
- `VIDEOS_PER_DAY`: Number of videos to generate (1-4 recommended)
- `DURATION_MINUTES`: Target video length (5-30 minutes)
- `TOPIC_CATEGORY`: Topic category (economics, technology, culture, lifestyle)
- `USE_WEB_SEARCH`: Enable/disable web search for trending topics (true/false)

**Quality Settings:**
- `USE_WHISPER_STT`: Enable Whisper STT for accurate subtitle timing (true/false, **100% FREE**, default: true, recommended)
- `WHISPER_MODEL_SIZE`: Whisper model size (tiny/base/small/medium/large, default: base)
- `USE_ELEVENLABS_STT`: Enable ElevenLabs STT for subtitle timing (true/false, paid API, requires API key)
- `ELEVENLABS_API_KEY`: API key for ElevenLabs STT (optional, only if USE_ELEVENLABS_STT=true)
- `USE_MOVIEPY`: Enable MoviePy for higher quality rendering (true/false, slower but better quality)

**YouTube Upload Settings (New):**
- `YOUTUBE_UPLOAD_ENABLED`: Enable automatic YouTube upload (true/false, requires OAuth setup)
- `YOUTUBE_PRIVACY_STATUS`: Privacy setting for uploads (private/unlisted/public)
- `YOUTUBE_PLAYLIST_ID`: Optional playlist ID to add videos to

## Architecture

### Two Generation Modes

1. **Simple Mode** (`daily_video_job.py`): Legacy 4-step pipeline with fixed topics
   - Gemini-based script generation → Image → Audio → Video

2. **Advanced Mode** (`advanced_video_pipeline.py`): Full 10-step production pipeline
   - Web search → Claude script → Image → Audio → Video → Metadata → Comments → Thumbnail → Tracking → YouTube Upload

### 10-Step Advanced Pipeline

The advanced pipeline provides complete automation from topic discovery to YouTube publishing:

1. **Web Search** (`web_search.py`): Discovers trending topics via Serper API
2. **Topic Selection** (`web_search.py`): Claude analyzes and selects optimal topic
3. **Script Generation** (`claude_generator.py`): Claude Opus/Sonnet creates dialogue
4. **Image Generation** (`nano_banana_client.py`): DALL-E 3 creates Lo-fi anime backgrounds
5. **Audio Generation** (`tts_generator.py`): Gemini TTS produces podcast-style audio
6. **Video Assembly** (`video_maker.py` / `video_maker_moviepy.py`): FFmpeg/MoviePy combines audio + background + subtitles
7. **Metadata Generation** (`claude_generator.py`): Claude creates SEO-optimized titles/descriptions
8. **Comment Generation** (`claude_generator.py`): Claude creates engagement comments
9. **Thumbnail Creation** (`thumbnail_generator.py`): Creates custom YouTube thumbnail
10. **Tracking & Upload** (`tracking.py`, `notifications.py`, `youtube_uploader.py`): Logs to Sheets/JSON, sends Slack notifications, uploads to YouTube (optional)

### Key Module Responsibilities

**Content Generation:**
- `claude_generator.py`: Three Claude API prompt stages with enhanced prompts (dialogue script, SEO metadata, character-based comments)
- `llm_story.py`: Gemini fallback for script generation
- `web_search.py`: Serper API integration + Claude-based topic curation
- `tts_generator.py`: Gemini TTS with ElevenLabs STT integration for accurate timing, gTTS fallback
- `nano_banana_client.py`: DALL-E 3 image generation wrapper

**Video Processing:**
- `video_maker.py`: FFmpeg orchestration, subtitle rendering with PIL, frame generation (fast)
- `video_maker_moviepy.py`: **NEW** MoviePy-based rendering with fade effects (high quality)
- `elevenlabs_stt.py`: **NEW** ElevenLabs Speech-to-Text for accurate subtitle synchronization
- `subtitle_generator.py`: Legacy subtitle system (not used in new pipeline)
- `thumbnail_generator.py`: PIL-based thumbnail creation with text overlays

**Operations:**
- `notifications.py`: Slack webhook notifications (start, complete, error, daily summary)
- `tracking.py`: Logs to Google Sheets or local JSON/CSV
- `youtube_uploader.py`: **NEW** YouTube Data API v3 integration for automatic uploads, thumbnail setting, and comment posting
- `advanced_video_pipeline.py`: Main orchestrator with error handling and batch processing
- `daily_video_job.py`: Simple orchestrator (legacy)

### Output Structure

All generated content is organized by date:

```
outputs/YYYY-MM-DD/video_NNN/
├── video.mp4           # Final video with subtitles
├── thumbnail.jpg       # YouTube thumbnail
├── background.png      # Generated background image
├── dialogue.mp3        # Audio track
├── script.json         # Dialogue script
├── metadata.json       # YouTube metadata (title, description, tags)
├── comments.json       # Engagement comments
├── topic.json          # Topic analysis from web search
├── timing.json         # Subtitle timing data
└── manifest.json       # Complete video metadata
```

## API Service Integration

### Primary Services
- **Claude API** (Anthropic): Script generation, topic selection, metadata creation
- **Gemini API** (Google): TTS audio generation, fallback script generation
- **DALL-E 3** (OpenAI): Background image generation

### Optional Services
- **Serper API**: Web search for trending topics (fallback topics available)
- **Slack**: Webhook notifications
- **Google Sheets**: Production logging (fallback to local JSON)
- **YouTube Data API v3**: **NEW** Automatic video upload, thumbnail setting, comment posting (requires OAuth 2.0 authentication)

### Fallback Strategy

The system gracefully degrades when APIs are unavailable:
- Claude unavailable → Falls back to Gemini for script generation
- Gemini TTS unavailable → Falls back to gTTS (Google Text-to-Speech)
- Web search unavailable → Uses predefined fallback topics
- YouTube upload unavailable → Continues without upload (video saved locally)
- All services have hardcoded fallbacks to ensure generation never fails completely

## Audio Timing System

The TTS system (`tts_generator.py`) implements a multi-tier timing strategy:

### Tier 1: Whisper STT (Default, 100% FREE)
1. Gemini TTS generates audio
2. Whisper transcribes audio locally with word-level timestamps
3. Script text is aligned with transcription using fuzzy matching
4. Produces 95%+ accurate subtitle timing with zero API costs
5. Model size configurable: tiny (fastest) to large (most accurate)

### Tier 2: ElevenLabs STT (Optional, Paid)
1. Gemini TTS generates audio
2. ElevenLabs API transcribes audio with word-level timestamps
3. Script text is aligned with transcription
4. Produces 99%+ accurate subtitle timing (requires API key)

### Tier 3: Estimation (Fallback)
1. System uses `ffprobe` to determine actual audio length
2. `_estimate_timing_scaled()` proportionally distributes subtitle timing across actual duration
3. Timing is weighted by text length (longer text = longer display time)
4. Small pauses (0.1s) inserted between speaker changes
5. Produces 80-90% accurate timing

The system automatically falls back through tiers if earlier options are unavailable.

## Video Rendering Details

`video_maker.py` creates podcast-style videos:

- **Resolution**: 1920x1080 @ 30fps
- **Subtitle Style**: Semi-transparent boxes with speaker color indicators
  - Speaker A: Blue accent (120, 200, 255)
  - Speaker B: Orange accent (255, 200, 120)
- **Font Handling**: Searches for Japanese fonts across platforms (Noto CJK, Hiragino, MS Gothic)
- **Text Wrapping**: Dynamically wraps Japanese text to fit width
- **Process**: Generate all frames → Encode with libx264 → Merge audio with AAC

## Batch Processing

`generate_multiple_videos()` in `advanced_video_pipeline.py`:
- Generates multiple videos in sequence (configured via `VIDEOS_PER_DAY`)
- 10-second delay between videos to avoid API rate limits
- Tracks success/failure counts
- Sends daily summary notification with all topics and total duration
- Each video is independent - failures don't stop the batch

## Error Handling Pattern

All major operations follow this pattern:
1. Try primary API service
2. Log specific error
3. Notify via Slack if configured
4. Attempt fallback service
5. Track failure in logging system
6. Return degraded result rather than crashing

Example: If Claude API fails during script generation, the system automatically uses Gemini with the same topic, logs the fallback, and continues.

## Japanese Language Considerations

- All prompts to Claude are in Japanese for optimal results
- Character count estimates: ~300 chars/minute for natural Japanese speech
- TTS timing: ~7 chars/second for Gemini TTS output
- Font support required: Noto Sans CJK or equivalent for subtitle rendering

## Testing Individual Components

Each major module is runnable standalone:

```bash
# Test web search and topic selection
docker compose run --rm ai-video-bot python web_search.py

# Test Claude script generation
docker compose run --rm ai-video-bot python claude_generator.py

# Test thumbnail generation
docker compose run --rm ai-video-bot python thumbnail_generator.py

# Test YouTube authentication
docker compose run --rm ai-video-bot python youtube_uploader.py
```

These execute the `if __name__ == "__main__"` blocks with test data.

## Dependencies

Core Python packages:
- `anthropic`: Claude API client
- `requests`: HTTP client for Gemini, Serper, Slack webhooks
- `gTTS`: Fallback TTS
- `Pillow`: Image manipulation and subtitle rendering
- `python-dotenv`: Environment variable management
- `google-auth-oauthlib`: **NEW** OAuth 2.0 authentication for YouTube API
- `google-api-python-client`: **NEW** YouTube Data API v3 client

System dependencies:
- `ffmpeg`: Audio/video processing
- `ffprobe`: Duration detection
- Japanese fonts: Noto Sans CJK or equivalent

## Model Selection

Claude models are configured in `claude_generator.py`:
- Current: `claude-3-5-sonnet-20241022` for all operations
- Can be upgraded to `claude-3-opus` for higher quality at increased cost
- Temperature: 0.9 for creative dialogue, default for analytical tasks

Gemini TTS configuration in `tts_generator.py`:
- Model: `gemini-2.5-flash-preview-tts`
- Voice: `Zephyr` (podcast-style)
- Format: PCM L16 24kHz mono, converted to MP3

## Cost Considerations

Per the Zenn article, approximate costs for 4 videos/day:
- Claude API: ~¥2,000/month
- Gemini TTS: ~¥1,500/month
- DALL-E 3: ~¥3,600/month
- Serper API: ~¥500/month
- **Total**: ~¥7,600/month (~$50-60 USD)

The article reports advertising revenue exceeded API costs.

## Recent Implementations

The following features have been recently implemented:
- ✅ **YouTube Data API v3 integration** (`youtube_uploader.py`): Automatic video uploads, thumbnail setting, and comment posting with OAuth 2.0 authentication
- ✅ **ElevenLabs STT integration** (`elevenlabs_stt.py`): Accurate subtitle synchronization
- ✅ **MoviePy rendering** (`video_maker_moviepy.py`): High-quality video rendering with fade effects
- ✅ **Template system** (`content_templates.py`): Script structures, title patterns, and persona-based comments

## Future Extension Points

The README mentions these planned features:
- BGM generation/addition (Suno AI / MusicGen)
- Whisper API for improved subtitle synchronization (alternative to ElevenLabs)
- A/B testing for thumbnails
- Cloud deployment (Render, AWS, GCP)
- GitHub Actions CI/CD
- Analytics dashboard

When implementing these, follow the existing fallback pattern and ensure the core pipeline remains functional even if extensions fail.
