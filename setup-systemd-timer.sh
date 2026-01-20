#!/bin/bash
# systemd Timerを使った毎朝7:00の動画生成設定
# ユーザー権限で実行可能

set -e

SCRIPT_DIR="/home/kawai/dev/ai-video-bot"
SERVICE_DIR="$HOME/.config/systemd/user"

echo "=== systemd Timerの設定 ==="
echo ""

# ディレクトリの作成
mkdir -p "$SERVICE_DIR"

# サービスファイルの作成
cat > "$SERVICE_DIR/daily-video.service" << 'EOF'
[Unit]
Description=Daily AI Video Generation and YouTube Upload
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/home/kawai/dev/ai-video-bot
ExecStart=/home/kawai/dev/ai-video-bot/cron-job.sh
StandardOutput=append:/home/kawai/dev/ai-video-bot/logs/systemd.log
StandardError=append:/home/kawai/dev/ai-video-bot/logs/systemd.log
EOF

# タイマーファイルの作成
cat > "$SERVICE_DIR/daily-video.timer" << 'EOF'
[Unit]
Description=Daily AI Video Generation Timer
Requires=daily-video.service

[Timer]
OnCalendar=*-*-* 07:00:00
Persistent=true
AccuracySec=1h

[Install]
WantedBy=timers.target
EOF

echo "✅ サービスファイルを作成しました:"
echo "  $SERVICE_DIR/daily-video.service"
echo "  $SERVICE_DIR/daily-video.timer"
echo ""

# systemdデーモンのリロード
echo "systemdデーモンをリロードします..."
systemctl --user daemon-reload

# タイマーの有効化
echo "タイマーを有効化します..."
systemctl --user enable daily-video.timer

# タイマーの開始
echo "タイマーを開始します..."
systemctl --user start daily-video.timer

echo ""
echo "✅ 設定が完了しました！"
echo ""
echo "確認コマンド:"
echo "  タイマーの状態: systemctl --user status daily-video.timer"
echo "  次回の実行: systemctl --user list-timers"
echo "  ログ: tail -f logs/systemd.log"
echo ""
echo "手動実行テスト:"
echo "  systemctl --user start daily-video.service"
echo ""
echo "ログの確認:"
echo "  journalctl --user -u daily-video.service -f"
echo ""
echo "⚠️  注意:"
echo "  systemdユーザーセッションが有効である必要があります。"
echo "  lingerが有効でない場合、ログアウト後にタイマーが停止する可能性があります。"
echo ""
echo "  lingerを有効にするには:"
echo "  sudo loginctl enable-linger kawai"
echo ""
