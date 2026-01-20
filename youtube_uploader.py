"""
YouTube Data API v3 Integration
Handles authentication, video upload, thumbnail setting, and comment posting
"""
import os
import json
import pickle
from pathlib import Path
from typing import Optional, Dict, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# YouTube API scopes
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

BASE = Path(__file__).parent
CREDENTIALS_FILE = BASE / "youtube_credentials.json"
TOKEN_FILE = BASE / "youtube_auth.pickle"  # Changed from youtube_token.pickle to avoid directory conflict


def authenticate_youtube() -> Optional[any]:
    """
    Authenticate with YouTube Data API v3 using Service Account or OAuth 2.0

    Returns:
        YouTube API service object or None if authentication fails
    """
    # Check for service account first
    service_account_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    service_account_file = BASE / "youtube_service_account.json"

    if service_account_path or service_account_file.exists():
        # Use service account authentication
        try:
            from google.oauth2 import service_account

            # Determine service account file path
            if service_account_path:
                sa_path = service_account_path
            else:
                sa_path = str(service_account_file)

            print(f"Using service account authentication: {sa_path}")

            credentials = service_account.Credentials.from_service_account_file(
                sa_path,
                scopes=SCOPES
            )

            return build('youtube', 'v3', credentials=credentials)

        except Exception as e:
            print(f"Service account authentication failed: {e}")
            print("Falling back to OAuth 2.0...")

    # Fallback to OAuth 2.0
    creds = None

    # Load existing token if available
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"Error loading token: {e}")

    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Refreshing YouTube API credentials...")
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                creds = None

        # If still no valid creds, need to authenticate
        if not creds:
            if not CREDENTIALS_FILE.exists():
                print(f"YouTube credentials file not found: {CREDENTIALS_FILE}")
                print("Please download OAuth 2.0 credentials from Google Cloud Console")
                print("and save as 'youtube_credentials.json' in the project root")
                return None

            try:
                print("Starting OAuth 2.0 authentication flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_FILE), SCOPES)

                # Try manual authorization flow for Docker environments
                try:
                    print("\n" + "="*60)
                    print("MANUAL AUTHORIZATION REQUIRED")
                    print("="*60)
                    print("\nDocker environment detected. Please follow these steps:")
                    print("1. The authentication will start on localhost")
                    print("2. Copy the URL that appears")
                    print("3. Open it in your browser on your host machine")
                    print("4. Authorize the application")
                    print("\nStarting local server (this may show an error in Docker, but should work)...")
                    creds = flow.run_local_server(
                        port=8080,
                        open_browser=False,
                        authorization_prompt_message='Please visit this URL to authorize: {url}',
                        success_message='Authorization complete! You can close this window.'
                    )
                except Exception as local_e:
                    print(f"\nLocal server failed: {local_e}")
                    print("\nAttempting alternative method...")

                    # Fallback: Get authorization URL manually
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    print("\n" + "="*60)
                    print("MANUAL AUTHORIZATION URL")
                    print("="*60)
                    print(f"\nPlease open this URL in your browser:\n\n{auth_url}\n")
                    print("After authorizing, you'll be redirected to a URL starting with")
                    print("'http://localhost:...' - paste that FULL URL here:")
                    print("="*60 + "\n")

                    code_url = input("Paste the full redirect URL here: ").strip()
                    flow.fetch_token(code=code_url.split('code=')[1].split('&')[0])
                    creds = flow.credentials

            except Exception as e:
                print(f"Error during OAuth flow: {e}")
                return None

        # Save the credentials for next run
        try:
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        except Exception as e:
            print(f"Error saving token: {e}")

    try:
        youtube = build('youtube', 'v3', credentials=creds)
        print("✅ YouTube API authentication successful")
        return youtube
    except Exception as e:
        print(f"Error building YouTube service: {e}")
        return None


def upload_video(
    youtube,
    video_path: str,
    title: str,
    description: str,
    tags: List[str] = None,
    category_id: str = "22",  # People & Blogs
    privacy_status: str = "private",  # private, unlisted, or public
    thumbnail_path: Optional[str] = None,
    playlist_id: Optional[str] = None
) -> Optional[Dict]:
    """
    Upload a video to YouTube

    Args:
        youtube: YouTube API service object
        video_path: Path to video file
        title: Video title
        description: Video description
        tags: List of tags
        category_id: YouTube category ID (default: 22 = People & Blogs)
        privacy_status: Privacy setting (private, unlisted, public)
        thumbnail_path: Optional path to custom thumbnail
        playlist_id: Optional playlist ID to add video to

    Returns:
        Dictionary with video information or None if upload fails
    """
    if not youtube:
        print("YouTube API not authenticated")
        return None

    if not Path(video_path).exists():
        print(f"Video file not found: {video_path}")
        return None

    # Prepare video metadata
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags or [],
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }

    try:
        print(f"\n📤 Uploading video to YouTube...")
        print(f"   Title: {title}")
        print(f"   Privacy: {privacy_status}")

        # Create media upload
        media = MediaFileUpload(
            video_path,
            chunksize=-1,  # Upload in a single request
            resumable=True,
            mimetype='video/mp4'
        )

        # Execute upload
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"   Upload progress: {progress}%")

        video_id = response['id']
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        print(f"✅ Video uploaded successfully!")
        print(f"   Video ID: {video_id}")
        print(f"   URL: {video_url}")

        # Upload thumbnail if provided
        if thumbnail_path and Path(thumbnail_path).exists():
            try:
                print(f"\n🖼️  Uploading custom thumbnail...")
                thumbnail_media = MediaFileUpload(
                    thumbnail_path,
                    mimetype='image/jpeg'
                )
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=thumbnail_media
                ).execute()
                print(f"✅ Thumbnail uploaded successfully!")
            except HttpError as e:
                print(f"⚠️  Failed to upload thumbnail: {e}")

        # Add to playlist if specified
        if playlist_id:
            try:
                print(f"\n📋 Adding video to playlist...")
                youtube.playlistItems().insert(
                    part='snippet',
                    body={
                        'snippet': {
                            'playlistId': playlist_id,
                            'resourceId': {
                                'kind': 'youtube#video',
                                'videoId': video_id
                            }
                        }
                    }
                ).execute()
                print(f"✅ Video added to playlist successfully!")
            except HttpError as e:
                print(f"⚠️  Failed to add to playlist: {e}")

        return {
            'video_id': video_id,
            'video_url': video_url,
            'title': title,
            'privacy_status': privacy_status
        }

    except HttpError as e:
        print(f"❌ YouTube API error: {e}")
        return None
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None


