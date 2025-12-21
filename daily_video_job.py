"""
Daily Video Job - Generates podcast-style videos automatically
"""
import datetime
import json
import os
from pathlib import Path
from dotenv import load_dotenv

BASE = Path(__file__).parent
if (BASE / ".env").exists():
    load_dotenv(BASE / ".env", override=True)

from llm_story import generate_story
from nano_banana_client import generate_image
from tts_generator import generate_dialogue_audio
from video_maker import make_podcast_video

OUT = BASE / "outputs"

def main():
    """Main entry point for video generation"""
import web_search

def main():
    """Main entry point for video generation"""
    today = str(datetime.date.today())
    outdir = OUT / today
    outdir.mkdir(parents=True, exist_ok=True)

    # Get configuration
    duration_minutes = int(os.getenv("DURATION_MINUTES", "2"))
    topic = os.getenv("VIDEO_TOPIC", None)
    use_web_search = os.getenv("USE_WEB_SEARCH", "false").lower() == "true"
    topic_category = os.getenv("TOPIC_CATEGORY", "ai_news")

    print(f"=== Generating {duration_minutes} minute video ===")
    
    news_articles = None
    
    # Fetch News if enabled
    if use_web_search:
        print(f"\n[0/4] Fetching latest news for category: {topic_category}...")
        try:
            if topic_category == "ai_news":
                search_results = web_search.search_latest_ai_news()
            else:
                search_results = web_search.search_trending_topics(topic_category)
            
            if search_results:
                # Select best topic
                selection = web_search.select_topic_with_claude(search_results, duration_minutes)
                if selection:
                    # Update topic and pass articles
                    if not topic:
                        topic = selection.get("title", "")
                    print(f"  Selected Topic: {topic}")
                    news_articles = [selection.get("selected_topic", {})]
                    # Also pass top 3 other results for context
                    news_articles.extend(search_results[:3])
        except Exception as e:
            print(f"  News fetch failed: {e}")

    # Step 1: Generate dialogue script
    print("\n[1/4] Generating dialogue script...")
    story = generate_story(topic=topic, duration_minutes=duration_minutes, news_articles=news_articles)
    print(f"  Title: {story['title']}")
    print(f"  Dialogues: {len(story['dialogues'])} exchanges")

    # Save script
    json.dump(story, open(outdir / "script.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # Step 2: Generate background image
    print("\n[2/4] Generating background image...")
    bg_path = outdir / "background.png"
    bg_prompt = story.get("background_prompt",
        "Cozy Japanese room, Lo-fi anime style, warm lighting, desk with lamp, peaceful atmosphere")
    generate_image(bg_prompt, bg_path)
    print(f"  Background saved: {bg_path}")

    # Step 3: Generate audio with dialogue
    print("\n[3/4] Generating dialogue audio...")
    audio_path = outdir / "dialogue"
    audio_file, timing_data = generate_dialogue_audio(story["dialogues"], audio_path)
    print(f"  Audio saved: {audio_file}")
    print(f"  Timing data: {len(timing_data)} segments")

    # Save timing data
    json.dump(timing_data, open(outdir / "timing.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # Step 4: Create video with subtitles
    print("\n[4/4] Creating video with subtitles...")
    video_path = outdir / "video.mp4"
    make_podcast_video(bg_path, timing_data, audio_file, video_path)

    # Save metadata
    metadata = {
        "title": story["title"],
        "description": story.get("description", ""),
        "thumbnail_text": story.get("thumbnail_text", ""),
        "duration_minutes": duration_minutes,
        "dialogue_count": len(story["dialogues"]),
        "created_at": datetime.datetime.now().isoformat()
    }
    json.dump(metadata, open(outdir / "metadata.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print(f"\n=== Complete! ===")
    print(f"Output: {video_path}")
    return video_path


if __name__ == "__main__":
    main()