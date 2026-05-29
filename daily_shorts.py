# On your local machine, run this once
python -c "
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
credentials = flow.run_local_server(port=8080)

with open('token.pickle', 'wb') as f:
    pickle.dump(credentials, f)
print('✅ Token created successfully!')
"

# Then encode for GitHub (Windows PowerShell)
[Convert]::ToBase64String([IO.File]::ReadAllBytes("token.pickle")) | Set-Content -NoNewline token_pickle_base64.txt

# Copy the content of token_pickle_base64.txt and update the GitHub secret
