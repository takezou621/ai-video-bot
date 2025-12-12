#!/usr/bin/env python3
"""
Custom Template Thumbnail Creator
Simple script to create thumbnails with custom text or auto-generated from title
"""
from pathlib import Path
from template_thumbnail_generator import create_template_thumbnail

def main():
    """Interactive thumbnail creation"""
    print("=" * 60)
    print("Template-based Thumbnail Creator")
    print("=" * 60)

    # Example 1: Auto-generate from title
    print("\n[Example 1] Auto-generate from title")
    print("-" * 60)

    title = "AI時代の新しい働き方！リモートワーク完全ガイド"
    color_code = "669AFF"  # Blue theme

    print(f"Title: {title}")
    print(f"Color: {color_code}")

    output_path = Path("outputs/my_thumbnail_auto.png")
    create_template_thumbnail(
        title=title,
        color_code=color_code,
        output_path=output_path,
        add_characters=True  # Add characters to thumbnail
    )

    # Example 2: Custom text specification
    print("\n[Example 2] Custom text specification")
    print("-" * 60)

    custom_texts = {
        'above': '完全初心者向け',
        'center': 'YouTube収益化\nゼロから始める方法',
        'below': '2025年最新版'
    }

    print(f"Above: {custom_texts['above']}")
    print(f"Center: {custom_texts['center'].replace(chr(10), '/n')}")
    print(f"Below: {custom_texts['below']}")

    output_path = Path("outputs/my_thumbnail_custom.png")
    create_template_thumbnail(
        title="",  # Not used when custom_texts is provided
        color_code="8C52FF",  # Purple theme
        output_path=output_path,
        custom_texts=custom_texts,
        add_characters=True  # Add characters to thumbnail
    )

    # Example 3: All color variations
    print("\n[Example 3] Generate all color variations")
    print("-" * 60)

    title = "最新AI技術を完全解説！ChatGPT活用術"
    colors = {
        '74AA9C': 'green',
        'CC9B7A': 'beige',
        '669AFF': 'blue',
        '8C52FF': 'purple'
    }

    for color_code, color_name in colors.items():
        output_path = Path(f"outputs/variation_{color_name}.png")
        print(f"  Creating {color_name} variation...")
        create_template_thumbnail(
            title=title,
            color_code=color_code,
            output_path=output_path,
            add_characters=True  # Add characters to thumbnail
        )

    print("\n" + "=" * 60)
    print("✅ All thumbnails created successfully!")
    print(f"📁 Check: outputs/ directory")
    print("=" * 60)


if __name__ == "__main__":
    main()
