"""
Test script for three-bar thumbnail layout
Creates a sample thumbnail using the new three_bar_layout preset
"""
from pathlib import Path
from thumbnail_generator import create_thumbnail, _get_layout_by_name
from nano_banana_client import generate_image

def test_three_bar_layout():
    """Test the three-bar layout with sample content"""
    print("Testing three-bar thumbnail layout...")
    print("=" * 60)

    # Create test output directory
    test_dir = Path("test_output")
    test_dir.mkdir(exist_ok=True)

    # Generate background image
    bg_path = test_dir / "three_bar_bg.png"
    print(f"\n📸 Generating background image...")
    generate_image(
        "Cozy Japanese room with bookshelves, Lo-fi anime style, warm lighting, sunset",
        bg_path
    )
    print(f"✅ Background created: {bg_path}")

    # Verify the layout exists
    layout = _get_layout_by_name("three_bar_layout")
    if layout:
        print(f"\n✅ Layout preset found: {layout['name']}")
    else:
        print(f"\n❌ Layout preset not found!")
        return

    # Test data similar to reference image
    test_cases = [
        {
            "title": "YouTubeサムネを一発で自動作成",
            "subtitle": "GPTsの作り方",
            "badge": "プログラミング不要",
            "output": "thumbnail_three_bar_1.jpg"
        },
        {
            "title": "日本のキャッシュレス革命",
            "subtitle": "経済の未来を解説",
            "badge": "経済",
            "output": "thumbnail_three_bar_2.jpg"
        },
        {
            "title": "AI時代の働き方",
            "subtitle": "未来を予測する",
            "badge": "テック",
            "output": "thumbnail_three_bar_3.jpg"
        }
    ]

    print(f"\n🎨 Creating {len(test_cases)} test thumbnails...")
    print("-" * 60)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Creating thumbnail:")
        print(f"   Title: {test_case['title']}")
        print(f"   Subtitle: {test_case['subtitle']}")
        print(f"   Badge: {test_case['badge']}")

        output_path = test_dir / test_case['output']

        # Explicitly use the three_bar_layout preset
        create_thumbnail(
            background_image_path=bg_path,
            thumbnail_text=test_case['title'],
            subtitle_text=test_case['subtitle'],
            output_path=output_path,
            accent_color_index=i - 1,
            add_characters=True,
            topic_badge_text=test_case['badge'],
            layout_name="three_bar_layout"  # Force three-bar layout
        )
        print(f"   ✅ Saved: {output_path}")

    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print(f"📁 Check output in: {test_dir.absolute()}")
    print("\n💡 Usage: Use layout_name='three_bar_layout' to force this layout")
    print("   Example: create_thumbnail(..., layout_name='three_bar_layout')")

if __name__ == "__main__":
    test_three_bar_layout()
