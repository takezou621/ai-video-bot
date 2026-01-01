"""
YouTube OAuth 2.0 Token Exchange
Exchange authorization code for access token
"""
import sys
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

def exchange_code(auth_code):
    """Exchange authorization code for credentials"""
    if not CREDENTIALS_FILE.exists():
        print(f"❌ Credentials file not found: {CREDENTIALS_FILE}")
        return None

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            SCOPES,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )

        # Exchange the authorization code for credentials
        flow.fetch_token(code=auth_code)
        creds = flow.credentials

        # Save the credentials
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

        print("✅ Authentication successful!")
        print(f"✅ Token saved to: {TOKEN_FILE}")
        return creds

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python youtube_auth_with_code.py <authorization_code>")
        print("\n1. Visit the authorization URL from the previous step")
        print("2. Grant permission and copy the authorization code")
        print("3. Run: python youtube_auth_with_code.py <your_code>")
        sys.exit(1)

    auth_code = sys.argv[1]
    creds = exchange_code(auth_code)

    if creds:
        print("\n✅ You can now run YouTube upload!")
        print("Run: docker compose -f docker-compose-cpu.yml run --rm ai-video-bot python youtube_upload_single.py")
    else:
        print("\n❌ Failed to authenticate. Please try again.")
