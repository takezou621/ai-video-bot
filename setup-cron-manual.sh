#!/bin/bash
# Cron設定スクリプト（ユーザー実行用）

echo "=== 毎朝7:00 AIニュース動画生成のCron設定 ==="
echo ""

# 現在のcrontabを取得
echo "現在のcrontab:"
crontab -l 2>/dev/null || echo "# (まだcrontabは設定されていません)"
echo ""

# 新しいcronジョブを表示
echo "追加するcronジョブ:"
echo "--------------------------------------------------"
cat << 'CRON_JOB'
# 毎朝7:00にAIニュース動画を生成してYouTubeに公開
0 7 * * * cd /home/kawai/dev/ai-video-bot && ./cron-job.sh >> logs/cron.log 2>&1
CRON_JOB
echo "--------------------------------------------------"
echo ""

# 手動設定の手順を表示
echo "設定手順:"
echo "1. 以下のコマンドを実行してcrontabを開きます:"
echo "   crontab -e"
echo ""
echo "2. エディタが開いたら、最後に以下の行を追加してください:"
echo ""
echo "   # 毎朝7:00にAIニュース動画を生成してYouTubeに公開"
echo "   0 7 * * * cd /home/kawai/dev/ai-video-bot && ./cron-job.sh >> logs/cron.log 2>&1"
echo ""
echo "3. 保存してエディタを終了します（viの場合: :wq）"
echo ""
echo "または、以下のコマンドで一括設定できます:"
echo ""
echo "   (crontab -l 2>/dev/null; echo '# 毎朝7:00にAIニュース動画を生成してYouTubeに公開'; echo '0 7 * * * cd /home/kawai/dev/ai-video-bot && ./cron-job.sh >> logs/cron.log 2>&1') | crontab -"
echo ""
echo "設定後に確認:"
echo "   crontab -l"
echo ""
