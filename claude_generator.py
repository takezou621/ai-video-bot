"""
Claude API Integration - Multi-stage content generation
Based on the Zenn blog's approach using Claude Opus and Sonnet
"""
import os
import json
import requests
from typing import Dict, Any, List

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")


def generate_dialogue_script_with_claude(
    topic_analysis: Dict[str, Any],
    duration_minutes: int = 10
) -> Dict[str, Any]:
    """
    Generate podcast-style dialogue using Claude Opus
    (Blog's "Prompt B: Generate dialogue script")

    Args:
        topic_analysis: Topic analysis from web search
        duration_minutes: Target duration in minutes

    Returns:
        Dialogue script with metadata
    """
    if not CLAUDE_API_KEY:
        print("Claude API key not found, using Gemini fallback")
        from llm_story import generate_story
        topic_text = topic_analysis.get("title", "")
        return generate_story(topic=topic_text, duration_minutes=duration_minutes)

    try:
        # Estimate content length (Japanese: ~300 chars/minute for natural speech)
        char_count = duration_minutes * 300
        dialogue_count = duration_minutes * 6  # ~6 exchanges per minute

        # Get topic details
        title = topic_analysis.get("title", "")
        angle = topic_analysis.get("angle", "")
        key_points = topic_analysis.get("key_points", [])
        selected_topic = topic_analysis.get("selected_topic", {})
        snippet = selected_topic.get("snippet", "")

        prompt = f"""あなたは日本のYouTube向けに、経済・ビジネストピックを解説する対話形式ポッドキャストの台本を作成します。

# トピック情報
タイトル: {title}
切り口: {angle}
重要ポイント: {', '.join(key_points)}
詳細: {snippet}

# 台本要件
- 対話形式: Speaker A（メインホスト、分かりやすく説明）とSpeaker B（サブホスト、質問や補足コメント）
- 全体で約{duration_minutes}分（音声にすると、合計約{char_count}文字程度）
- 対話交換回数: 約{dialogue_count}回
- 言葉遣い: 自然な会話調の日本語
- 構成: イントロ → メイン解説 → まとめ
- 視聴者: ビジネスパーソン、経済に興味がある一般層
- スタイル: 教育的だが堅苦しくない、親しみやすい

# 台本スタイル
- Speaker Aが主に説明、Speaker Bが疑問や驚き、共感を表現
- 専門用語は分かりやすく噛み砕く
- 具体例や比喩を使って理解しやすく
- 視聴者が「なるほど！」と思える気づきを提供

以下のJSON形式で出力してください:
{{
  "title": "動画タイトル（SEOを意識した魅力的な表現）",
  "description": "YouTube用説明文（2-3文、150文字以内）",
  "thumbnail_text": "サムネイル用短文（10文字以内）",
  "background_prompt": "Lo-fi anime style background image prompt in English (cozy room, warm lighting, desk setup)",
  "dialogues": [
    {{"speaker": "A", "text": "対話内容1"}},
    {{"speaker": "B", "text": "対話内容2"}},
    ...
  ],
  "tags": ["タグ1", "タグ2", "タグ3", "タグ4", "タグ5"]
}}

JSONのみを出力してください。"""

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": "claude-3-5-sonnet-20241022",  # Using Sonnet (Opus can be used for higher quality)
            "max_tokens": 8192,
            "temperature": 0.9,
            "messages": [{"role": "user", "content": prompt}]
        }

        print("Generating dialogue with Claude...")
        response = requests.post(url, json=payload, headers=headers, timeout=180)
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

        script = json.loads(content)
        print(f"Generated script: {script['title']} ({len(script['dialogues'])} dialogues)")
        return script

    except Exception as e:
        print(f"Claude dialogue generation failed: {e}")
        # Fallback to Gemini
        from llm_story import generate_story
        topic_text = topic_analysis.get("title", "")
        return generate_story(topic=topic_text, duration_minutes=duration_minutes)


