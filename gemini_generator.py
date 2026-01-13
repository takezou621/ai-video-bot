"""
Gemini Content Generator - Multi-stage content generation

This module was previously named claude_generator.py (legacy name).
It now correctly reflects that it uses Gemini API, not Claude API.

Features:
- Gemini-based dialogue script generation with template system
- Metadata generation for YouTube SEO
- Engagement comment generation
- Ollama local LLM support as fallback
- API key rotation for rate limit handling

Based on the Zenn blog's approach using large language models.
"""
import os
import json
import re
import requests
from datetime import datetime
from typing import Dict, Any, List
from content_templates import ContentTemplates
from llm_story import get_past_topics
from api_key_manager import get_api_key, report_api_success, report_api_failure

# Ollama integration
try:
    from ollama_client import call_ollama, check_ollama_health
    USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"
except ImportError:
    USE_OLLAMA = False
    print("[WARNING] ollama_client not found. Ollama integration disabled.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")


import re

def _clean_json_string(json_str: str) -> str:
    """Clean JSON string from LLM before parsing"""
    # Remove control characters
    json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
    
    # Fix trailing commas
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    # Extract JSON if wrapped in markdown
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0]
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0]
        
    return json_str.strip()

def _call_gemini(prompt: str, max_output_tokens: int = 8192, temperature: float = 0.9) -> str:
    """
    Unified LLM call - tries Ollama first, falls back to Gemini with API key rotation.
    Implements the blog's strategy of multiple API keys for rate limit handling.
    """

    # Try Ollama first
    if USE_OLLAMA:
        try:
            if check_ollama_health():
                print(f"[LLM] Using Ollama (model: {os.getenv('OLLAMA_MODEL', 'llama3.1:8b-instruct-q4_K_M')})")
                return call_ollama(prompt, max_output_tokens, temperature)
            else:
                print("[LLM] Ollama unavailable, falling back to Gemini")
        except Exception as e:
            print(f"[LLM] Ollama failed: {e}, falling back to Gemini")

    # Fallback to Gemini API with key rotation (blog's approach)
    if not GEMINI_API_KEY and not os.getenv("GEMINI_API_KEYS"):
        raise RuntimeError("Neither Ollama nor GEMINI_API_KEY is available")

    print(f"[LLM] Using Gemini API (model: {GEMINI_MODEL})")

    # Try up to 3 different API keys before giving up
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            # Get next available API key
            api_key = get_api_key("GEMINI")

            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{GEMINI_MODEL}:generateContent?key={api_key}"
            )
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_output_tokens
                }
            }

            response = requests.post(url, json=payload, timeout=180)

            # Check for rate limiting
            if response.status_code == 429:
                # Rate limit - report and try next key
                report_api_failure("GEMINI", api_key, is_rate_limit=True)
                print(f"[LLM] Rate limit hit (attempt {attempt + 1}/{max_retries}), trying next key...")
                continue

            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_msg = str(data["error"])
                # Check if error is rate limit related
                is_rate_limit = "quota" in error_msg.lower() or "rate" in error_msg.lower()
                report_api_failure("GEMINI", api_key, is_rate_limit=is_rate_limit)

                if is_rate_limit and attempt < max_retries - 1:
                    print(f"[LLM] Quota/rate error (attempt {attempt + 1}/{max_retries}), trying next key...")
                    continue
                raise RuntimeError(error_msg)

            candidates = data.get("candidates", [])
            if not candidates:
                report_api_failure("GEMINI", api_key)
                raise RuntimeError("Gemini returned no candidates")

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                report_api_failure("GEMINI", api_key)
                raise RuntimeError("Gemini response missing content parts")

            # Success!
            report_api_success("GEMINI", api_key)
            return parts[0].get("text", "")

        except requests.exceptions.RequestException as e:
            last_error = e
            # Network error - report failure and try next key
            if 'api_key' in locals():
                is_rate_limit = "429" in str(e) or "quota" in str(e).lower()
                report_api_failure("GEMINI", api_key, is_rate_limit=is_rate_limit)

            if attempt < max_retries - 1:
                print(f"[LLM] Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                continue
            raise

    # All retries exhausted
    raise RuntimeError(f"Gemini API failed after {max_retries} attempts: {last_error}")


def generate_dialogue_script(
    topic_analysis: Dict[str, Any],
    duration_minutes: int = 10
) -> Dict[str, Any]:
    """
    Generate podcast-style dialogue using Gemini.

    This function was previously named generate_dialogue_script_with_claude
    (legacy name). The module uses Gemini API, not Claude.

    Args:
        topic_analysis: Topic analysis from web search
        duration_minutes: Target duration in minutes

    Returns:
        Dialogue script with metadata
    """
    named_entities = topic_analysis.get("named_entities", [])
    named_entity_labels = [entity.get("label") for entity in named_entities if entity.get("label")]
    entity_hint = "、".join(named_entity_labels[:3]) if named_entity_labels else "注目企業名（NVIDIA, OpenAI など）"

    # Date prefix for title (e.g., "12/19")
    date_prefix = datetime.now().strftime("%m/%d").lstrip("0").replace("/0", "/")

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
        hook_description = ContentTemplates.describe_hook_structure(title or "このトピック")
        
        # Check if this is an International AI News topic
        is_ai_news = selected_topic.get("is_english", False)
        source_name = selected_topic.get("source", "海外メディア")
        source_url = selected_topic.get("url", "")
        benefit = angle or "今日から先回りできる視点"

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

        if is_ai_news:
            # === AI NEWS SPECIAL PROMPT ===
            # Check if we have multiple news articles for summary
            all_news = topic_analysis.get("all_news_articles", [])

            if all_news and len(all_news) > 1:
                # Multiple news summary mode
                articles_text = ""
                for i, article in enumerate(all_news[:10], 1):
                    articles_text += f"\n[記事 {i}]\n"
                    articles_text += f"タイトル: {article.get('title', '')}\n"
                    articles_text += f"内容: {article.get('snippet', '')}\n"
                    articles_text += f"ソース: {article.get('source', '')}\n"
                    articles_text += f"URL: {article.get('url', '')}\n"

                prompt = f"""あなたは日本トップクラスのAIトレンド分析官です。
複数の海外AIニュースから、エンジニアやテック愛好家が今知るべき「核心」を抽出し、深く解説してください。

# 最新AIニュース一覧 ({len(all_news)}件)
{articles_text}

# あなたのミッション
表面的なニュース読み上げではなく、以下の視点を含む**「技術的深掘り（Deep Dive）」**を行ってください。
1. **ベンチマーク至上主義**: "高性能になった"等の曖昧な表現はNG。「MMLUスコアが〇〇%向上」「コンテキストウィンドウが〇〇万トークンに拡大」など**具体的な数値**を必ず出す。
2. **競合比較**: OpenAI, Google, Anthropic, Metaなどの競合モデルと比べて何が優れているか/劣っているかを明確に。
3. **技術的背景**: アーキテクチャ（MoE, SSM等）や学習手法に新規性があれば触れる。

# 動画構成
{structure_desc}

# 台本要件
- 対話形式:
    - 男性（AIリサーチャー）: 技術オタク。スペックや論文の中身に詳しく、冷静に分析する。
    - 女性（テックキャスター）: 開発者/ユーザー視点。「実際に何に使えるの？」「コストは？」など鋭く突っ込む。
- 全体で約{duration_minutes}分
- **必須**: 各トピックで「情報ソース（論文名や企業ブログ）」を明示。
- 専門用語（RAG, Fine-tuning, Inference等）は使いつつ、文脈でさらっと意味が伝わるように。

# 構成イメージ
1. フック: 「今週、AI界隈を震撼させた3つのニュース。特に〇〇の数値が異常です」
2. ニュース解説: [技術名/モデル名] → 数値的スペック → 競合比較
3. 深掘り議論: 「なぜこの技術が重要なのか？」エンジニア視点で議論
4. まとめ: 今後のAI開発トレンドへの示唆

以下のJSON形式で出力してください:
{{
  "title": "【最新AI】(モデル名/数値を入れた具体的タイトル)",
  "description": "YouTube用説明文（ベンチマーク数値やモデル名を列挙）",
  "thumbnail_text": "サムネイル用短文（例: GPT-5級!?）",
  "background_prompt": "Futuristic AI lab, glowing neural networks, data visualization screens, cyberpunk atmosphere, 8k",
  "sections": [
    {{
      "title": "ニュース1のタイトル",
      "start_dialogue_index": 0,
      "image_prompt": "Detailed DALL-E prompt for news 1",
      "benchmarks": [
        {{"name": "MMLU", "value": "88.7%", "comparison": "+2.1%"}},
        {{"name": "HumanEval", "value": "90.2%", "comparison": "+5.4%"}}
      ]
    }},
    ...
  ],
  "dialogues": [
    {{"speaker": "男性", "text": "..."}},
    {{"speaker": "女性", "text": "..."}}
  ],
  "tags": ["AI", "LLM", "機械学習", "生成AI", "論文解説"],
  "source_urls": [複数のニュースURL]
}}
JSONのみを出力してください。"""
            else:
                # Single news article mode
                prompt = f"""あなたは最新論文や技術ブログを読み解く「AI技術リサーチャー」です。
このトピックについて、エンジニアやAIガチ勢が満足するレベルの技術解説を行ってください。

# トピック情報
タイトル: {title}
ソース元: {source_name}
内容: {snippet}
URL: {source_url}

# 解説の必須要素 (Technical Deep Dive)
1. **「何が」凄いのか（SOTA達成など）**: State-of-the-Art（最高性能）更新や、従来手法との違いを明確に。
2. **定量的評価**: ベンチマークスコア、処理速度(tokens/s)、コスト($/1M tokens)などの**数字**を必ず盛り込む。
3. **実用性評価**: 「デモを見た感想」や「実際にコードを書く場面での有用性」など、ハンズオンな視点。
4. **競合比較**: GPT-4oやClaude 3.5 Sonnetと比べてどう使い分けるべきか？

# 動画構成
{structure_desc}

# 台本要件
- 対話形式: 
    - 男性（AIリサーチャー）: 論文やドキュメントを読み込んでいる専門家。
    - 女性（開発者/エンジニア）: 実際にツールを使う立場から、実装やコストについて質問する。
- 全体で約{duration_minutes}分
- **重要**: 一般ニュースのような「便利になりますね」等の浅い感想は禁止。「APIのレイテンシが...」「推論コストが...」といった技術的な会話にする。

# 構成イメージ
1. 技術フック: 「ついに{title}が登場。ベンチマークで〇〇超えを記録しました」
2. 詳細スペック: アーキテクチャ、学習データ、各種スコアの解説
3. 比較議論: 「ぶっちゃけGPT-4とどっち使う？」
4. 結論: エンジニアはどう動くべきか

以下のJSON形式で出力してください:
{{
  "title": "【検証】(モデル名/技術名)の実力は？(具体的な成果/数値)",
  "description": "YouTube用説明文（技術的なキーワードを多用）",
  "thumbnail_text": "サムネイル用短文（例: 精度99.8%）",
  "background_prompt": "High-tech server room, floating code holograms, AI chip close-up, blue and orange lighting, 8k",
  "sections": [
    {{
      "title": "セクションタイトル",
      "start_dialogue_index": 0,
      "image_prompt": "Detailed prompt for this specific section",
      "benchmarks": [
         {{"name": "Benchmark Name", "value": "Score", "comparison": "+X%"}}
      ]
    }}
  ],
  "dialogues": [
    {{"speaker": "男性", "text": "..."}}, 
    {{"speaker": "女性", "text": "..."}}
  ],
  "tags": ["AI", "技術解説", "LLM", "プログラミング", "{title} (英語表記も含む)"],
  "source_urls": ["{source_url}"]
}}
JSONのみを出力してください。"""
        else:
            # === STANDARD PROMPT (Podcast) ===
            prompt = f"""あなたは日本のYouTube向けに、経済・ビジネストピックを**詳細に**解説する対話形式ニュース解説番組の台本を作成するプロのシナリオライターです。

視聴者は**具体的な数値、出典、歴史的文脈、複数の視点**を求める情報感度の高い層です。表面的な解説ではなく、専門家レベルの深い分析を提供してください。

{duplicate_avoidance}
# 動画構成テンプレート
以下の構成に沿って台本を作成してください：
{structure_desc}

# トピック情報
タイトル: {title}
切り口: {angle}
重要ポイント: {', '.join(key_points)}
詳細: {snippet}

# 台本要件（重要）
- 対話形式: 男性（メインキャスター、アナリスト）と女性（サブキャスター、質問役）
- 全体で約{duration_minutes}分（音声にすると、合計約{char_count}文字程度）
- 対話交換回数: 約{dialogue_count}回
- 言葉遣い: 丁寧な敬語調（「～です」「～ます」「～でしょうか」）で統一
- 構成:
  1. フック（最初の15秒）
  2. テーマ提示と背景説明
  3. 詳細解説（複数の視点を提示）
  4. 今後の展望・複数シナリオ
  5. まとめ
  6. 軽い雑談風の感想
  7. CTA（チャンネル登録促進）

# **必須：詳細解説の品質基準**

## 1. 具体的な数値データを豊富に含める
- ❌ NG: 「大きく上昇しました」「多くの人が注目しています」
- ✅ OK: 「79%の確率で上昇」「平均1.3%のリターンを記録」「40倍の水準に達しています」
- 統計、パーセンテージ、比率、金額、人数など、可能な限り数値で表現

## 2. 情報源・出典を明示する
- 形式: 「（情報源名）が（日付）に公開した（記事/レポート/調査）によりますと」
- 例:
  - 「モトリーフールが12月17日に公開した記事によりますと」
  - 「Wikipediaの記録によりますと」
  - 「247ウォールストリートが12月21日に公開した分析記事では」
  - 「ゴールドマンサックスは12月20日に発表した経済見通しで」
- 架空の出典は使用禁止。{snippet}の情報を元に、それらしい出典形式で表現すること

## 3. 歴史的文脈を提供する
- 「1972年以来」「1950年以降のデータでは」「過去50年で2回のみ」
- 「dotcomバブル以来の高水準」「リーマンショック後初めて」
- 現在の状況を歴史的スパンで位置づける

## 4. 専門用語は必ず説明する
- 形式: 「（専門用語） - これは（説明）を指します」
- 例:
  - 「シラーケープ比率 - これはインフレ調整済みの過去10年間の平均利益に基づく株価収益率ですが」
  - 「ウィンドウドレッシング - これはファンドマネージャーが年末の報告書でポートフォリオの見栄えを良くするために...」

## 5. 複数の視点・シナリオを提示する
- 楽観論と悲観論の両方
- 「一方では～という見方もあります」「ただし～というリスクも」
- 異なる専門家の意見を対比させる
- 例: 「シナリオ1: 健全なローテーション」「シナリオ2: AI選別調整」

## 6. 質疑応答形式を徹底
- 女性キャスターの質問形式: 「～でしょうか」「～ですか」「～について教えてください」
- 男性キャスターの応答形式: 「その通りです」「はい」「いい質問ですね」「確かに」
- 確認と深掘りの繰り返しで情報密度を高める

## 7. まとめ後に軽い雑談風コメントを追加
- フォーマルな解説が終わった後、少しくだけたトーンで
- 「正直なところ」「まあでも」「さすがに」などの口語表現
- 個人的な感想や率直な印象を述べる
- 例: 「正直なところ今年の年末は読みづらいですよね」「シラーケープ比率45近いっていうのもさすがにちょっと背筋がヒやっとしますよね」

# タイトル・SEO要件
- タイトルの先頭には必ず【{date_prefix}】の形式で日付を含める
- 日付の後に固有名詞を配置（推奨: {entity_hint}）
- ❌ NG: 【衝撃】【緊急】【暴露】などの煽りパワーワードは使用しない

# 冒頭15秒フック
{hook_description}

# 対話スタイルの具体例（必読）

**開始部分の例:**
男性: おはようございます。本日のテーマは{title}です。
女性: よろしくお願いします。まず基本的な定義から確認しておきたいのですが、～とは何でしょうか？
男性: はい、これは（具体的な説明）を指します。（出典）によりますと、（具体的な数値データ）という統計があります。

**詳細解説部分の例:**
女性: 具体的にはどの程度の信頼性があるのでしょうか？
男性: （情報源）が（日付）に公開した記事によりますと、（歴史的データ）のデータでは、約（数値）%の確率で（結果）を記録しています。つまり、（解釈）ということになります。
女性: その通りですね。では、今回の状況について詳しく見ていきましょう。

**シナリオ提示の例:**
男性: ここで今後の展開について2つの仮説を検討してみたいと思います。
女性: はい、お願いします。
男性: まず1つ目は（シナリオ1の名称）です。これは（説明）という解釈です。
女性: このシナリオが実現する場合、どのような展開が予想されますか？
男性: （詳細な説明）というシナリオです。

**まとめ後の雑談風コメント例:**
女性: ありがとうございました。えっと、いや正直なところ（率直な感想）ですよね。
男性: そうですね。（数値）っていうのもさすがにちょっと（個人的な印象）ますよね。でも（前向きなコメント）と思いますよ。
女性: 本当にそうですね。では明日も最新の情報をお届けします。チャンネル登録と高評価をよろしくお願いします。それでは今日も良い1日になりますように。

# NGポイント
- 曖昧な表現（「大きく」「多くの」「かなり」など数値で表せるものは数値化）
- 出典なしの断定
- 専門用語を説明なしで使用
- 一方的な視点のみの提示
- カジュアルすぎる口調（まとめ前まではフォーマルに）

以下のJSON形式で出力してください:
{{
  "title": "【{date_prefix}】(固有名詞)(具体的な内容)｜(数値や驚きの要素)",
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

重要:
- speakerは必ず「男性」または「女性」としてください
- dialoguesは最低{dialogue_count}回以上の質疑応答を含めること
- 数値データ、出典、歴史的文脈を可能な限り多く含めること

JSONのみを出力してください。"""

        # Add explicit JSON instruction for Ollama models
        if USE_OLLAMA:
            prompt += "\n\n重要: 必ず有効なJSONのみを出力してください。JSONの前後に説明文やマークダウンを含めないでください。"

        print("Generating dialogue with LLM...")
        content = _call_gemini(prompt, max_output_tokens=8192, temperature=0.9)

        # Clean and parse JSON
        content = _clean_json_string(content)
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            content = content[start:end]

        script = json.loads(content)
        if named_entities:
            script["named_entities"] = named_entities
        script = _ensure_structured_hook(script, topic_analysis)
        print(f"Generated script: {script['title']} ({len(script['dialogues'])} dialogues)")
        return script

    except Exception as e:
        import traceback
        print(f"Gemini dialogue generation failed: {e}")
        print("Full traceback:")
        traceback.print_exc()
        # Fallback to Gemini
        from llm_story import generate_story
        topic_text = topic_analysis.get("title", "")
        script = generate_story(topic=topic_text, duration_minutes=duration_minutes)
        if named_entities:
            script["named_entities"] = named_entities
        script = _ensure_structured_hook(script, topic_analysis)
        return script


def generate_metadata(
    script: Dict[str, Any],
    video_duration_seconds: float
) -> Dict[str, Any]:
    """
    Generate enhanced metadata using Gemini.

    This function was previously named generate_metadata_with_claude
    (legacy name). The module uses Gemini API, not Claude.

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

        # Date prefix for title (e.g., "12/19")
        date_prefix = datetime.now().strftime("%m/%d").lstrip("0").replace("/0", "/")

        prompt = f"""あなたはYouTube SEOのエキスパートです。以下の動画から、検索上位表示とクリック率（CTR）を最大化するメタデータを生成してください。

タイトル: {title}
長さ: {int(video_duration_seconds / 60)}分{int(video_duration_seconds % 60)}秒

台本抜粋:
{dialogues_preview}

# メタデータ生成のポイント
1. **タイトル**: タイトルの先頭には必ず【{date_prefix}】の形式で日付を含める
   - 例: 「【{date_prefix}】NVIDIA 新発表の全貌」「【{date_prefix}】なぜ〇〇は注目されているのか？」
   - ❌ NG: 【衝撃】【緊急】【暴露】などの煽りパワーワードは使用しない
   - 日付の後に固有名詞（推奨: {entity_hint}）を配置すること
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

# ⚠️ 重要: タイトルのルール
- タイトルは必ず【{date_prefix}】で始めること（例: 【{date_prefix}】NVIDIA 最新動向を徹底解説）
- 【衝撃】【緊急】【暴露】【速報】【革命】などの煽り表現は絶対に使用禁止

以下のJSON形式で出力してください:
{{
  "youtube_title": "【{date_prefix}】（固有名詞）（内容を端的に表すタイトル）",
  "youtube_description": "詳細な説明文（最初の3行で引き込み、タイムスタンプ含む、400-500文字）",
  "tags": ["メインキーワード", "関連キーワード1", "関連キーワード2", ...（15-20個）],
  "category": "Education",
  "hashtags": ["#ハッシュタグ1", "#ハッシュタグ2", "#ハッシュタグ3"]
}}

JSONのみを出力してください。"""

        content = _call_gemini(prompt, max_output_tokens=2048, temperature=0.4)

        # Clean and parse JSON
        content = _clean_json_string(content)
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


def generate_comments(
    script: Dict[str, Any],
    count: int = 5
) -> List[str]:
    """
    Generate engaging comments for the video.

    This function was previously named generate_comments_with_claude
    (legacy name). The module uses Gemini API, not Claude.

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

        # Clean and parse JSON
        content = _clean_json_string(content)
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


def _build_hook_context(topic_analysis: Dict[str, Any], script: Dict[str, Any]) -> Dict[str, str]:
    selected = topic_analysis.get("selected_topic", {})
    topic_title = topic_analysis.get("title") or script.get("title") or "このテーマ"
    return {
        "topic": topic_title,
        "percentage": "78",
        "misconception": topic_analysis.get("angle", "本質を見誤っている"),
        "problem": f"{selected.get('source', '現場')}で急増中",
        "stat": f"{selected.get('source', '最新レポート')}で判明",
        "entity": selected.get("source", "専門家"),
        "data": selected.get("snippet", "予想外のデータ"),
        "numbers": "わずか30日で15%の差",
        "benefit": topic_analysis.get("angle", "今日から先回りできる視点"),
        "solution": topic_analysis.get("angle", "3つのステップ"),
        "action": "あなたの戦略を一歩進める",
    }


def _validate_hook_quality(script: Dict[str, Any]) -> bool:
    dialogues = script.get("dialogues", [])
    if len(dialogues) < 3:
        return False
    combined = "".join(d.get("text", "") for d in dialogues[:3])
    if len(combined) < 30:
        return False
    has_question = any(ch in combined for ch in ("？", "?", "！", "!"))
    has_number = bool(re.search(r"[0-9０-９％%億万]", combined))
    entities = [
        entity.get("label")
        for entity in script.get("named_entities", [])
        if entity.get("label")
    ]
    has_entity = any(label in combined for label in entities)
    benefit_keywords = ["わかります", "理解できます", "学べます", "解説します", "方法", "できる", "お伝えします", "紹介します", "分かります"]
    has_benefit = any(word in combined for word in benefit_keywords)
    return (has_entity or has_number) and has_question and has_benefit


def _ensure_structured_hook(script: Dict[str, Any], topic_analysis: Dict[str, Any]) -> Dict[str, Any]:
    if _validate_hook_quality(script):
        return script

    context = _build_hook_context(topic_analysis, script)
    sentences = ContentTemplates.generate_three_sentence_hook(context["topic"], context)
    structured_dialogues = [
        {"speaker": "男性", "text": sentences[0]},
        {"speaker": "女性", "text": sentences[1]},
        {"speaker": "男性", "text": sentences[2]},
    ]

    dialogues = script.get("dialogues", [])
    script["dialogues"] = structured_dialogues + dialogues[3:]
    return script


# =============================================================================
# Backward Compatibility Aliases
# =============================================================================
# The following aliases are provided for backward compatibility with code that
# imports from the old module name (claude_generator.py) or uses old function names.

# Legacy function names (module was previously named claude_generator.py)
generate_dialogue_script_with_claude = generate_dialogue_script
generate_metadata_with_claude = generate_metadata
generate_comments_with_claude = generate_comments


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

    script = generate_dialogue_script(test_topic, duration_minutes=5)
    print(f"\nScript: {script.get('title', 'Unknown')}")
    print(f"Dialogues: {len(script.get('dialogues', []))}")

    metadata = generate_metadata(script, 300)
    print(f"\nMetadata: {metadata.get('youtube_title', 'Unknown')}")

    comments = generate_comments(script)
    print(f"\nComments: {len(comments)}")
