# Generated state in git (issue #16)

## Rule
Do not commit runtime DBs, harness snapshots, or regenerable indexes.

Already in `.gitignore`:
- `*.sqlite3`, `chroma/`, `*.jsonl`, `entries/*.json`, vector indexes

## If large harness files reappear
```bash
git rm --cached -f entries/harness:project-*.json entries/harness-roster-*.json
git rm --cached -f data/*.sqlite3 mem20owebz/data/webui.db*
```

Colon-bearing filenames (`harness:project-…`) are illegal on Windows — rename
generators to use `-` or `_` instead of `:`.
