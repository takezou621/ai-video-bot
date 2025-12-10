"""
Gemini API Integration - Multi-stage content generation
Based on the Zenn blog's approach using large language models
Enhanced with template system for consistent, high-quality content
"""
import os
import json
import requests
from typing import Dict, Any, List
from content_templates import ContentTemplates
from llm_story import get_past_topics

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def _call_gemini(prompt: str, max_output_tokens: int = 8192, temperature: float = 0.9) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured")

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
    response = requests.post(url, json=payload, timeout=180)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise RuntimeError("Gemini response missing content parts")
    return parts[0].get("text", "")


def generate_dialogue_script_with_claude(
    topic_analysis: Dict[str, Any],
    duration_minutes: int = 10
) -> Dict[str, Any]:
    """
    Generate podcast-style dialogue using Gemini
    (Blog's "Prompt B: Generate dialogue script")

    Args:
        topic_analysis: Topic analysis from web search
        duration_minutes: Target duration in minutes

    Returns:
        Dialogue script with metadata
    """
    named_entities = topic_analysis.get("named_entities", [])
    named_entity_labels = [entity.get("label") for entity in named_entities if entity.get("label")]
    entity_hint = "、".join(named_entity_labels[:3]) if named_entity_labels else "注目企業名（NVIDIA, OpenAI など）"

    if not GEMINI_API_KEY:
        print("Gemini API key not found, using fallback story generator")
        from llm_story import generate_story
        topic_text = topic_analysis.get("title", "")
        script = generate_story(topic=topic_text, duration_minutes=duration_minutes)
        if named_entities:
            script["named_entities"] = named_entities
        return script

    try:
        # Estimate content length (Japanese: ~300 chars/minute for natural speech)
        char_count = duration_minutes * 300
        dialogue_count = duration_minutes * 6  # ~6 exchanges per minute

        # Get past topics to avoid duplicates
        past_topics = get_past_topics(max_count=20)

        # Get topic details
        title = topic_analysis.get("title", "")
        angle = topic_analysis.get("angle", "")
        key_points = topic_analysis.get("key_points", [])
        selected_topic = topic_analysis.get("selected_topic", {})
        snippet = selected_topic.get("snippet", "")

        # Get script structure from template
        script_structure = ContentTemplates.generate_script_structure(
            topic=title,
            duration_minutes=duration_minutes,
            structure_type="standard"
        )

        # Format structure for prompt
        structure_desc = "\n".join([
            f"- {s['type']} ({int(s['duration_seconds'])}秒): {s['purpose']}"
            for s in script_structure['sections']
        ])

        # Build duplicate avoidance section
        duplicate_avoidance = ""
        if past_topics:
            duplicate_avoidance = "\n# ⚠️ 重要: 過去の動画との重複を避けてください\n"
            duplicate_avoidance += "以下のトピックは既に扱っているため、完全に異なるテーマを選んでください：\n"
            for i, past_topic in enumerate(past_topics[:10], 1):
                duplicate_avoidance += f"{i}. {past_topic}\n"
            duplicate_avoidance += "\n→ これらとは明確に区別できる、新鮮で独自性のあるトピックで台本を作成してください。\n"

        prompt = f"""あなたは日本のYouTube向けに、経済・ビジネストピックを解説する対話形式ポッドキャストの台本を作成するプロのシナリオライターです。
{duplicate_avoidance}
# 動画構成テンプレート
以下の構成に沿って台本を作成してください：
{structure_desc}

# トピック情報
タイトル: {title}
切り口: {angle}
重要ポイント: {', '.join(key_points)}
詳細: {snippet}

# 台本要件
- 対話形式: 男性（メインホスト、落ち着いた声で分かりやすく説明）と女性（サブホスト、明るい声で質問や補足コメント）
- 全体で約{duration_minutes}分（音声にすると、合計約{char_count}文字程度）
- 対話交換回数: 約{dialogue_count}回
- 言葉遣い: 自然な会話調の日本語
- 構成: フック（最初の15秒で視聴者を引き込む）→ イントロ → メイン解説 → まとめ → CTA（チャンネル登録促進）
- 視聴者: ビジネスパーソン、経済に興味がある一般層
- スタイル: 教育的だが堅苦しくない、親しみやすい、エンタメ性も意識

# タイトル・SEO要件（Issue #1 対応）
- 固有名詞を最初の3単語以内に配置（推奨固有名詞: {entity_hint}）
- 可能であれば数字（例:「3つの理由」「5分で分かる」）を含めてクリックを誘発
- 感情的なパワーワード（例:「衝撃」「緊急」「革命」）を最低1つ含める
- 固有名詞と動画内容に整合性を持たせ、ミスリードを避ける

# キャラクター設定
- 男性ホスト: 知識豊富で丁寧な説明が得意。落ち着いた語り口。30代後半のイメージ。
- 女性ホスト: 好奇心旺盛で視聴者目線の質問をする。明るく親しみやすい。20代後半のイメージ。

# 高品質な台本のポイント（必須）
1. **冒頭15秒でフック**: 驚きの事実、疑問形、または結論の一部を先出しして視聴者を引き込む
2. **ストーリー性**: 単なる情報の羅列ではなく、流れのある物語として構成
3. **感情の起伏**: 驚き、納得、共感など、視聴者の感情を動かす
4. **具体例と数字**: 抽象的な説明ではなく、具体的な事例や数字を使う
5. **視聴者目線**: 「これって私に関係あるの？」という疑問に常に答える
6. **テンポ**: 長すぎる説明を避け、リズミカルな会話を心がける
7. **意外性**: 視聴者の予想を良い意味で裏切る情報や視点を入れる
8. **男女の掛け合い**: 男性の説明に女性が共感・驚きの反応を示し、視聴者を代弁する

# 対話スタイルの具体例
- 男性: 「実はこれ、意外なデータがあって...」（興味を引く）
- 女性: 「え、そうなんですか！？気になります！」（視聴者の代弁）
- 男性: 「そうなんです。具体的には...」（詳細説明）
- 女性: 「なるほど！じゃあ、私たちの生活にはどう影響するんですか？」（視聴者の疑問を代弁）

# NGポイント
- 堅苦しい敬語表現
- 専門用語の羅列
- 抽象的すぎる説明
- 単調なリズム
- 一方的な講義形式

以下のJSON形式で出力してください:
{{
  "title": "動画タイトル（SEOを意識した魅力的な表現）",
  "description": "YouTube用説明文（2-3文、150文字以内）",
  "thumbnail_text": "サムネイル用短文（10文字以内）",
  "background_prompt": "Lo-fi anime style background image prompt in English (cozy room, warm lighting, desk setup)",
  "dialogues": [
    {{"speaker": "男性", "text": "対話内容1"}},
    {{"speaker": "女性", "text": "対話内容2"}},
    ...
  ],
  "tags": ["タグ1", "タグ2", "タグ3", "タグ4", "タグ5"]
}}

重要: speakerは必ず「男性」または「女性」としてください（"A"や"B"は使用しない）。

JSONのみを出力してください。"""

        print("Generating dialogue with Gemini...")
        content = _call_gemini(prompt, max_output_tokens=8192, temperature=0.9)

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
        if named_entities:
            script["named_entities"] = named_entities
        print(f"Generated script: {script['title']} ({len(script['dialogues'])} dialogues)")
        return script

    except Exception as e:
        print(f"Gemini dialogue generation failed: {e}")
        # Fallback to Gemini
        from llm_story import generate_story
        topic_text = topic_analysis.get("title", "")
        script = generate_story(topic=topic_text, duration_minutes=duration_minutes)
        if named_entities:
            script["named_entities"] = named_entities
        return script


