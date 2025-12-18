# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Video Bot is an automated YouTube video generation system that creates podcast-style dialogue videos using multiple AI services. The project is based on a successful YouTube monetization case study documented in a [Zenn article](https://zenn.dev/xtm_blog/articles/da1eba90525f91).

**Core Value Proposition**: Generates complete, publish-ready videos with minimal human intervention - from topic discovery through final video with thumbnails, metadata, and engagement comments.

**IMPORTANT**: Despite the filename `claude_generator.py`, the codebase now uses **Gemini API** (not Claude API) for all content generation. The module name is legacy but the implementation is 100% Gemini-based.

## Recent Quality Improvements (v2.0)

The system has been enhanced with high-quality features based on the Zenn article's successful approach:

1. **Whisper STT Integration** (`whisper_stt.py`): **100% FREE** accurate subtitle synchronization using OpenAI Whisper (local execution, no API costs, 95%+ accuracy)
2. **ElevenLabs STT Integration** (`elevenlabs_stt.py`): Optional paid alternative for subtitle synchronization (99%+ accuracy)
3. **Enhanced Gemini Prompts** (`claude_generator.py`): Template-driven content generation with Gemini 3.0 Flash
...
3. **Script Generation** (`claude_generator.py`): Gemini 3.0 Flash creates template-driven dialogue
4. **MoviePy Rendering** (`video_maker_moviepy.py`): Higher quality subtitle rendering with fade effects
5. **Template System** (`content_templates.py`): 4 script structures, 6 title patterns, 5 character personas
6. **Pre-upload Validation** (`pre_upload_checks.py`): Automated quality checks before YouTube upload
7. **Thumbnail Tooling** (`thumb_lint.py`): Quality assurance for thumbnail generation
8. **YouTube Auto-Upload** (`youtube_uploader.py`): OAuth-based automated publishing with comment posting

See `QUALITY_IMPROVEMENTS.md` and `TEMPLATE_SYSTEM.md` for detailed information.

## Development Commands

### Running Video Generation

