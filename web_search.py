"""
Web Search Module - Finds trending topics for video content
Based on the Zenn blog's news discovery approach
Now supports local LLM via Ollama for topic selection
"""
import os
import json
import re
import requests
from typing import List, Dict, Any
from datetime import datetime, timezone
from topic_history import (
    load_topic_history,
    filter_duplicate_topics,
    clean_old_history
)

# RSS Integration
try:
    import rss_fetcher
    USE_RSS_FEED = os.getenv("USE_RSS_FEED", "true").lower() == "true"
except ImportError:
    USE_RSS_FEED = False

# Ollama integration
try:
    from ollama_client import call_ollama, check_ollama_health
    USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"
except ImportError:
    USE_OLLAMA = False
    print("[WARNING] ollama_client not found. Ollama integration disabled.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")  # Google Search API alternative

# High-priority entities that frequently boost CTR when highlighted in titles
NAMED_ENTITY_LIBRARY = [
    {
        "entity": "NVIDIA",
        "aliases": ["NVIDIA", "エヌビディア"],
        "type": "company",
        "priority": 3.0,
    },
    {
        "entity": "OpenAI",
        "aliases": ["OpenAI", "オープンAI", "ChatGPT"],
        "type": "company",
        "priority": 3.0,
    },
    {
        "entity": "Apple",
        "aliases": ["Apple", "アップル", "Apple Vision Pro"],
        "type": "company",
        "priority": 2.5,
    },
    {
        "entity": "Microsoft",
        "aliases": ["Microsoft", "マイクロソフト", "Copilot"],
        "type": "company",
        "priority": 2.5,
    },
    {
        "entity": "Google",
        "aliases": ["Google", "グーグル", "Gemini", "DeepMind"],
        "type": "company",
        "priority": 2.3,
    },
    {
        "entity": "Anthropic",
        "aliases": ["Anthropic", "Claude"],
        "type": "company",
        "priority": 2.2,
    },
    {
        "entity": "Meta",
        "aliases": ["Meta", "メタ", "Facebook", "Llama"],
        "type": "company",
        "priority": 2.0,
    },
    {
        "entity": "Amazon",
        "aliases": ["Amazon", "アマゾン", "AWS"],
        "type": "company",
        "priority": 2.0,
    },
    {
        "entity": "Samsung",
        "aliases": ["Samsung", "サムスン"],
        "type": "company",
        "priority": 1.8,
    },
    {
        "entity": "Perplexity",
        "aliases": ["Perplexity", "Perplexity AI"],
        "type": "company",
        "priority": 2.4,
    },
    {
        "entity": "Stability AI",
        "aliases": ["Stability AI", "Stable Diffusion"],
        "type": "company",
        "priority": 2.1,
    },
    {
        "entity": "Mistral",
        "aliases": ["Mistral", "Mistral AI"],
        "type": "company",
        "priority": 2.0,
    },
    {
        "entity": "Hugging Face",
        "aliases": ["Hugging Face", "HuggingFace"],
        "type": "company",
        "priority": 2.2,
    },
]


def _call_gemini(prompt: str, max_output_tokens: int = 2048, temperature: float = 0.4) -> str:
    """Unified LLM call - tries Ollama first, falls back to Gemini"""

    # Try Ollama first
    if USE_OLLAMA:
        try:
            if check_ollama_health():
                print(f"[LLM] Using Ollama for topic selection")
                return call_ollama(prompt, max_output_tokens, temperature)
            else:
                print("[LLM] Ollama unavailable, falling back to Gemini")
        except Exception as e:
            print(f"[LLM] Ollama failed: {e}, falling back to Gemini")

    # Fallback to Gemini API (original code)
    if not GEMINI_API_KEY:
        raise RuntimeError("Neither Ollama nor GEMINI_API_KEY is available")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens
        }
    }
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini response did not include candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise RuntimeError("Gemini response missing content parts")
    return parts[0].get("text", "")


