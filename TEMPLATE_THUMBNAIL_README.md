# Template-based Thumbnail Generator

## 概要

GPTsベースのYouTubeサムネイル自動生成システムを実装しました。事前定義されたカラーテンプレートを使用し、タイトルから自動的に3つのテキスト要素を生成します。

## 機能

### 1. テンプレート画像（1280x720px）

4色のテンプレートが用意されています:

- `74AA9C` - 緑系（落ち着いたトーン）
- `CC9B7A` - ベージュ系（暖かいトーン）
- `669AFF` - 青系（信頼感のあるトーン）
- `8C52FF` - 紫系（高級感のあるトーン）

各テンプレートは以下のレイアウトで構成:
- **上部バー**（薄い色）: カテゴリー/ターゲット層表示
- **中央バー**（濃い色）: メインタイトル表示
- **下部バー**（薄い色）: サブタイトル/補足情報表示

### 2. 自動テキスト生成

Claude APIを使用して、動画タイトルから以下を自動生成:

#### AboveText（上部テキスト）
- タイトルからターゲット層や記事のレベルを推測
- 10文字程度
- 例: "GPTs作成入門編"、"プログラミング未経験でもOK"

#### CenterOfText（中央テキスト）
- タイトルから最も重要な部分を抽出
- 18文字以内
- `/n`で改行を含む
- 例: "たった1分で/n自分用のGPTsを作成"

#### BelowText（下部テキスト）
- CenterOfTextで含められなかった補足情報
- 6〜10文字
- 例: "EasyGPTsMaker"、"GPTsの作り方"

### 3. 自動フォントサイズ調整

各テキスト領域に対して:
- 最大100pxから最小10pxの範囲で自動調整
- テキストが領域内に収まるよう最適化
- 複数行テキストに対応

### 4. 影付きテキスト描画

- テキストの視認性を高める影効果
- ガウシアンブラーによる滑らかな影
- 上下左右中央揃えで配置

### 5. キャラクター画像の自動配置

- **2人のキャラクター**：男性と女性の対話キャラクターが同時に表示
- **透過背景処理**：白背景を自動的に透過処理（threshold: 240）
- **右側配置**：サムネイルの右下に自動配置
- **重なり配置**：女性キャラクターを男性よりやや高く、やや左に配置
- ジブリ風のデザイン

## 使用方法

### 基本的な使い方

```python
from pathlib import Path
from template_thumbnail_generator import create_template_thumbnail

# タイトルからサムネイルを自動生成（キャラクター付き）
thumbnail_path = create_template_thumbnail(
    title="1分で自分専用GPTsを作成！忙しいあなたに贈る『EasyGPTsMaker』活用術",
    color_code="74AA9C",
    output_path=Path("output/thumbnail.png"),
    add_characters=True  # デフォルトでTrue
)
```

### カスタムテキストを指定

```python
# 自動生成せず、テキストを直接指定
custom_texts = {
    'above': 'プログラミング不要',
    'center': 'YouTubeサムネを\n一発で自動作成',
    'below': 'GPTsの作り方'
}

thumbnail_path = create_template_thumbnail(
    title="",  # タイトルは使用されません
    color_code="669AFF",
    output_path=Path("output/custom_thumbnail.png"),
    custom_texts=custom_texts
)
```

### Docker環境での実行

```bash
# テンプレート生成（初回のみ）
docker compose run --rm ai-video-bot python3 -c "
# (テンプレート生成コード - 既に実行済み)
"

# サムネイル生成テスト
docker compose run --rm ai-video-bot python template_thumbnail_generator.py
```

## ファイル構成

```
ai-video-bot/
├── assets/
│   └── templates/
│       ├── thumbnail_template_color(74AA9C).png
│       ├── thumbnail_template_color(CC9B7A).png
│       ├── thumbnail_template_color(669AFF).png
│       └── thumbnail_template_color(8C52FF).png
├── template_thumbnail_generator.py  # メインモジュール
├── generate_thumbnail_templates.py  # テンプレート生成スクリプト
└── TEMPLATE_THUMBNAIL_README.md     # このファイル
```

## 実装詳細

### テキスト領域の座標

要件仕様に基づく各テキスト領域の座標:

