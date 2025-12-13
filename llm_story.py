"""
LLM Story Generator - Generates podcast-style dialogue scripts
"""
import os
import json
import requests
from typing import Dict, Any, List
from pathlib import Path

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_DURATION_MINUTES = int(os.getenv("DURATION_MINUTES", "10"))

SYSTEM_PROMPT = """You are creating a podcast-style dialogue script about news or interesting topics.
The dialogue is between two hosts:
- Speaker A: The main host who explains topics clearly
- Speaker B: The co-host who asks questions and adds insights

Output in this exact JSON format:
{{
  "title": "Japanese title for the video",
  "description": "Brief description in Japanese for YouTube",
  "thumbnail_text": "Short catchy text for thumbnail (max 10 chars in Japanese)",
  "background_prompt": "Single background image prompt in English, Lo-fi anime style, cozy room with warm lighting",
  "dialogues": [
    {{"speaker": "A", "text": "Japanese dialogue line"}},
    {{"speaker": "B", "text": "Japanese dialogue line"}},
    ...
  ]
}}

Rules:
- Total dialogue should be approximately {duration_minutes} minutes when read aloud (about {char_count} characters total)
- Dialogue must be in natural conversational Japanese
- Speaker A explains, Speaker B asks follow-up questions or adds commentary
- Include about {dialogue_count} dialogue exchanges
- Make it engaging and educational
- Background prompt should be a cozy, Lo-fi Girl inspired anime scene
- Output ONLY valid JSON, no other text
"""

TOPIC_PROMPT = """Create an engaging podcast dialogue about: {topic}

The content should be informative yet conversational, like a friendly discussion between two knowledgeable hosts."""

AI_NEWS_SUMMARY_PROMPT = """You are creating a Japanese podcast about the LATEST international AI news.

CONTEXT: You have {news_count} recent English AI news articles. Your job is to:
1. Select 3-5 most important/interesting news items
2. Explain them clearly in Japanese for general audience
3. Add context and implications for Japan/listeners

NEWS ARTICLES:
{news_articles}

Create an engaging dialogue that:
- Opens with a hook about the AI industry trends
- Discusses each selected news item in detail with:
  * What happened (translate key facts)
  * Why it matters
  * Impact on industry/society
  * Japanese perspective when relevant
- Closes with takeaways and future outlook

Speaker A: Main host who explains news clearly
Speaker B: Co-host who asks questions, adds reactions

Make it informative yet accessible. Translate technical terms but keep original company/product names in English."""