def generate_metadata_with_claude(
    script: Dict[str, Any],
    video_duration_seconds: float
) -> Dict[str, Any]:
    """
    Generate enhanced metadata using Gemini
    (Blog's "Prompt C: Create metadata")

    Args:
        script: Generated dialogue script
        video_duration_seconds: Actual video duration

    Returns:
        Enhanced metadata for YouTube
    """
    if not GEMINI_API_KEY:
        return _fallback_metadata(script)

    try:
        title = script.get("title", "")
        named_entities = script.get("named_entities", [])
        entity_hint = ", ".join(e.get("label") for e in named_entities if e.get("label")) or "NVIDIA / OpenAI などの固有名詞"
        dialogues_preview = "\n".join([
            f"{d['speaker']}: {d['text'][:100]}..."
            for d in script.get("dialogues", [])[:5]
        ])

        prompt = f"""あなたはYouTube SEOのエキスパートです。以下の動画から、検索上位表示とクリック率（CTR）を最大化するメタデータを生成してください。

タイトル: {title}
長さ: {int(video_duration_seconds / 60)}分{int(video_duration_seconds % 60)}秒

台本抜粋:
{dialogues_preview}

# メタデータ生成のポイント
1. **タイトル**: クリックしたくなる要素（数字、疑問形、意外性）を含める
   - 例: 「【衝撃】〇〇の真実」「なぜ〇〇は失敗したのか？」「〇〇が教える3つの秘訣」
   - 固有名詞（推奨: {entity_hint}）をタイトル冒頭に配置すること
2. **説明文**: 最初の3行で視聴者を引き込む（この3行がスマホで表示される）
   - 動画の価値を明確に
   - タイムスタンプを含める
   - 関連動画へのリンクやCTAを入れる
3. **タグ**: メインキーワード + ロングテールキーワード + 関連キーワードのミックス
4. **ハッシュタグ**: トレンド性のあるもの3-5個（多すぎない）

# 目標
- 検索結果で上位表示
- サムネイル+タイトルでCTR 10%以上
- 視聴者維持率を高める説明文

以下のJSON形式で出力してください:
{{
  "youtube_title": "SEO最適化されたタイトル（60-70文字、数字や記号で目を引く）",
  "youtube_description": "詳細な説明文（最初の3行で引き込み、タイムスタンプ含む、400-500文字）",
  "tags": ["メインキーワード", "関連キーワード1", "関連キーワード2", ...（15-20個）],
  "category": "Education",
  "hashtags": ["#ハッシュタグ1", "#ハッシュタグ2", "#ハッシュタグ3"]
}}

JSONのみを出力してください。"""

        content = _call_gemini(prompt, max_output_tokens=2048, temperature=0.4)

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
    if not GEMINI_API_KEY:
        return _fallback_comments()

    try:
        title = script.get("title", "")
        description = script.get("description", "")

        prompt = f"""あなたは、YouTubeで注目を集めるコメントを書くプロです。以下の動画に対して、視聴者エンゲージメントを最大化する{count}個のコメントを生成してください。

動画タイトル: {title}
内容: {description}

# コメントのキャラクター設定
以下の5つのキャラクターから1つずつコメントを生成:

1. **鋭い分析家**: 動画の内容を深掘りし、気づきにくいポイントを指摘
   - 「この視点見逃してる人多いけど...」「実はこれ、〇〇とも関連してて...」

2. **共感型リアクター**: 視聴者の気持ちを代弁、感情的な反応
   - 「まさに今これで悩んでた！」「え、知らなかった...衝撃」

3. **実体験シェア型**: 自分の経験と結びつけてコメント
   - 「うちの会社でもまさにこの状況で...」「去年これやって失敗した経験あります」

4. **質問・議論型**: 次の疑問を投げかけ、コメント欄での議論を促進
   - 「じゃあ〇〇の場合はどうなんですか？」「これって△△にも適用できますか？」

5. **応援・感謝型**: チャンネルへの感謝やポジティブなフィードバック（軽い毒舌も可）
   - 「この説明分かりやすすぎて草」「なんで学校でこれ教えてくれないの」

# コメントの質を高めるポイント
- 100文字前後（長すぎず短すぎず）
- 絵文字は1-2個程度（多用しない）
- 「いいね」を押したくなる要素を含める
- 他の視聴者が返信したくなる内容
- ネガティブすぎない（建設的な批判はOK）

以下のJSON形式で出力してください:
{{
  "comments": [
    "コメント1（キャラクター1）",
    "コメント2（キャラクター2）",
    "コメント3（キャラクター3）",
    "コメント4（キャラクター4）",
    "コメント5（キャラクター5）"
  ]
}}

JSONのみを出力してください。"""

        content = _call_gemini(prompt, max_output_tokens=1500, temperature=0.8)

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
    """Fallback metadata when Gemini is unavailable"""
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
