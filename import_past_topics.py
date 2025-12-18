"""
Import past topics from existing videos into history
"""
import json
from pathlib import Path
from topic_history import add_topic_to_history

def import_past_topics():
    """Import topics from all existing video outputs"""
    outputs_dir = Path("outputs")

    if not outputs_dir.exists():
        print("No outputs directory found")
        return

    # Find all topic.json files
    topic_files = list(outputs_dir.glob("*/video_*/topic.json"))
    print(f"Found {len(topic_files)} existing videos")

    imported_count = 0
    for topic_file in sorted(topic_files):
        try:
            with open(topic_file, 'r', encoding='utf-8') as f:
                topic = json.load(f)

            # Extract title
            title = topic.get("title", "")
            if not title:
                title = topic.get("selected_topic", {}).get("title", "Unknown")

            # Extract main URL
            url = topic.get("selected_topic", {}).get("url", "")
            if not url:
                # Try to get from source_urls
                urls = topic.get("source_urls", [])
                url = urls[0] if urls else ""

            # Extract source URLs
            source_urls = topic.get("source_urls", [])
            if not source_urls and "all_news_articles" in topic:
                source_urls = [article.get("url", "") for article in topic.get("all_news_articles", [])]

            # Extract date from file path (directory name)
            date_str = topic_file.parent.parent.name  # e.g., "2025-12-13"
            try:
                # Convert to ISO format with time
                from datetime import datetime
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                iso_date = date_obj.isoformat()
            except:
                iso_date = None

            # Add to history
            if title and url:
                add_topic_to_history(
                    title=title,
                    url=url,
                    source_urls=source_urls,
                    date=iso_date
                )
                imported_count += 1
                print(f"  ✓ Imported: {title[:60]}...")
            else:
                print(f"  ✗ Skipped: {topic_file} (missing title or URL)")

        except Exception as e:
            print(f"  ✗ Error importing {topic_file}: {e}")

    print(f"\n✅ Imported {imported_count} topics into history")


if __name__ == "__main__":
    import_past_topics()
