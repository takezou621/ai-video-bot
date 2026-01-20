# 毎朝7:00 AIニュース動画自動生成設定

毎朝7:00にAIニュース動画を生成してYouTubeに公開するための設定手順です。

## 前提条件

1. YouTube Data API v3のOAuth認証が完了していること
2. `.env`ファイルで`YOUTUBE_UPLOAD_ENABLED=true`に設定されていること
3. 必要なAPIキー（GEMINI_API_KEY, SERPER_API_KEY等）が設定されていること

## アプローチ1: GitHub Actions（推奨）

### メリット
- GitHub上で実行履歴を確認できる
- 手動実行も可能
- サーバーリソースを消費しない

### 設定手順

1. **GitHub Secretsの設定**

   GitHubリポジトリの `Settings` > `Secrets and variables` > `Actions` で以下のSecretsを追加：

   ```bash
   GEMINI_API_KEY=your_gemini_api_key
   SERPER_API_KEY=your_serper_api_key
   SLACK_WEBHOOK_URL=your_slack_webhook_url  # 任意
   ```

2. **ワークフローの有効化**

   `.github/workflows/daily-video-generation.yml`は既に作成されています。

   次回のコミットで自動的に有効化されます。

3. **手動実行テスト**

   GitHubの `Actions` タブ > `Daily AI Video Generation` > `Run workflow` で手動実行できます。

### スケジュール

- 毎朝7:00 JST（前日の22:00 UTC）に実行
- 日本時間の朝7:00に動画が生成されます

## アプローチ2: サーバーCronジョブ（シンプル）

### メリット
- 設定が簡単
- サーバー上で直接実行される
- ローカルファイルシステムへのアクセスが容易

### 設定手順

1. **crontabを編集**

   ```bash
   crontab -e
   ```

2. **以下の行を追加**

   ```bash
   # 毎朝7:00に動画を生成
   0 7 * * * cd /home/kawai/dev/ai-video-bot && ./cron-job.sh >> logs/cron.log 2>&1
   ```

3. **cronを再読み込み**

   ```bash
   sudo systemctl restart cron
   ```

### ログの確認

```bash
# 最新のログ
tail -f logs/daily_video_*.log

# cronのログ
sudo grep CRON /var/log/syslog | grep daily_video
```

## 共通の設定

### .envファイルの設定

```bash
# YouTubeアップロードを有効化
YOUTUBE_UPLOAD_ENABLED=true
YOUTUBE_PRIVACY_STATUS=public
YOUTUBE_POST_COMMENTS=true

# 動画生成設定
VIDEOS_PER_DAY=1
DURATION_MINUTES=10
TOPIC_CATEGORY=ai_news

# Web検索を有効化（最新のAIニュースを取得）
USE_WEB_SEARCH=true
SERPER_API_KEY=your_serper_api_key

# 通知（任意）
SLACK_WEBHOOK_URL=your_slack_webhook_url
```

### YouTube OAuth認証の初期設定

まだ設定していない場合：

```bash
docker compose run --rm ai-video-bot python youtube_uploader.py
```

ブラウザが開き、Googleアカウントで認証を行います。

認証が成功すると、`youtube_token.pickle`と`youtube_credentials.json`が作成されます。

### 既存のトークンがある場合

```bash
ls -la youtube_*.pickle youtube_*.json
```

ファイルが存在する場合は、既に認証済みです。

## 動作確認

### 手動実行テスト

```bash
# cronスクリプトをテスト
./cron-job.sh

# または直接Dockerで実行
docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

### スケジュールの確認

```bash
# cronの設定を確認
crontab -l | grep daily_video
```

## トラブルシューティング

### 動画が生成されない

1. **ログを確認**
   ```bash
   tail -100 logs/daily_video_*.log
   ```

2. **Dockerコンテナの状態を確認**
   ```bash
   docker compose ps
   docker compose logs --tail=50 ai-video-bot
   ```

3. **環境変数を確認**
   ```bash
   docker compose config
   ```

### YouTubeアップロードが失敗する

1. **OAuthトークンの有効期限を確認**
   ```bash
   ls -la youtube_token.pickle youtube_credentials.json
   ```

2. **再認証**
   ```bash
   rm youtube_token.pickle youtube_credentials.json
   docker compose run --rm ai-video-bot python youtube_uploader.py
   ```

### GitHub Actionsが実行されない

1. **ワークフローファイルを確認**
   - `.github/workflows/daily-video-generation.yml`が存在するか

2. **GitHub Actionsが有効になっているか**
   - `Settings` > `Actions` > `General` > `Actions permissions` = `Allow all actions and reusable workflows`

3. **Secretsが設定されているか**
   - `Settings` > `Secrets and variables` > `Actions`

## 監視と通知

### Slack通知

SlackのIncoming Webhookを設定すると、動画生成の開始/完了/エラーが通知されます。

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### ログのローテーション

```bash
# logrotateの設定（オプション）
sudo nano /etc/logrotate.d/ai-video-bot
```

```
/home/kawai/dev/ai-video-bot/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

## 次のステップ

1. **アプローチを選択**: GitHub Actions または Cronジョブ
2. **設定を完了**: 上記の手順に従って設定
3. **テスト実行**: 手動で実行して動作を確認
4. **初回スケジュール実行**: 翌朝7:00に自動実行されるか確認

## サポート

問題が発生した場合は、以下を確認してください：

1. [GitHub Issues](https://github.com/takezou621/ai-video-bot/issues)
2. ログファイル: `logs/daily_video_*.log`
3. Dockerログ: `docker compose logs ai-video-bot`