```bash
# Advanced generation (recommended, with all features)
docker compose run --rm ai-video-bot python advanced_video_pipeline.py

# Simple generation (legacy, fixed nostalgic topics)
docker compose run --rm ai-video-bot python daily_video_job.py

# Test individual modules
docker compose run --rm ai-video-bot python web_search.py
docker compose run --rm ai-video-bot python claude_generator.py  # Actually uses Gemini
docker compose run --rm ai-video-bot python thumbnail_generator.py
docker compose run --rm ai-video-bot python youtube_uploader.py  # OAuth setup test
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
- `TOPIC_CATEGORY`: Topic category (economics, technology, culture, lifestyle, ai_news)
- `USE_WEB_SEARCH`: Enable/disable web search for trending topics (true/false)

**Gemini TTS Settings (December 2025 - Latest Models):**
- `GEMINI_TTS_MODEL`: Gemini TTS model selection (default: gemini-2.5-flash-preview-tts)
  - `gemini-2.5-flash-preview-tts`: Faster, cost-efficient for everyday use
  - `gemini-2.5-pro-preview-tts`: State-of-the-art quality for complex prompts
- `GEMINI_TTS_MALE_VOICE`: Male voice name for dialogue (default: Zephyr)
  - Supported: Zephyr, Puck, Charon, Fenrir, Orus
- `GEMINI_TTS_FEMALE_VOICE`: Female voice name for dialogue (default: Aoede)
  - Supported: Aoede, Leda, Despina, Callirrhoe

**Quality Settings:**
- `USE_WHISPER_STT`: Enable Whisper STT for accurate subtitle timing (true/false, **100% FREE**, default: true, recommended)
- `WHISPER_MODEL_SIZE`: Whisper model size (tiny/base/small/medium/large, default: base)
- `USE_ELEVENLABS_STT`: Enable ElevenLabs STT for subtitle timing (true/false, paid API, requires API key)
- `ELEVENLABS_API_KEY`: API key for ElevenLabs STT (optional, only if USE_ELEVENLABS_STT=true)
- `USE_MOVIEPY`: Enable MoviePy for higher quality rendering (true/false, slower but better quality)

**YouTube Upload Settings:**
- `YOUTUBE_UPLOAD_ENABLED`: Enable automatic YouTube upload (true/false, requires OAuth setup)
- `YOUTUBE_PRIVACY_STATUS`: Privacy setting for uploads (private/unlisted/public, default: private)
- `YOUTUBE_POST_COMMENTS`: Post auto-generated engagement comments (true/false, default: false)
- `YOUTUBE_PLAYLIST_ID`: Optional playlist ID to add videos to

**Image Generation Settings:**
- `USE_NANO_BANANA_PRO`: Use local Nano Banana Pro instead of DALL-E (true/false, default: false)
- `NANO_BANANA_PRO_BIN`: Path to nanobanana binary (default: nanobanana)
- `NANO_BANANA_PRO_STYLE`: Style preset (default: cinematic-newsroom)
- `NANO_BANANA_PRO_WIDTH`: Image width (default: 1792)
- `NANO_BANANA_PRO_HEIGHT`: Image height (default: 1024)

## Architecture

### Two Generation Modes

1. **Simple Mode** (`daily_video_job.py`): Legacy 4-step pipeline with fixed topics
   - Gemini-based script generation → Image → Audio → Video

2. **Advanced Mode** (`advanced_video_pipeline.py`): Full 11-step production pipeline
   - Web search → Gemini script → Image → Audio → Video → Metadata → Comments → Thumbnail → Pre-flight checks → Tracking → YouTube Upload

### 11-Step Advanced Pipeline

The advanced pipeline provides complete automation from topic discovery to YouTube publishing:

1. **Web Search** (`web_search.py`): Discovers trending topics via Serper API
2. **Topic Selection** (`web_search.py`): Gemini analyzes and selects optimal topic
3. **Script Generation** (`claude_generator.py`): Gemini 3.0 Flash creates template-driven dialogue
4. **Image Generation** (`nano_banana_client.py`): DALL-E 3 or Nano Banana Pro creates Lo-fi anime backgrounds
5. **Audio Generation** (`tts_generator.py`): Gemini TTS (2.5 Flash/Pro) produces podcast-style audio
6. **Video Assembly** (`video_maker.py` / `video_maker_moviepy.py`): FFmpeg/MoviePy combines audio + background + subtitles
7. **Metadata Generation** (`metadata_generator.py`): Template-based SEO-optimized titles/descriptions with Gemini enhancement
8. **Comment Generation** (`metadata_generator.py`): 5 character personas generate engagement comments
9. **Thumbnail Creation** (`thumbnail_generator.py`): Creates custom YouTube thumbnail with multiple layouts
10. **Pre-flight Checks** (`pre_upload_checks.py`, `thumb_lint.py`): Validates video, thumbnail, metadata quality
11. **Tracking & Upload** (`tracking.py`, `notifications.py`, `youtube_uploader.py`): Logs to Sheets/JSON, sends Slack notifications, uploads to YouTube (optional)

### Key Module Responsibilities

**Content Generation:**
- `claude_generator.py`: **Gemini-based** content generation (legacy name) - dialogue script, SEO metadata, character-based comments
- `llm_story.py`: Gemini fallback for script generation
- `content_templates.py`: Template system for script structures, title patterns, timestamps
- `metadata_generator.py`: Template-based metadata generation with Gemini enhancement
- `web_search.py`: Serper API integration + Gemini-based topic curation with named entity extraction
- `tts_generator.py`: Gemini TTS (2.5 Flash/Pro) with Whisper/ElevenLabs STT integration, gTTS fallback
- `nano_banana_client.py`: DALL-E 3 or Nano Banana Pro (local) image generation wrapper

**Video Processing:**
- `video_maker.py`: FFmpeg orchestration, subtitle rendering with PIL, frame generation (fast)
- `video_maker_moviepy.py`: MoviePy-based rendering with fade effects (high quality)
- `whisper_stt.py`: **FREE** OpenAI Whisper (local) Speech-to-Text for accurate subtitle synchronization
- `elevenlabs_stt.py`: ElevenLabs Speech-to-Text (paid API) for accurate subtitle synchronization
- `subtitle_generator.py`: Legacy subtitle system (not used in new pipeline)
- `thumbnail_generator.py`: PIL-based thumbnail creation with multiple layouts, text overlays, character blending

**Quality & Operations:**
- `pre_upload_checks.py`: Pre-upload validation (video, thumbnail, metadata, timestamps, script)
- `thumb_lint.py`: Thumbnail quality assurance (color count, contrast, file size)
- `notifications.py`: Slack webhook notifications (start, complete, error, daily summary)
- `tracking.py`: Logs to Google Sheets or local JSON/CSV
- `youtube_uploader.py`: YouTube Data API v3 integration for automatic uploads, thumbnail setting, and comment posting
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

### Primary Services (Required)
- **Gemini API** (Google): Script generation, topic selection, metadata creation, TTS audio generation
- **OpenAI API**: DALL-E 3 background image generation (or Nano Banana Pro for local generation)

### Optional Services
- **Serper API**: Web search for trending topics (fallback topics available if missing)
- **Slack**: Webhook notifications for pipeline status
- **Google Sheets**: Production logging (fallback to local JSON/CSV)
- **YouTube Data API v3**: Automatic video upload, thumbnail setting, comment posting (requires OAuth 2.0 authentication)
- **ElevenLabs API**: High-accuracy STT for subtitle timing (Whisper STT is free alternative)

### Fallback Strategy

The system gracefully degrades when APIs are unavailable:
- Gemini unavailable → Uses hardcoded fallback topics and basic script templates
- Gemini TTS unavailable → Falls back to gTTS (Google Text-to-Speech, lower quality)
- Web search unavailable → Uses predefined fallback topics from `llm_story.py`
- DALL-E unavailable → Can use Nano Banana Pro (local) if configured
- Whisper/ElevenLabs STT unavailable → Falls back to timing estimation (80-90% accuracy)
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
2. Log specific error with context
3. Notify via Slack if configured
4. Attempt fallback service
5. Track failure in logging system
6. Return degraded result rather than crashing

Example: If Gemini API fails during script generation, the system automatically uses hardcoded fallback topics, logs the failure, and continues with basic template-based generation.

## Japanese Language Considerations

- All prompts to Gemini are in Japanese for optimal results
- Character count estimates: ~300 chars/minute for natural Japanese speech
- TTS timing: ~7 chars/second for Gemini TTS output
- Font support required: Noto Sans CJK or equivalent for subtitle rendering
- Named entity extraction: Uses bilingual entity library (English company names + Japanese aliases)
- Template system: Designed for Japanese content structure and SEO patterns

## Testing Individual Components

Each major module is runnable standalone:

```bash
# Test web search and topic selection
docker compose run --rm ai-video-bot python web_search.py

