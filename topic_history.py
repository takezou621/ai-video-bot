"""
Topic History Manager - Prevents duplicate topic selection
"""
import json
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime, timedelta

HISTORY_FILE = Path("outputs/history/used_topics.json")
HISTORY_DAYS = 30  # Keep history for 30 days


def load_topic_history() -> Dict:
    """Load topic history from JSON file"""
    if not HISTORY_FILE.exists():
        return {"topics": []}

    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load topic history: {e}")
        return {"topics": []}


def save_topic_history(history: Dict):
    """Save topic history to JSON file"""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save topic history: {e}")


def clean_old_history(history: Dict, days: int = HISTORY_DAYS) -> Dict:
    """Remove topics older than specified days"""
    cutoff_date = datetime.now() - timedelta(days=days)

    cleaned_topics = []
    for topic in history.get("topics", []):
        try:
            topic_date = datetime.fromisoformat(topic.get("date", ""))
            if topic_date >= cutoff_date:
                cleaned_topics.append(topic)
        except:
            # Keep if date parsing fails (fallback)
            cleaned_topics.append(topic)

    history["topics"] = cleaned_topics
    return history


def get_used_urls(history: Dict) -> Set[str]:
    """Extract all used URLs from history"""
    urls = set()
    for topic in history.get("topics", []):
        # Add selected topic URL
        if "url" in topic:
            urls.add(topic["url"])

        # Add all source URLs
        for url in topic.get("source_urls", []):
            urls.add(url)

    return urls


def get_used_titles(history: Dict) -> Set[str]:
    """Extract all used titles from history (normalized)"""
    titles = set()
    for topic in history.get("topics", []):
        if "title" in topic:
            # Normalize title: remove punctuation, lowercase
            normalized = topic["title"].lower()
            titles.add(normalized)

    return titles


def is_duplicate_topic(new_url: str, new_title: str, history: Dict) -> bool:
    """
    Check if a topic is a duplicate based on URL or title similarity

    Args:
        new_url: URL of the new topic
        new_title: Title of the new topic
        history: Topic history dict

    Returns:
        True if duplicate, False otherwise
    """
    used_urls = get_used_urls(history)
    used_titles = get_used_titles(history)

    # Check URL match
    if new_url in used_urls:
        return True

    # Check title similarity (simple keyword overlap)
    new_title_normalized = new_title.lower()
    for used_title in used_titles:
        # Extract keywords (simple split by space, filter short words)
        new_keywords = set(w for w in new_title_normalized.split() if len(w) > 3)
        used_keywords = set(w for w in used_title.split() if len(w) > 3)

        # If 70%+ keywords overlap, consider duplicate
        if new_keywords and used_keywords:
            overlap = len(new_keywords & used_keywords)
            similarity = overlap / min(len(new_keywords), len(used_keywords))
            if similarity > 0.7:
                return True

    return False


def filter_duplicate_topics(topics: List[Dict], history: Dict) -> List[Dict]:
    """
    Filter out duplicate topics from a list

    Args:
        topics: List of topic dictionaries (each with 'url' and 'title')
        history: Topic history dict

    Returns:
        Filtered list of non-duplicate topics
    """
    filtered = []
    for topic in topics:
        url = topic.get("url", "")
        title = topic.get("title", "")

        if not is_duplicate_topic(url, title, history):
            filtered.append(topic)
        else:
            print(f"  Skipping duplicate topic: {title[:50]}...")

    return filtered


def add_topic_to_history(
    title: str,
    url: str,
    source_urls: List[str] = None,
    date: str = None
):
    """
    Add a new topic to history

    Args:
        title: Topic title
        url: Main topic URL
        source_urls: List of source URLs used in the video
        date: ISO format date string (defaults to now)
    """
    history = load_topic_history()

    # Clean old entries
    history = clean_old_history(history)

    # Add new topic
    new_topic = {
        "title": title,
        "url": url,
        "source_urls": source_urls or [],
        "date": date or datetime.now().isoformat()
    }

    history["topics"].append(new_topic)

    save_topic_history(history)
    print(f"  Added topic to history: {title[:50]}...")


if __name__ == "__main__":
    # Test the module
    print("Topic History Manager - Test")
    print("=" * 50)

    # Load history
    history = load_topic_history()
    print(f"Loaded {len(history.get('topics', []))} topics from history")

    # Show used URLs
    used_urls = get_used_urls(history)
    print(f"\nUsed URLs ({len(used_urls)}):")
    for url in list(used_urls)[:5]:
        print(f"  - {url}")

    # Show used titles
    used_titles = get_used_titles(history)
    print(f"\nUsed Titles ({len(used_titles)}):")
    for title in list(used_titles)[:5]:
        print(f"  - {title}")
