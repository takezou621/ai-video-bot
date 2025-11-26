#!/bin/bash
# YouTube OAuth 再認証スクリプト

echo "=========================================="
echo "  YouTube API 再認証"
echo "=========================================="
echo ""
echo "このスクリプトは、YouTubeへの動画アップロード権限を"
echo "新しいスコープで再認証します。"
echo ""
echo "⚠️  事前準備:"
echo "1. Google Cloud Console で OAuth同意画面のスコープを更新済みか確認"
echo "2. 以下のスコープが追加されているか確認:"
echo "   - https://www.googleapis.com/auth/youtube.upload"
echo "   - https://www.googleapis.com/auth/youtube.force-ssl"
echo ""
read -p "準備ができたら Enter キーを押してください..."

cd "$(dirname "$0")"

echo ""
echo "🔐 認証プロセスを開始します..."
echo "ブラウザが開きますので、Googleアカウントでログインしてください。"
echo ""

# Activate virtual environment
source venv/bin/activate

# Run authentication
python3 youtube_uploader.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 認証成功！"
    echo "=========================================="
    echo ""
    echo "次のステップ:"
    echo "1. 動画をアップロードする:"
    echo "   python3 advanced_video_pipeline.py"
    echo ""
    echo "2. または既存の動画をアップロード:"
    echo "   python3 -c 'from youtube_uploader import upload_video_with_metadata; ...'"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ 認証失敗"
    echo "=========================================="
    echo ""
    echo "トラブルシューティング:"
    echo "1. Google Cloud Console で OAuth同意画面のスコープを確認"
    echo "2. youtube_credentials.json が正しいか確認"
    echo "3. インターネット接続を確認"
    echo ""
fi
