"""
Advanced Video Generation Pipeline
Integrates all the blog's features: web search, Gemini AI, thumbnails, notifications, tracking, YouTube upload
"""
import os
import datetime
import json
from pathlib import Path
from dotenv import load_dotenv

# Import all our new modules
from web_search import search_trending_topics, select_topic_with_claude, search_latest_ai_news
from claude_generator import (
    generate_dialogue_script_with_claude,
    generate_metadata_with_claude,
    generate_comments_with_claude
)
from tts_generator import generate_dialogue_audio
from thumbnail_generator import create_thumbnail
from thumbnail_prompt_generator import generate_thumbnail_prompt
from llm_story import get_past_topics
from topic_history import add_topic_to_history
from cleanup import cleanup_video_temp_files
import shutil

# Import video maker with MoviePy support
try:
    from video_maker_moviepy import make_podcast_video
    USE_MOVIEPY = os.getenv("USE_MOVIEPY", "true").lower() == "true"
except ImportError:
    from video_maker import make_podcast_video
    USE_MOVIEPY = False
from nano_banana_client import generate_image
from notifications import (
    notify_video_start,
    notify_video_complete,
    notify_video_error,
    notify_daily_summary
)
from tracking import log_video_to_sheets, create_video_log_entry
from metadata_generator import (
    generate_complete_metadata,
    generate_title_variations,
    generate_engagement_comments
)
from youtube_uploader import upload_video_with_metadata

BADGE_LABELS = {
    "economics": "経済",
    "technology": "テック",
    "culture": "カルチャー",
    "lifestyle": "ライフ",
}
from pre_upload_checks import run_pre_upload_checks
from thumb_lint import lint_thumbnail

# Spreadsheet input support
from sheets_reader import (
    is_sheets_input_enabled,
    get_pending_rows,
    update_row_status,
    create_script_from_sheet_row
)

# Podcast API input support
from podcast_api import (
    is_podcast_api_enabled,
    get_pending_podcasts,
    update_podcast_status,
    create_script_from_podcast
)

BASE = Path(__file__).parent
OUT = BASE / "outputs"


