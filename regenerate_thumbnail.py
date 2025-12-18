"""
Regenerate thumbnail for existing video with text overlay
"""
import json
from pathlib import Path
from thumbnail_generator import create_thumbnail
from thumbnail_prompt_generator import generate_thumbnail_prompt

# Path to the generated video
VIDEO_DIR = Path("/app/outputs/2025-12-17/video_001")

def main():
    print("\n" + "="*70)
    print("REGENERATE THUMBNAIL WITH TEXT")
    print("="*70 + "\n")

    # Load metadata
    metadata_path = VIDEO_DIR / "metadata.json"
    script_path = VIDEO_DIR / "script.json"
    
    if not metadata_path.exists() or not script_path.exists():
        print(f"❌ Required files not found")
        return

    with open(metadata_path) as f:
        metadata = json.load(f)
    
    with open(script_path) as f:
        script = json.load(f)

    print(f"✓ Title: {metadata['youtube_title']}")
    
    # Generate thumbnail prompt
    thumbnail_data = generate_thumbnail_prompt(
        title=script.get("title", ""),
        topic_category="ai_news",
        thumbnail_text=script.get("thumbnail_text"),
        named_entities=metadata.get("named_entities", [])
    )
    
    print(f"✓ Thumbnail text: {thumbnail_data['thumbnail_text']}")
    
    # Background path
    bg_path = VIDEO_DIR / "background.png"
    thumbnail_path = VIDEO_DIR / "thumbnail.jpg"
    
    # Generate thumbnail with PIL text overlay
    create_thumbnail(
        background_image_path=bg_path,
        thumbnail_text=thumbnail_data["thumbnail_text"],
        topic_badge_text="AI_NEWS",
        output_path=thumbnail_path,
        image_prompt=thumbnail_data["prompt"],
        emotion=thumbnail_data["emotion"]
    )
    
    print("\n" + "="*70)
    print("✅ THUMBNAIL REGENERATED")
    print("="*70)
    print(f"\nNew thumbnail: {thumbnail_path}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
