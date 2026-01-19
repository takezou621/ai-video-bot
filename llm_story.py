"""
LLM Story Generator - Generates podcast-style dialogue scripts
Now supports local LLM via Ollama as primary option
"""
import os
import json
import requests
import re
from typing import Dict, Any, List
from pathlib import Path

# Ollama integration
try:
    from ollama_client import call_ollama, check_ollama_health
    USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"
except ImportError:
    USE_OLLAMA = False
    print("[WARNING] ollama_client not found. Ollama integration disabled.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_DURATION_MINUTES = int(os.getenv("DURATION_MINUTES", "10"))

TEXT_GENERATION_PROMPT = """あなたは日本のニュース台本作家です。
提供された英語のニュースに基づいて、ポッドキャスト形式の対話を作成してください。

**重要ルール:**
1.  **言語**: すべて**日本語**で作成してください。
2.  **カタカナ表記**: 外来語は必ずカタカナで書いてください。（例：「スキル」「コパイロット」「オープンエーアイ」）
3.  **⚠️ 英語禁止**: 台本内に英語の文章や単語を含めないでください
    - 固有名詞（OpenAI, Microsoft等）はカタカナ表記（オープンAI, マイクロソフト）にしてください
    - 技術用語（API, GPU等）はカタカナ表記として使用可
    - 英語のニュース見出しや記事内容は、日本語で要約・解説してください
4.  **フォーマット**: 必ず以下の形式で出力してください。余計な説明は不要です。

Title: [動画タイトル]
A: [話者Aのセリフ]
B: [話者Bのセリフ]
A: [話者Aのセリフ]
...

**ニュースソース:**
{news_articles}

**出力:**
"""

def get_past_topics(max_count: int = 20) -> List[str]:
    """Get past video topics to avoid duplicates."""
    past_topics = []
    outputs_dir = Path(__file__).parent / "outputs"
    if not outputs_dir.exists():
        return past_topics
    for date_dir in sorted(outputs_dir.iterdir(), reverse=True):
        if not date_dir.is_dir(): continue
        for video_dir in date_dir.iterdir():
            if not video_dir.is_dir(): continue
            metadata_file = video_dir / "metadata.json"
            script_file = video_dir / "script.json"
            try:
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        title = metadata.get("youtube_title", "") or metadata.get("title", "")
                        if title: past_topics.append(title)
                elif script_file.exists():
                    with open(script_file, 'r', encoding='utf-8') as f:
                        script = json.load(f)
                        title = script.get("title", "")
                        if title: past_topics.append(title)
            except: continue
            if len(past_topics) >= max_count: return past_topics
    return past_topics

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
    repeats = max(1, duration_minutes)
    for _ in range(repeats):
        for speaker, text in sample_exchanges:
            dialogues.append({"speaker": speaker, "text": text})
    return {
        "title": "昭和ノスタルジー：あの頃の日本",
        "description": "昭和時代の日本の暮らしについて、二人のホストが語り合います。",
        "thumbnail_text": "昭和の記憶",
        "background_prompt": "Cozy Japanese room interior, warm lighting, Lo-fi anime style",
        "dialogues": dialogues
    }

def generate_story(topic: str = None, duration_minutes: int = None, news_articles: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate a podcast-style dialogue script using a robust Text-First approach."""
    duration_minutes = duration_minutes or DEFAULT_DURATION_MINUTES
    if not GEMINI_API_KEY and not USE_OLLAMA:
        return _fallback_story(duration_minutes)

    try:
        articles_text = ""
        if news_articles:
            for article in news_articles[:5]:
                # Convert English to Katakana in article titles and snippets
                try:
                    from english_to_katakana import preprocess_text_for_tts
                    title = preprocess_text_for_tts(article.get('title', ''))
                    snippet = preprocess_text_for_tts(article.get('snippet', ''))
                    articles_text += f"- {title}: {snippet}\n"
                except ImportError:
                    articles_text += f"- {article.get('title', '')}: {article.get('snippet', '')}\n"
        else:
            # Convert English topic to Katakana
            if topic:
                try:
                    from english_to_katakana import preprocess_text_for_tts
                    topic_kana = preprocess_text_for_tts(topic)
                    articles_text = f"トピック: {topic_kana}"
                except ImportError:
                    articles_text = f"Topic: {topic}"
            else:
                articles_text = "トピック: 最新AIトレンド"

        prompt = TEXT_GENERATION_PROMPT.format(news_articles=articles_text)
        print("[LLM] Generating script...")
        text = ""
        if USE_OLLAMA and check_ollama_health():
            text = call_ollama(prompt, max_tokens=4096, temperature=0.7)
        
        if not text: return _fallback_story(duration_minutes)

        print("[LLM] Parsing text...")
        lines = text.strip().split('\n')
        dialogues = []
        title = "AIニュース"
        
        for line in lines:
            line = line.strip()
            if not line: continue
            if line.lower().startswith("title:"):
                title = line[6:].strip()
                continue
            
            # Match A: text, B: text, "A": "text", Speaker A: text
            match = re.match(r'^(?:Speaker\s*)?["\\]?([AB])["\\]?(?:さん)?\s*[:：]\s*(.+)', line, re.IGNORECASE)
            if match:
                speaker = match.group(1).upper()
                content = match.group(2).strip().strip('"').strip("'")
                if content:
                    dialogues.append({"speaker": speaker, "text": content})
                continue
            
            if dialogues and not line.startswith(("{ ", "}", "[", "]")):
                dialogues[-1]["text"] += " " + line.strip().strip('"').strip("'")

        if not dialogues:
            return _fallback_story(duration_minutes)

        return {
            "title": title,
            "description": f"{title}についての解説です。",
            "thumbnail_text": "最新AIニュース",
            "background_prompt": "A cozy Lo-fi anime room with a laptop and warm lighting",
            "dialogues": dialogues
        }
    except Exception as e:
        print(f"Error: {e}")
        return _fallback_story(duration_minutes)
