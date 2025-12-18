"""
YouTube OAuth 2.0 Console Authentication
For use in Docker/headless environments
"""
import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

BASE = Path(__file__).parent
CREDENTIALS_FILE = BASE / "youtube_credentials.json"
TOKEN_FILE = BASE / "youtube_token.pickle"

def authenticate_console():
    """Authenticate using console flow (no browser required)"""
    creds = None

    # Try to load existing token
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
            print("Loaded existing token")
        except Exception as e:
            print(f"Error loading token: {e}")

    # Check if credentials are valid
    if creds and creds.valid:
        print("✅ Existing credentials are still valid!")
        return creds

    # Try to refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
            print("✅ Credentials refreshed successfully!")

            # Save refreshed token
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
            return creds
        except Exception as e:
            print(f"⚠️  Refresh failed: {e}")
            print("Need to re-authenticate...")

    # Need new authentication
    if not CREDENTIALS_FILE.exists():
        print(f"❌ Credentials file not found: {CREDENTIALS_FILE}")
        print("Please download OAuth 2.0 credentials from Google Cloud Console")
        return None

    print("\n" + "="*60)
    print("Starting OAuth 2.0 authentication (console mode)")
    print("="*60)
    print("\nThis will display a URL. Please:")
    print("1. Open the URL in your browser")
    print("2. Sign in with your Google account")
    print("3. Grant permissions")
    print("4. Copy the authorization code")
    print("5. Paste it back here\n")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            SCOPES
        )

        # Use console flow instead of local server
        creds = flow.run_console()

        # Save the credentials
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

        print("\n✅ Authentication successful!")
        print(f"✅ Token saved to: {TOKEN_FILE}")
        return creds

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

if __name__ == "__main__":
    creds = authenticate_console()
    if creds:
        print("\n✅ You can now run the video pipeline with YouTube upload enabled!")
    else:
        print("\n❌ Authentication failed. Please check your credentials.")
