# 毎朝7:00 AIニュース動画生成の設定代替案

cronに権限の問題があるため、以下の3つの代替案を提案します。

## アプローチA: GitHub Actions（推奨）

### メリット
- サーバーの権限不要
- GitHub上で実行履歴を確認できる
- 手動実行も可能

### 設定手順

1. **GitHub Secretsの設定**

   GitHubリポジトリで以下のSecretsを設定：
   - `GEMINI_API_KEY`
   - `SERPER_API_KEY` （任意）
   - `SLACK_WEBHOOK_URL` （任意）

2. **ワークフローの有効化**

   `.github/workflows/daily-video-generation.yml` は既に作成済みです。

3. **コミットしてプッシュ**

   ```bash
   git add .github/workflows/
   git commit -m "Add daily video generation workflow"
   git push
   ```

4. **手動テスト**

   GitHubの `Actions` タブから手動実行できます。

## アプローチB: 手動でcrontabを設定

ユーザー自身がターミナルから実行：

```bash
crontab -e
```

エディタが開いたら、以下を追加：

```bash
# 毎朝7:00にAIニュース動画を生成してYouTubeに公開
0 7 * * * cd /home/kawai/dev/ai-video-bot && ./cron-job.sh >> logs/cron.log 2>&1
```

保存して終了（viの場合: `:wq`）

## アプローチC: systemd Timer（Linuxサーバー）

### サービスファイルの作成

`~/.config/systemd/user/daily-video.service`:

```ini
[Unit]
Description=Daily AI Video Generation
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/home/kawai/dev/ai-video-bot
ExecStart=/home/kawai/dev/ai-video-bot/cron-job.sh
StandardOutput=append:/home/kawai/dev/ai-video-bot/logs/systemd.log
StandardError=append:/home/kawai/dev/ai-video-bot/logs/systemd.log
```

### タイマーファイルの作成

`~/.config/systemd/user/daily-video.timer`:

```ini
[Unit]
Description=Daily AI Video Generation Timer
Requires=daily-video.service

[Timer]
OnCalendar=*-*-* 07:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### 有効化

```bash
systemctl --user daemon-reload
systemctl --user enable daily-video.timer
systemctl --user start daily-video.timer
```

## 推奨順序

1. **まずGitHub Actionsを試す**（最も簡単）
2. それがダメなら **systemd Timer**（Linux標準）
3. 最後の手段として **手動crontab**

## 現在の状況

- ✅ `.github/workflows/daily-video-generation.yml` - 作成済み
- ✅ `cron-job.sh` - 作成済み
- ✅ `.env` - YouTube設定済み
- ⚠️ cron設定 - 権限のため未設定

## 次のステップ

どのアプローチで進めますか？
