# 🚀 クイックスタートガイド

**5分で最初の高品質AI動画を生成！**

## 最速で1本生成する手順

### ステップ 1: 環境変数を設定

```bash
cp .env.sample .env
```

`.env`ファイルを編集して**最低限のAPIキー**を設定：

```env
# 必須（これだけでOK）
GEMINI_API_KEY=your_gemini_key_here
CLAUDE_API_KEY=your_claude_key_here
OPENAI_API_KEY=your_openai_key_here
```

### ステップ 2: Dockerイメージをビルド

```bash
docker compose build
```

### ステップ 3: 動画を生成

```bash
# 最新の高品質機能をすべて使用
docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

### ステップ 4: 出力を確認

```bash
ls -la outputs/$(date +%Y-%m-%d)/video_001/
```

動画は `outputs/YYYY-MM-DD/video_001/video.mp4` に生成されます。

---

## 🎁 含まれる機能（デフォルト）

✅ **ElevenLabs STT統合**: 字幕が音声と完璧に同期（APIキーがあれば）
✅ **MoviePy高品質レンダリング**: プロレベルの仕上がり
✅ **テンプレート構造**: 実証済みシナリオパターン
✅ **SEO最適化メタデータ**: CTR 8-12%目標のタイトル
✅ **自動タイムスタンプ**: 説明文に自動挿入
✅ **5つのペルソナコメント**: エンゲージメント最大化

---

## 📝 各APIキーの取得方法

### Gemini API（音声生成用）- 必須

1. [Google AI Studio](https://aistudio.google.com/app/apikey) にアクセス
2. "Get API Key" をクリック
3. キーをコピーして `.env` の `GEMINI_API_KEY` に設定

### Claude API（台本生成用）- 必須

1. [Anthropic Console](https://console.anthropic.com/) にアクセス
2. "Get API Keys" から新しいキーを作成
3. キーをコピーして `.env` の `CLAUDE_API_KEY` に設定

### OpenAI API（画像生成用）- 必須

1. [OpenAI Platform](https://platform.openai.com/api-keys) にアクセス
2. "Create new secret key" をクリック
3. キーをコピーして `.env` の `OPENAI_API_KEY` に設定

---

## ⭐ オプション機能を有効にする

### ElevenLabs STT（字幕精度99%+）

字幕を音声と完璧に同期させたい場合：

1. [ElevenLabs](https://elevenlabs.io/) でアカウント作成
2. APIキーを取得
3. `.env` に設定：

```env
ELEVENLABS_API_KEY=your_elevenlabs_key
USE_ELEVENLABS_STT=true
```

**効果**: 字幕精度 80-90% → 99%+

### Web検索で最新トピックを自動発見

1. [Serper.dev](https://serper.dev/) でアカウント作成
2. APIキーを取得
3. `.env` に設定：

```env
SERPER_API_KEY=your_serper_key
USE_WEB_SEARCH=true
TOPIC_CATEGORY=economics
```

**効果**: 固定トピック → トレンド自動追従

### Slack通知を有効にする

1. Slackワークスペースで Incoming Webhook を作成
2. Webhook URLを取得
3. `.env` に設定：

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**効果**: 生成開始・完了・エラーを即座に通知

---

## ⚙️ カスタマイズ設定

### 動画の長さを変更

```env
DURATION_MINUTES=15    # 5〜30分推奨
```

### 複数動画を生成

```env
VIDEOS_PER_DAY=4    # 1日4本生成
```

### トピックカテゴリを変更

```env
TOPIC_CATEGORY=technology    # technology, culture, lifestyle等
```

### 品質 vs 速度を調整

#### 最高品質（推奨）
```env
USE_ELEVENLABS_STT=true    # 字幕精度最高
USE_MOVIEPY=true           # 映像品質最高
```
- 時間: 約30-40分
- 品質: プロレベル

#### 速度優先
```env
USE_ELEVENLABS_STT=false   # 推定タイミング
USE_MOVIEPY=false          # 高速レンダリング
```
- 時間: 約15-20分
- 品質: 良好

---

## よくある質問

### Q: どのAPIキーが必須ですか？

**必須:**
- `GEMINI_API_KEY` - 音声生成
- `CLAUDE_API_KEY` - 台本生成（推奨）
- `OPENAI_API_KEY` - 画像生成

**オプション:**
- `ELEVENLABS_API_KEY` - 字幕精度向上（推奨）
- `SERPER_API_KEY` - トレンド自動発見
- `SLACK_WEBHOOK_URL` - 通知

### Q: 動画1本あたりのコストは？

**基本構成（10分動画）：**
- Claude API: ¥20〜30
- Gemini TTS: ¥15〜20
- DALL-E 3: ¥30
- **合計: ¥65〜80/本**

**品質向上オプション：**
- ElevenLabs STT: +¥10
- **合計: ¥75〜90/本**

### Q: 生成にかかる時間は？

- **最高品質**: 30-40分
- **バランス型**: 20-25分
- **速度優先**: 15-20分

### Q: エラーが出た場合は？

#### 1. APIキーを確認
```bash
# .env ファイルのAPIキーが正しいか確認
cat .env | grep API_KEY
```

#### 2. Dockerイメージを再ビルド
```bash
docker compose build
```

#### 3. ログを確認
```bash
docker compose logs
```

#### 4. よくあるエラー

**"GEMINI_API_KEY is required"**
→ `.env` にGemini APIキーを設定

**"Claude API key not found"**
→ `.env` にClaude APIキーを設定

**"Docker daemon not running"**
→ Dockerを起動

**"Memory error"**
→ Dockerのメモリ設定を増やす（8GB推奨）

---

## 🎯 次のステップ

### 1. テスト動画を確認

```bash
# 生成された動画を確認
open outputs/$(date +%Y-%m-%d)/video_001/video.mp4
```

### 2. メタデータを確認

```bash
# タイトル、説明文、タグを確認
cat outputs/$(date +%Y-%m-%d)/video_001/metadata.json
```

### 3. コメントを確認

```bash
# エンゲージメント用コメントを確認
cat outputs/$(date +%Y-%m-%d)/video_001/comments.json
```

### 4. 複数動画を生成

```bash
# .envを編集
VIDEOS_PER_DAY=4

