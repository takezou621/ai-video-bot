# サービスアカウントを使用したYouTube認証（ブラウザなし）

## 概要

ブラウザが使えない環境向けに、Googleサービスアカウントを使用したYouTube認証の設定手順です。

## 手順

### 1. 管理者に依頼する内容

以下の内容を管理者(root権限)に依頼してください：

#### 依頼内容

```
YouTube動画の自動アップロードのため、Googleサービスアカウントの作成をお願いします。

プロジェクト: ai-video-bot
必要な権限: YouTube Data API v3

以下の手順で作成したJSONキーファイルをいただければ、設定できます。
```

### 2. 管理者向けの詳細手順

管理者に以下のドキュメントを共有してください：

#### Google Cloud Consoleでの作業

1. **Google Cloud Consoleにアクセス**

   https://console.cloud.google.com/

2. **新しいプロジェクトを作成**

   - プロジェクト名: `ai-video-bot`
   - 組織を選択（個人または組織）

3. **YouTube Data API v3を有効化**

   - 「APIとサービス」>「YouTube Data API v3」>「有効にする」

4. **サービスアカウントを作成**

   - 「IAMと管理」>「サービスアカウント」>「サービスアカウントを作成」
   - サービスアカウント名: `youtube-uploader`
   - ロール: `プロジェクト > オーナー` または `プロジェクト > 編集者`

5. **JSONキーを作成**

   - サービスアカウントの詳細ページ>「キー」>「キーを追加」
   - キーのタイプ: `JSON`
   - ダウンロードして `youtube_service_account.json` という名前で保存

6. **YouTubeチャンネルへの権限付与**

   - サービスアカウントのメールアドレスをコピー
   - YouTube Studio (https://studio.youtube.com/) にアクセス
   - 「設定」>「チャンネルの権限」>「招待」
   - サービスアカウントのメールアドレスを追加
   - 役割: 「マネージャー」

### 3. JSONキーの受け取り

管理者から `youtube_service_account.json` を受け取り、プロジェクトのルートディレクトリに配置します：

```bash
mv ~/downloads/youtube_service_account.json /home/kawai/dev/ai-video-bot/
chmod 600 /home/kawai/dev/ai-video-bot/youtube_service_account.json
```

### 4. 認証スクリプトの修正

サービスアカウントを使用するには、`youtube_uploader.py` を修正する必要があります。

または、以下の環境変数を設定：

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/home/kawai/dev/ai-video-bot/youtube_service_account.json
```

### 5. テスト

```bash
cd /home/kawai/dev/ai-video-bot
docker compose run --rm -e GOOGLE_APPLICATION_CREDENTIALS=/app/youtube_service_account.json ai-video-bot python youtube_uploader.py
```

## 注意事項

- サービスアカウントはブラウザを使わずに認証できます
- しかし、最初の設定はGoogle Cloud Consoleで行う必要があります
- YouTubeチャンネルへの権限付与も必要です
- セキュリティのため、JSONキーファイルは安全に管理してください（`.gitignore`に追加済み）

## トラブルシューティング

### 権限エラー

```
Error: The caller does not have permission
```

解決策:
- サービスアカウントがYouTubeチャンネルに追加されているか確認
- 役割が「マネージャー」または「オーナー」であることを確認

### 認証エラー

```
Error: Could not automatically determine credentials
```

解決策:
- 環境変数 `GOOGLE_APPLICATION_CREDENTIALS` が正しく設定されているか確認
- JSONキーファイルのパスが正しいか確認

## ファイル構成

設定完了後のファイル構成:

```
/home/kawai/dev/ai-video-bot/
├── youtube_service_account.json  # サービスアカウントのJSONキー
├── youtube_uploader.py          # YouTubeアップロードスクリプト
└── .env                          # 環境変数設定
```

## 次のステップ

1. 管理者にサービスアカウントの作成を依頼
2. JSONキーファイルを受け取って配置
3. テスト実行
4. 明日の朝7:00の自動実行を確認
