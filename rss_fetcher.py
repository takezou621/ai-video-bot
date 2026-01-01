import os
import feedparser
from typing import List, Dict, Any
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# RSS Feeds List (free sources for AI/Tech news)
RSS_FEEDS = {
    "technology": [
        "https://feeds.feedburner.com/TechCrunch/",
        "https://www.theverge.com/rss/index.xml",
        "https://wired.jp/feed/",
        "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml",
        "https://gizmodo.com/rss"
    ],
    "ai_news": [
        # Corporate AI Blogs (Primary Sources)
        "http://googleaiblog.blogspot.com/atom.xml",  # Google AI
        "https://blogs.microsoft.com/ai/feed/",       # Microsoft AI
        "https://aws.amazon.com/blogs/machine-learning/feed/", # AWS ML
        "https://blogs.nvidia.com/blog/category/deep-learning/feed/", # NVIDIA
        "https://openai.com/news/rss.xml", # OpenAI (If available, otherwise reliant on aggregators)

        # AI Tech News (Speed)
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://venturebeat.com/category/ai/feed/",
        "https://www.theverge.com/rss/artificial-intelligence/index.xml",
        "https://arstechnica.com/tag/ai/feed/",
        "https://www.theregister.com/software/ai_ml/headlines.atom",

        # Research & Deep Dives
        "https://mittr-kokusai.jp/category/ai/feed",
        "https://blog.langchain.dev/rss/",
        "https://simonwillison.net/atom/everything/", # Often covers AI engineering
    ]
}

def fetch_rss_news(category: str = "technology", max_results: int = 15) -> List[Dict[str, Any]]:
    """
    Fetch news from RSS feeds for a specific category.
    
    Args:
        category: The category of news to fetch (technology, ai_news, economics)
        max_results: Maximum number of combined results to return
        
    Returns:
        List of news items standardized for the pipeline
    """
    feeds = RSS_FEEDS.get(category, RSS_FEEDS["technology"])
    
    # If category is "ai_news", also mix in some general tech feeds
    if category == "ai_news":
        feeds = RSS_FEEDS["ai_news"] + RSS_FEEDS["technology"][:2]

    all_entries = []

    print(f"[RSS] Fetching {category} news from {len(feeds)} feeds...")

    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            
            # Identify source name
            source_title = feed.feed.get('title', 'Unknown Source')
            
            for entry in feed.entries[:5]: # Take top 5 from each feed
                # Standardize date
                published_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
                if published_parsed:
                    dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                    date_str = dt.isoformat()
                else:
                    date_str = datetime.now(timezone.utc).isoformat()

                # Basic content extraction
                title = entry.get('title', '')
                link = entry.get('link', '')
                summary = entry.get('summary', '') or entry.get('description', '')
                
                # Simple HTML tag stripping for summary
                import re
                summary = re.sub('<[^<]+?>', '', summary)[:300] + "..."

                item = {
                    "title": title,
                    "snippet": summary,
                    "url": link,
                    "source": source_title,
                    "date": date_str,
                    "is_rss": True
                }
                all_entries.append(item)
                
        except Exception as e:
            print(f"[RSS] Failed to parse {feed_url}: {e}")
            continue

    # Sort by date (newest first)
    all_entries.sort(key=lambda x: x['date'], reverse=True)
    
    # Deduplicate by URL
    seen_urls = set()
    unique_entries = []
    for entry in all_entries:
        if entry['url'] not in seen_urls:
            unique_entries.append(entry)
            seen_urls.add(entry['url'])
            
    print(f"[RSS] Collected {len(unique_entries)} unique items. Returning top {max_results}.")
    return unique_entries[:max_results]

if __name__ == "__main__":
    # Test run
    items = fetch_rss_news("ai_news")
    for i, item in enumerate(items[:3]):
        print(f"{i+1}. {item['title']} ({item['source']})")
        print(f"   {item['url']}")
