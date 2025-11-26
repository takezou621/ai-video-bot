# 🚀 クイックスタートガイド

## 最速で1本生成する手順

### 1. 環境変数を設定

```bash
cp .env.sample .env
```

`.env`ファイルを編集して最低限のAPIキーを設定：

```env
# 必須（どれか1つでOK）
GEMINI_API_KEY=your_gemini_key_here
CLAUDE_API_KEY=your_claude_key_here
OPENAI_API_KEY=your_openai_key_here
```

### 2. 動画を生成

#### A. シンプル版（従来の方法）

```bash
docker compose run --rm ai-video-bot python daily_video_job.py
```

#### B. 高度版（推奨・Zenn記事の方法）

```bash
docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

### 3. 出力を確認

```bash
ls -la outputs/$(date +%Y-%m-%d)/
```

動画は `outputs/YYYY-MM-DD/video_001/video.mp4` に生成されます。

---

## 各APIキーの取得方法

### Gemini API（音声生成用）

1. [Google AI Studio](https://aistudio.google.com/app/apikey) にアクセス
2. "Get API Key" をクリック
3. キーをコピーして `.env` の `GEMINI_API_KEY` に設定

### Claude API（台本生成用）

1. [Anthropic Console](https://console.anthropic.com/) にアクセス
2. "Get API Keys" から新しいキーを作成
3. キーをコピーして `.env` の `CLAUDE_API_KEY` に設定

### OpenAI API（画像生成用）

1. [OpenAI Platform](https://platform.openai.com/api-keys) にアクセス
2. "Create new secret key" をクリック
3. キーをコピーして `.env` の `OPENAI_API_KEY` に設定

---

## オプション機能を有効にする

### Web検索で最新トピックを自動発見

1. [Serper.dev](https://serper.dev/) でアカウント作成
2. APIキーを取得
3. `.env` に設定：

```env
SERPER_API_KEY=your_serper_key
USE_WEB_SEARCH=true
TOPIC_CATEGORY=economics
```

### Slack通知を有効にする

1. Slackワークスペースで Incoming Webhook を作成
2. Webhook URLを取得
3. `.env` に設定：

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## よくある質問

**Q: どのAPIキーが必須ですか？**

最低限、以下のどれか1つがあれば動作します：
- `GEMINI_API_KEY` - 音声生成とフォールバック台本に使用
- `CLAUDE_API_KEY` - 高品質な台本生成に使用（推奨）

画像生成は `OPENAI_API_KEY` がなくてもダミー画像で動作します。

**Q: 動画1本あたりのコストは？**

概算（10分動画）：
- Claude API: ¥20〜30
- Gemini TTS: ¥15〜20
- DALL-E 3: ¥30
- 合計: ¥65〜80/本

**Q: 生成にかかる時間は？**

- シンプル版: 5〜10分
- 高度版: 15〜30分（APIレスポンス次第）

**Q: エラーが出た場合は？**

1. `.env` のAPIキーが正しいか確認
2. `docker compose build` でイメージを再ビルド
3. ログを確認: `docker compose logs`

---

## 次のステップ

1. **複数動画生成**: `.env` で `VIDEOS_PER_DAY=4` に設定
2. **cron で自動化**: README の cron 設定例を参照
3. **YouTube アップロード**: `youtube_uploader.py` を実装（TODO）

詳細は [README.md](README.md) を参照してください。
