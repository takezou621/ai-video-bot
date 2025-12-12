# Nano Banana Pro Integration

Nano Banana Pro はローカルGPU/NPUで高解像度の16:9イメージを生成できるデスクトップアプリです。  
`nano_banana_client.py` は以下の流れで動作します:

1. `.env` で `USE_NANO_BANANA_PRO=true` を設定すると、OpenAI APIの代わりにCLIを呼び出す。
2. `NANO_BANANA_PRO_BIN` にCLIの実行ファイル（例: `nanobanana`）へのパスを指定。
3. プロンプト・スタイル・出力サイズをCLIに渡し、生成結果を `outputs/.../background.png` などへ保存。

## インストールと設定
1. Nano Banana Pro をインストール（例: `/Applications/NanoBananaPro.app/Contents/MacOS/nanobanana`）。
2. `.env` に以下を追加:
   ```env
   USE_NANO_BANANA_PRO=true
   NANO_BANANA_PRO_BIN=/Applications/NanoBananaPro.app/Contents/MacOS/nanobanana
   NANO_BANANA_PRO_STYLE=cinematic-newsroom
   ```
3. CLIが `--mode image --prompt ... --output ...` を受け付ける状態であることを確認。

## フォールバック
- CLIが見つからない、タイムアウト、エラーになった場合は自動的にOpenAI (DALL·E 3) へフォールバックする。
- 完全オフラインで運用したい場合は、`.env` で `OPENAI_API_KEY` を空にし、Nano Banana Pro だけを有効にする。
