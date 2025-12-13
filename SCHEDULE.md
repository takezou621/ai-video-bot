# AI Video Bot - 自動実行スケジュール設定

## 概要

毎朝6時に最新AIニュースの動画を自動生成してYouTubeに公開する設定が完了しています。

## 設定ファイル

### 1. 実行スクリプト
- **場所**: `/Users/kawai/dev/ai-video-bot/run_daily_video.sh`
- **機能**: Docker経由で動画生成パイプラインを実行し、ログを記録

### 2. launchd設定
- **場所**: `~/Library/LaunchAgents/com.ai-video-bot.daily.plist`
- **スケジュール**: 毎日 6:00 AM
- **ログ**: `/Users/kawai/dev/ai-video-bot/logs/`

## 管理コマンド

### スケジュール確認
```bash
launchctl list | grep ai-video-bot
```

### スケジュール停止
```bash
launchctl unload ~/Library/LaunchAgents/com.ai-video-bot.daily.plist
```

### スケジュール再開
```bash
launchctl load ~/Library/LaunchAgents/com.ai-video-bot.daily.plist
```

### 手動実行（テスト用）
```bash
/Users/kawai/dev/ai-video-bot/run_daily_video.sh
```

### ログ確認
```bash
# 本日のログ
cat /Users/kawai/dev/ai-video-bot/logs/daily-video-$(date +%Y-%m-%d).log

# launchdのログ
cat /Users/kawai/dev/ai-video-bot/logs/launchd-stdout.log
cat /Users/kawai/dev/ai-video-bot/logs/launchd-stderr.log

# 最新10ファイルのリスト
ls -lt /Users/kawai/dev/ai-video-bot/logs/ | head -10
```

## ログの保存期間

- 実行ログは30日間保存されます
- 古いログは自動的に削除されます

## トラブルシューティング

### 実行されない場合

1. **launchdジョブの状態確認**
   ```bash
   launchctl list com.ai-video-bot.daily
   ```

2. **スクリプトの実行権限確認**
   ```bash
   ls -l /Users/kawai/dev/ai-video-bot/run_daily_video.sh
   ```
   実行権限がない場合:
   ```bash
   chmod +x /Users/kawai/dev/ai-video-bot/run_daily_video.sh
   ```

3. **Dockerの起動確認**
   ```bash
   docker ps
   ```

4. **エラーログ確認**
   ```bash
   cat /Users/kawai/dev/ai-video-bot/logs/launchd-stderr.log
   ```

### スケジュール時刻の変更

`~/Library/LaunchAgents/com.ai-video-bot.daily.plist` の以下の部分を編集:

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>6</integer>  <!-- 時刻を変更（0-23） -->
    <key>Minute</key>
    <integer>0</integer>  <!-- 分を変更（0-59） -->
</dict>
```

変更後は再読み込み:
```bash
launchctl unload ~/Library/LaunchAgents/com.ai-video-bot.daily.plist
launchctl load ~/Library/LaunchAgents/com.ai-video-bot.daily.plist
```

## 動画生成の設定

動画の内容は `.env` ファイルで設定できます:

```bash
# 1日に生成する動画数
VIDEOS_PER_DAY=1

# 動画の長さ（分）
DURATION_MINUTES=5

# トピックカテゴリ
TOPIC_CATEGORY=ai_news

# Web検索を使用
USE_WEB_SEARCH=true

# YouTube自動アップロード
YOUTUBE_UPLOAD_ENABLED=true
YOUTUBE_PRIVACY_STATUS=public
```

## セキュリティに関する注意

- このスケジュールはユーザーがログインしている時のみ実行されます
- マシンをスリープさせると実行されません
- 常に実行したい場合は、macOSの「省エネルギー」設定でスリープを無効にしてください

## 次回実行予定

次回の実行は **明日の 6:00 AM** です。

実行予定を確認:
```bash
# launchdは次回実行時刻を直接表示しませんが、
# 翌朝6時に自動実行されます
echo "次回実行: $(date -v+1d '+%Y-%m-%d') 06:00"
```