def post_comments(
    youtube,
    video_id: str,
    comments: List[str]
) -> int:
    """
    Post comments to a video

    Args:
        youtube: YouTube API service object
        video_id: YouTube video ID
        comments: List of comment texts to post

    Returns:
        Number of successfully posted comments
    """
    if not youtube:
        print("YouTube API not authenticated")
        return 0

    posted_count = 0

    print(f"\n💬 Posting {len(comments)} comments...")

    for i, comment_text in enumerate(comments, 1):
        try:
            youtube.commentThreads().insert(
                part='snippet',
                body={
                    'snippet': {
                        'videoId': video_id,
                        'topLevelComment': {
                            'snippet': {
                                'textOriginal': comment_text
                            }
                        }
                    }
                }
            ).execute()
            print(f"   Comment {i}/{len(comments)} posted")
            posted_count += 1
        except HttpError as e:
            print(f"   ⚠️  Failed to post comment {i}: {e}")
        except Exception as e:
            print(f"   ⚠️  Error posting comment {i}: {e}")

    print(f"✅ Posted {posted_count}/{len(comments)} comments successfully")
    return posted_count


def update_video_metadata(
    youtube,
    video_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    category_id: Optional[str] = None
) -> bool:
    """
    Update video metadata

    Args:
        youtube: YouTube API service object
        video_id: YouTube video ID
        title: New title (optional)
        description: New description (optional)
        tags: New tags (optional)
        category_id: New category ID (optional)

    Returns:
        True if update successful, False otherwise
    """
    if not youtube:
        print("YouTube API not authenticated")
        return False

    try:
        # Get current video data
        video = youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()

        if not video.get('items'):
            print(f"Video not found: {video_id}")
            return False

        snippet = video['items'][0]['snippet']

        # Update only provided fields
        if title:
            snippet['title'] = title
        if description:
            snippet['description'] = description
        if tags:
            snippet['tags'] = tags
        if category_id:
            snippet['categoryId'] = category_id

        # Update video
        youtube.videos().update(
            part='snippet',
            body={
                'id': video_id,
                'snippet': snippet
            }
        ).execute()

        print(f"✅ Video metadata updated successfully")
        return True

    except HttpError as e:
        print(f"❌ Failed to update video metadata: {e}")
        return False
    except Exception as e:
        print(f"❌ Error updating metadata: {e}")
        return False


