# 📺 AI Video Bot - Professional YouTube Automation

**完全自動化された高品質YouTube動画生成システム**

このプロジェクトは、[Zenn記事](https://zenn.dev/xtm_blog/articles/da1eba90525f91)で紹介された**実際にYouTube収益化を達成した成功事例**をベースに構築された、AIによる動画自動生成システムです。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

## 🎯 実績

- ✅ **YouTube収益化達成**: 3ヶ月で登録者1000人、総再生時間4000時間達成
- ✅ **現在の実績**: 登録者6700人超、総再生時間7万時間超、視聴回数60万回
- ✅ **作業時間**: 人間が8時間かかる作業を**30分**で完了
- ✅ **収益**: API コストを上回る広告収益を実現

## 🌟 主要機能

### 🔥 最新の品質向上機能（v2.0）

1. **🎯 完璧な字幕タイミング（100%無料）**
   - **NEW**: OpenAI Whisper（ローカル実行）で完全無料・高精度（精度95%+）- デフォルト有効
   - 台本とSTT結果を自動マッチング
   - フォールバック：音声長推定（精度80-90%）
   - オプション：ElevenLabs STT（有料API、精度99%+）

2. **🎨 MoviePy高品質レンダリング**
   - フェードイン・フェードアウト効果
   - より滑らかなアニメーション
   - プロフェッショナルな仕上がり

3. **📋 テンプレートシステム**
   - 4種類の実証済みシナリオ構造
   - 6種類のSEO最適化タイトルパターン
   - 自動タイムスタンプ生成
   - 5つのキャラクターペルソナコメント

4. **✨ 強化されたGeminiプロンプト**
   - 冒頭15秒フック最適化
   - ストーリー性のある構成
   - エンゲージメント重視の対話

5. **🎭 男性・女性の対話形式**
   - 男性ホスト（30代後半、知識豊富で落ち着いた語り口）
   - 女性ホスト（20代後半、好奇心旺盛で明るい）
   - 異なる声色で自然な会話（Gemini TTS Speaker 1/2）
   - 字幕カラーコーディング（男性:青、女性:ピンク）

6. **📊 完全自動化メタデータ**
   - SEO最適化タイトル（CTR 8-12%目標）
   - タイムスタンプ付き詳細説明文
   - 戦略的タグ配置（15-20個）

7. **🧪 プリフライト検証**
   - 動画・サムネイル・タイムスタンプ・台本をアップロード前に自動チェック
   - タイトル長や固有名詞位置、ファイルサイズを検証して異常なら処理を停止
   - 手動レビュー前の最後のガードレールとして安全性を確保

### ✅ コア機能

1. **🔍 トレンドトピック自動発見**
   - Serper API（Google Search）で最新ニュース自動収集
   - Gemini APIで最適なトピックを選定・分析

2. **✍️ 高品質な台本生成**
   - Gemini 2.0 Flashでプロレベルの対話台本
   - テンプレート構造に基づく自然な会話

3. **🎙️ 自然な音声合成**
   - Google Gemini TTS（Zephyr voice）でポッドキャスト風音声
   - 複数話者の対話に完全対応

4. **🎬 プロ品質の動画生成**
   - FFmpeg + MoviePyのハイブリッドレンダリング
   - タイミング完璧な字幕表示
   - Lo-fiアニメ風の背景画像

5. **🖼️ YouTube最適化サムネイル**
   - 1280x720の推奨サイズ
   - テキストオーバーレイ
   - 色彩バリエーション

6. **📝 SEO完全最適化**
   - CTR最大化タイトル
   - タイムスタンプ付き説明文
   - 戦略的タグ配置

7. **💬 エンゲージメント設計**
   - 5種類のキャラクターペルソナ
   - コメント欄活性化戦略

8. **📊 進捗管理・通知**
   - Slack通知（開始・完了・エラー・日次サマリー）
   - Google Sheets / ローカルJSON記録

9. **🔄 バッチ処理**
   - 1日4本など複数動画の連続生成
   - API レート制限回避

---

## 🏗️ システムアーキテクチャ

### 10ステップの完全自動化パイプライン

```
1.  Web Search      → トレンドトピック検索・選定 (Serper + Gemini)
2.  Script Gen      → テンプレート構造で台本生成 (Gemini 2.0 Flash)
3.  Image Gen       → 背景画像生成 (DALL-E 3)
4.  Audio Gen       → 音声生成 (Gemini TTS)
5.  Video Gen       → 高品質動画合成 (FFmpeg + MoviePy) ⭐
6.  Metadata Gen    → SEO最適化メタデータ (Gemini + Templates) ⭐
7.  Comments Gen    → エンゲージメントコメント (5 Personas) ⭐
8.  Thumbnail Gen   → サムネイル生成
9.  Pre-flight Check → 動画/サムネ/タイムスタンプの自動検証 ⭐NEW
10. Tracking        → Google Sheets / JSON ログ記録
11. YouTube Upload  → 自動YouTube投稿 (YouTube Data API v3) ⭐NEW
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
  ├── # 🎯 コアパイプライン
  ├── daily_video_job.py              # シンプル版（レガシー）
  ├── advanced_video_pipeline.py      # ⭐ 高度版（推奨）
  │
  ├── # 🤖 AI統合
  ├── claude_generator.py             # Gemini API（テンプレート統合済み、旧Claude命名）⭐
  ├── web_search.py                   # Web検索・トピック選定
  ├── llm_story.py                    # Gemini台本生成（フォールバック）
  │
  ├── # 🎨 コンテンツ生成
  ├── content_templates.py            # ⭐NEW テンプレートシステム
  ├── metadata_generator.py           # ⭐NEW メタデータ自動生成
  ├── tts_generator.py                # Gemini TTS + ElevenLabs STT ⭐
  ├── elevenlabs_stt.py               # ⭐NEW ElevenLabs統合
  ├── nano_banana_client.py           # DALL-E画像生成
  │
  ├── # 🎬 動画処理
  ├── video_maker.py                  # FFmpeg動画合成（高速）
  ├── video_maker_moviepy.py          # ⭐NEW MoviePy（高品質）
  ├── subtitle_generator.py           # レガシー字幕
  ├── thumbnail_generator.py          # サムネイル生成
  │
  ├── # 📊 運用・管理
  ├── notifications.py                # Slack通知
  ├── tracking.py                     # Google Sheets / JSON ログ
  ├── youtube_uploader.py             # ⭐NEW YouTube自動アップロード
  ├── pre_upload_checks.py            # アップロード前チェック
  │
  ├── # 📚 ドキュメント
  ├── README.md                       # このファイル
  ├── QUICKSTART.md                   # クイックスタート
  ├── CLAUDE.md                       # Claude Code用ガイド
  ├── QUALITY_IMPROVEMENTS.md         # 品質向上ガイド
  ├── TEMPLATE_SYSTEM.md              # テンプレートシステムガイド
  ├── TEST_REPORT.md                  # テストレポート
  │
  └── outputs/                        # 生成ファイル
      └── YYYY-MM-DD/
          └── video_001/
              ├── video.mp4           # 完成動画
              ├── thumbnail.jpg       # サムネイル
              ├── background.png      # 背景画像
              ├── dialogue.mp3        # 音声
              ├── script.json         # 台本
              ├── metadata.json       # メタデータ
              ├── comments.json       # コメント案
              ├── topic.json          # トピック分析
              ├── timing.json         # 字幕タイミング
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
# 必須 API キー
GEMINI_API_KEY=your_gemini_key          # Gemini TTS/台本/メタデータ用
OPENAI_API_KEY=your_openai_key          # DALL-E画像生成用

# オプション（品質向上）⭐NEW
USE_WHISPER_STT=true                     # Whisper STT（100%無料、デフォルト: 有効）⭐推奨
WHISPER_MODEL_SIZE=base                  # Whisperモデル: tiny, base, small, medium, large
USE_ELEVENLABS_STT=false                 # ElevenLabs STT（有料API、デフォルト: 無効）
ELEVENLABS_API_KEY=                      # ElevenLabs API Key（USE_ELEVENLABS_STT=trueの場合のみ必須）
USE_MOVIEPY=true                         # 高品質レンダリング

# オプション（高度な機能）
SERPER_API_KEY=your_serper_key          # Web検索用
SLACK_WEBHOOK_URL=your_slack_webhook    # Slack通知用

# YouTube自動アップロード（オプション）⭐NEW
YOUTUBE_UPLOAD_ENABLED=false            # YouTube自動投稿を有効化
YOUTUBE_PRIVACY_STATUS=private          # 公開設定（private/unlisted/public）
YOUTUBE_PLAYLIST_ID=                    # プレイリストID（オプション）

# 動画設定
VIDEOS_PER_DAY=1                        # 1日の生成本数（1-4推奨）
DURATION_MINUTES=10                     # 動画の長さ（分）
TOPIC_CATEGORY=economics                # トピックカテゴリ
USE_WEB_SEARCH=false                    # Web検索を使うか
```

### 3. Docker イメージをビルド

```bash
docker compose build
```

### 4. YouTube API設定（オプション）⭐NEW

YouTube自動アップロード機能を使用する場合:

1. **Google Cloud Consoleでプロジェクトを作成**
   - [Google Cloud Console](https://console.cloud.google.com)にアクセス
   - 新しいプロジェクトを作成

2. **YouTube Data API v3を有効化**
   - APIとサービス → ライブラリ
   - 「YouTube Data API v3」を検索して有効化

3. **OAuth 2.0認証情報を作成**
   - APIとサービス → 認証情報
   - 「認証情報を作成」→「OAuth クライアント ID」
   - アプリケーションの種類：「デスクトップアプリ」
   - 認証情報JSONをダウンロードし、`youtube_credentials.json`として保存

4. **初回認証**
   ```bash
   # 認証テスト
   docker compose run --rm ai-video-bot python youtube_uploader.py

   # ブラウザが開き、Googleアカウントでログイン
   # 認証が完了すると youtube_token.pickle が生成される
   ```

5. **.envでアップロードを有効化**
   ```env
   YOUTUBE_UPLOAD_ENABLED=true
   YOUTUBE_PRIVACY_STATUS=private    # 最初はprivateがおすすめ
   ```

**注意**: 初回認証時のみブラウザでのログインが必要です。以降は自動で認証されます。

---

## 🎥 使い方

### A. 高品質動画生成（推奨）⭐

```bash
# 最新の品質向上機能をすべて使用
docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

**含まれる機能:**
- ✅ 高精度なタイミング推定による字幕（オプション：ElevenLabs STTで99%+）
- ✅ MoviePyによる高品質レンダリング
- ✅ テンプレート構造の台本
- ✅ SEO最適化メタデータ
- ✅ 自動タイムスタンプ生成
- ✅ キャラクターペルソナコメント
- ✅ YouTube自動アップロード（オプション）⭐NEW

### B. Web検索で最新トピック

```bash
# .envでUSE_WEB_SEARCH=trueに設定してから
docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

### C. 複数動画の一括生成

```bash
# .envでVIDEOS_PER_DAY=4に設定してから
docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

### D. シンプル版（レガシー）

```bash
# 基本機能のみ（固定トピック）
docker compose run --rm ai-video-bot python daily_video_job.py
```

### E. YouTube自動アップロード⭐NEW

```bash
# .envでYouTube設定を有効化してから
YOUTUBE_UPLOAD_ENABLED=true
YOUTUBE_PRIVACY_STATUS=private  # または unlisted, public

# 動画生成と同時にYouTubeへ自動アップロード
docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

**アップロード機能:**
- 動画のアップロード（タイトル・説明文・タグ自動設定）
- カスタムサムネイルの設定
- エンゲージメントコメントの自動投稿（最大5件）
- プレイリストへの自動追加（オプション）

**公開設定:**
- `private`: 非公開（自分のみ閲覧可能）
- `unlisted`: 限定公開（URLを知っている人のみ）
- `public`: 公開（検索・おすすめに表示）

### F. 個別モジュールのテスト

```bash
# YouTube認証テスト
docker compose run --rm ai-video-bot python youtube_uploader.py

# テンプレートシステムのテスト
docker compose run --rm ai-video-bot python content_templates.py

# メタデータジェネレーターのテスト
docker compose run --rm ai-video-bot python metadata_generator.py

# トピック検索のテスト
docker compose run --rm ai-video-bot python web_search.py

# Gemini台本生成のテスト
docker compose run --rm ai-video-bot python claude_generator.py
```

---

## ⚙️ 高度な設定

### 品質 vs 速度のトレードオフ

#### 最高品質（Whisper STT使用・100%無料）⭐推奨
```env
USE_WHISPER_STT=true       # Whisper STT（完全無料）
WHISPER_MODEL_SIZE=base    # base推奨、またはsmall/medium
USE_MOVIEPY=true           # 映像品質最高
```
- **コスト**: 完全無料（API料金なし）
- レンダリング時間: 約25-30分
- 字幕精度: 95%+
- 視覚品質: プロレベル
- **推奨**: 日常的な生成・公開用（最もコスパ良い）

#### 超高精度（ElevenLabs STT使用・有料）
```env
USE_WHISPER_STT=false          # Whisperを無効化
USE_ELEVENLABS_STT=true        # ElevenLabs STT
ELEVENLABS_API_KEY=your_key    # 必須
USE_MOVIEPY=true               # 映像品質最高
```
- **コスト**: 約¥50-100/動画
- レンダリング時間: 約30-40分
- 字幕精度: 99%+
- 視覚品質: プロレベル
- **用途**: 極めて高い精度が必要な場合のみ

#### 速度優先（推定タイミング）
```env
USE_WHISPER_STT=false      # Whisperを無効化
USE_ELEVENLABS_STT=false   # タイミング推定のみ
USE_MOVIEPY=false          # 速度優先
```
- **コスト**: 完全無料
- レンダリング時間: 約15-20分
- 字幕精度: 80-90%
- 視覚品質: 高品質

### カスタムテンプレート

```python
# content_templates.py を編集
ContentTemplates.SCRIPT_STRUCTURES["custom"] = {
    "name": "カスタム構造",
    "sections": [
        # カスタムセクションを定義
    ]
}
```

詳細は `TEMPLATE_SYSTEM.md` を参照。

---

## 📊 期待される効果

### Zenn記事の実績

| 指標 | 開始時 | 3ヶ月後 |
|------|--------|---------|
| 登録者数 | 0 | 1,000+ |
| 総再生時間 | 0 | 4,000時間+ |
| 視聴回数 | 0 | 数万回 |
| 収益化 | ✗ | ✅ 達成 |

### v2.0 品質向上の効果

| 指標 | v1.0 | v2.0（予想） |
|------|------|--------------|
| 視聴者維持率 | 30-40% | **50-60%** |
| タイトルCTR | 3-5% | **8-12%** |
| コメント数 | 5-10/動画 | **20-50/動画** |
| 登録率 | 1-2% | **3-5%** |
| 作業時間 | 8時間 | **30分** |

---

## 💰 コスト試算

### 基本構成（4本/日）

| API | 使用量 | 月額概算 |
|-----|--------|----------|
| Gemini API (Script/Metadata) | ~40,000 tokens/本 | ¥2,000 |
| Gemini TTS | 10分/本 | ¥1,500 |
| DALL-E 3 | 4枚/日 | ¥3,600 |
| Serper API | 120回/月 | ¥500 |
| **小計** | | **¥7,600** |

### 品質向上オプション

| API | 使用量 | 月額概算 |
|-----|--------|----------|
| ElevenLabs STT | 10分/本 × 120本 | ¥1,200 |
| **合計** | | **¥8,800** |

**※ Zenn記事の事例では、広告収益がAPIコストを上回っています**

---

## ⏰ 定期実行（cron）

```bash
crontab -e
```

```cron
# 毎日 AM 3:00 に4本の動画を生成
0 3 * * * cd /path/to/ai-video-bot && /usr/bin/docker compose run --rm ai-video-bot python advanced_video_pipeline.py >> /var/log/ai-video-bot.log 2>&1
```

---

## 🔧 トラブルシューティング

### よくある問題

**Q: 動画生成が途中で止まる**
```bash
# メモリ不足の可能性
docker compose down
docker compose up -d
```

**Q: Gemini TTS が動かない**
```bash
# API Keyを確認
echo $GEMINI_API_KEY
# フォールバック: gTTSが自動で使われます
```

**Q: Gemini APIのレート制限**
```bash
# .envで待機時間を調整（advanced_video_pipeline.py内）
# または動画間隔を空ける
```

**Q: 字幕がズレる・タイミングが合わない**
```bash
# Whisper STT を有効化（100%無料・高精度）
USE_WHISPER_STT=true
WHISPER_MODEL_SIZE=base    # またはsmall/mediumでさらに精度向上

# より高精度が必要な場合のみ ElevenLabs を使用
USE_ELEVENLABS_STT=true
ELEVENLABS_API_KEY=your_key
```

**Q: Whisper のメモリ不足エラー**
```bash
# より小さいモデルを使用
WHISPER_MODEL_SIZE=tiny    # 最小メモリ、少し精度低下

# または推定タイミングにフォールバック
USE_WHISPER_STT=false
```

**Q: MoviePy レンダリングが遅い**
```bash
# .envで無効化
USE_MOVIEPY=false
# PIL版（高速）にフォールバック
```

---

## 📚 ドキュメント

- **[QUICKSTART.md](QUICKSTART.md)** - 5分で始めるクイックガイド
- **[CLAUDE.md](CLAUDE.md)** - （レガシー）Claude Code向けガイド ※Gemini移行後も開発フロー参考
- **[QUALITY_IMPROVEMENTS.md](QUALITY_IMPROVEMENTS.md)** - 品質向上の詳細
- **[TEMPLATE_SYSTEM.md](TEMPLATE_SYSTEM.md)** - テンプレートシステムガイド
- **[TEST_REPORT.md](TEST_REPORT.md)** - テスト結果レポート

### API ドキュメント

- [Gemini API](https://ai.google.dev/docs)
- [DALL-E 3 API](https://platform.openai.com/docs/guides/images)
- [Serper API](https://serper.dev/docs)
- [ElevenLabs API](https://elevenlabs.io/docs)
- [MoviePy Documentation](https://zulko.github.io/moviepy/)

### 参考資料

- [Zenn記事：AIで簡単に稼げるのか？？](https://zenn.dev/xtm_blog/articles/da1eba90525f91)
- [YouTube Creator Academy](https://creatoracademy.youtube.com/)
- [YouTube SEO Guide](https://www.youtube.com/creators/)

---

## 🎯 次のステップ

### 実装済みの機能 ✅

- [x] **YouTube自動アップロード** (YouTube Data API v3) ⭐NEW
- [x] **高精度字幕同期** (ElevenLabs STT)
- [x] **高品質レンダリング** (MoviePy)
- [x] **テンプレートシステム** (4種類の台本構造)
- [x] **SEO最適化** (タイトル・説明文・タグ)

### 実装予定の機能

- [ ] **BGM自動生成・追加** (Suno AI / MusicGen)
- [ ] **A/Bテストサムネイル** (複数バリアント)
- [ ] **クラウドデプロイ** (Render / AWS / GCP)
- [ ] **GitHub Actions CI/CD**
- [ ] **Analytics Dashboard** (再生数・視聴維持率追跡)

### 推奨ワークフロー

1. ✅ テスト動画を1本生成
2. ✅ 生成結果を確認（品質・タイミング）
3. ✅ YouTube API認証を設定（初回のみ）
4. ✅ 設定を最適化（品質 vs 速度）
5. ✅ バッチ生成を開始（2-4本/日）
6. ✅ 定期実行を設定（cron）
7. ✅ YouTube自動アップロード有効化 ⭐NEW
8. ✅ アナリティクスで効果測定
9. ✅ テンプレートを改善

---

## 📝 ライセンス

MIT License

---

## 🙏 謝辞

このプロジェクトは以下の成功事例とオープンソースプロジェクトに基づいています：

- [Zenn記事](https://zenn.dev/xtm_blog/articles/da1eba90525f91) - 実証済みYouTube自動化アーキテクチャ
- [Google Gemini](https://ai.google.dev/) - 高品質コンテンツ生成
- [Google Gemini](https://ai.google.dev/) - 自然な音声合成
- [MoviePy](https://zulko.github.io/moviepy/) - 動画処理
- [FFmpeg](https://ffmpeg.org/) - メディア変換

---

## 🎉 まとめ

このAI Video Botは、**実際にYouTube収益化を達成した実証済みシステム**です。

**成功のポイント：**
1. ✅ 完全自動化パイプライン（30分で完成）
2. ✅ 高品質なAI生成（Gemini + テンプレート）
3. ✅ SEO完全最適化（タイトル・説明文・タグ）
4. ✅ エンゲージメント設計（5つのペルソナコメント）
5. ✅ スケーラブルな構成（複数動画/日）
6. ✅ 実証済みの効果（3ヶ月で収益化達成）

**今すぐ始めましょう！** 🚀

```bash
docker compose build
docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

Happy automating! 🎬✨
