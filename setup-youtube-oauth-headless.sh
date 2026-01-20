#!/bin/bash
# YouTube OAuthヘッドレス認証スクリプト
# ブラウザなしでOAuth認証を行う

set -e

SCRIPT_DIR="/home/kawai/dev/ai-video-bot"
cd "$SCRIPT_DIR" || exit 1

echo "=== YouTube OAuth ヘッドレス認証 ==="
echo ""
echo "このスクリプトはブラウザなしでYouTube OAuth認証を行います。"
echo "認証には以下のいずれかが必要です："
echo "  1. 別のマシンで認証URLを開く"
echo "  2. スマホで認証URLを開く"
echo "  3. サービスアカウントを使用（管理者にお願いする）"
echo ""

# YouTube認証スクリプトを実行（Docker環境）
echo "YouTube OAuth認証を開始します..."
echo "認証URLが表示されるので、それをコピーして別の方法で開いてください。"
echo ""

docker compose run --rm ai-video-bot python youtube_uploader.py

# 認証完了の確認
if [ -f youtube_token.pickle ] && [ -f youtube_credentials.json ]; then
    echo ""
    echo "✅ 認証が完了しました！"
    echo ""
    echo "認証ファイル:"
    ls -la youtube_token.pickle youtube_credentials.json
    echo ""
    echo "次のステップ:"
    echo "  テスト実行: ./cron-job.sh"
else
    echo ""
    echo "❌ 認証に失敗しました。"
    echo ""
    echo "代替案: サービスアカウントを使用"
    echo "  管理者にGoogle Cloud Consoleでサービスアカウントを作成してもらってください。"
fi
