import sys
import re
PAT = re.compile(r'https://docs.google.com/document/d/(.*)/')

for m in PAT.finditer(sys.stdin.read()):
    print(m.group(1))
