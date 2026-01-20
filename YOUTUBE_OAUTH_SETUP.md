# YouTube OAuth認証の設定手順

## 手順

1. **YouTube認証スクリプトを実行**

   以下のコマンドを実行して、YouTube OAuth認証を開始します：

   ```bash
   cd /home/kawai/dev/ai-video-bot
   docker compose run --rm ai-video-bot python youtube_uploader.py
   ```

2. **ブラウザで認証**

   - ブラウザが自動的に開き、Googleログインページが表示されます
   - ご自身のGoogleアカウントでログインしてください
   - 「このアプリはまだ確認されていません」という警告が出ます
   - 「詳細」をクリック > 「ai-video-bot（安全ではない）に移動」をクリック
   - 「許可」をクリックして進みます

3. **認証コードの入力**

   - ブラウザに認証コードが表示されます
   - ターミナルにそのコードを入力してください

4. **認証完了の確認**

   以下のファイルが作成されたら成功です：

   ```bash
   ls -la youtube_token.pickle youtube_credentials.json
   ```

## 認証後のテスト

認証完了後、以下のコマンドでテスト実行できます：

```bash
# 完全な動画生成パイプラインのテスト
docker compose run --rm ai-video-bot python advanced_video_pipeline.py

# または、cronスクリプトのテスト
./cron-job.sh
```

## トラブルシューティング

### ブラウザが開かない場合

Dockerコンテナ内からブラウザを開けない場合は、以下の手順で手動認証できます：

1. **認証URLを取得**

   ターミナルに表示されるURLをコピーします。

2. **手動でブラウザを開く**

   コピーしたURLをブラウザのアドレスバーに貼り付けて開きます。

3. **認証コードをコピー**

   表示された認証コードをコピーして、ターミナルに入力します。

### トークンの有効期限切れ

以下のエラーが出た場合は、トークンの有効期限が切れています：

```
Error loading token: Token has been expired or revoked
```

再認証してください：

```bash
rm youtube_token.pickle youtube_credentials.json
docker compose run --rm ai-video-bot python youtube_uploader.py
```

### アクセス拒否エラー

```
Error: Access denied
```

これはOAuth認証が失敗しています。以下を確認してください：

1. GoogleアカウントでYouTubeチャンネルを持っていること
2. チャンネルのアップロード権限があること
3. APIが有効になっていること

## 確認コマンド

認証が成功したか確認：

```bash
# ファイルの存在確認
ls -la youtube_*.pickle youtube_*.json

# トークンの有効期限を確認（有効な場合）
python -c "import pickle; print('Token valid' if pickle.load(open('youtube_token.pickle', 'rb')) else 'Token invalid')"
```

## 次のステップ

認証完了後：

1. `./cron-job.sh` でテスト実行
2. 動画が生成されてYouTubeにアップロードされることを確認
3. 明日の朝7:00に自動実行されるのを待つ
