from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os

# Step 1: Set up the OAuth 2.0 flow for authentication
SCOPES = ['https://www.googleapis.com/auth/documents.readonly', 'https://www.googleapis.com/auth/drive.metadata.readonly']
creds = None
token_file = 'token.json'
credentials_file = 'credentials.json'

if os.path.exists(token_file):
    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
        creds = flow.run_local_server(port=0)
    with open(token_file, 'w') as token:
        token.write(creds.to_json())

# Step 2: Build the Google Drive service object
drive_service = build('drive', 'v3', credentials=creds)

# Step 3: Query Google Drive for Google Docs files
results = drive_service.files().list(
    pageSize=50, 
    fields="nextPageToken, files(id, name, mimeType)",
    q="mimeType='application/vnd.google-apps.document'"
).execute()
items = results.get('files', [])

# Step 4: Print the names and IDs for each document found
if not items:
    print('No Google Docs files found.')
else:
    print('Google Docs files:')
    for item in items:
        print(u'{1}\t{0}'.format(item['name'], item['id']))