def search_latest_ai_news(max_results: int = 15) -> List[Dict[str, Any]]:
    """
    Search specifically for latest English AI news to report in Japan
    """
    # 1. Try RSS if enabled (Cost-saving measure)
    if USE_RSS_FEED:
        try:
            rss_results = rss_fetcher.fetch_rss_news("ai_news", max_results=max_results)
            if rss_results:
                print(f"[Search] Using RSS feed for AI news ({len(rss_results)} items)")
                annotated = _annotate_topics_with_entities(rss_results)
                
                # Filter duplicates
                history = load_topic_history()
                history = clean_old_history(history)
                filtered = filter_duplicate_topics(annotated, history)
                return filtered
        except Exception as e:
            print(f"[Search] RSS fetch failed: {e}")

    if not SERPER_API_KEY:
        return _annotate_topics_with_entities(_fallback_topics("technology"))

    try:
        url = "https://google.serper.dev/news"
        
        # Specific query for AI news from reputable sources
        query = 'artificial intelligence news "AI model" OR "LLM" OR "OpenAI" OR "Google DeepMind" OR "Anthropic" -site:youtube.com'
        
        payload = {
            "q": query,
            "gl": "us", # Search US news
            "hl": "en", # English results
            "num": max_results,
            "tbm": "nws"
        }

        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data = response.json()
        news_items = data.get("news", [])

        results = []
        for item in news_items:
            # Filter out very short snippets or irrelevant sources if needed
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("link", ""),
                "source": item.get("source", "Unknown Source"), # Keep source name
                "date": item.get("date", ""),
                "is_english": True # Marker for translation needs
            })

        results = _annotate_topics_with_entities(results)
        print(f"Found {len(results)} latest AI news topics (US)")

        # Filter out duplicate topics based on history
        history = load_topic_history()
        history = clean_old_history(history)
        filtered_results = filter_duplicate_topics(results, history)
        print(f"After filtering duplicates: {len(filtered_results)} unique topics")

        return filtered_results

    except Exception as e:
        print(f"AI News Search failed: {e}")
        return _annotate_topics_with_entities(_fallback_topics("technology"))


