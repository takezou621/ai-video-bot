# YouTube API セットアップガイド

このガイドでは、AI Video BotでYouTube自動アップロード機能を有効化するための手順を説明します。

## 目次

1. [前提条件](#前提条件)
2. [Google Cloud Console設定](#google-cloud-console設定)
3. [OAuth 2.0認証情報の作成](#oauth-20認証情報の作成)
4. [初回認証](#初回認証)
5. [動画のアップロード](#動画のアップロード)
6. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

- Googleアカウント（YouTubeチャンネルが紐付いているもの）
- AI Video Botのセットアップが完了していること
- Docker環境が動作していること

---

## Google Cloud Console設定

### 1. Google Cloud Consoleにアクセス

[Google Cloud Console](https://console.cloud.google.com)にアクセスし、Googleアカウントでログインします。

### 2. 新しいプロジェクトを作成

1. 画面上部の「プロジェクト選択」をクリック
2. 「新しいプロジェクト」をクリック
3. プロジェクト名を入力（例: `ai-video-bot-youtube`）
4. 「作成」をクリック

### 3. YouTube Data API v3を有効化

1. 左側のメニューから「APIとサービス」→「ライブラリ」を選択
2. 検索バーに「YouTube Data API v3」と入力
3. 「YouTube Data API v3」をクリック
4. 「有効にする」をクリック

---

## OAuth 2.0認証情報の作成

### 1. OAuth同意画面の設定

1. 左側のメニューから「APIとサービス」→「OAuth同意画面」を選択
2. ユーザータイプ：「外部」を選択して「作成」をクリック
3. アプリ情報を入力：
   - **アプリ名**: AI Video Bot（任意）
   - **ユーザーサポートメール**: あなたのメールアドレス
   - **デベロッパーの連絡先情報**: あなたのメールアドレス
4. 「保存して次へ」をクリック
5. スコープの追加：
   - 「スコープを追加または削除」をクリック
   - 以下のスコープを検索して追加：
     - `https://www.googleapis.com/auth/youtube.upload`
     - `https://www.googleapis.com/auth/youtube.force-ssl`
   - 「更新」→「保存して次へ」をクリック
6. テストユーザーの追加：
   - 「テストユーザーを追加」をクリック
   - YouTubeチャンネルのメールアドレスを入力
   - 「保存して次へ」をクリック
7. 「ダッシュボードに戻る」をクリック

### 2. OAuth 2.0クライアントIDの作成

1. 左側のメニューから「APIとサービス」→「認証情報」を選択
2. 「認証情報を作成」→「OAuth クライアント ID」をクリック
3. アプリケーションの種類：「デスクトップアプリ」を選択
4. 名前を入力（例: `AI Video Bot Desktop Client`）
5. 「作成」をクリック

### 3. 認証情報JSONのダウンロード

1. 作成されたクライアントIDの右側にある「ダウンロード」アイコン（↓）をクリック
2. ダウンロードしたJSONファイルを、AI Video Botプロジェクトのルートディレクトリに配置
3. ファイル名を `youtube_credentials.json` に変更

```bash
# ファイルを配置（例）
mv ~/Downloads/client_secret_*.json /path/to/ai-video-bot/youtube_credentials.json
```

---

## 初回認証

### 1. 認証テストの実行

```bash
# プロジェクトルートディレクトリで実行
cd /path/to/ai-video-bot

# YouTube認証テスト
docker compose run --rm ai-video-bot python youtube_uploader.py
```

### 2. ブラウザでの認証

1. コマンドを実行すると、ブラウザが自動的に開きます
2. Googleアカウントでログイン
3. 「このアプリは確認されていません」と表示された場合：
   - 「詳細」→「AI Video Botに移動（安全ではないページ）」をクリック
4. アプリがYouTubeへのアクセスを求める画面が表示されます：
   - 「許可」をクリック
5. 「認証フローが完了しました」というメッセージが表示されたらブラウザを閉じます

### 3. 認証トークンの確認

認証が成功すると、プロジェクトルートに `youtube_token.pickle` ファイルが作成されます。

```bash
ls -la youtube_token.pickle
# -rw-r--r-- 1 user user 1234 Dec 26 10:00 youtube_token.pickle
```

このファイルには認証情報が保存されており、次回以降は再認証不要で自動的にYouTubeにアクセスできます。

---

## 動画のアップロード

### 1. .envファイルの設定

```bash
# .env ファイルを編集
nano .env
```

以下の設定を追加/変更：

```env
# YouTube自動アップロードを有効化
YOUTUBE_UPLOAD_ENABLED=true

# 公開設定（最初はprivateがおすすめ）
YOUTUBE_PRIVACY_STATUS=private    # private, unlisted, または public

# プレイリストID（オプション）
YOUTUBE_PLAYLIST_ID=              # 動画を特定のプレイリストに追加する場合
```

### 2. 動画生成とアップロード

```bash
# 動画を生成し、自動的にYouTubeへアップロード
docker compose run --rm ai-video-bot python advanced_video_pipeline.py
```

### 3. アップロード結果の確認

アップロードが成功すると、以下のような出力が表示されます：

```
[10/10] 📤 Uploading to YouTube...
   Title: あなたの動画タイトル
   Privacy: private
   Upload progress: 100%
✅ Video uploaded successfully!
   Video ID: abc123xyz
   URL: https://www.youtube.com/watch?v=abc123xyz
✅ Thumbnail uploaded successfully!
✅ Posted 5/5 comments successfully
```

### 4. YouTubeで確認

1. [YouTube Studio](https://studio.youtube.com)にアクセス
2. 左側のメニューから「コンテンツ」を選択
3. アップロードされた動画を確認

---

## 公開設定

### private（非公開）

- 自分のみが閲覧可能
- 検索結果やおすすめに表示されない
- テスト用に最適

### unlisted（限定公開）

- URLを知っている人のみが閲覧可能
- 検索結果には表示されないが、共有可能
- 特定のユーザーに共有する場合に便利

### public（公開）

- 全員が閲覧可能
- 検索結果やおすすめに表示される
- 本番環境での使用

---

## プレイリストへの追加

動画を特定のプレイリストに自動追加するには：

### 1. プレイリストIDの取得

1. [YouTube Studio](https://studio.youtube.com)にアクセス
2. 左側のメニューから「プレイリスト」を選択
3. 対象のプレイリストをクリック
4. ブラウザのURLを確認：
   ```
   https://studio.youtube.com/playlist/PLxxxxxxxxxxxxxxxxxxxxxx/videos
   ```
   この `PLxxxxxxxxxxxxxxxxxxxxxx` の部分がプレイリストIDです

### 2. .envに設定

```env
YOUTUBE_PLAYLIST_ID=PLxxxxxxxxxxxxxxxxxxxxxx
```

---

## トラブルシューティング

### 認証エラー: 「youtube_credentials.json not found」

**原因**: 認証情報ファイルが見つからない

**解決策**:
```bash
# ファイルが存在するか確認
ls -la youtube_credentials.json

# ない場合は、Google Cloud Consoleから再ダウンロードして配置
```

### 認証エラー: 「OAuth flow failed」

**原因**: OAuth同意画面の設定が不完全

**解決策**:
1. Google Cloud Consoleで「OAuth同意画面」を確認
2. 必要なスコープが追加されているか確認
3. テストユーザーに自分のメールアドレスが追加されているか確認

### アップロードエラー: 「Upload quota exceeded」

**原因**: YouTube Data APIの1日の使用上限（10,000ユニット）を超えた

**解決策**:
- 翌日まで待つ（太平洋時間の午前0時にリセット）
- 1日のアップロード本数を減らす（`.env`の`VIDEOS_PER_DAY`を調整）

### アップロードエラー: 「Invalid request」

**原因**: メタデータ（タイトル、説明文など）が無効

**解決策**:
1. `outputs/YYYY-MM-DD/video_XXX/metadata.json`を確認
2. タイトルや説明文に不正な文字がないか確認
3. タイトルが100文字以内、説明文が5000文字以内か確認

### コメント投稿エラー

**原因**: コメント機能が無効、またはスパム判定

**解決策**:
- YouTubeチャンネルの設定でコメント機能が有効か確認
- コメント投稿間隔を空ける（動画生成のタイミングを調整）

### 認証トークンの期限切れ

**症状**: 以前は動作していたが、突然認証エラーが発生

**解決策**:
```bash
# トークンファイルを削除して再認証
rm youtube_token.pickle
docker compose run --rm ai-video-bot python youtube_uploader.py
# ブラウザで再度認証
```

---

## セキュリティに関する注意事項

### 認証情報の管理

- `youtube_credentials.json` と `youtube_token.pickle` は機密情報です
- これらのファイルをGitリポジトリにコミットしないでください
- `.gitignore` に以下を追加することを推奨：
  ```
  youtube_credentials.json
  youtube_token.pickle
  ```

### 本番環境での使用

本番環境（クラウドサーバーなど）では：

1. **サービスアカウントの使用を検討**
   - より安全な認証方法
   - ブラウザでの認証が不要

2. **認証情報の暗号化**
   - 環境変数や秘密管理サービスを使用
   - ファイルシステムに直接保存しない

3. **定期的なトークン更新**
   - 長期間使用する場合は定期的に再認証

---

## 参考リンク

- [YouTube Data API v3 Documentation](https://developers.google.com/youtube/v3)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [YouTube API Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost)

---

## サポート

問題が解決しない場合は、以下を確認してください：

1. [README.md](README.md) - 全般的なセットアップガイド
2. [CLAUDE.md](CLAUDE.md) - 開発者向け詳細ドキュメント
3. [GitHub Issues](https://github.com/your-repo/issues) - 既知の問題と解決策

Happy uploading! 🎬✨
