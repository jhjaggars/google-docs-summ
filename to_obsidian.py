# given a document id, produce a valid obsidian markdown file with a summary as well as a link to the full document
import os
import argparse
import time
from langchain_community.llms import Ollama
from gdocs import get_docs_service
from concurrent.futures import ThreadPoolExecutor
import logging
logging.basicConfig(level=logging.INFO)

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

def _fetch(document_id, docs_service, directory, sum_exec):
    try:
        start = time.time()

        doc = docs_service.documents().get(documentId=document_id).execute()

        elapsed = time.time() - start
        logging.info(f"fetched [{document_id}]: {elapsed} elapsed")
    except Exception as e:
        logging.info(f"failed to fetch [{document_id}]: {e}")
        return

    doc_title, context, rev = parse_doc(doc)

    # see if the revisionId has changed since the last run
    full_path = None
    should_summarize = True

    if directory:
        full_path = os.path.join(directory, "%s.md" % slug(doc_title))
        try:
            with open(full_path) as fp:
                for line in fp:
                    if line.strip().startswith("revisionId:"):
                        revision_id = line.split(":")[1]
                        # if we've summarized the document in the past and
                        # it does not have a revision id then we can't
                        # really know if it has changed this way, so don't
                        # bother summarizing again
                        should_summarize = rev is not None and revision_id.strip() != rev
        except FileNotFoundError:
            logging.info(f"{full_path} does not exist")

    if should_summarize:
        sum_exec.submit(_summarize, doc_title, context, document_id, rev, full_path)


def _summarize(title, context, document_id, rev, full_path):
    start = time.time()
    summary = summarize(context)
    elapsed= time.time() - start

    logging.info(f"summarized '{title}' ({len(context)} chars) {elapsed} elapsed")

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('documents', nargs='+', help='the document id to convert')
    parser.add_argument('-d', '--directory', help='directory to put output files', default="/home/jhjaggars/Documents/ObsidianVault/docs")
    args = parser.parse_args()

    docs_service = get_docs_service()
    
    summarizer = ThreadPoolExecutor(max_workers=1)

    with ThreadPoolExecutor(max_workers=5) as executor:
        for document_id in args.documents:
            executor.submit(_fetch, document_id, docs_service,args.directory, summarizer)
    
    summarizer.shutdown()
