"""Test thumbnail generation with characters"""
from pathlib import Path
from thumbnail_generator import create_thumbnail

# Use existing background image
bg_path = Path("outputs/2025-12-02/video_001/background.png")

if not bg_path.exists():
    print(f"Background image not found: {bg_path}")
    exit(1)

# Create test thumbnail with characters in outputs directory
test_output = Path("outputs/2025-12-02/video_001/test_thumbnail_with_characters.jpg")

print("Generating test thumbnail with characters...")
create_thumbnail(
    background_image_path=bg_path,
    thumbnail_text="日本のスタートアップ最前線",
    subtitle_text="",
    output_path=test_output,
    accent_color_index=0,
    add_characters=True  # Enable characters
)

print(f"\n✅ Test thumbnail created: {test_output}")
print("\nPlease check the thumbnail to verify characters appear in bottom-right corner.")
