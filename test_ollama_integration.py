#!/usr/bin/env python3
"""Test Ollama integration with claude_generator.py"""

from claude_generator import generate_dialogue_script_with_claude

# テスト用のトピック分析
topic_analysis = {
    'title': 'AIの最新動向について',
    'angle': '2025年のAI業界の注目トピック',
    'key_points': ['大規模言語モデルの進化', 'ローカルLLMの普及', 'コスト削減'],
    'selected_topic': {
        'title': 'ローカルLLMで月額コストを削減',
        'snippet': 'APIからローカルLLMへの移行',
        'source': 'Tech News'
    },
    'named_entities': []
}

print('=' * 60)
print('Ollama統合テスト: スクリプト生成')
print('=' * 60)
print()
print('Ollamaでスクリプト生成を開始します...')
print('（1分程度の動画用スクリプト、約300文字）')
print()

try:
    script = generate_dialogue_script_with_claude(topic_analysis, duration_minutes=1)

    print()
    print('✅ スクリプト生成成功!')
    print('=' * 60)
    print(f'タイトル: {script.get("title", "N/A")}')
    print(f'対話数: {len(script.get("dialogues", []))}')
    print(f'説明: {script.get("description", "N/A")[:100]}...')
    print()

    dialogues = script.get("dialogues", [])
    if dialogues:
        print('最初の3つの対話:')
        for i, d in enumerate(dialogues[:3], 1):
            speaker = d.get("speaker", "不明")
            text = d.get("text", "")
            print(f'{i}. [{speaker}] {text[:80]}{"..." if len(text) > 80 else ""}')

    print()
    print('=' * 60)
    print('✅ Phase 1（Ollama LLM統合）のテストが完了しました！')
    print('=' * 60)

except Exception as e:
    print()
    print(f'❌ エラー: {e}')
    print()
    import traceback
    traceback.print_exc()
