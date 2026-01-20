#!/bin/bash
# YouTube OAuth認証URLを取得するスクリプト
# ブラウザなし環境用

set -e

SCRIPT_DIR="/home/kawai/dev/ai-video-bot"
cd "$SCRIPT_DIR" || exit 1

echo "=== YouTube OAuth認証URLの取得 ==="
echo ""
echo "このスクリプトはYouTube認証URLを取得して、別のデバイスで認証を完了する手順です。"
echo ""

# client_secret.jsonの存在確認
if [ ! -f youtube_credentials.json ]; then
    echo "❌ youtube_credentials.json が見つかりません。"
    echo ""
    echo "以下の手順で準備してください："
    echo ""
    echo "1. Google Cloud Consoleにアクセス（管理者にお願いするか、別のデバイスで）:"
    echo "   https://console.cloud.google.com/"
    echo ""
    echo "2. プロジェクトを作成または選択"
    echo ""
    echo "3. YouTube Data API v3を有効化"
    echo "   APIs & Services > Library > YouTube Data API v3 > Enable"
    echo ""
    echo "4. OAuth 2.0 クライアントIDを作成"
    echo "   APIs & Services > Credentials > Create Credentials > OAuth client ID"
    echo "   Application type: Desktop app"
    echo "   Name: ai-video-bot"
    echo ""
    echo "5. JSONをダウンロード"
    echo "   Download JSON"
    echo "   ファイル名を 'youtube_credentials.json' に変更"
    echo ""
    echo "6. このファイルを現在のディレクトリに配置:"
    echo "   $SCRIPT_DIR/youtube_credentials.json"
    echo ""
    echo "または、管理者にサービスアカウントの作成を依頼してください。"
    echo "詳細: SERVICE_ACCOUNT_SETUP.md を参照"
    echo ""
    exit 1
fi

echo "✅ youtube_credentials.json が見つかりました"
echo ""

# Pythonを使って認証URLを取得
cat > /tmp/get_auth_url.py << 'EOF'
import sys
sys.path.insert(0, '/app')

try:
    from google_auth_oauthlib.flow import InstalledAppFlow

    SCOPES = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube.force-ssl'
    ]

    flow = InstalledAppFlow.from_client_secrets_file(
        '/app/youtube_credentials.json', SCOPES)

    auth_url, _ = flow.authorization_url(
        prompt='consent',
        redirect_uri='http://localhost:8080/'
    )

    print("=" * 60)
    print("YouTube OAuth 認証URL")
    print("=" * 60)
    print()
    print("以下の手順で認証を完了してください:")
    print()
    print("1. このURLをコピーしてください:")
    print()
    print(auth_url)
    print()
    print("2. スマホや別のPCでこのURLを開いてください")
    print()
    print("3. Googleアカウントでログインして認証してください")
    print()
    print("4. 認証後、リダイレクト先のURLをコピーしてください")
    print("   (http://localhost:8080/?code=... のようなURL)")
    print()
    print("5. そのURLを以下に入力してください:")
    print()

except Exception as e:
    print(f"エラー: {e}")
    sys.exit(1)
EOF

echo "認証URLを取得します..."
echo ""

docker compose run --rm -v /tmp:/tmp ai-video-bot python /tmp/get_auth_url.py

echo ""
echo "リダイレクトURLを入力してください:"
read -p "http://localhost:8080/?code=... の形式: " redirect_url

# コードを抽出して認証を完了
cat > /tmp/complete_auth.py << 'EOF'
import sys
import re
sys.path.insert(0, '/app')

try:
    from google_auth_oauthlib.flow import InstalledAppFlow

    SCOPES = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube.force-ssl'
    ]

    flow = InstalledAppFlow.from_client_secrets_file(
        '/app/youtube_credentials.json', SCOPES)

    # リダイレクトURLからコードを抽出
    import os
    redirect_url = os.environ.get('REDIRECT_URL', '').strip()

    if 'code=' not in redirect_url:
        print("❌ 無効なURLです。http://localhost:8080/?code=... の形式である必要があります。")
        sys.exit(1)

    code = redirect_url.split('code=')[1].split('&')[0]

    print(f"コードを取得: {code[:10]}...")

    # トークンを取得
    flow.fetch_token(
        code=code,
        redirect_uri='http://localhost:8080/'
    )

    # トークンを保存
    with open('/app/youtube_token.pickle', 'wb') as token:
        import pickle
        pickle.dump(flow.credentials, token)

    print("✅ 認証が完了しました！")
    print("トークンを保存しました: youtube_token.pickle")

except Exception as e:
    print(f"❌ 認証エラー: {e}")
    sys.exit(1)
EOF

echo ""
echo "認証を完了しています..."
export REDIRECT_URL="$redirect_url"
docker compose run --rm -e REDIRECT_URL="$redirect_url" -v /tmp:/tmp ai-video-bot python /tmp/complete_auth.py

# 認証完了の確認
if [ -f youtube_token.pickle ]; then
    echo ""
    echo "✅ YouTube OAuth認証が完了しました！"
    echo ""
    ls -la youtube_token.pickle
else
    echo ""
    echo "❌ 認証に失敗しました"
fi
