# published/history — the mem20 program record

Durable, in-repository copy of the mem20 program history. This directory exists because a document about durability that lives only behind a token-gated URL is not itself durable — see `published/README.md`, rule 2: *The Sidney host is retired and is not a storage location.*

| File | What it is |
|---|---|
| `mem20-program-history.md` | The record, in Markdown. 13,382 words, 16 sections. |

Markdown rather than HTML deliberately: every other preserved document under `published/` is Markdown, the archive's integrity mechanism is a SHA-256 list (`MANIFEST.tsv`), and a second rendering of the same text is a second thing to keep in sync. Convert at read time if a page is wanted.

## Scope

A dated narrative of the program from the root commit (`2b07f7d`, 2026-09-06) to the frontier (`7c0b3e8`, 2026-10-26), built from the repository's own primary sources: the full commit log with diffstats, the four failure ledgers, the audits, the ADRs, and the three daily ops reports.

The spine is the **what broke / what we learned** thread, told at the point in the narrative where each failure happened rather than collected at the end. Deliberate refusals are kept: the decimator that refuses instead of returning a broken mesh, the 310 records left unlabelled on purpose, the 228 clone packages specified rather than deleted, the branch closed at zero unique commits instead of merged for the appearance of activity.

## Standing

This is a snapshot, not a live view. It was measured against `7c0b3e8d9525cd8c3a9f8f1825267aed52fac68a` and says so in its own footer. A later reader should expect the frontier to have moved and should re-derive any figure rather than quote this document's — the repository has already shown, in `CHANGELOG.md`, how fast a number typed by a human goes stale.

Section 14 of the document reconciles every figure against the brief that commissioned it, including two that were wrong. Section 15 lists every claim that could not be checked, in the form `PROOF.md` established.

## Verification

Every figure is reproducible from a full (non-shallow) clone. The commands appear inline, next to the numbers they produce:

```
git rev-list --count HEAD                                  # 234
git rev-list --count --all                                 # 309
git ls-tree -r --name-only HEAD | wc -l                    # 7,915
python3 verify_mcp.py                                      # TOOL_COUNT: 270 -> RESULT: PASS
```

`verify_mcp.py` needs its own dependencies installed first; on a bare interpreter it reports `EOF from server` rather than a failure, which is a fact the document records in §11.1 because it is the same defect class the rest of the document is about.

## Secrets and personal data

No credentials, tokens, keys, host addresses, ports, internal DNS names, personal filesystem paths, or email addresses. Personal names appear only as the public repository attribution the commit log itself publishes. Where a source document quoted a personal filesystem path, the finding is reported with the path replaced by `[home]` — the count is the evidence and the string is not.
