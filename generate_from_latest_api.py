
import os
import sys
from podcast_api import fetch_podcasts
from advanced_video_pipeline import generate_single_video

# Configuration
os.environ["PODCAST_API_ENABLED"] = "true"
# Ensure we use the local voicevox URL
os.environ["VOICEVOX_URL"] = "http://localhost:50021"

def main():
    print("Fetching latest podcast from API...")
    try:
        # User requested the latest data (limit=1 is sufficient since order is id.desc)
        podcasts = fetch_podcasts(limit=1, order="id.desc")
        
        if not podcasts:
            print("No podcasts found.")
            return

        latest_podcast = podcasts[0]
        print(f"Found latest podcast: ID={latest_podcast.get('id')} Date={latest_podcast.get('date')}")
        print(f"Title: {latest_podcast.get('youtube_title')}")
        
        # Parse scenario to ensure valid dialogues before processing
        from podcast_api import parse_podcast_scenario
        dialogues = parse_podcast_scenario(latest_podcast.get("podcast_scenario", ""))
        
        if not dialogues:
            print("❌ Error: No valid dialogues found in the scenario.")
            return
            
        # Enrich the data object with parsed dialogues if not present
        latest_podcast["dialogues"] = dialogues
        
        print(f"Starting video generation for ID={latest_podcast.get('id')}...")
        
        # Execute generation
        generate_single_video(
            video_number=1,
            topic_category="ai_news",
            duration_minutes=10,
            use_web_search=False,
            podcast_api_data=latest_podcast
        )
        print("✅ Video generation process completed.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
