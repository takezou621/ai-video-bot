"""
Upload the already generated video to YouTube
"""
import json
from pathlib import Path
from youtube_uploader import authenticate_youtube, upload_video

# Path to the generated video
VIDEO_DIR = Path("/app/outputs/2025-12-17/video_001")

def main():
    print("\n" + "="*70)
    print("UPLOAD EXISTING VIDEO TO YOUTUBE")
    print("="*70 + "\n")

    # Load metadata
    metadata_path = VIDEO_DIR / "metadata.json"
    if not metadata_path.exists():
        print(f"❌ Metadata not found: {metadata_path}")
        return

    with open(metadata_path) as f:
        metadata = json.load(f)

    # Video paths
    video_path = VIDEO_DIR / "video.mp4"
    thumbnail_path = VIDEO_DIR / "thumbnail.jpg"

    if not video_path.exists():
        print(f"❌ Video not found: {video_path}")
        return

    print(f"✓ Video: {video_path}")
    print(f"✓ Thumbnail: {thumbnail_path}")
    print(f"✓ Title: {metadata['youtube_title']}")
    print(f"✓ Tags: {len(metadata['tags'])} tags")

    # Authenticate
    print("\n📡 Authenticating with YouTube...")
    youtube = authenticate_youtube()
    if not youtube:
        print("❌ Authentication failed")
        return

    # Upload
    print("\n📤 Uploading video to YouTube...")
    result = upload_video(
        youtube=youtube,
        video_path=str(video_path),
        title=metadata['youtube_title'],
        description=metadata['youtube_description'],
        tags=metadata['tags'],
        category_id="27",  # Education
        privacy_status="public",
        thumbnail_path=str(thumbnail_path) if thumbnail_path.exists() else None
    )

    if result:
        video_id = result.get('video_id')
        print("\n" + "="*70)
        print("✅ VIDEO UPLOADED SUCCESSFULLY!")
        print("="*70)
        print(f"\nVideo ID: {video_id}")
        print(f"URL: https://www.youtube.com/watch?v={video_id}")
        print("="*70 + "\n")
    else:
        print("\n❌ Upload failed")

if __name__ == "__main__":
    main()
