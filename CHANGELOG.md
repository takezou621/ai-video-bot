# Changelog

All notable changes to this project will be documented in this file.

## [2.1.0] - 2025-11-26

### Added - Male/Female Dialogue Format
1. **Character-Based Dialogue**
   - Changed from generic "Speaker A/B" to "男性/女性" (Male/Female)
   - Male host: 30s, knowledgeable, calm demeanor
   - Female host: 20s, curious, bright personality
   - Natural conversational dynamics with distinct character roles

2. **Visual Differentiation**
   - Male speaker: Blue accent (#78C8FF)
   - Female speaker: Pink accent (#FF96B4)
   - Color-coded subtitle indicator bars for instant speaker recognition
   - Maintained backward compatibility with legacy A/B format

3. **Enhanced TTS Support**
   - Gemini TTS Speaker 1/2 mapping for male/female voices
   - Automatic voice differentiation in multi-speaker dialogues
   - Preserved speaker labels throughout processing pipeline

### Changed
- `claude_generator.py`: Updated prompts to generate male/female dialogue
- `video_maker.py`: Added color coding for male/female speakers
- `video_maker_moviepy.py`: Added color coding for high-quality rendering
- `tts_generator.py`: Added support for male/female speaker labels
- `README.md`: Documented male/female dialogue feature

### Benefits
- **More engaging content**: Character-based dialogue feels more natural
- **Better viewer retention**: Distinct speaker voices and colors improve comprehension
- **SEO improvement**: Personality-driven content increases watch time

## [2.0.1] - 2025-11-26

### Changed
- **ElevenLabs STT now disabled by default** - Changed from opt-out to opt-in
  - `.env.sample`: `USE_ELEVENLABS_STT=false` (was `true`)
  - Automatically disabled if `ELEVENLABS_API_KEY` is not set
  - Clear console messages when STT is disabled or API key is missing
  - Users can still enable by setting both `USE_ELEVENLABS_STT=true` AND providing API key

### Benefits
- **Easier onboarding**: New users don't need ElevenLabs account to get started
- **Lower cost**: Reduces monthly API costs for users who don't need 99%+ subtitle accuracy
- **Better UX**: Clear feedback when feature is disabled vs when API key is missing
- **Still excellent quality**: Default timing estimation provides 80-90% accuracy

### Documentation Updates
- Updated README.md with "High Quality (Default)" recommendation
- Updated QUICKSTART.md to clarify ElevenLabs is optional
- Added clear notes that 80-90% subtitle accuracy works well without extra API

## [2.0.0] - 2025-11-26

### Added - Based on Zenn Blog Success Case

#### Core Features (Zenn Article Implementation)
1. **Web Search Integration** (`web_search.py`)
   - Serper API for trending topic discovery
   - Claude API for topic selection and analysis
   - Fallback topics when search unavailable

2. **Claude API Integration** (`claude_generator.py`)
   - Multi-stage content generation (Prompts A, B, C, D from blog)
   - Dialogue script generation with Claude Sonnet 4.5
   - SEO-optimized metadata generation
   - Engagement comments generation

3. **Advanced Video Pipeline** (`advanced_video_pipeline.py`)
   - 9-step automated generation pipeline
   - Multi-video batch processing (4 videos/day capability)
   - Complete integration of all modules

4. **Thumbnail Generator** (`thumbnail_generator.py`)
   - YouTube-optimized size (1280x720)
   - Text overlays with shadows
   - Multiple color variants

5. **Slack Notifications** (`notifications.py`)
   - Video start/complete/error alerts
   - Daily summary reports
   - Context manager for automatic notifications

6. **Video Tracking** (`tracking.py`)
   - Local JSON logging
   - Google Sheets integration (optional)
   - CSV export capability
   - Statistics and analytics

#### Quality Enhancement Features (v2.0)
7. **Template System** (`content_templates.py`)
   - 4 proven script structures
   - 6 SEO-optimized title patterns
   - 5 character persona comments
   - Automatic timestamp generation

8. **Metadata Generator** (`metadata_generator.py`)
   - CTR-optimized titles (8-12% target)
   - Automatic timestamp generation
   - Strategic tag placement (15-20 tags)

9. **ElevenLabs STT Integration** (`elevenlabs_stt.py`)
   - Accurate subtitle timing from audio transcription
   - Script-to-audio alignment
   - 99%+ subtitle accuracy

10. **MoviePy Video Rendering** (`video_maker_moviepy.py`)
    - High-quality rendering option
    - Fade in/out effects
    - Professional finish

### Changed
- Enhanced `claude_generator.py` with template integration
- Updated `advanced_video_pipeline.py` to use all new modules
- Improved `tts_generator.py` with ElevenLabs STT support

### Documentation
- Comprehensive README.md with architecture overview
- QUICKSTART.md for 5-minute setup
- QUALITY_IMPROVEMENTS.md detailing enhancement strategies
- TEMPLATE_SYSTEM.md explaining template customization
- TEST_REPORT.md with implementation results

### Dependencies
- Added `anthropic>=0.18.0` for Claude API
- Added `moviepy>=1.0.3` for high-quality rendering
- All dependencies documented in requirements.txt

## [1.0.0] - Initial Release

### Features
- Basic video generation with Gemini TTS
- DALL-E 3 background image generation
- FFmpeg video composition
- Subtitle overlay
- Docker containerization

---

## Roadmap

### Planned Features
- [ ] YouTube auto-upload (YouTube Data API v3)
- [ ] BGM generation and integration (Suno AI / MusicGen)
- [ ] A/B testing for thumbnails
- [ ] Cloud deployment (Render / AWS / GCP)
- [ ] GitHub Actions CI/CD
- [ ] Analytics dashboard

### Success Metrics (Target)
- YouTube monetization: 3 months
- Viewer retention: 50-60%
- Title CTR: 8-12%
- Comments per video: 20-50
- Subscriber rate: 3-5%
# [2.2.0] - 2025-12-10

### Changed
- Migrated topic selection, script generation, metadata, and engagement comments to the Gemini API (legacy `claude_*` module names retained for compatibility).
- Updated `web_search.py` to analyze Serper results with Gemini, preserving named-entity scoring.
- Refreshed `advanced_video_pipeline.py` logging to reflect the Gemini-first workflow.

### Documentation
- Removed `CLAUDE_API_KEY` from setup instructions and clarified that `GEMINI_API_KEY` now powers scripts, metadata, and TTS.
- Updated README/QUICKSTART/QUALITY_IMPROVEMENTS/package metadata to describe the Gemini-based pipeline and marked `CLAUDE.md` as legacy guidance.
# [2.2.0] - 2025-12-10

### Changed
- Migrated topic selection, script generation, metadata、コメント生成を Gemini API ベースへ統一（legacyファイル名は維持）。
- `web_search.py` を Serper のニュースエンドポイント＋`organic` フォールバックに変更し、最新ニュースを確実に取得。
- `thumbnail_generator.py` を改良し、文字とキャラクターのレイアウトを分離＋ドロップシャドウで自然な合成に。
- `content_templates.py` のタイムスタンプ生成を改良し、重複ラベルや短間隔での繰り返しを抑制。
- `advanced_video_pipeline.py` にプリフライト検証を追加し、アップロード前に動画・サムネ・メタデータを自動チェック。

### Added
- `pre_upload_checks.py`: ファイルサイズ、タイトル/タイムスタンプ、タイミング整合性などを検査する安全弁。
