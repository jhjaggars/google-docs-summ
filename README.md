# Summarize Google Docs

This project feeds the text from google docs into a local ollama served model and asks it to summarize the supplied doc.

I'm using this to maintain summarized notes in Obsidian for google docs that I have linked like this:

```
rg https://docs.google.com/document/d $HOME/Documents/ObsidianVault/ | python extract.py | xargs -n 1 bin/python to_obsidian.py
```

In order to fetch google docs you'll need to configure an [oauth credential](https://console.cloud.google.com/apis/credentials).
