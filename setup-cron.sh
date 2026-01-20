#!/bin/bash
# 毎朝7:00のAIニュース動画生成を設定するスクリプト

echo "=== 毎朝7:00 AIニュース動画生成の設定 ==="
echo ""
echo "このスクリプトはcrontabに毎朝7:00の動画生成ジョブを追加します。"
echo ""
echo "追加されるジョブ:"
echo "  毎朝7:00 JST に cron-job.sh を実行"
echo ""
echo "現在のcrontab:"
crontab -l 2>/dev/null || echo "# (まだcrontabは設定されていません)"
echo ""
echo "-----------------------------------"
read -p "続行しますか？ (y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "キャンセルしました。"
    exit 0
fi

echo ""
echo "crontabを設定します..."
echo ""

# 既存のcrontabを取得（daily_videoの行は除外）
existing_cron=$(crontab -l 2>/dev/null | grep -v "daily_video" || true)

# 新しいcrontabを作成
new_cron="$existing_cron

# 毎朝7:00にAIニュース動画を生成してYouTubeに公開
0 7 * * * cd /home/kawai/dev/ai-video-bot && ./cron-job.sh >> logs/cron.log 2>&1"

# crontabを設定
echo "$new_cron" | crontab -

echo ""
echo "✅ crontabが設定されました！"
echo ""
echo "設定内容の確認:"
crontab -l | grep -E "daily_video|^# .*7:00"
echo ""
echo "-----------------------------------"
echo "次のステップ:"
echo "1. 明日の朝7:00に自動実行されます"
echo "2. ログは logs/daily_video_YYYYMMDD_HHMMSS.log に保存されます"
echo "3. 手動実行テスト: ./cron-job.sh"
echo ""
echo "実行中のジョブを確認:"
echo "  ps aux | grep advanced_video_pipeline"
echo ""
echo "ログの確認:"
echo "  tail -f logs/daily_video_*.log"
