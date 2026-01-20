# 別のマシンでYouTube OAuth認証を行う手順

## 概要

ブラウザが使える別のマシン（PCやスマホ）でOAuth認証を行い、認証ファイルを現在のマシンに転送する手順です。

## 手順

### 方法A: GitHub Codespacesを使用（推奨）

GitHub Codespacesはブラウザベースで、無料で使えます。

#### 1. GitHub Codespaceを作成

1. リポジトリのページを開く
2. 「Code」>「Codespaces」>「New codespace」
3. ブランチを選択して「Create codespace」

#### 2. Codespaceで認証

```bash
cd /workspaces/ai-video-bot
python youtube_uploader.py
```

ブラウザが開くので、認証を完了してください。

#### 3. 認証ファイルをダウンロード

```bash
# ファイルを確認
ls -la youtube_token.pickle youtube_credentials.json

# ダウンロード（Codespaceのファイルをクリックしてダウンロード）
```

#### 4. 現在のマシンにアップロード

```bash
# SCPで転送（例）
scp user@codespace:/workspaces/ai-video-bot/youtube_token.pickle ~/dev/ai-video-bot/
scp user@codespace:/workspaces/ai-video-bot/youtube_credentials.json ~/dev/ai-video-bot/
```

または、GitHub Codespaceのファイルを直接ダウンロードして、現在のマシンの `/home/kawai/dev/ai-video-bot/` に配置します。

### 方法B: 別のPCで認証

#### 1. リポジトリをクローン

```bash
git clone https://github.com/takezou621/ai-video-bot.git
cd ai-video-bot
```

#### 2. Python環境をセットアップ

```bash
# Windows (PowerShell)
python -m pip install -r requirements.txt

# macOS/Linux
python3 -m pip install -r requirements.txt
```

#### 3. 環境変数を設定

```bash
# .envファイルを作成
cp .env.sample .env

# GEMINI_API_KEYなどを設定
nano .env
```

#### 4. 認証スクリプトを実行

```bash
python youtube_uploader.py
```

ブラウザが開くので、認証を完了してください。

#### 5. 認証ファイルを転送

認証完了後、以下のファイルを転送します：

```bash
# Windowsの場合
youtube_token.pickle
youtube_credentials.json
```

転送方法（選択）:

**SCP/SFTP**:
```bash
scp youtube_token.pickle youtube_credentials.json kawai@server:/home/kawai/dev/ai-video-bot/
```

**USBメモリ**:
```bash
# ファイルをUSBにコピー
# USBをサーバーに接続
cp /media/usb/youtube_token.pickle /home/kawai/dev/ai-video-bot/
cp /media/usb/youtube_credentials.json /home/kawai/dev/ai-video-bot/
```

**GitHubのプライベートリポジトリ**:
```bash
# 認証ファイルを一時的にリポジトリに追加（.gitignoreに追加済みなので安全）
git add youtube_token.pickle youtube_credentials.json
git commit -m "Add YouTube OAuth tokens"
git push

# サーバーでプル
git pull
```

### 方法C: スマホで認証

#### 1. Termuxを使用（Android）

TermuxはAndroidで動作するターミナルエミュレータです。

```bash
# Termuxでインストール
pkg update
pkg install python git

# リポジトリをクローン
git clone https://github.com/takezou621/ai-video-bot.git
cd ai-video-bot

# Pythonパッケージをインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.sample .env
nano .env  # 必要なAPIキーを設定

# 認証スクリプトを実行
python youtube_uploader.py
```

ブラウザが開くので、認証を完了してください。

#### 2. 認証ファイルを転送

認証ファイルをメール、Google Drive、またはクラウドストレージ経由で転送し、サーバーに配置します。

### 方法D: 友人/同僚に依頼

ブラウザが使える友人や同僚に依頼して、以下の手順でお願いします：

1. リポジトリをクローン
2. Python環境をセットアップ
3. `python youtube_uploader.py` を実行
4. 認証ファイルを転送（メールなど）

## 認証ファイルの配置

認証ファイルを転送した後、配置します：

```bash
cd /home/kawai/dev/ai-video-bot

# ファイルを配置
# （転送した方法により異なります）

# 権限を設定
chmod 600 youtube_token.pickle youtube_credentials.json

# 確認
ls -la youtube_token.pickle youtube_credentials.json
```

## テスト

```bash
# 認証のテスト
python youtube_uploader.py

# 完全な動画生成パイプラインのテスト
./cron-job.sh
```

## 注意事項

- 認証ファイルには機密情報が含まれます
- 転送の際は暗号化を使用してください
- 使用後は安全に削除してください

## 推奨順序

1. **GitHub Codespaces**（最も簡単、無料）
2. **別のPC**（Windows/macOS）
3. **スマホ（Termux）**
4. **友人/同僚に依頼**

## トラブルシューティング

### 認証ファイルが見つからない

```bash
ls -la youtube_token.pickle youtube_credentials.json
```

ファイルが存在しない場合は、認証が完了していません。再試行してください。

### トークンの有効期限切れ

```
Error: Token has been expired or revoked
```

別のマシンで再度認証を行い、新しいファイルを転送してください。
