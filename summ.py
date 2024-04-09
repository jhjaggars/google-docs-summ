from langchain_community.llms import Ollama
import sys
 
context = sys.stdin.read()
TEMPLATE = f"""
Produce a summary of the supplied context.  The summary should be at least 2 sentences long.  Try to include the names of people mentioned in the context.

Context: {context}
"""

llm = Ollama(model="mistral")
print(llm.invoke(TEMPLATE))