# 実行
docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

### 5. 定期実行を設定

```bash
# crontabを編集
crontab -e

# 毎日AM 3:00に実行
0 3 * * * cd /path/to/ai-video-bot && /usr/bin/docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

---

## 📚 さらに詳しく知りたい方へ

- **[README.md](README.md)** - 完全なドキュメント
- **[TEMPLATE_SYSTEM.md](TEMPLATE_SYSTEM.md)** - テンプレートカスタマイズ
- **[QUALITY_IMPROVEMENTS.md](QUALITY_IMPROVEMENTS.md)** - 品質向上の詳細
- **[TEST_REPORT.md](TEST_REPORT.md)** - テスト結果

---

## 💡 プロからのヒント

### ヒント 1: 最初は1本生成して確認

```bash
# .envで設定
VIDEOS_PER_DAY=1
DURATION_MINUTES=5    # 短めでテスト
```

### ヒント 2: 品質設定を段階的に有効化

```bash
# まずは基本機能のみ
USE_ELEVENLABS_STT=false
USE_MOVIEPY=false

# 確認後、段階的に有効化
USE_ELEVENLABS_STT=true    # 字幕精度向上
USE_MOVIEPY=true           # 映像品質向上
```

### ヒント 3: コスト管理

```bash
# 無料枠で試す
# - Gemini: 無料枠あり
# - Claude: トライアルクレジット
# - DALL-E: $5で約166枚生成可能
```

### ヒント 4: バックアップ設定

```bash
# 生成された動画は定期的にバックアップ
cp -r outputs/ /path/to/backup/
```

---

## 🎬 サンプル出力

### 生成されるファイル

```
outputs/2025-11-26/video_001/
├── video.mp4              # 完成動画（字幕付き）
├── thumbnail.jpg          # YouTubeサムネイル
├── background.png         # 背景画像
├── dialogue.mp3           # 音声ファイル
├── script.json            # 台本（対話形式）
├── metadata.json          # YouTube用メタデータ
├── comments.json          # エンゲージメント用コメント
├── topic.json             # トピック分析結果
├── timing.json            # 字幕タイミングデータ
└── manifest.json          # 全体情報まとめ
```

### metadata.json の例

```json
{
  "youtube_title": "【徹底解説】円安が私たちの生活に与える5つの影響",
  "youtube_description": "この動画では、円安の影響について...\n\n📚 この動画で学べること：\n✅ 円安のメカニズム\n...\n\n⏱️ タイムスタンプ：\n00:00 オープニング\n...",
  "tags": ["経済", "円安", "為替", "生活", "影響"],
  "timestamps": [
    {"time": 0, "label": "オープニング"},
    {"time": 90, "label": "円安とは？"}
  ]
}
```

---

## 🚀 準備完了！

これで最初の高品質AI動画を生成する準備が整いました！

```bash
docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

Happy automating! 🎉
