# サムネイル品質ガイド（Yukkuriスタイル）

このガイドは `thumbnail_generator.py` を使って自動生成されるサムネイルのアートディレクション、トーン、QAチェックをまとめたものです。ColdFusion / AI Explained / ゆっくり解説系チャンネルのリサーチ結果（`COMPETITIVE_RESEARCH.md` 参照）を踏まえ、**クリック率とブランド一貫性を両立**させることが目的です。

## 🎯 クリエイティブゴール
- **左：情報 / 右：キャラクター** の二分レイアウトでYukkuri解説に近い安心感を演出。
- タイトルは2〜3行で完結、固有名詞と数字を先頭に置き、10文字以内の短い`thumbnail_text`を想定。
- 男性＋女性キャラクターの会話感を出し、音声（男性×女性の掛け合い）と整合。
- 背景は暗めに処理し、グラデーション＋斜めパターンで奥行きを出す。
- カテゴリバッジで「経済/テック/カルチャー/ライフ」を一目表示。

## 🧱 レイアウト分解
```
┌────────────────────────────────────────┐
│  トップアクセントバー（accent color）                               │
├────────────────────────────────────────┤
│  左：タイトル/サブタイトル  │  右下：キャラクター＋吹き出し          │
│  - drop shadow + white text  │  - male前面 / female背面              │
│  - subtitleはaccent色        │  - 320px基準で自動リサイズ            │
└────────────────────────────────────────┘
```
- 背景画像は `background.png` を1280x720へリサイズ後、`GaussianBlur(2)`＋明度60%＋グラデ/パターン/楕円グロウを適用。
- テキストは `NotoSansCJK`（自動検出）で影付き描画。キャラを配置する場合、テキストブロックは左寄せで `CHARACTER_MARGIN_LEFT + cluster_width` をオフセット。
- キャラ周辺に白いラウンド矩形を置き、`CHARACTER_SHADOW_COLOR=(0,0,0,160)` でソフトシャドウを重ねる。

## 🏷 カテゴリバッジ
- `BADGE_LABELS` は `advanced_video_pipeline.py` から `topic_badge_text` として渡されます。
- 色パレットは `ACCENT_COLORS` のインデックスと同期。バッジで視覚的にカテゴリを明示し、ニュース性を補強。
- アイコンを置きたい場合は `create_thumbnail(..., badge_icon_path=Path('assets/icons/economy.png'))` のように指定。

## 👥 キャラクター運用
- キャラクターデータは `assets/characters/{male,female}_host.png`。`generate_thumbnail_characters.py` でDALL·E 3、`generate_characters.py` でNano Banana背景を利用できます。
- 透明PNG推奨。640px以上で生成すれば `CHARACTER_HEIGHT=320` に縮小してもディテール保持。
- 片方のみ差し替えたい場合は `generate_male_character.py` の単体スクリプトを使用。

## ⚙️ 生成ワークフロー例
```bash
# 1. キャラクター生成（必要な場合）
./venv/bin/python generate_thumbnail_characters.py

# 2. 背景を既存出力から取得 or nano_banana_client で生成
ls outputs/<date>/video_<id>/background.png

# 3. テスト用サムネイル作成
./venv/bin/python test_thumbnail_with_characters.py
# or 任意テキストで生成
./venv/bin/python - <<'PY'
from pathlib import Path
from thumbnail_generator import create_thumbnail
create_thumbnail(
    Path('outputs/2025-12-02/video_001/background.png'),
    'NVIDIAが逆襲',
    '国際ロボット展で何が？',
    Path('outputs/2025-12-02/video_001/sample_thumbnail.jpg'),
    accent_color_index=1,
    topic_badge_text='テック'
)
PY
```

## ✅ プリフライトQA（サムネイル）
1. **固有名詞が先頭10文字に入っているか**（例: `NVIDIA`, `OpenAI`）。
2. **男性・女性キャラのバランス**：男性を少し前、女性を15px上に配置して立体感を出す。
3. **文字の可読性**：2行までで折り返し、影と下部グラデで視認性を確保。
4. **カテゴリバッジ**：動画テーマに合っているか、不要なら引数で空文字にする。
5. **出力サイズ**：`1280x720 / <= 2MB` を `pre_upload_checks.py` で確認。

## 🔁 自動パイプラインとの連携
- `advanced_video_pipeline.py` のステップ8で `create_thumbnail` が呼ばれ、`topic_category` から自動でバッジを設定。
- プリフライト検証では `thumbnail_file` チェックで50KB未満のNGや存在チェックを実施。
- 一括生成時も `accent_color_index=video_number % 4` で色をローテーションし、一覧性を担保。
- ベンチマーク用のリファレンスサムネは `docs/reference_thumbnails/examples/` にカテゴリごとに保存してあり、視覚的に確認しながらテンプレを改善できます。カラーパレットやレイアウト仕様は `docs/layout_guides/thumbnail_presets.md` と `assets/layout_guides/README.md` に統合。

## 🧭 さらなる改善アイデア
- `assets/patterns/*.png` を読み込んで、カテゴリ別に背景テクスチャを切り替える。
- 「速報」「解説」「図解」などの左上バナーを `topic_badge_text` とは別レイヤーで追加。
- `ACCENT_COLORS` をJSON化し、ブランドテーマごとに差し替え。

このガイドに沿ってサムネイルを生成すると、競合チャンネルの「デザイナー感」を保ちながら、自動生成でも品質を崩さずに展開できます。`pre_upload_checks.py` の `thumbnail_file` をパスするまで微調整してからYouTubeへアップロードしてください。
