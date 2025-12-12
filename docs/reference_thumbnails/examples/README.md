# Reference Thumbnail Examples

各カテゴリごとに「これはクリックされる」と感じた実例（スクリーンショットやデザインモック）を PNG で配置してください。

## 保存ルール
1. ファイル名: `yyyy-mm-dd_<source>_<short-desc>.png`
2. 解説コメントを添える場合は同名の `.md` を配置し、下記テンプレを利用
   ```md
   ## Context
   - Channel / Source: XXXXX
   - Layout Type: L-Split / Before-After / Badge Stack
   - Key Elements: 例) 固有名詞 + 数字 + 感情アイコン
   - Color Palette: #0B1D3A, #FBDC62, #FFFFFF
   ```
3. 著作権に配慮し、社内用途のみの保存とする（公開リポへ push しない）

## ディレクトリ
- `economics/` : 経済・金融ニュース系
- `tech/` : AI / ガジェット / IT
- `culture/` : カルチャー / エンタメ
- `lifestyle/` : 生活 / 教育 / How-to

> 実サンプルをこのフォルダに集約すると、`thumbnail_generator.py` のレイアウト検証や prompt 作成が容易になります。
