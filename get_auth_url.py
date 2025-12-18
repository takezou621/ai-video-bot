"""
Generate YouTube OAuth authorization URL
"""
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

CREDENTIALS_FILE = Path(__file__).parent / "youtube_credentials.json"

if __name__ == "__main__":
    if not CREDENTIALS_FILE.exists():
        print(f"Error: {CREDENTIALS_FILE} not found")
        exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        SCOPES,
        redirect_uri='http://localhost:8080'
    )

    auth_url, _ = flow.authorization_url(
        prompt='consent',
        access_type='offline',
        include_granted_scopes='true'
    )

    print("\n" + "="*70)
    print("YOUTUBE OAUTH AUTHORIZATION")
    print("="*70)
    print("\nStep 1: Open this URL in your browser:")
    print("\n" + auth_url + "\n")
    print("Step 2: Sign in with your Google account and authorize")
    print("Step 3: You'll be redirected to http://localhost:8080/?code=...")
    print("Step 4: Copy the FULL redirect URL")
    print("="*70)
    print("\nAfter completing authorization, run:")
    print("  docker compose run --rm ai-video-bot python save_auth_code.py")
    print("\nAnd paste the full redirect URL when prompted.")
    print("="*70 + "\n")
