# Series delivery record

What this covers: the reader-facing pages under `/series/` for both mem20
properties — The Comicbook Artist (comic) and Mem20-naration's Chronicles.

## What was built

The series pages are **generated**, not hand-written. `docs/series/_build.py`
reads what actually exists in the repo and writes every page from it:

| Source | Becomes |
| --- | --- |
| `comics/the-z-corps/issue-NN/*.pdf` | one reader page per finished issue |
| `comics/the-z-corps/issue-NN/*Shooting_Script.md` | that issue's page-by-page beats |
| `docs/app/narrative/serial-*.md` | one reader page per chronicle installment |

It writes, in one pass, so the index and the data can never disagree:

- `comic/issue-NN.html` — 12 issue readers
- `chronicles/NNN.html` — 35 installment readers
- `comic/index.html`, `chronicles/index.html`, `index.html`
- `data/comic-issues.json`, `data/chronicles.json`, `chronicles/feed.xml`

`docs/series/_verify.py` then asserts that the page count, the JSON entry
count, the index links and the RSS item count all agree, and that every reader
page loads the shared `series.css` and `analytics.js`. The build workflow runs
both, so a page can never ship describing a corpus it does not match.

## Live

- https://mem20.com/series/
- https://mem20.com/series/comic/
- https://mem20.com/series/chronicles/
- https://mem20.com/series/data/comic-issues.json
- https://mem20.com/series/data/chronicles.json
- https://mem20.com/series/chronicles/feed.xml

## Artifacts

The generator and its modules, as published from the build sandbox:

- https://static.teamily.ai/files/98c0e271-9e36-4af0-8467-a0a8aa1a1665/_build.py
- https://static.teamily.ai/files/0c93e4ce-884d-4bf2-9ca3-53642eb1db5f/_md.py

## Editorial state

Counts are measured from the corpus on every build, never typed in. An issue is
listed as `ready` only because its PDF exists at its own path; a chronicle is
listed only because its chapter exists in a serial file. Nothing is marked
published on the strength of a plan.
