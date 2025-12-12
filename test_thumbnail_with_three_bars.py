"""
Quick test for three-bar thumbnail layout using existing background
"""
from pathlib import Path
from thumbnail_generator import create_thumbnail

def test_three_bar_with_existing_bg():
    """Test the three-bar layout with an existing background"""
    print("Testing three-bar thumbnail layout...")
    print("=" * 60)

    # Use existing background from recent video generation
    bg_path = Path("outputs/2025-12-10/video_001/background.png")

    if not bg_path.exists():
        print(f"❌ Background not found: {bg_path}")
        print("Please run the video generation first.")
        return

    print(f"✅ Found background: {bg_path}")

    # Create output directory
    test_dir = Path("test_output")
    test_dir.mkdir(exist_ok=True)

    # Test the three-bar layout
    print("\n🎨 Creating three-bar layout thumbnail...")

    create_thumbnail(
        background_image_path=bg_path,
        thumbnail_text="YouTubeサムネを一発で自動作成",
        subtitle_text="GPTsの作り方",
        output_path=test_dir / "thumbnail_three_bar_test.jpg",
        accent_color_index=0,
        add_characters=True,
        topic_badge_text="プログラミング不要",
        layout_name="three_bar_layout"  # Force three-bar layout
    )

    print(f"\n✅ Test complete!")
    print(f"📁 Output: {test_dir / 'thumbnail_three_bar_test.jpg'}")
    print("\n💡 The three-bar layout includes:")
    print("   - Top bar: Light color for category badge")
    print("   - Middle bar: Dark color for main title")
    print("   - Bottom bar: Light color for subtitle")
    print("   - Character images on the right side")

if __name__ == "__main__":
    test_three_bar_with_existing_bg()
