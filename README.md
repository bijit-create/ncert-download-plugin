# NCERT download plugin for Claude Code

This Claude Code plugin downloads NCERT textbook chapter PDFs (classes 3-10, Maths, Science, EVS and
Social Science) from ncert.nic.in. It covers English, Hindi, Urdu, Telugu, Punjabi, Tamil, Odia, Bengali,
Marathi, Gujarati and Kannada. It checks every file and sets the files out in folders for translation.

## Install

In Claude Code:

```
/plugin marketplace add bijit-create/ncert-download-plugin
/plugin install ncert-download@ncert-download
```

Then ask Claude, for example: "download the Kannada NCERT chapters for class 6".

## Without Claude

The scripts run on their own with Python 3 (`pip install requests pymupdf`). The steps are in
[`plugins/ncert-download/skills/ncert-download/SKILL.md`](plugins/ncert-download/skills/ncert-download/SKILL.md).
