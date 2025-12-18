#!/usr/bin/env python3
"""
Test script for transparent character thumbnails
Verifies that both characters appear with transparent backgrounds
"""
from pathlib import Path
from template_thumbnail_generator import create_template_thumbnail

def test_transparent_characters():
    """Test thumbnail generation with transparent character backgrounds"""
    print("=" * 60)
    print("Testing Transparent Characters in Template Thumbnails")
    print("=" * 60)

    output_dir = Path("outputs/transparent_characters_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    test_cases = [
        {
            'title': 'プログラミング未経験でもOK！YouTubeサムネイルを一発で自動作成',
            'color': '669AFF',
            'name': 'test_blue_transparent'
        },
        {
            'title': '最新AI技術を完全解説！ChatGPT活用術',
            'color': '8C52FF',
            'name': 'test_purple_transparent'
        },
        {
            'title': 'GPTs作成入門編！たった1分で自分用のGPTsを作成',
            'color': '74AA9C',
            'name': 'test_green_transparent'
        }
    ]

    print("\nGenerating thumbnails with transparent characters...")
    print("-" * 60)

    for i, test in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {test['name']}")
        print(f"  Title: {test['title'][:40]}...")
        print(f"  Color: {test['color']}")

        output_path = output_dir / f"{test['name']}.png"
        create_template_thumbnail(
            title=test['title'],
            color_code=test['color'],
            output_path=output_path,
            add_characters=True
        )

    print("\n" + "=" * 60)
    print("✅ All test thumbnails generated!")
    print(f"📁 Location: {output_dir}")
    print("\n💡 Check that:")
    print("  1. Both male and female characters appear")
    print("  2. Character backgrounds are transparent (not white)")
    print("  3. Characters are positioned on the right side")
    print("=" * 60)


if __name__ == "__main__":
    test_transparent_characters()
