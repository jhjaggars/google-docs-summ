# given a document id, produce a valid obsidian markdown file with a summary as well as a link to the full document

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import argparse
import time
import sys
from langchain_community.llms import Ollama

def get_docs_service():
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
    return docs_service

def parse_doc(doc):
    doc_title = doc.get('title')
    doc_content = doc.get('body').get('content')

    context = ''
    for element in doc_content:
        if 'paragraph' in element:
            for para_element in element.get('paragraph').get('elements'):
                try:
                    context += para_element.get('textRun').get('content', '')
                except Exception:
                    pass

    return doc_title, context, doc.get("revisionId")

def summarize(ctx):
    prompt_template = f"""
    Produce a summary of the supplied context.  The summary should be at least 2 sentences long.  The summary should be no more than 4 sentences long.  Try to include the names of people mentioned in the context.

    Context: {ctx}
    """
    llm = Ollama(model="mistral")
    return llm.invoke(prompt_template)


def encode(ch):
    if ch in ('/', '?'):
        return "-"
    return ch


def slug(term):
    return "".join(encode(ch) for ch in term)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('documents', nargs='+', help='the document id to convert')
    parser.add_argument('-d', '--directory', help='directory to put output files', default="/home/jhjaggars/Documents/ObsidianVault/docs")
    args = parser.parse_args()

    docs_service = get_docs_service()


    for document_id in args.documents:
        try:
            sys.stdout.write(f"fetching google doc {document_id}")
            sys.stdout.flush()
            start = time.time()

            doc = docs_service.documents().get(documentId=document_id).execute()

            elapsed = time.time() - start
            sys.stdout.write(f" {elapsed} elapsed\n")
            sys.stdout.flush()
        except Exception:
            continue

        doc_title, context, rev = parse_doc(doc)

        # see if the revisionId has changed since the last run
        full_path = None
        should_summarize = True
        if args.directory:
            full_path = os.path.join(args.directory, "%s.md" % slug(doc_title))
            try:
                with open(full_path) as fp:
                    for line in fp:
                        if line.strip().startswith("revisionId:"):
                            revision_id = line.split(":")[1]
                            print(f"{revision_id.strip()} == {rev}?")
                            should_summarize = revision_id.strip() != rev
            except FileNotFoundError:
                pass

        if should_summarize:
            sys.stdout.write(f"summarizing '{doc_title}' ({len(context)} chars)")
            sys.stdout.flush()
            start = time.time()
            summary = summarize(context)
            elapsed= time.time() - start

            sys.stdout.write(f" {elapsed} elapsed\n")
            sys.stdout.flush()

            final_output = "\n".join((
                '---',
                f"documentId: {document_id}",
                f"revisionId: {rev}",
                f"url: https://docs.google.com/document/d/{document_id}",
                "aliases:",
                f"  - {document_id}",
                "---",
                f"{summary}"
            ))

            if full_path:
                with open(full_path, 'w') as fp:
                    fp.write(final_output)
            else:
                print(final_output)
