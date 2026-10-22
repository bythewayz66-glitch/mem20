# Generated state (issue #16)

Do not commit runtime DBs or harness snapshots.

Ignored: `*.sqlite3`, `chroma/`, `*.jsonl`, `entries/*.json`, `mem20owebz/data/webui.db*`.

If large files reappear:
```bash
git rm --cached -f entries/harness*.json 'entries/harness:*.json'
git rm --cached -f data/*.sqlite3 mem20owebz/data/webui.db*
```
