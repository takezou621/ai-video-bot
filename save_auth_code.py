"""
Save YouTube OAuth authorization code and create token
"""
import pickle
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

BASE = Path(__file__).parent
CREDENTIALS_FILE = BASE / "youtube_credentials.json"
TOKEN_FILE = BASE / "youtube_token.pickle"

if __name__ == "__main__":
    if not CREDENTIALS_FILE.exists():
        print(f"Error: {CREDENTIALS_FILE} not found")
        exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        SCOPES,
        redirect_uri='http://localhost:8080'
    )

    # Generate state for security (must match the one used in URL generation)
    auth_url, state = flow.authorization_url(
        prompt='consent',
        access_type='offline',
        include_granted_scopes='true'
    )

    print("\n" + "="*70)
    print("PASTE REDIRECT URL")
    print("="*70)
    print("\nPaste the full redirect URL from your browser:")
    print("(Should start with http://localhost:8080/?code=...)")
    print("="*70 + "\n")

    redirect_url = input("Redirect URL: ").strip()

    if not redirect_url or 'code=' not in redirect_url:
        print("\n❌ Invalid URL. Please make sure you copied the full redirect URL.")
        exit(1)

    try:
        # Extract code from URL
        code = redirect_url.split('code=')[1].split('&')[0]
        print(f"\n✓ Extracted authorization code")

        # Exchange code for token
        print("✓ Exchanging code for access token...")
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Save token
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

        print(f"✓ Token saved to: {TOKEN_FILE}")
        print("\n" + "="*70)
        print("✅ AUTHENTICATION SUCCESSFUL!")
        print("="*70)
        print("\nYou can now run the video pipeline with YouTube upload enabled:")
        print("  docker compose run --rm ai-video-bot python advanced_video_pipeline.py")
        print("\nOr upload the existing video:")
        print("  docker compose run --rm ai-video-bot python upload_existing_video.py")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease make sure:")
        print("1. You completed the authorization in your browser")
        print("2. You copied the FULL redirect URL including the code parameter")
        print("3. The URL starts with http://localhost:8080/?code=")
        exit(1)
