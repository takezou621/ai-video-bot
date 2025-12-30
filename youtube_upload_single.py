"""
YouTube Single Video Upload
Upload the most recently generated video
"""
import json
import os
from pathlib import Path
from datetime import datetime
from youtube_uploader import authenticate_youtube, upload_video, post_comments

def find_latest_video():
    """Find the most recently generated video"""
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        return None

    # Find the latest date folder
    date_dirs = sorted([d for d in outputs_dir.iterdir() if d.is_dir()], reverse=True)
    if not date_dirs:
        return None

    for date_dir in date_dirs:
        # Find video folders
        video_dirs = sorted([d for d in date_dir.iterdir() if d.is_dir() and d.name.startswith("video_")], reverse=True)
        if video_dirs:
            latest_video = video_dirs[0]
            video_path = latest_video / "video.mp4"
            if video_path.exists():
                return latest_video

    return None

def main():
    video_dir = find_latest_video()
    if not video_dir:
        print("❌ No video found in outputs directory")
        return

    print(f"📁 Found video directory: {video_dir}")

    video_path = video_dir / "video.mp4"
    metadata_path = video_dir / "metadata.json"
    thumbnail_path = video_dir / "thumbnail.jpg"
    comments_path = video_dir / "comments.json"

    if not video_path.exists():
        print(f"❌ Video file not found: {video_path}")
        return

    # Authenticate
    print("\n🔐 Authenticating with YouTube...")
    youtube = authenticate_youtube()
    if not youtube:
        print("❌ Failed to authenticate with YouTube")
        return
    print("✅ Authenticated successfully")

    # Load metadata
    title = f"Video {datetime.now().strftime('%Y-%m-%d')}"
    description = ""
    tags = []

    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            title = metadata.get("youtube_title", metadata.get("title", title))
            description = metadata.get("description", "")
            tags = metadata.get("tags", [])
        print(f"📝 Title: {title[:60]}...")
    else:
        print("⚠️  No metadata.json found, using defaults")

    # Upload video
    print("\n📤 Uploading video to YouTube...")
    privacy_status = os.getenv("YOUTUBE_PRIVACY_STATUS", "public")

    thumbnail_str = str(thumbnail_path) if thumbnail_path.exists() else None

    result = upload_video(
        youtube,
        str(video_path),
        title,
        description,
        tags,
        privacy_status=privacy_status,
        thumbnail_path=thumbnail_str
    )

    if not result:
        print("❌ Upload failed")
        return

    video_id = result.get("id")
    print(f"✅ Video uploaded! ID: {video_id}")
    print(f"📺 URL: https://www.youtube.com/watch?v={video_id}")

    # Post comments
    do_post_comments = os.getenv("YOUTUBE_POST_COMMENTS", "false").lower() == "true"
    if do_post_comments and comments_path.exists():
        print("\n💬 Posting comments...")
        with open(comments_path, 'r', encoding='utf-8') as f:
            comments_data = json.load(f)

        comment_texts = []
        for comment in comments_data[:3]:  # Max 3 comments
            text = comment.get("text", comment.get("comment", ""))
            if text:
                comment_texts.append(text)

        if comment_texts:
            post_comments(youtube, video_id, comment_texts)

    print("\n" + "="*60)
    print("🎉 Upload complete!")
    print(f"📺 Video URL: https://www.youtube.com/watch?v={video_id}")
    print("="*60)

if __name__ == "__main__":
    main()
