from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import googleapiclient
import google_auth_httplib2
import httplib2
import os

def get_credentials():
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
    return creds


def get_docs_service(creds=None):
    
    if creds is None:
        creds = get_credentials()

    def build_request(http, *args, **kwargs):
        new_http = google_auth_httplib2.AuthorizedHttp(creds, http=httplib2.Http())
        return googleapiclient.http.HttpRequest(new_http, *args, **kwargs)

    # Step 2: Build the service objects
    docs_service = build('docs', 'v1', requestBuilder=build_request, http=httplib2.Http())
    return docs_service
