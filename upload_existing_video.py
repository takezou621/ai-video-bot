"""
Upload the already generated video to YouTube
"""
import json
import argparse
import sys
from pathlib import Path
from youtube_uploader import authenticate_youtube, upload_video

def main():
    parser = argparse.ArgumentParser(description="Upload an existing video to YouTube")
    parser.add_argument("--dir", type=str, required=True, help="Path to the video directory (containing video.mp4, metadata.json, etc.)")
    parser.add_argument("--privacy", type=str, default="private", choices=["private", "unlisted", "public"], help="Privacy status (default: private)")
    args = parser.parse_args()

    # Path to the generated video
    video_dir = Path(args.dir)

    print("\n" + "="*70)
    print("UPLOAD EXISTING VIDEO TO YOUTUBE")
    print("="*70 + "\n")

    if not video_dir.exists():
        print(f"❌ Directory not found: {video_dir}")
        sys.exit(1)

    # Load metadata
    metadata_path = video_dir / "metadata.json"
    if not metadata_path.exists():
        print(f"❌ Metadata not found: {metadata_path}")
        sys.exit(1)

    with open(metadata_path) as f:
        metadata = json.load(f)

    # Video paths
    video_path = video_dir / "video.mp4"
    thumbnail_path = video_dir / "thumbnail.jpg"

    if not video_path.exists():
        print(f"❌ Video not found: {video_path}")
        sys.exit(1)

    print(f"✓ Video: {video_path}")
    print(f"✓ Thumbnail: {thumbnail_path}")
    print(f"✓ Title: {metadata.get('youtube_title', 'No Title')}")
    print(f"✓ Privacy: {args.privacy}")
    
    # Authenticate
    print("\n📡 Authenticating with YouTube...")
    youtube = authenticate_youtube()
    if not youtube:
        print("❌ Authentication failed")
        sys.exit(1)

    # Upload
    print("\n📤 Uploading video to YouTube...")
    result = upload_video(
        youtube=youtube,
        video_path=str(video_path),
        title=metadata.get('youtube_title', 'Uploaded Video'),
        description=metadata.get('youtube_description', ''),
        tags=metadata.get('tags', []),
        category_id="27",  # Education
        privacy_status=args.privacy,
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
        sys.exit(1)

if __name__ == "__main__":
    main()
