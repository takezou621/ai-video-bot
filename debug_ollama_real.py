import os
import json
import web_search
from ollama_client import call_ollama

# Use real news fetching logic
print("Fetching real news...")
try:
    news_results = web_search.search_latest_ai_news(max_results=5)
    articles_text = ""
    for i, article in enumerate(news_results[:5]):
        articles_text += f"- {article.get('title', '')}: {article.get('snippet', '')}\n"
except Exception as e:
    print(f"News fetch failed: {e}")
    articles_text = "Mock news for fallback..."

DEFAULT_DURATION_MINUTES = 1
char_count = DEFAULT_DURATION_MINUTES * 300
dialogue_count = DEFAULT_DURATION_MINUTES * 6

SYSTEM_PROMPT = """You are a specialized JSON generator for a Japanese AI news podcast.
Your ONLY task is to output a valid JSON object based on the provided news.
Do NOT output explanations, markdown backticks, or intro text. JUST THE JSON.

Output Content Rules:
1.  **Language**: All text values (title, description, dialogues) MUST be in **natural JAPANESE** (Kanji/Kana). No English script.
2.  **Content**: Summarize the provided English news into a dialogue between Speaker A (Host) and Speaker B (Assistant).
3.  **Format**: Strictly follow this JSON structure. Escape all double quotes inside strings (e.g., \"text\").

JSON Structure Example:
{
  "title": "最新AIニュース：Geminiの進化",
  "description": "Googleの新しいAIモデルについて解説します。",
  "thumbnail_text": "Gemini速報",
  "background_prompt": "A lo-fi anime style room with a cat",
  "dialogues": [
    {"speaker": "A", "text": "こんにちは。今回はGoogleのGeminiについて話しましょう。"},
    {"speaker": "B", "text": "へえ、どんな機能が追加されたんですか？"},
    {"speaker": "A", "text": "推論能力が大幅に向上したそうです。"}
  ]
}
"""

AI_NEWS_SUMMARY_PROMPT = """SOURCE NEWS (English):
{news_articles}

INSTRUCTIONS:
- Select key topics from the news above.
- Create a script in JAPANESE explaining them.
- Speaker A explains, Speaker B reacts.
- Duration: approx {duration_minutes} mins ({dialogue_count} exchanges).
- Ensure valid JSON format.
"""

user_content = AI_NEWS_SUMMARY_PROMPT.format(
    news_articles=articles_text,
    duration_minutes=DEFAULT_DURATION_MINUTES,
    dialogue_count=dialogue_count
)

print("\n--- Sending Request to Ollama (Real News) ---")
try:
    # Testing with slightly higher temp to avoid empty strings
    response = call_ollama(user_content, max_tokens=4096, temperature=0.7, system_prompt=SYSTEM_PROMPT)
    print("\n--- RAW OLLAMA RESPONSE START ---")
    print(response)
    print("--- RAW OLLAMA RESPONSE END ---\n")
    
    try:
        data = json.loads(response)
        print("✅ JSON Parse Successful.")
        # Check for empty text
        if not data.get('dialogues') or not data['dialogues'][0]['text']:
             print("❌ Content is empty.")
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Failed: {e}")

except Exception as e:
    print(f"Ollama call failed: {e}")