# Test Gemini script generation (note: file named claude_generator.py)
docker compose run --rm ai-video-bot python claude_generator.py

# Test content templates
docker compose run --rm ai-video-bot python content_templates.py

# Test metadata generation
docker compose run --rm ai-video-bot python metadata_generator.py

# Test thumbnail generation
docker compose run --rm ai-video-bot python thumbnail_generator.py

# Test YouTube authentication (OAuth setup)
docker compose run --rm ai-video-bot python youtube_uploader.py

# Test pre-upload validation
python pre_upload_checks.py  # Requires test video/thumbnail/metadata files

# Test thumbnail quality assurance
python thumb_lint.py outputs/2025-12-XX/video_001/thumbnail.jpg
```

These execute the `if __name__ == "__main__"` blocks with test data.

## Dependencies

Core Python packages:
- `requests`: HTTP client for Gemini, Serper, Slack webhooks
- `openai-whisper`: **FREE** Local STT for subtitle timing (recommended)
- `gTTS`: Fallback TTS
- `Pillow`: Image manipulation and subtitle rendering
- `moviepy`: High-quality video rendering with effects
- `python-dotenv`: Environment variable management
- `google-auth-oauthlib`: OAuth 2.0 authentication for YouTube API
- `google-api-python-client`: YouTube Data API v3 client

System dependencies:
- `ffmpeg`: Audio/video processing
- `ffprobe`: Duration detection
- Japanese fonts: Noto Sans CJK or equivalent

Optional:
- `elevenlabs`: Paid STT API (alternative to Whisper)

## Model Selection

**Gemini models** are configured via environment variables:

Content Generation (`claude_generator.py` and `llm_story.py`):
- Current: `gemini-3-flash-preview` (via `GEMINI_MODEL` env var)
- Fast, cost-efficient, optimized for creative dialogue generation
- Temperature: 0.9 for creative dialogue, default for analytical tasks

Gemini TTS configuration in `tts_generator.py` (December 2025 - Latest Models):
- Model: Configurable via `GEMINI_TTS_MODEL` environment variable
  - Default: `gemini-2.5-flash-preview-tts` (faster, cost-efficient, **recommended**)
  - Alternative: `gemini-2.5-pro-preview-tts` (state-of-the-art quality)
- Voices: Configurable via environment variables
  - Male: `GEMINI_TTS_MALE_VOICE` (default: Zephyr)
  - Female: `GEMINI_TTS_FEMALE_VOICE` (default: Aoede)
- Format: PCM L16 24kHz mono, converted to MP3

Whisper STT configuration:
- Model: Configurable via `WHISPER_MODEL_SIZE` (tiny/base/small/medium/large)
- Default: `base` (good balance of speed and accuracy)
- Runs locally - 100% FREE with no API costs

## Cost Considerations

Approximate costs for 4 videos/day (10 minutes each):
- Gemini API (Script/Metadata): ~¥2,000/month
- Gemini TTS: ~¥1,500/month
- DALL-E 3: ~¥3,600/month (or FREE with Nano Banana Pro local generation)
- Serper API: ~¥500/month
- Whisper STT: **¥0/month (100% FREE, local)**
- ElevenLabs STT (optional): ~¥1,200/month if used
- **Total (with Whisper)**: ~¥7,600/month (~$50-60 USD)
- **Total (with ElevenLabs)**: ~¥8,800/month (~$60-70 USD)

Per the Zenn article case study, advertising revenue exceeded API costs after reaching monetization thresholds.

## Recent Implementations (v2.0)

The following features have been recently implemented:
- ✅ **Whisper STT integration** (`whisper_stt.py`): FREE local subtitle synchronization with 95%+ accuracy
- ✅ **YouTube Data API v3 integration** (`youtube_uploader.py`): Automatic video uploads, thumbnail setting, and comment posting with OAuth 2.0 authentication
- ✅ **ElevenLabs STT integration** (`elevenlabs_stt.py`): Optional paid accurate subtitle synchronization (99%+ accuracy)
- ✅ **MoviePy rendering** (`video_maker_moviepy.py`): High-quality video rendering with fade effects
- ✅ **Template system** (`content_templates.py`): 4 script structures, 6 title patterns, 5 persona-based comments
- ✅ **Pre-upload validation** (`pre_upload_checks.py`): Automated quality checks before YouTube upload
- ✅ **Thumbnail tooling** (`thumb_lint.py`): Color, contrast, and file size validation
- ✅ **Named entity extraction** (`web_search.py`): Bilingual entity library for CTR optimization
- ✅ **Nano Banana Pro support** (`nano_banana_client.py`): Local image generation alternative to DALL-E

## Current Development Status

**Modified Files (Uncommitted):**
Based on git status, the following files have recent uncommitted changes:
- `advanced_video_pipeline.py`: Main pipeline orchestration
- `claude_generator.py`: Gemini API integration (legacy name)
- `llm_story.py`: Fallback story generation
- `metadata_generator.py`: Template-based metadata generation
- `pre_upload_checks.py`: Quality validation system
- `web_search.py`: Topic discovery and entity extraction

**Recent Commits (Last 10):**
1. Full Nano Banana thumbnail generation and TTS voice updates
2. Enhanced thumbnail generation system with new layouts
3. Nano Banana via Gemini CLI fallback support
4. Left-aligned character thumbnail layout
5. Distinct voices for male/female dialogue
6. Three-sentence hook structure enforcement
7. Pre-upload validation addition
8. Timestamp label deduplication
9. Thumbnail text layout and character blending improvements
10. Serper news endpoint with fallback to organic results

These commits show active development on thumbnail quality, TTS voices, and validation systems.

## Architecture Patterns & Development Guidelines

When extending this codebase:

1. **Fallback Pattern**: Always implement graceful degradation
   - Primary service → Fallback service → Hardcoded defaults
   - Log failures but continue processing
   - Example: Gemini TTS → gTTS → Skip audio

2. **Module Naming**: Some modules have legacy names (e.g., `claude_generator.py` uses Gemini)
   - Don't rename modules without reviewing all imports
   - Document discrepancies in module docstrings

3. **Template-First Design**: Use templates for consistent content quality
   - Prefer `content_templates.py` over ad-hoc generation
   - Combine templates with AI enhancement, not replacement

4. **Quality Gates**: Validate before expensive operations
   - Pre-flight checks before YouTube upload
   - Thumbnail linting before rendering final video
   - Metadata validation before publishing

5. **Japanese-First**: Content is optimized for Japanese audience
   - Prompts, templates, and SEO patterns are Japanese-focused
   - Named entity library includes Japanese aliases
   - Character count and timing estimates are Japanese-specific

## Future Extension Points

Planned features from README:
- BGM generation/addition (Suno AI / MusicGen)
- A/B testing for thumbnails
- Cloud deployment (Render, AWS, GCP)
- GitHub Actions CI/CD
- Analytics dashboard

When implementing these, follow the existing fallback pattern and ensure the core pipeline remains functional even if extensions fail.
