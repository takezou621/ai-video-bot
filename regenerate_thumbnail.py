"""Regenerate thumbnail for existing video with characters"""
from pathlib import Path
from thumbnail_generator import create_thumbnail

# Video directory
video_dir = Path("outputs/2025-12-02/video_001")
bg_path = video_dir / "background.png"
output_path = video_dir / "thumbnail_with_characters.jpg"

if not bg_path.exists():
    print(f"❌ Background not found: {bg_path}")
    exit(1)

print(f"Regenerating thumbnail with characters...")
print(f"  Background: {bg_path}")
print(f"  Output: {output_path}")

create_thumbnail(
    background_image_path=bg_path,
    thumbnail_text="ｽﾀｰﾄｱｯﾌﾟ最前線",
    subtitle_text="",
    output_path=output_path,
    accent_color_index=0,
    add_characters=True
)

print(f"\n✅ Thumbnail with characters created!")
print(f"   Path: {output_path}")