def upload_video_with_metadata(
    video_path: str,
    metadata: Dict,
    thumbnail_path: Optional[str] = None,
    comments: Optional[List[str]] = None,
    privacy_status: str = "private",
    playlist_id: Optional[str] = None
) -> Optional[Dict]:
    """
    Complete workflow: authenticate, upload video, set thumbnail, post comments

    Args:
        video_path: Path to video file
        metadata: Video metadata dictionary (title, description, tags, etc.)
        thumbnail_path: Optional path to thumbnail
        comments: Optional list of comments to post
        privacy_status: Privacy setting (private, unlisted, public)
        playlist_id: Optional playlist ID

    Returns:
        Dictionary with upload results or None if upload fails
    """
    # Authenticate
    youtube = authenticate_youtube()
    if not youtube:
        print("⚠️  YouTube authentication failed - skipping upload")
        return None

    # Extract metadata
    title = metadata.get('youtube_title', metadata.get('title', 'Untitled'))
    description = metadata.get('youtube_description', metadata.get('description', ''))
    tags = metadata.get('tags', [])

    # Upload video
    result = upload_video(
        youtube=youtube,
        video_path=video_path,
        title=title,
        description=description,
        tags=tags,
        privacy_status=privacy_status,
        thumbnail_path=thumbnail_path,
        playlist_id=playlist_id
    )

    if not result:
        return None

    video_id = result['video_id']

    # Post comments if provided
    if comments:
        post_comments(youtube, video_id, comments)

    return result


# Test function
if __name__ == "__main__":
    import sys

    print("YouTube Uploader Test")
    print("=" * 60)

    # Test authentication
    youtube = authenticate_youtube()
    if youtube:
        print("\n✅ Authentication successful!")
        print("\nTo upload a video, use:")
        print("  python youtube_uploader.py upload <video_path>")
    else:
        print("\n❌ Authentication failed")
        print("\nSetup instructions:")
        print("1. Go to Google Cloud Console (https://console.cloud.google.com)")
        print("2. Create a new project or select existing one")
        print("3. Enable YouTube Data API v3")
        print("4. Create OAuth 2.0 credentials (Desktop app)")
        print("5. Download credentials JSON and save as 'youtube_credentials.json'")
        sys.exit(1)

    # Upload test (if video path provided)
    if len(sys.argv) > 2 and sys.argv[1] == "upload":
        video_path = sys.argv[2]

        metadata = {
            'youtube_title': 'Test Video Upload',
            'youtube_description': 'This is a test upload from AI Video Bot',
            'tags': ['test', 'ai-video-bot']
        }

        result = upload_video_with_metadata(
            video_path=video_path,
            metadata=metadata,
            privacy_status='private'
        )

        if result:
            print(f"\n✅ Upload complete!")
            print(f"   Video URL: {result['video_url']}")
        else:
            print("\n❌ Upload failed")