```python
ABOVE_TEXT_BBOX = (171.5, 24, 731.4, 100.8)   # (x, y, width, height)
CENTER_TEXT_BBOX = (55, 200, 804, 302)
BELOW_TEXT_BBOX = (55.5, 578.4, 804.2, 100.8)
```

### フォント設定

使用可能なフォント（優先順）:
1. `/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc` （Docker環境）
2. `/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc` （macOS）
3. システムデフォルト（フォールバック）

### Claude API統合

環境変数`CLAUDE_API_KEY`が設定されている場合:
- Claude 3.5 Sonnetを使用してテキスト自動生成
- JSON形式で構造化された結果を返却
- APIが利用できない場合は簡易的なルールベース生成にフォールバック

### キャラクター画像の透過処理

キャラクター画像は以下の処理で透過背景化されます:

1. **RGB→RGBA変換**: 元画像をRGBA形式に変換
2. **白背景検出**: RGB値が240以上のピクセルを「白」と判定
3. **透過処理**: 白と判定されたピクセルのアルファ値を0に設定
4. **リサイズ**: 指定の高さ（280px）にアスペクト比を維持してリサイズ
5. **配置**: 男性と女性を重ねて配置（女性は30px高く、spacing分左に）

```python
def make_white_transparent(image: Image.Image, threshold: int = 240) -> Image.Image:
    """白背景を透過処理（threshold: 240）"""
    # RGB値が240以上の場合は透過
    if item[0] > 240 and item[1] > 240 and item[2] > 240:
        new_data.append((255, 255, 255, 0))  # 完全透過
```

## テスト

3つのテストケースが含まれています:

```bash
# テスト実行
docker compose run --rm ai-video-bot python template_thumbnail_generator.py
```

出力:
- `test_output/template_thumbnail_1.png` - GPTs作成サンプル（緑テーマ）
- `test_output/template_thumbnail_2.png` - サムネイル自動作成サンプル（青テーマ）
- `test_output/template_thumbnail_3.png` - キャッシュレス革命サンプル（ベージュテーマ）

生成済みサンプル:
- `outputs/template_samples/sample_1_green.png` (263KB) - 2キャラクター、透過背景
- `outputs/template_samples/sample_2_blue.png` (266KB) - 2キャラクター、透過背景
- `outputs/template_samples/sample_3_beige.png` (207KB) - 2キャラクター、透過背景

## advanced_video_pipeline.pyとの統合

動画生成パイプラインで使用する場合:

```python
from template_thumbnail_generator import create_template_thumbnail

# Step 8でテンプレートベースのサムネイル生成
thumbnail_path = create_template_thumbnail(
    title=metadata.get('youtube_title', topic_text),
    color_code='74AA9C',  # または環境変数から
    output_path=output_dir / "thumbnail.png"
)
```

環境変数で切り替え:
```bash
# .env
THUMBNAIL_MODE=template  # 'template' or 'three_bar'
THUMBNAIL_COLOR_CODE=74AA9C
```

## カラーコード選択ガイド

- **74AA9C**（緑）: 環境、健康、経済、ライフスタイル系
- **CC9B7A**（ベージュ）: 教育、ビジネス、歴史、文化系
- **669AFF**（青）: テクノロジー、科学、ビジネス、信頼性重視
- **8C52FF**（紫）: クリエイティブ、エンターテイメント、高級感

## トラブルシューティング

### テンプレート画像が見つからない

```bash
# テンプレートを再生成
docker compose run --rm ai-video-bot python generate_thumbnail_templates.py
```

### フォントが表示されない

Dockerイメージに`fonts-noto-cjk`がインストールされていることを確認:
```bash
docker compose run --rm ai-video-bot fc-list | grep Noto
```

### Claude APIエラー

`.env`ファイルに`CLAUDE_API_KEY`が正しく設定されていることを確認。
APIが利用できない場合は自動的にフォールバックモードで動作します。

## パフォーマンス

- テンプレート読み込み: <0.1秒
- テキスト生成（Claude API）: 1-3秒
- 画像描画・保存: <0.5秒
- **合計**: 約2-4秒/サムネイル

## 今後の拡張案

- [ ] カスタムフォント対応
- [ ] アイコン/ロゴの追加機能
- [ ] グラデーション効果のカスタマイズ
- [ ] A/Bテスト用の複数バリエーション生成
- [ ] 動画内容に基づく自動カラー選択
- [ ] テンプレートのカスタマイズUI
