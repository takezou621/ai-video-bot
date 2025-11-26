# 📺 AI Video Bot - Advanced YouTube Automation

**Automated Video Generation System using Claude + Gemini + Python**

このプロジェクトは、[Zenn記事](https://zenn.dev/xtm_blog/articles/da1eba90525f91)で紹介された成功事例をベースに、
AI動画を自動生成する高度なシステムです。

## 🌟 主要機能

### ✅ 実装済み（Zenn記事ベース）

1. **🔍 トレンドトピック自動発見**
   - Web検索APIで最新ニュース・トピックを自動収集
   - Claude APIで最適なトピックを選定・分析

2. **✍️ 高品質な台本生成**
   - Claude Sonnet/Opusで対話形式の台本を生成
   - 自然な会話調の日本語対話

3. **🎙️ 自然な音声合成**
   - Google Gemini TTS でポッドキャスト風の音声生成
   - 複数話者の対話に対応

4. **🎬 字幕付き動画生成**
   - タイミング同期された字幕表示
   - Lo-fiアニメ風の背景画像

5. **🖼️ サムネイル自動生成**
   - YouTube最適化されたサムネイル
   - テキストオーバーレイ対応

6. **📝 メタデータ最適化**
   - SEO最適化されたタイトル・説明文
   - タグ・ハッシュタグ自動生成

7. **💬 エンゲージメント強化**
   - 視聴者を惹きつけるコメント自動生成

8. **📊 進捗管理・通知**
   - Slack通知（開始・完了・エラー・日次サマリー）
   - Google Sheets または ローカルJSONでログ記録

9. **🔄 複数動画一括生成**
   - 1日4本など、複数動画の連続生成に対応

---

## 🏗️ システムアーキテクチャ

### 9ステップの自動生成パイプライン

```
1. Web Search      → トレンドトピック検索・選定 (Claude)
2. Script Gen      → 対話台本生成 (Claude Opus/Sonnet)
3. Image Gen       → 背景画像生成 (DALL-E 3 / Gemini)
4. Audio Gen       → 音声生成 (Gemini TTS)
5. Video Gen       → 字幕付き動画合成 (FFmpeg)
6. Metadata Gen    → メタデータ生成 (Claude Sonnet)
7. Comments Gen    → エンゲージメントコメント生成 (Claude)
8. Thumbnail Gen   → サムネイル生成
9. Logging         → Sheets/JSON記録 + Slack通知
```

---

## 🗂️ ディレクトリ構成

```
ai-video-bot/
  ├── Dockerfile
  ├── docker-compose.yml
  ├── requirements.txt
  ├── .env.sample
  │
  ├── # Core modules
  ├── daily_video_job.py              # 旧版シンプル生成
  ├── advanced_video_pipeline.py      # 🆕 新版高度な生成パイプライン
  │
  ├── # Content generation
  ├── web_search.py                   # 🆕 Web検索・トピック選定
  ├── claude_generator.py             # 🆕 Claude API統合
  ├── llm_story.py                    # Gemini台本生成（フォールバック）
  ├── tts_generator.py                # Gemini TTS音声生成
  ├── nano_banana_client.py           # DALL-E画像生成
  │
  ├── # Video processing
  ├── video_maker.py                  # 動画合成
  ├── subtitle_generator.py           # 字幕生成（レガシー）
  ├── thumbnail_generator.py          # 🆕 サムネイル生成
  │
  ├── # Monitoring & logging
  ├── notifications.py                # 🆕 Slack通知
  ├── tracking.py                     # 🆕 Google Sheets / JSON ログ
  │
  └── outputs/                        # 生成ファイル出力先
      └── YYYY-MM-DD/
          └── video_001/
              ├── video.mp4           # 完成動画
              ├── thumbnail.jpg       # サムネイル
              ├── script.json         # 台本
              ├── metadata.json       # メタデータ
              ├── comments.json       # コメント案
              └── manifest.json       # 全体情報
```

---

## 🚀 セットアップ

### 1. リポジトリをクローン

```bash
git clone <repository-url>
cd ai-video-bot
```

### 2. 環境変数を設定

```bash
cp .env.sample .env
```

`.env` ファイルを編集：

```env
# 必須
GEMINI_API_KEY=your_gemini_key          # Gemini TTS用
CLAUDE_API_KEY=your_claude_key          # Claude AI用
OPENAI_API_KEY=your_openai_key          # DALL-E画像生成用

# オプション（高度な機能）
SERPER_API_KEY=your_serper_key          # Web検索用（任意）
SLACK_WEBHOOK_URL=your_slack_webhook    # Slack通知用（任意）

# 動画設定
VIDEOS_PER_DAY=1                        # 1日の生成本数（1-4推奨）
DURATION_MINUTES=10                     # 動画の長さ（分）
TOPIC_CATEGORY=economics                # トピックカテゴリ
USE_WEB_SEARCH=false                    # Web検索を使うか（true/false）
```

### 3. Docker イメージをビルド

```bash
docker compose build
```

---

## 🎥 使い方

### A. シンプル生成（従来版）

1本の動画を生成（ノスタルジー系固定テーマ）：

```bash
docker compose run --rm ai-video-bot python daily_video_job.py
```

### B. 高度な生成（新版・推奨）

**1本だけ生成（Web検索なし）：**

```bash
docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

**1本生成（Web検索あり）：**

```bash
# .envでUSE_WEB_SEARCH=trueに設定してから
docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

**複数動画を一括生成（例：4本）：**

```bash
# .envでVIDEOS_PER_DAY=4に設定してから
docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

### C. 個別モジュールのテスト

```bash
# トピック検索のテスト
docker compose run --rm ai-video-bot python web_search.py

# Claude台本生成のテスト
docker compose run --rm ai-video-bot python claude_generator.py

# サムネイル生成のテスト
docker compose run --rm ai-video-bot python thumbnail_generator.py
```

---

## ⏰ 定期実行（cron）

毎日自動で複数動画を生成する設定例：

### crontab設定

```bash
crontab -e
```

```cron
# 毎日 AM 3:00 に4本の動画を生成
0 3 * * * cd /path/to/ai-video-bot && /usr/bin/docker compose run --rm ai-video-bot python advanced_video_pipeline.py >> /var/log/ai-video-bot.log 2>&1
```

---

## 📊 出力ファイル

生成される動画は以下のように整理されます：

```
outputs/
  2025-11-26/
    video_001/
      ├── video.mp4              # 完成動画（字幕付き）
      ├── thumbnail.jpg          # YouTubeサムネイル
      ├── background.png         # 背景画像
      ├── dialogue.mp3           # 音声ファイル
      ├── script.json            # 台本（対話形式）
      ├── metadata.json          # YouTube用メタデータ
      ├── comments.json          # エンゲージメント用コメント案
      ├── topic.json             # トピック分析結果
      ├── timing.json            # 字幕タイミングデータ
      └── manifest.json          # 全体情報まとめ
    video_002/
      └── ...
```

---

## 🧠 各コンポーネントの詳細

### 1. **web_search.py** - トピック自動発見

- Serper API（Google Search）で最新ニュースを検索
- Claude APIで最適なトピックを選定・分析
- フォールバックトピック対応

### 2. **claude_generator.py** - Claude AI統合

- **台本生成**：Claude Sonnet/Opusで自然な対話を生成
- **メタデータ生成**：SEO最適化されたタイトル・説明文
- **コメント生成**：視聴者エンゲージメント向上用コメント

### 3. **tts_generator.py** - 音声生成

- Gemini TTS（Zephyr voice）でポッドキャスト風音声
- gTTSフォールバック対応
- タイミングデータ自動生成

### 4. **video_maker.py** - 動画合成

- FFmpegで高品質な動画合成
- タイミング同期された字幕表示
- Lo-fiアニメ風のビジュアル

### 5. **thumbnail_generator.py** - サムネイル生成

- YouTube推奨サイズ（1280x720）
- テキストオーバーレイ
- 複数バリエーション生成

### 6. **notifications.py** - Slack通知

- 動画生成開始・完了通知
- エラー通知
- 日次サマリー

### 7. **tracking.py** - ログ・トラッキング

- Google Sheets連携（オプション）
- ローカルJSON記録
- CSV出力

---

## 🔧 カスタマイズ

### トピックカテゴリの変更

`.env`で変更：

```env
TOPIC_CATEGORY=technology    # technology, culture, lifestyle等
```

### 動画の長さ調整

```env
DURATION_MINUTES=15          # 5〜30分推奨
```

### 1日の生成本数

```env
VIDEOS_PER_DAY=4            # Zenn記事と同じく4本/日
```

---

## 📦 拡張ポイント

現在のシステムに追加可能な機能：

- [ ] **YouTube自動アップロード** (YouTube Data API v3)
- [ ] **BGM自動生成・追加** (Suno AI / MusicGen)
- [ ] **Speech-to-Text字幕同期** (Whisper API)
- [ ] **A/Bテストサムネイル** (複数バリアント)
- [ ] **クラウドデプロイ** (Render / AWS / GCP)
- [ ] **GitHub Actions CI/CD**
- [ ] **Analytics Dashboard** (再生数・視聴維持率追跡)

---

## 🧩 推奨動作環境

### ローカル

- Docker / Docker Compose v2
- ffmpeg インストール済み
- 8GB+ RAM推奨

### クラウド（例：Render）

```yaml
# render.yaml (例)
services:
  - type: cron
    name: ai-video-bot
    env: docker
    schedule: "0 3 * * *"  # 毎日3AM
    dockerfilePath: ./Dockerfile
    envVars:
      - key: GEMINI_API_KEY
        sync: false
```

---

## 💰 コスト試算（参考）

| API | 使用量（4本/日） | 月額概算 |
|-----|-----------------|----------|
| Claude API | ~40,000 tokens/本 | ¥2,000〜 |
| Gemini TTS | 10分/本 | ¥1,500〜 |
| DALL-E 3 | 4枚/日 | ¥3,600 |
| Serper API | 120回/月 | ¥500 |
| **合計** | | **¥7,600〜** |

※ Zenn記事の事例では、広告収益がAPIコストを上回っています

---

## 📞 サポート・参考情報

### 参考記事

- [Zenn記事：AIで簡単に稼げるのか？？（YouTube収益化まで3ヶ月）](https://zenn.dev/xtm_blog/articles/da1eba90525f91)

### API ドキュメント

- [Claude API](https://docs.anthropic.com/)
- [Gemini API](https://ai.google.dev/docs)
- [DALL-E 3 API](https://platform.openai.com/docs/guides/images)
- [Serper API](https://serper.dev/docs)

### トラブルシューティング

**Q: 動画生成が途中で止まる**
- メモリ不足の可能性：`docker compose down && docker compose up -d`

**Q: Gemini TTS が動かない**
- API Keyの確認：`.env`のGEMINI_API_KEYが正しいか
- フォールバック：gTTSが自動で使われます

**Q: Claude APIのレート制限**
- `.env`でモデルをOpus→Sonnet→Haikuに変更
- 動画間のwait時間を増やす（`time.sleep(60)`等）

---

## 📝 ライセンス

MIT License

---

## 🎯 まとめ

このプロジェクトは、実際にYouTube収益化を達成したZenn記事のアーキテクチャを実装しています。

**成功のポイント：**
1. ✅ 完全自動化パイプライン
2. ✅ 高品質なAI生成（Claude + Gemini）
3. ✅ SEO最適化されたメタデータ
4. ✅ エンゲージメント設計
5. ✅ スケーラブルな構成（複数動画/日）

**次のステップ：**
- YouTube自動アップロード実装
- Analytics追跡
- A/Bテスト最適化

Happy automating! 🚀
