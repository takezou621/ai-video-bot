#!/usr/bin/env python3
"""Direct test of Ollama with claude_generator.py logic"""

import os
os.environ['USE_OLLAMA'] = 'true'
os.environ['GEMINI_API_KEY'] = 'dummy'  # Set dummy key to bypass fallback

from claude_generator import _call_gemini
import json

print('=' * 60)
print('Ollama直接テスト: JSON生成')
print('=' * 60)
print()

# シンプルなJSON生成テスト
simple_prompt = """以下のJSON形式で出力してください:
{
  "title": "テストタイトル",
  "description": "テスト説明文",
  "dialogues": [
    {"speaker": "男性", "text": "こんにちは"},
    {"speaker": "女性", "text": "こんにちは、元気ですか？"}
  ]
}

重要: 必ず有効なJSONのみを出力してください。JSONの前後に説明文やマークダウンを含めないでください。"""

print('シンプルなJSON生成テスト...')
print()

try:
    response = _call_gemini(simple_prompt, max_output_tokens=500, temperature=0.7)
    print('Raw Response:')
    print('-' * 60)
    print(response)
    print('-' * 60)
    print()

    # JSONパース試行
    # Extract JSON
    content = response
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    content = content.strip()
    start = content.find("{")
    end = content.rfind("}") + 1
    if start >= 0 and end > start:
        content = content[start:end]

    result = json.loads(content)
    print('✅ JSONパース成功!')
    print(f'タイトル: {result.get("title")}')
    print(f'対話数: {len(result.get("dialogues", []))}')

except json.JSONDecodeError as e:
    print(f'❌ JSONパースエラー: {e}')
    print(f'エラー位置: 行{e.lineno}, 列{e.colno}')
    print()
    print('デバッグ用に抽出されたコンテンツ:')
    print(repr(content))

except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc()
