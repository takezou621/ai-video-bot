import os
import rss_fetcher
from web_search import search_latest_ai_news

# Mock env
os.environ["USE_RSS_FEED"] = "true"

def test_rss():
    print("Testing RSS Feed Integration...")
    
    # Test 1: Direct Fetch
    print("\n1. Direct Fetch Test (AI News):")
    items = rss_fetcher.fetch_rss_news("ai_news", max_results=3)
    if items:
        for i, item in enumerate(items):
            print(f"   [{i+1}] {item['title']} - {item['source']}")
            print(f"       {item['date']}")
        print("✅ Direct RSS fetch successful")
    else:
        print("❌ Direct RSS fetch returned no items")

    # Test 2: Integration via web_search
    print("\n2. Integration Test (search_latest_ai_news):")
    results = search_latest_ai_news(max_results=3)
    if results and results[0].get("is_rss"):
        print(f"✅ Integrated search returned {len(results)} items from RSS")
        print(f"   Top item: {results[0]['title']}")
    else:
        print("❌ Integrated search did not return RSS items (or fallback was used)")

if __name__ == "__main__":
    test_rss()
