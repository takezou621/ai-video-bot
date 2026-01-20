from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

flow = InstalledAppFlow.from_client_secrets_file('youtube_credentials.json', SCOPES)

# 認証コードからトークンを取得
code = "4/0ASc3gC0kqxpnRZdAsybZPY8CzV7wKcOWxL5NSSV1mafORGEoZSneMHuoudOl5LZfePlEog"
flow.fetch_token(code=code)

# トークンを保存
with open('youtube_auth.pickle', 'wb') as f:
    pickle.dump(flow.credentials, f)

print("✅ 認証が完了しました！")
print(f"トークンを保存: youtube_auth.pickle")
