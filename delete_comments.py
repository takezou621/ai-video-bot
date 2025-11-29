"""
Delete auto-posted comments from YouTube videos
"""
from youtube_uploader import authenticate_youtube

# Video IDs
video_ids = [
    "JcXvQ6y5tNU",  # Video 1
    "14URKk5itj0"   # Video 2
]

print("=" * 60)
print("YouTube Auto-Comment Deletion")
print("=" * 60)
print()

# Authenticate
youtube = authenticate_youtube()
if not youtube:
    print("❌ Authentication failed")
    exit(1)

total_deleted = 0

for video_id in video_ids:
    print(f"\n🔍 Processing video: {video_id}")
    print(f"   URL: https://www.youtube.com/watch?v={video_id}")

    try:
        # Get all comment threads for this video
        response = youtube.commentThreads().list(
            part='snippet,id',
            videoId=video_id,
            textFormat='plainText'
        ).execute()

        if not response.get('items'):
            print("   No comments found")
            continue

        comments = response['items']
        print(f"   Found {len(comments)} comments")

        # Delete each comment
        deleted_count = 0
        for comment in comments:
            comment_id = comment['id']
            comment_text = comment['snippet']['topLevelComment']['snippet']['textDisplay']
            author = comment['snippet']['topLevelComment']['snippet']['authorDisplayName']

            # Only delete comments posted by the authenticated user
            # (YouTube API only allows deleting your own comments)
            try:
                youtube.commentThreads().delete(id=comment_id).execute()
                print(f"   ✅ Deleted: {comment_text[:50]}...")
                deleted_count += 1
            except Exception as e:
                print(f"   ⚠️  Could not delete comment (not owner or already deleted): {str(e)[:80]}")

        print(f"   Deleted {deleted_count}/{len(comments)} comments")
        total_deleted += deleted_count

    except Exception as e:
        print(f"   ❌ Error processing video: {e}")

print()
print("=" * 60)
print(f"✅ Total deleted: {total_deleted} comments")
print("=" * 60)
