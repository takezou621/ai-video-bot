"""
Web Search Module - Finds trending topics for video content
Based on the Zenn blog's news discovery approach
"""
import os
import json
import requests
from typing import List, Dict, Any
from datetime import datetime

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")  # Google Search API alternative


def search_trending_topics(
    topic_category: str = "economics",
    region: str = "jp",
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for trending topics using Serper API (Google Search)

    Args:
        topic_category: Category to search (economics, technology, etc.)
        region: Region code (jp, us, etc.)
        max_results: Maximum number of results

    Returns:
        List of trending topics with titles, snippets, and URLs
    """
    if not SERPER_API_KEY:
        return _fallback_topics(topic_category)

    try:
        url = "https://google.serper.dev/search"

        # Build search query
        queries = {
            "economics": "最新 経済ニュース OR 注目の経済トピック",
            "technology": "最新 テクノロジー ニュース",
            "culture": "話題のカルチャー トレンド",
            "lifestyle": "ライフスタイル トレンド",
        }

        query = queries.get(topic_category, "最新ニュース トレンド")

        payload = {
            "q": query,
            "gl": region,
            "hl": "ja",
            "num": max_results,
            "tbm": "nws"  # News search
        }

        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data = response.json()

        # Parse results
        results = []
        for item in data.get("news", [])[:max_results]:
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("link", ""),
                "source": item.get("source", ""),
                "date": item.get("date", ""),
            })

        print(f"Found {len(results)} trending topics in {topic_category}")
        return results

    except Exception as e:
        print(f"Search failed: {e}, using fallback topics")
        return _fallback_topics(topic_category)


def select_topic_with_claude(
    search_results: List[Dict[str, Any]],
    target_duration_minutes: int = 10
) -> Dict[str, Any]:
    """
    Use Claude to select and analyze the best topic from search results
    (Similar to the blog's "Prompt A: Web search for current news")

    Args:
        search_results: List of topics from search
        target_duration_minutes: Target video duration

    Returns:
        Selected topic with analysis
    """
    if not CLAUDE_API_KEY:
        # Return first topic if no Claude API
        if search_results:
            return {
                "selected_topic": search_results[0],
                "angle": "最新のトレンドについて解説",
                "key_points": ["概要", "背景", "影響"],
            }
        return _fallback_selected_topic()

    try:
        # Format search results for Claude
        topics_text = "\n\n".join([
            f"Topic {i+1}:\nTitle: {t['title']}\nSnippet: {t['snippet']}\nSource: {t['source']}"
            for i, t in enumerate(search_results[:10])
        ])

        prompt = f"""あなたは日本のYouTube視聴者向けに、経済・ビジネストピックを選定するエディターです。

以下の最新ニュースから、約{target_duration_minutes}分の対話形式動画に最適なトピックを1つ選び、分析してください。

検索結果:
{topics_text}

以下のJSON形式で出力してください:
{{
  "selected_index": 選んだトピックの番号 (1-10),
  "title": "動画タイトル (興味を引く表現で)",
  "angle": "このトピックを扱う切り口・視点",
  "key_points": ["重要ポイント1", "重要ポイント2", "重要ポイント3"],
  "why_interesting": "なぜこのトピックが視聴者に刺さるか",
  "target_audience": "想定視聴者層"
}}

JSONのみを出力してください。"""

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(url, json=payload, headers=headers, timeout=60)
        data = response.json()

        content = data["content"][0]["text"]

        # Extract JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        content = content.strip()
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            content = content[start:end]

        analysis = json.loads(content)

        # Add the selected topic data
        selected_idx = analysis.get("selected_index", 1) - 1
        if 0 <= selected_idx < len(search_results):
            analysis["selected_topic"] = search_results[selected_idx]
        else:
            analysis["selected_topic"] = search_results[0] if search_results else {}

        print(f"Selected topic: {analysis.get('title', 'Unknown')}")
        return analysis

    except Exception as e:
        print(f"Topic selection failed: {e}")
        if search_results:
            return {
                "selected_topic": search_results[0],
                "title": search_results[0]["title"],
                "angle": "最新のトレンドについて解説",
                "key_points": ["概要", "背景", "影響"],
            }
        return _fallback_selected_topic()


def _fallback_topics(category: str) -> List[Dict[str, Any]]:
    """Fallback topics when search is unavailable"""
    topics_by_category = {
        "economics": [
            {
                "title": "日本の経済成長率と今後の見通し",
                "snippet": "最新の経済指標から見る日本経済の現状と課題",
                "url": "",
                "source": "Fallback",
                "date": datetime.now().isoformat(),
            },
            {
                "title": "円相場の動向と私たちの生活への影響",
                "snippet": "為替レートの変動が日常生活に与える影響を解説",
                "url": "",
                "source": "Fallback",
                "date": datetime.now().isoformat(),
            },
        ],
        "technology": [
            {
                "title": "AI技術の最新動向",
                "snippet": "生成AIの進化と社会への影響",
                "url": "",
                "source": "Fallback",
                "date": datetime.now().isoformat(),
            },
        ],
    }

    return topics_by_category.get(category, topics_by_category["economics"])


def _fallback_selected_topic() -> Dict[str, Any]:
    """Fallback selected topic"""
    return {
        "title": "昭和時代の日本経済と暮らし",
        "angle": "高度経済成長期の人々の生活を振り返る",
        "key_points": [
            "経済成長と生活水準の向上",
            "家族の在り方の変化",
            "技術革新と日常生活"
        ],
        "selected_topic": {
            "title": "昭和ノスタルジー",
            "snippet": "昭和時代の日本について",
            "url": "",
            "source": "Fallback",
            "date": datetime.now().isoformat(),
        }
    }


if __name__ == "__main__":
    # Test
    results = search_trending_topics("economics")
    print(f"\nFound {len(results)} topics")

    if results:
        selected = select_topic_with_claude(results, target_duration_minutes=10)
        print(f"\nSelected: {selected.get('title', 'Unknown')}")
        print(f"Angle: {selected.get('angle', 'N/A')}")