def generate_single_video(
    video_number: int = 1,
    topic_category: str = "economics",
    duration_minutes: int = 10,
    use_web_search: bool = True,
    sheet_row_data: dict = None,
    podcast_api_data: dict = None
) -> dict:
    """
    Generate a single video with all advanced features including YouTube upload

    10-Step Pipeline:
    1. Web Search: Discover trending topics (or load from spreadsheet)
    2. Script Generation: Create dialogue with Gemini (or use spreadsheet data)
    3. Image Generation: Generate background image
    4. Audio Generation: Create dialogue audio with TTS
    5. Video Assembly: Combine audio, image, and subtitles
    6. Metadata Generation: Create YouTube-optimized metadata
    7. Comments Generation: Generate engagement comments
    8. Thumbnail Creation: Create custom thumbnail
    9. Tracking: Log to Google Sheets
    10. YouTube Upload: Automatically upload to YouTube (optional)

    Args:
        video_number: Video number for this session
        topic_category: Category for topic search
        duration_minutes: Target video duration
        use_web_search: Whether to use web search for topics
        sheet_row_data: Pre-loaded data from spreadsheet (skips Step 1-2)
        podcast_api_data: Pre-loaded data from Podcast API (skips Step 1-2)

    Returns:
        Dictionary with video information
    """
    today = str(datetime.date.today())
    video_id = f"{today}-{video_number:03d}"
    outdir = OUT / today / f"video_{video_number:03d}"
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Video #{video_number} - {video_id}")
    print(f"{'='*60}\n")

    try:
        # Check if using spreadsheet data
        if sheet_row_data:
            # Step 1-2: Load from spreadsheet (skip web search and script generation)
            print("[1-2/10] 📊 Loading from spreadsheet...")
            print(f"  Row: {sheet_row_data.get('row_index')}")

            # Create script from sheet data
            script = create_script_from_sheet_row(sheet_row_data)
            topic_title = script.get("title", "Unknown Topic")
            print(f"  Title: {topic_title}")
            print(f"  Dialogues: {len(script['dialogues'])} exchanges")

            # Create topic_analysis for compatibility
            topic_analysis = {
                "title": topic_title,
                "angle": sheet_row_data.get("summary", ""),
                "key_points": [],
                "source": "spreadsheet",
                "sheet_row_index": sheet_row_data.get("row_index")
            }

            # Save topic analysis
            json.dump(topic_analysis, open(outdir / "topic.json", "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)

            # Save script
            json.dump(script, open(outdir / "script.json", "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)

            # Notify start
            notify_video_start(video_number, topic_title, duration_minutes)

        elif podcast_api_data:
            # Step 1-2: Load from Podcast API (skip web search and script generation)
            print("[1-2/10] 🎙️  Loading from Podcast API...")
            print(f"  Podcast ID: {podcast_api_data.get('id')}")

            # Create script from API data
            script = create_script_from_podcast(podcast_api_data)
            topic_title = script.get("title", "Unknown Topic")
            print(f"  Title: {topic_title}")
            print(f"  Dialogues: {len(script['dialogues'])} exchanges")
            print(f"  Hosts: {script.get('host_names', {}).get('male', 'Unknown')} & {script.get('host_names', {}).get('female', 'Unknown')}")

            # Create topic_analysis for compatibility
            topic_analysis = {
                "title": topic_title,
                "angle": podcast_api_data.get("summary", ""),
                "key_points": [],
                "source": "podcast_api",
                "podcast_id": podcast_api_data.get("id")
            }

            # Save topic analysis
            json.dump(topic_analysis, open(outdir / "topic.json", "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)

            # Save script
            json.dump(script, open(outdir / "script.json", "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)

            # Notify start
            notify_video_start(video_number, topic_title, duration_minutes)

        else:
            # Step 1: Discover trending topic (Blog's Prompt A)
            print("[1/10] 🔍 Searching for trending topics...")
            if use_web_search:
                if topic_category == "ai_news":
                    print("  Mode: Latest International AI News")
                    search_results = search_latest_ai_news()
                    # For AI news, we want to summarize multiple articles, not just one
                    topic_analysis = select_topic_with_claude(search_results, duration_minutes, topic_category)
                    # Add all news articles for multi-article summary
                    topic_analysis["all_news_articles"] = search_results
                else:
                    search_results = search_trending_topics(topic_category)
                    topic_analysis = select_topic_with_claude(search_results, duration_minutes, topic_category)
            else:
                # Use fallback topic - avoid duplicates with past topics
                past_topics = get_past_topics(max_count=20)

                # If VIDEO_TOPIC is explicitly set, use it
                explicit_topic = os.getenv("VIDEO_TOPIC", "")

                if explicit_topic:
                    topic_title = explicit_topic
                else:
                    # Generate diverse topic suggestion based on category
                    # Leave title empty to let Gemini generate it with duplicate avoidance
                    topic_title = ""
                    print(f"  Past topics found: {len(past_topics)}")
                    if past_topics:
                        print(f"  Avoiding duplicates of: {', '.join(past_topics[:3])}...")

                topic_analysis = {
                    "title": topic_title,
                    "angle": f"{topic_category}に関する興味深い視点",
                    "key_points": ["最新トレンド", "実用的な知識", "視聴者の関心"],
                }

            topic_title = topic_analysis.get("title", "Unknown Topic")
            print(f"  Selected: {topic_title}")

            # Save topic analysis
            json.dump(topic_analysis, open(outdir / "topic.json", "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)

            # Notify start
            notify_video_start(video_number, topic_title, duration_minutes)

            # Step 2: Generate dialogue script (Blog's Prompt B)
            print("\n[2/10] ✍️  Generating dialogue script with Gemini...")
            script = generate_dialogue_script_with_claude(topic_analysis, duration_minutes)
            print(f"  Title: {script['title']}")
            print(f"  Dialogues: {len(script['dialogues'])} exchanges")

            # Save script
            json.dump(script, open(outdir / "script.json", "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)

        # Step 3: Generate background image
        print("\n[3/10] 🎨 Generating background image with optimized prompt...")
        bg_path = outdir / "background.png"
        
        # Generate optimized prompt and thumbnail data
        thumbnail_data = generate_thumbnail_prompt(
            title=script["title"],
            topic_category=topic_category,
            thumbnail_text=script.get("thumbnail_text")
        )
        bg_prompt = thumbnail_data["prompt"]
        print(f"  Prompt: {bg_prompt[:50]}...")
        
        generate_image(bg_prompt, bg_path)
        print(f"  Background saved: {bg_path}")

        # Step 4: Generate audio with dialogue
        print("\n[4/10] 🎙️  Generating dialogue audio with Gemini TTS...")
        audio_path = outdir / "dialogue"
        audio_file, timing_data = generate_dialogue_audio(script["dialogues"], audio_path)
        print(f"  Audio saved: {audio_file}")
        print(f"  Timing data: {len(timing_data)} segments")

        # Save timing data
        json.dump(timing_data, open(outdir / "timing.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)

        # Step 5: Create video with subtitles
        print("\n[5/10] 🎬 Creating video with subtitles...")
        if USE_MOVIEPY:
            print("  Using MoviePy for high-quality rendering...")
        video_path = outdir / "video.mp4"
        make_podcast_video(bg_path, timing_data, audio_file, video_path, use_moviepy=USE_MOVIEPY)

        # Get video duration
        import subprocess
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "csv=p=0", str(video_path)
        ], capture_output=True, text=True)
        video_duration = float(result.stdout.strip()) if result.stdout.strip() else 0

        # Step 6: Generate metadata with templates
        print("\n[6/10] 📝 Generating metadata with Gemini + Templates...")
        claude_metadata = generate_metadata_with_claude(script, video_duration)

        # Get source URL directly from topic analysis to avoid LLM truncation
        verified_urls = []
        if topic_analysis.get("selected_topic", {}).get("url"):
            verified_urls.append(topic_analysis["selected_topic"]["url"])

        # Enhance with template system
        metadata = generate_complete_metadata(
            script=script,
            timing_data=timing_data,
            video_duration_seconds=video_duration,
            claude_metadata=claude_metadata,
            verified_source_urls=verified_urls
        )
        print(f"  YouTube Title: {metadata.get('youtube_title', 'N/A')}")
        print(f"  Timestamps: {len(metadata.get('timestamps', []))}")

        # Save metadata
        json.dump(metadata, open(outdir / "metadata.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)

        # Step 7: Generate engagement comments with templates
        print("\n[7/10] 💬 Generating engagement comments...")

        # Get Gemini-generated comments
        claude_comments = generate_comments_with_claude(script, count=3)

        # Add template-generated comments
        template_comments = generate_engagement_comments(script, count=2)

        # Combine both types
        comments = claude_comments + template_comments
        json.dump({"comments": comments}, open(outdir / "comments.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"  Generated {len(comments)} comments (Gemini: {len(claude_comments)}, Template: {len(template_comments)})")

        # Step 8: Generate thumbnail with background + PIL text overlay
        print("\n[8/10] 🖼️  Generating thumbnail...")
        thumbnail_path = outdir / "thumbnail.jpg"
        badge_text = BADGE_LABELS.get(topic_category, topic_category or "解説")

        # Generate thumbnail prompt for BACKGROUND ONLY (text will be added with PIL)
        # Use YouTube title to generate concise thumbnail text
        thumbnail_prompt_data = generate_thumbnail_prompt(
            title=metadata["youtube_title"],  # Use YouTube title for consistency
            topic_category=topic_category,
            thumbnail_text=None,  # Let it auto-generate from title
            named_entities=metadata.get("named_entities", [])
        )
        thumbnail_final_prompt = thumbnail_prompt_data["prompt"]

        # Get thumbnail image model from environment
        thumbnail_image_model = os.getenv("THUMBNAIL_IMAGE_MODEL", None)

        create_thumbnail(
            background_image_path=bg_path,
            thumbnail_text=thumbnail_prompt_data["thumbnail_text"],  # Use generated text
            subtitle_text="",
            output_path=thumbnail_path,
            accent_color_index=video_number % 4,
            topic_badge_text=badge_text,
            image_prompt=None,  # Use existing background.png instead of generating new image
            emotion=thumbnail_data["emotion"],
            image_model=thumbnail_image_model  # Use environment-specified model
        )
        print(f"  Thumbnail saved: {thumbnail_path}")
        lint_warnings = lint_thumbnail(thumbnail_path)
        if lint_warnings:
            print("⚠️  Thumbnail QA warnings (Continuing...):")
            for warn in lint_warnings:
                print(f"    - {warn}")
            # raise RuntimeError("Thumbnail lint failed - regenerate or adjust layout.")
        else:
            print("  Thumbnail QA passed ✅")

        print("\n[8.5/10] ✅ Running pre-upload checks...")
        validation = run_pre_upload_checks(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            metadata=metadata,
            timestamps=metadata.get("timestamps", []),
            script=script,
            timing_data=timing_data,
            expected_duration_seconds=video_duration
        )
        for check in validation["checks"]:
            status = "PASS" if check.passed else "FAIL"
            print(f"   [{status}] {check.detail}")
        if not validation["passed"]:
            print("⚠️  Pre-upload validation failed (Continuing for testing)...")
            # raise RuntimeError("Pre-upload validation failed. Resolve the failed checks before uploading.")

        # Step 9: Log to tracking system
        print("\n[9/10] 📊 Logging to tracking system...")
        log_entry = create_video_log_entry(
            video_id=video_id,
            title=script["title"],
            file_path=str(video_path),
            duration_seconds=video_duration,
            metadata=metadata,
            topic_data=topic_analysis,
            status="generated"
        )
        log_video_to_sheets(log_entry)

        # Step 10: Upload to YouTube (optional)
        youtube_result = None
        youtube_upload_enabled = os.getenv("YOUTUBE_UPLOAD_ENABLED", "false").lower() == "true"

        if youtube_upload_enabled:
            print("\n[10/10] 📤 Uploading to YouTube...")
            try:
                privacy_status = os.getenv("YOUTUBE_PRIVACY_STATUS", "private")
                playlist_id = os.getenv("YOUTUBE_PLAYLIST_ID", "")

                # Check if comment posting is enabled
                post_comments = os.getenv("YOUTUBE_POST_COMMENTS", "false").lower() == "true"

                # Extract comments text from comments list
                comment_texts = None
                if post_comments:
                    comment_texts = [c.get("comment", c.get("text", "")) for c in comments if isinstance(c, dict)]
                    if not comment_texts:
                        comment_texts = [str(c) for c in comments if c]
                    comment_texts = comment_texts[:5]  # Limit to 5 comments

                youtube_result = upload_video_with_metadata(
                    video_path=str(video_path),
                    metadata=metadata,
                    thumbnail_path=str(thumbnail_path),
                    comments=comment_texts,
                    privacy_status=privacy_status,
                    playlist_id=playlist_id if playlist_id else None
                )

                if youtube_result:
                    print(f"✅ YouTube upload complete!")
                    print(f"   Video URL: {youtube_result['video_url']}")
                else:
                    print("⚠️  YouTube upload failed - continuing without upload")

            except Exception as e:
                print(f"⚠️  YouTube upload error: {e}")
                print("   Continuing without upload...")
        else:
            print("\n[10/10] ⏭️  YouTube upload disabled (set YOUTUBE_UPLOAD_ENABLED=true to enable)")

        # Save complete manifest
        manifest = {
            "video_id": video_id,
            "video_number": video_number,
            "topic_analysis": topic_analysis,
            "script": script,
            "metadata": metadata,
            "comments": comments,
            "files": {
                "video": str(video_path),
                "audio": str(audio_file),
                "background": str(bg_path),
                "thumbnail": str(thumbnail_path),
            },
            "duration_seconds": video_duration,
            "youtube_upload": youtube_result,
            "created_at": datetime.datetime.now().isoformat()
        }
        json.dump(manifest, open(outdir / "manifest.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)

        # Notify completion
        notify_video_complete(video_number, topic_title, str(video_path), video_duration, metadata)

        # Add topic to history to prevent duplicates
        topic_url = topic_analysis.get("selected_topic", {}).get("url", topic_analysis.get("url", ""))
        source_urls = topic_analysis.get("source_urls", [])
        if not source_urls and "all_news_articles" in topic_analysis:
            # Extract URLs from all news articles
            source_urls = [article.get("url", "") for article in topic_analysis.get("all_news_articles", [])]

        add_topic_to_history(
            title=topic_title,
            url=topic_url,
            source_urls=source_urls
        )

        print(f"\n✅ Video #{video_number} Complete!")
        print(f"   Output: {video_path}")
        print(f"   Duration: {int(video_duration // 60)}:{int(video_duration % 60):02d}")
        if youtube_result:
            print(f"   YouTube: {youtube_result['video_url']}")

        # Update spreadsheet status if using sheet data
        if sheet_row_data and sheet_row_data.get("row_index"):
            try:
                update_row_status(sheet_row_data["row_index"], "done")
                print(f"   Spreadsheet row {sheet_row_data['row_index']} marked as done")
            except Exception as e:
                print(f"   Warning: Failed to update spreadsheet status: {e}")

        # Update Podcast API status if using API data
        if podcast_api_data and podcast_api_data.get("id"):
            try:
                update_podcast_status(podcast_api_data["id"], "done")
                print(f"   Podcast API id={podcast_api_data['id']} marked as done")
            except Exception as e:
                print(f"   Warning: Failed to update Podcast API status: {e}")

        # Cleanup temporary files
        cleanup_video_temp_files(outdir)

        return manifest

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Error generating video #{video_number}: {error_msg}")

        # Notify error
        notify_video_error(video_number, topic_title if 'topic_title' in locals() else "Unknown", error_msg)

        # Log failure
        try:
            log_entry = create_video_log_entry(
                video_id=video_id,
                title=topic_title if 'topic_title' in locals() else "Failed Video",
                file_path="",
                duration_seconds=0,
                status="failed"
            )
            log_entry["error"] = error_msg
            log_video_to_sheets(log_entry)
        except:
            pass

        # Cleanup temporary files even on error
        try:
            if 'outdir' in locals() and outdir.exists():
                cleanup_video_temp_files(outdir)
        except Exception as cleanup_error:
            print(f"Warning: Cleanup failed: {cleanup_error}")

        raise


def generate_multiple_videos(
    count: int = 4,
    topic_category: str = "economics",
    duration_minutes: int = 10,
    use_web_search: bool = True
) -> list:
    """
    Generate multiple videos (like the blog's 4 videos/day)

    Args:
        count: Number of videos to generate
        topic_category: Category for topic search
        duration_minutes: Target duration per video
        use_web_search: Whether to use web search

    Returns:
        List of video manifests
    """
    print(f"\n{'='*60}")
    print(f"  Generating {count} videos")
    print(f"  Category: {topic_category}")
    print(f"  Duration: {duration_minutes} minutes each")
    print(f"{'='*60}\n")

    results = []
    successful = 0
    failed = 0
    total_duration = 0
    topics = []

    for i in range(1, count + 1):
        try:
            manifest = generate_single_video(
                video_number=i,
                topic_category=topic_category,
                duration_minutes=duration_minutes,
                use_web_search=use_web_search
            )
            results.append(manifest)
            successful += 1
            total_duration += manifest.get("duration_seconds", 0)
            topics.append(manifest.get("script", {}).get("title", "Unknown"))

            # Wait between videos to avoid rate limits
            if i < count:
                print(f"\n⏳ Waiting 10 seconds before next video...\n")
                import time
                time.sleep(10)

        except Exception as e:
            print(f"Failed to generate video {i}: {e}")
            failed += 1
            results.append({"error": str(e), "video_number": i})

    # Send daily summary
    notify_daily_summary(
        total_videos=count,
        successful=successful,
        failed=failed,
        total_duration_minutes=total_duration / 60,
        topics=topics
    )

    print(f"\n{'='*60}")
    print(f"  Batch Complete!")
    print(f"  Successful: {successful}/{count}")
    print(f"  Failed: {failed}/{count}")
    print(f"  Total Duration: {int(total_duration / 60)} minutes")
    print(f"{'='*60}\n")

    return results


def generate_videos_from_sheets(
    topic_category: str = "economics",
    duration_minutes: int = 10
) -> list:
    """
    Generate videos from spreadsheet data

    Reads pending rows from the configured spreadsheet and generates
    a video for each row.

    Args:
        topic_category: Category for topic (used for metadata)
        duration_minutes: Target duration per video

    Returns:
        List of video manifests
    """
    print(f"\n{'='*60}")
    print(f"  Spreadsheet Mode - Processing pending rows")
    print(f"{'='*60}\n")

    try:
        pending_rows = get_pending_rows()
    except Exception as e:
        print(f"❌ Failed to read spreadsheet: {e}")
        print("   Falling back to normal mode...")
        return []

    if not pending_rows:
        print("No pending rows found in spreadsheet")
        return []

    print(f"Found {len(pending_rows)} pending row(s)")

    results = []
    successful = 0
    failed = 0
    total_duration = 0
    topics = []

    for idx, row_data in enumerate(pending_rows, start=1):
        try:
            print(f"\n--- Processing row {row_data['row_index']} ({idx}/{len(pending_rows)}) ---")

            manifest = generate_single_video(
                video_number=idx,
                topic_category=topic_category,
                duration_minutes=duration_minutes,
                use_web_search=False,
                sheet_row_data=row_data
            )
            results.append(manifest)
            successful += 1
            total_duration += manifest.get("duration_seconds", 0)
            topics.append(manifest.get("script", {}).get("title", "Unknown"))

            # Wait between videos to avoid rate limits
            if idx < len(pending_rows):
                print(f"\n⏳ Waiting 10 seconds before next video...\n")
                import time
                time.sleep(10)

        except Exception as e:
            print(f"Failed to generate video from row {row_data['row_index']}: {e}")
            failed += 1
            results.append({"error": str(e), "row_index": row_data['row_index']})

            # Mark as error in spreadsheet
            try:
                update_row_status(row_data['row_index'], "error")
            except:
                pass

    # Send daily summary
    notify_daily_summary(
        total_videos=len(pending_rows),
        successful=successful,
        failed=failed,
        total_duration_minutes=total_duration / 60,
        topics=topics
    )

    print(f"\n{'='*60}")
    print(f"  Spreadsheet Batch Complete!")
    print(f"  Successful: {successful}/{len(pending_rows)}")
    print(f"  Failed: {failed}/{len(pending_rows)}")
    print(f"  Total Duration: {int(total_duration / 60)} minutes")
    print(f"{'='*60}\n")

    return results


def generate_videos_from_podcast_api(
    topic_category: str = "ai_news",
    duration_minutes: int = 10
) -> list:
    """
    Generate videos from Podcast API data

    Fetches pending podcasts from the API and generates
    a video for each one.

    Args:
        topic_category: Category for topic (used for metadata)
        duration_minutes: Target duration per video

    Returns:
        List of video manifests
    """
    print(f"\n{'='*60}")
    print(f"  Podcast API Mode - Processing pending podcasts")
    print(f"{'='*60}\n")

    try:
        pending_podcasts = get_pending_podcasts()
    except Exception as e:
        print(f"❌ Failed to fetch from Podcast API: {e}")
        print("   Falling back to normal mode...")
        return []

    if not pending_podcasts:
        print("No pending podcasts found in API")
        return []

    print(f"Found {len(pending_podcasts)} pending podcast(s)")

    results = []
    successful = 0
    failed = 0
    total_duration = 0
    topics = []

    for idx, podcast_data in enumerate(pending_podcasts, start=1):
        try:
            print(f"\n--- Processing podcast id={podcast_data['id']} ({idx}/{len(pending_podcasts)}) ---")

            manifest = generate_single_video(
                video_number=idx,
                topic_category=topic_category,
                duration_minutes=duration_minutes,
                use_web_search=False,
                podcast_api_data=podcast_data
            )
            results.append(manifest)
            successful += 1
            total_duration += manifest.get("duration_seconds", 0)
            topics.append(manifest.get("script", {}).get("title", "Unknown"))

            # Wait between videos to avoid rate limits
            if idx < len(pending_podcasts):
                print(f"\n⏳ Waiting 10 seconds before next video...\n")
                import time
                time.sleep(10)

        except Exception as e:
            print(f"Failed to generate video from podcast id={podcast_data['id']}: {e}")
            failed += 1
            results.append({"error": str(e), "podcast_id": podcast_data['id']})

            # Mark as error in API
            try:
                update_podcast_status(podcast_data['id'], "error")
            except:
                pass

    # Send daily summary
    notify_daily_summary(
        total_videos=len(pending_podcasts),
        successful=successful,
        failed=failed,
        total_duration_minutes=total_duration / 60,
        topics=topics
    )

    print(f"\n{'='*60}")
    print(f"  Podcast API Batch Complete!")
    print(f"  Successful: {successful}/{len(pending_podcasts)}")
    print(f"  Failed: {failed}/{len(pending_podcasts)}")
    print(f"  Total Duration: {int(total_duration / 60)} minutes")
    print(f"{'='*60}\n")

    return results


def main():
    """Main entry point"""
    if (BASE / ".env").exists():
        load_dotenv(BASE / ".env")

    # Get configuration
    videos_per_day = int(os.getenv("VIDEOS_PER_DAY", "1"))
    duration_minutes = int(os.getenv("DURATION_MINUTES", "5"))
    topic_category = os.getenv("TOPIC_CATEGORY", "ai_news")
    use_web_search = os.getenv("USE_WEB_SEARCH", "true").lower() == "true"

    # Priority 1: Check if Podcast API input is enabled
    if is_podcast_api_enabled():
        print("🎙️  Podcast API input mode enabled")
        results = generate_videos_from_podcast_api(
            topic_category=topic_category,
            duration_minutes=duration_minutes
        )
        # If pending podcasts found, exit after processing
        if results:
            return
        print("No videos generated from Podcast API, checking other modes...")

    # Priority 2: Check if spreadsheet input is enabled
    if is_sheets_input_enabled():
        print("📊 Spreadsheet input mode enabled")
        results = generate_videos_from_sheets(
            topic_category=topic_category,
            duration_minutes=duration_minutes
        )
        # If no pending rows, fall back to normal mode
        if not results:
            print("No videos generated from spreadsheet, falling back to normal mode...")
        else:
            return  # Exit after processing spreadsheet

    # Normal mode (web search or fallback topics)
    if videos_per_day > 1:
        generate_multiple_videos(
            count=videos_per_day,
            topic_category=topic_category,
            duration_minutes=duration_minutes,
            use_web_search=use_web_search
        )
    else:
        generate_single_video(
            video_number=1,
            topic_category=topic_category,
            duration_minutes=duration_minutes,
            use_web_search=use_web_search
        )


if __name__ == "__main__":
    main()