def get_past_topics(max_count: int = 20) -> List[str]:
    """
    Get past video topics to avoid duplicates.

    Args:
        max_count: Maximum number of past topics to retrieve

    Returns:
        List of past topic titles
    """
    past_topics = []
    outputs_dir = Path(__file__).parent / "outputs"

    if not outputs_dir.exists():
        return past_topics

    # Scan all date directories
    for date_dir in sorted(outputs_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue

        # Scan all video directories
        for video_dir in date_dir.iterdir():
            if not video_dir.is_dir():
                continue

            # Try to read metadata or script
            metadata_file = video_dir / "metadata.json"
            script_file = video_dir / "script.json"

            try:
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        title = metadata.get("youtube_title", "")
                        if title:
                            past_topics.append(title)
                elif script_file.exists():
                    with open(script_file, 'r', encoding='utf-8') as f:
                        script = json.load(f)
                        title = script.get("title", "")
                        if title:
                            past_topics.append(title)
            except Exception as e:
                # Skip if file is corrupted
                continue

            if len(past_topics) >= max_count:
                return past_topics

    return past_topics


def generate_story(topic: str = None, duration_minutes: int = None, news_articles: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate a podcast-style dialogue script.

    Args:
        topic: Topic to discuss (if None, generates about nostalgic Japan)
        duration_minutes: Target duration in minutes
        news_articles: List of news articles for AI news summary mode

    Returns:
        Dictionary with title, dialogues, and metadata
    """
    duration_minutes = duration_minutes or DEFAULT_DURATION_MINUTES

    # Estimate: ~300 chars/minute for natural Japanese speech
    char_count = duration_minutes * 300
    dialogue_count = duration_minutes * 6  # ~6 exchanges per minute

    if not GEMINI_API_KEY:
        return _fallback_story(duration_minutes)

    try:
        # Get past topics to avoid duplicates
        past_topics = get_past_topics(max_count=20)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

        prompt = SYSTEM_PROMPT.format(
            duration_minutes=duration_minutes,
            char_count=char_count,
            dialogue_count=dialogue_count
        )

        # Add duplicate avoidance instruction
        if past_topics:
            prompt += "\n\nIMPORTANT: Avoid topics similar to these past videos:\n"
            for i, past_topic in enumerate(past_topics[:10], 1):
                prompt += f"{i}. {past_topic}\n"
            prompt += "\nCreate a COMPLETELY DIFFERENT topic that has not been covered before.\n"

        if news_articles:
            # AI News Summary mode - format articles for prompt
            articles_text = ""
            for i, article in enumerate(news_articles[:10], 1):
                articles_text += f"\n[Article {i}]\n"
                articles_text += f"Title: {article.get('title', '')}\n"
                articles_text += f"Content: {article.get('snippet', '')}\n"
                articles_text += f"Source: {article.get('source', '')}\n"
                articles_text += f"URL: {article.get('url', '')}\n"

            prompt += "\n\n" + AI_NEWS_SUMMARY_PROMPT.format(
                news_count=len(news_articles),
                news_articles=articles_text
            )
        elif topic:
            prompt += "\n\n" + TOPIC_PROMPT.format(topic=topic)
        else:
            # Generate diverse topics instead of always "Showa-era Japan"
            topic_categories = os.getenv("TOPIC_CATEGORY", "economics")
            prompt += f"\n\nTopic: Create an engaging topic about {topic_categories} in Japan. "
            prompt += "Choose from diverse themes like: modern economy, technology trends, business innovation, "
            prompt += "financial literacy, startup culture, work culture, industry analysis, consumer trends, etc. "
            prompt += "Make it current, relevant, and different from past topics."

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.9, "maxOutputTokens": 8192}
        }

        r = requests.post(url, json=payload, timeout=120)
        data = r.json()

        if "error" in data:
            print(f"Gemini API Error: {data['error']}")
            return _fallback_story(duration_minutes)

        text = data["candidates"][0]["content"]["parts"][0]["text"]

        # Extract JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        text = text.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]

        story = json.loads(text)
        print(f"Generated story: {story['title']} ({len(story['dialogues'])} dialogues)")
        return story

    except Exception as e:
        print(f"Story generation error: {e}")
        return _fallback_story(duration_minutes)


def _fallback_story(duration_minutes: int) -> Dict[str, Any]:
    """Fallback story when API is unavailable"""
    dialogues = []

    sample_exchanges = [
        ("A", "皆さん、こんにちは。今日は昭和時代の日本について話していきましょう。"),
        ("B", "昭和時代って、今とは全然違う雰囲気だったんですよね。"),
        ("A", "そうなんです。特に昭和50年代は、高度経済成長が終わって、日本が成熟していく時期でした。"),
        ("B", "駄菓子屋とか、今ではほとんど見かけなくなりましたよね。"),
        ("A", "駄菓子屋は子供たちの社交場でした。十円玉を握りしめて、何を買おうか悩む時間が楽しかったんです。"),
        ("B", "今の子供たちにはない体験ですね。他にはどんな特徴がありましたか？"),
        ("A", "テレビが家族の中心でした。みんなで同じ番組を見て、翌日学校で話題にする。"),
        ("B", "インターネットもスマホもない時代だからこそ、共通の話題があったんですね。"),
        ("A", "その通りです。時代は変わりましたが、あの頃の温かさは今でも大切にしたいものです。"),
        ("B", "素敵なお話でした。また次回もよろしくお願いします。"),
    ]

    # Repeat to fill duration
    repeats = max(1, duration_minutes)
    for _ in range(repeats):
        for speaker, text in sample_exchanges:
            dialogues.append({"speaker": speaker, "text": text})

    return {
        "title": "昭和ノスタルジー：あの頃の日本",
        "description": "昭和時代の日本の暮らしについて、二人のホストが語り合います。",
        "thumbnail_text": "昭和の記憶",
        "background_prompt": "Cozy Japanese room interior, warm lighting, Lo-fi anime style, desk with lamp, window showing sunset, potted plants, books on shelf, peaceful atmosphere, soft colors",
        "dialogues": dialogues
    }
