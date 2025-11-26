# 📘 AI Video Bot

**Daily Automatic Video Generator using Docker + Python + Nano Banana Pro (Gemini 3 Pro Image)**

このプロジェクトは、
**1日1本のAI動画（昭和ノスタルジー系など）を自動生成する最小構成**
として設計されています。

Docker コンテナ 1つで完結し、

* 台本生成（スタブ／後からLLM化）
* 画像生成（Nano Banana Pro / Gemini 3 Pro Image API）
* ナレーション音声生成（gTTS）
* 動画スライドショー作成（ffmpeg）
* 日付ごとに `outputs/YYYY-MM-DD/` に保存

という流れを完全自動で実行します。

cron に登録すれば **自動で毎日1本生成** できます。

---

# 🗂 ディレクトリ構成

```
ai-video-bot/
  ├── Dockerfile
  ├── docker-compose.yml
  ├── requirements.txt
  ├── .env.sample
  ├── llm_story.py
  ├── nano_banana_client.py
  ├── video_maker.py
  ├── daily_video_job.py
  └── outputs/
```

---

# 🚀 セットアップ

## 1. ZIP を展開

```
unzip ai-video-bot.zip
cd ai-video-bot
```

---

## 2. `.env` を作成

```
cp .env.sample .env
```

必要に応じて API Key を設定：

```env
GEMINI_API_KEY=あなたのキー
NARRATION_LANG=ja
```

※ APIキー未設定の場合は **ダミー画像生成** で動きます。

---

## 3. Dockerイメージをビルド

```
docker compose build
```

---

## 4. 動画生成テスト（1本だけ実行）

```
docker compose run --rm ai-video-bot
```

完了すると以下のような構造で生成されます：

```
outputs/
  2025-11-26/
    images/
      scene_01.png
      ...
    narration.mp3
    video.mp4     ← 完成動画
    meta.json
```

---

# ⏰ 毎日1本 自動生成（cron）

Docker を動かす VM（Proxmox 内など）で：

```
crontab -e
```

例：毎日 AM3:30 に1本生成

```
30 3 * * * cd /path/to/ai-video-bot && /usr/bin/docker compose run --rm ai-video-bot >> /var/log/ai-video-bot.log 2>&1
```

---

# 🧠 各コンポーネントの役割

### 1. **llm_story.py（台本生成）**

現在は固定の昭和テーマのストーリーを返します。
LLM API（OpenAI/Gemini）呼び出しに差し替え可能。

---

### 2. **nano_banana_client.py（画像生成）**

* `GEMINI_API_KEY` が設定されていれば
  → **Nano Banana Pro（Gemini 3 Pro Image）API** に投げて画像生成
* キーが無い場合
  → ダミー画像生成でワークフローを維持

---

### 3. **video_maker.py（動画合成）**

* ffmpeg を使い画像 → スライドショー動画に変換
* gTTS で生成したナレーション音声を合成
* 最終 mp4 を出力

---

### 4. **daily_video_job.py（1本生成の実行エントリ）**

以下をまとめて実行するメイン処理：

1. 台本生成
2. 画像生成（複数シーン）
3. ナレーション生成
4. ffmpegで動画化
5. メタデータ保存

---

# 📦 拡張ポイント（任意）

* 台本生成を LLM（OpenAI / Gemini / Claude）に置き換え
* 画像生成を高品質化（プロンプト強化、複数パターン生成）
* BGM 自動追加
* トランジション（クロスフェード等）強化
* YouTube 自動アップロード（Workspace Flows or API）
* Redis Queue / Kafka によるジョブ管理
* プロンプト自動最適化ループ

---

# 🧩 推奨動作環境

* Proxmox 上の VM (Ubuntu 24.04 / Debian 12+)
* Docker / Docker Compose v2
* ffmpeg インストール済み
* Python 3.12（コンテナ内）

---

# 📞 サポート

追加機能の実装や、YouTube 自動投稿、BGM生成、
LLM統合など、拡張を行いたい場合はお知らせください。

# ai-video-bot
