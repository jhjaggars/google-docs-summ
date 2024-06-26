from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import argparse

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

# Step 2: Build the service objects
docs_service = build('docs', 'v1', credentials=creds)
drive_service = build('drive', 'v3', credentials=creds)

parser = argparse.ArgumentParser()
parser.add_argument('document', help='the document id to convert')
args = parser.parse_args()
document_id = args.document.split()[0] # list formats doc id \t name

# Use the Google Docs API to get the document content
doc = docs_service.documents().get(documentId=document_id).execute()
doc_content = doc.get('body').get('content')

# Convert the document content to plain text
text_output = ''
for element in doc_content:
    if 'paragraph' in element:
        for para_element in element.get('paragraph').get('elements'):
            print(para_element)
            try:
                text_output += para_element.get('textRun').get('content', '')
            except Exception:
                pass

# Save or process the plain text as needed
print(text_output)
