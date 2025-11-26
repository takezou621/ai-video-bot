"""
LLM Story Generator - Generates podcast-style dialogue scripts
"""
import os
import json
import requests
from typing import Dict, Any

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


def generate_story(topic: str = None, duration_minutes: int = None) -> Dict[str, Any]:
    """
    Generate a podcast-style dialogue script.

    Args:
        topic: Topic to discuss (if None, generates about nostalgic Japan)
        duration_minutes: Target duration in minutes

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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

        prompt = SYSTEM_PROMPT.format(
            duration_minutes=duration_minutes,
            char_count=char_count,
            dialogue_count=dialogue_count
        )

        if topic:
            prompt += "\n\n" + TOPIC_PROMPT.format(topic=topic)
        else:
            prompt += "\n\nTopic: Interesting facts about daily life in Showa-era Japan (1950s-1980s)"

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