def generate_metadata_with_claude(
    script: Dict[str, Any],
    video_duration_seconds: float
) -> Dict[str, Any]:
    """
    Generate enhanced metadata using Claude Sonnet
    (Blog's "Prompt C: Create metadata")

    Args:
        script: Generated dialogue script
        video_duration_seconds: Actual video duration

    Returns:
        Enhanced metadata for YouTube
    """
    if not CLAUDE_API_KEY:
        return _fallback_metadata(script)

    try:
        title = script.get("title", "")
        dialogues_preview = "\n".join([
            f"{d['speaker']}: {d['text'][:100]}..."
            for d in script.get("dialogues", [])[:5]
        ])

        prompt = f"""以下の動画の台本から、YouTubeに最適化されたメタデータを生成してください。

タイトル: {title}
長さ: {int(video_duration_seconds / 60)}分{int(video_duration_seconds % 60)}秒

台本抜粋:
{dialogues_preview}

以下のJSON形式で出力してください:
{{
  "youtube_title": "SEO最適化されたタイトル（100文字以内）",
  "youtube_description": "詳細な説明文（視聴者を惹きつける内容、300文字程度）",
  "tags": ["関連タグ1", "関連タグ2", ...（10個程度）],
  "category": "カテゴリ（Education/News/Entertainment等）",
  "hashtags": ["#ハッシュタグ1", "#ハッシュタグ2", "#ハッシュタグ3"]
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

        metadata = json.loads(content)
        print(f"Generated metadata for: {metadata.get('youtube_title', 'Unknown')}")
        return metadata

    except Exception as e:
        print(f"Metadata generation failed: {e}")
        return _fallback_metadata(script)


def generate_comments_with_claude(
    script: Dict[str, Any],
    count: int = 5
) -> List[str]:
    """
    Generate engaging comments for the video
    (Blog's "Prompt D: Generate witty comments")

    Args:
        script: Generated dialogue script
        count: Number of comments to generate

    Returns:
        List of comment texts
    """
    if not CLAUDE_API_KEY:
        return _fallback_comments()

    try:
        title = script.get("title", "")
        description = script.get("description", "")

        prompt = f"""以下の動画に対して、視聴者エンゲージメントを高める{count}個のコメントを生成してください。

動画タイトル: {title}
内容: {description}

コメントの要件:
- 視聴者が思わず「いいね」を押したくなるような気の利いた内容
- 動画の内容に関連した質問や感想
- 他の視聴者との対話を促すもの
- 100文字以内で簡潔に
- 様々な視点（共感、質問、補足情報、関連トピック、感謝等）

以下のJSON形式で出力してください:
{{
  "comments": [
    "コメント1",
    "コメント2",
    ...
  ]
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
            "max_tokens": 1500,
            "temperature": 0.9,
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

        result = json.loads(content)
        comments = result.get("comments", [])
        print(f"Generated {len(comments)} engagement comments")
        return comments

    except Exception as e:
        print(f"Comment generation failed: {e}")
        return _fallback_comments()


def _fallback_metadata(script: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback metadata when Claude is unavailable"""
    return {
        "youtube_title": script.get("title", "動画タイトル"),
        "youtube_description": script.get("description", "動画の説明"),
        "tags": script.get("tags", ["経済", "ニュース", "解説"]),
        "category": "Education",
        "hashtags": ["#経済ニュース", "#ビジネス", "#解説"]
    }


def _fallback_comments() -> List[str]:
    """Fallback comments"""
    return [
        "とても分かりやすい解説でした！",
        "この視点は新しいですね。勉強になります。",
        "次回も楽しみにしています！",
    ]


if __name__ == "__main__":
    # Test
    test_topic = {
        "title": "円安の影響と今後の見通し",
        "angle": "日常生活への影響を中心に解説",
        "key_points": ["為替レートの基本", "円安のメリット・デメリット", "今後の予測"],
        "selected_topic": {
            "snippet": "最近の円安について、専門家が分析"
        }
    }

    script = generate_dialogue_script_with_claude(test_topic, duration_minutes=5)
    print(f"\nScript: {script.get('title', 'Unknown')}")
    print(f"Dialogues: {len(script.get('dialogues', []))}")

    metadata = generate_metadata_with_claude(script, 300)
    print(f"\nMetadata: {metadata.get('youtube_title', 'Unknown')}")

    comments = generate_comments_with_claude(script)
    print(f"\nComments: {len(comments)}")