def search_trending_topics(
    topic_category: str = "economics",
    region: str = "jp",
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for trending topics using Serper API (Google Search) or RSS
    """
    # 1. Try RSS if enabled (Cost-saving measure)
    if USE_RSS_FEED:
        try:
            rss_results = rss_fetcher.fetch_rss_news(topic_category, max_results=max_results)
            if rss_results:
                print(f"[Search] Using RSS feed for {topic_category} ({len(rss_results)} items)")
                return _annotate_topics_with_entities(rss_results)
        except Exception as e:
            print(f"[Search] RSS fetch failed: {e}")

    if not SERPER_API_KEY:
        return _annotate_topics_with_entities(_fallback_topics(topic_category))

    try:
        url = "https://google.serper.dev/news"

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
        news_items = data.get("news", [])
        if not news_items and "organic" in data:
            news_items = data.get("organic", [])

        results = []
        for item in news_items[:max_results]:
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("link", ""),
                "source": item.get("source", ""),
                "date": item.get("date", ""),
            })

        results = _annotate_topics_with_entities(results)
        print(f"Found {len(results)} trending topics in {topic_category}")
        return results

    except Exception as e:
        print(f"Search failed: {e}, using fallback topics")
        return _annotate_topics_with_entities(_fallback_topics(topic_category))


def select_topic(
    search_results: List[Dict[str, Any]],
    target_duration_minutes: int = 10,
    topic_category: str = "economics"
) -> Dict[str, Any]:
    """
    Use Gemini to select and analyze the best topic from search results
    (Same structure as the blog's "Prompt A: Web search for current news")

    Args:
        search_results: List of topics from search
        target_duration_minutes: Target video duration
        topic_category: Category for context (economics, ai_news, etc.)

    Returns:
        Selected topic with analysis

    Note:
        This function was previously named select_topic_with_claude for backward compatibility.
    """
    if not GEMINI_API_KEY:
        # Return first topic if no Gemini API
        if search_results:
            top = search_results[0]
            return {
                "selected_topic": top,
                "angle": "最新のトレンドについて解説",
                "key_points": ["概要", "背景", "影響"],
                "named_entities": top.get("named_entities", [])
            }
        return _fallback_selected_topic(topic_category)

    try:
        # Load past topics for semantic de-duplication
        history_dict = load_topic_history()
        history = history_dict.get("topics", [])
        # Extract just the titles/urls to check against
        past_topics_list = [h.get("title", "") for h in history[:30]]
        past_topics_text = "\n".join([f"- {t}" for t in past_topics_list])

        # Format search results for Gemini
        topics_text = "\n\n".join([
            _format_topic_for_prompt(i, t)
            for i, t in enumerate(search_results[:10])
        ])

        prompt = f"""あなたは日本のYouTube視聴者向けに、{topic_category}トピックを選定するエディターです。

以下の最新ニュースから、約{target_duration_minutes}分の対話形式動画に最適なトピックを1つ選び、分析してください。

# ⚠️ 重複チェック（厳守）
以下のトピックは過去に動画化済みです。これらと「内容が重複する」ニュースは絶対に選ばないでください。
ただし、**「同じ企業（例: OpenAI, Apple, Disney）」であっても、「全く新しいニュース」であれば選択して構いません。**
「ニュースの中身」が新しいかどうかで判断してください。

過去のトピック:
{past_topics_text}

# 検索結果（ここから選んでください）:
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

        content = _call_gemini(prompt, max_output_tokens=2048, temperature=0.2)

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
            selected_topic = search_results[selected_idx]
        else:
            selected_topic = search_results[0] if search_results else {}

        analysis["selected_topic"] = selected_topic

        # Carry named-entity information downstream for metadata/title modules
        entity_info = selected_topic.get("named_entities") if selected_topic else None
        if entity_info:
            analysis["named_entities"] = entity_info

        print(f"Selected topic: {analysis.get('title', 'Unknown')}")
        return analysis

    except Exception as e:
        print(f"Topic selection failed: {e}")
        if search_results:
            fallback = search_results[0]
            return {
                "selected_topic": fallback,
                "title": fallback["title"],
                "angle": "最新のトレンドについて解説",
                "key_points": ["概要", "背景", "影響"],
                "named_entities": fallback.get("named_entities", [])
            }
        return _fallback_selected_topic(topic_category)


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


def _annotate_topics_with_entities(topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    annotated = []
    for topic in topics:
        text_parts = [topic.get("title", ""), topic.get("snippet", "")]
        entities = _extract_entities(" ".join(text_parts))
        topic_copy = dict(topic)
        topic_copy["named_entities"] = entities
        topic_copy["entity_score"] = sum(e["priority"] for e in entities)
        topic_copy["freshness_score"] = _calculate_freshness(topic.get("date"))
        topic_copy["priority_score"] = topic_copy["entity_score"] + topic_copy["freshness_score"]
        annotated.append(topic_copy)
    annotated.sort(key=lambda item: item.get("priority_score", 0), reverse=True)
    return annotated


def _extract_entities(text: str) -> List[Dict[str, Any]]:
    entities = []
    normalized_text = text or ""
    for entity_config in NAMED_ENTITY_LIBRARY:
        for alias in entity_config["aliases"]:
            if alias and re.search(re.escape(alias), normalized_text, re.IGNORECASE):
                entities.append({
                    "label": entity_config["entity"],
                    "alias": alias,
                    "type": entity_config["type"],
                    "priority": entity_config["priority"],
                })
                break
    return entities


def _calculate_freshness(date_str: str) -> float:
    if not date_str:
        return 0.0
    try:
        parsed_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            return 0.0
    if not parsed_date.tzinfo:
        parsed_date = parsed_date.replace(tzinfo=timezone.utc)
    delta_hours = (datetime.now(timezone.utc) - parsed_date).total_seconds() / 3600
    if delta_hours <= 0:
        return 1.0
    return max(0.0, 1.0 - min(delta_hours / 168.0, 1.0))  # decay over 7 days


def _format_topic_for_prompt(index: int, topic: Dict[str, Any]) -> str:
    entities = topic.get("named_entities", [])
    entity_text = ", ".join(e["label"] for e in entities) if entities else "(no notable entities)"
    return (
        f"Topic {index + 1}:\n"
        f"Title: {topic.get('title', '')}\n"
        f"Snippet: {topic.get('snippet', '')}\n"
        f"Source: {topic.get('source', '')}\n"
        f"Entities: {entity_text}\n"
        f"Priority Score: {topic.get('priority_score', 0):.2f}\n"
    )


def _fallback_selected_topic(category: str = "economics") -> Dict[str, Any]:
    """Fallback selected topic based on category"""
    
    if category in ["ai_news", "technology"]:
        return {
            "title": "人工知能の歴史と未来予測",
            "angle": "AIがどのように進化し、これからどこへ向かうのか",
            "key_points": [
                "AIの誕生と冬の時代",
                "ディープラーニングの登場",
                "生成AIとシンギュラリティ"
            ],
            "selected_topic": {
                "title": "AIの歴史と進化",
                "snippet": "AI技術の発展の歴史と将来展望についての解説",
                "url": "",
                "source": "Fallback",
                "date": datetime.now().isoformat(),
            },
            "named_entities": [{"label": "AI"}, {"label": "Future"}]
        }
    
    # Default Economics fallback
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
        },
        "named_entities": []
    }


# Backward compatibility alias (function was previously named select_topic_with_claude)
select_topic_with_claude = select_topic


if __name__ == "__main__":
    # Test
    results = search_trending_topics("economics")
    print(f"\nFound {len(results)} topics")

    if results:
        selected = select_topic(results, target_duration_minutes=10)
        print(f"\nSelected: {selected.get('title', 'Unknown')}")
        print(f"Angle: {selected.get('angle', 'N/A')}")
