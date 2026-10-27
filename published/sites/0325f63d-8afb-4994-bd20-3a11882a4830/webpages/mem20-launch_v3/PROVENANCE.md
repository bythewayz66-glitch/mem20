# mem20-launch_v3 — provenance record

Republished `/sites/` launch page. This file records exactly what was published,
where it came from, and how the tool-count claim was established.

## Artifact

| Field | Value |
| --- | --- |
| Repo path | `published/sites/0325f63d-8afb-4994-bd20-3a11882a4830/webpages/mem20-launch_v3/index.html` |
| Bytes | 40727 |
| SHA-256 | `f51d90458858f32c612262f9da4458f127016d7845d44f0acdce3b053672e4d5` |
| Supersedes (repo path) | `published/sites/0325f63d-8afb-4994-bd20-3a11882a4830/webpages/mem20-launch_v2/index.html` |
| Superseded SHA-256 | `89b704a7b35d18ddba753bac27da3f03a9a5de5683dcee717c50196a206870c4` |

## Source

| Field | Value |
| --- | --- |
| Source file | `docs/index.html` |
| Bytes | 40727 |
| SHA-256 | `9bce8f7a39dd9a665cb3645db5df562c1c84892f00b23c6d34f178c3ea5f7cdd` |
| Basis commit | `7c0b3e8d9525cd8c3a9f8f1825267aed52fac68a` (unchanged through `b908ba9`) |

The published page is the source file with exactly four anchored replacements
applied, and no other change. Source and artifact are the same length because
each replacement swaps `268`->`270` and `26`->`27`: character counts are equal.

| # | Original text (line in docs/index.html) | Replacement |
| --- | --- | --- |
| 1 | `...origin-tagged ledger. 268 tools across 26 domains.` (416) | `...origin-tagged ledger. 270 tools across 27 domains.` |
| 2 | `JSON-RPC 2.0 over stdio, 268 tools across 26 domains - drops into LangGraph...` (565) | same sentence, `270` / `27` |
| 3 | `MCP-native: JSON-RPC 2.0 over stdio, 268 tools across 26 domains.` (785) | `270` / `27` |
| 4 | `<li>268 tools . 26 domains</li>` (841) | `<li>270 tools . 27 domains</li>` |

## Why 270 / 27 is the number published

- **Tool count 270 is handshake-verified, not copied.** `verify_mcp.py` (the
  repo's own verifier) instantiates the server and counts `tools/list`:
  `TOOL_COUNT: 270` and `RESULT: PASS` against `MEM20_EXPECTED_TOOLS=270`.
- **The 27 is the domain count the project itself documents.** The domain table
  in `docs/README.md` ("270 Tools Across 27 Domains") lists per-domain counts
  whose arithmetic sums to exactly 270.
- `CHANGELOG.md` records the 257/26 -> 270/27 reconciliation as the intended
  correction, and `verify_mcp.py` fails CI unless the count is exactly 270.
- Note for reviewers: `docs/README.md`'s table carries **30** rows labelled as
  27 domains, because several rows group multiple prefixes (`cog_*` / `tot_*` /
  substrate, `cloud_*` / `cloudstorage_*`, `self_model_*`). The 27 is therefore
  a grouping choice, not a raw prefix count (the raw `tools/list` surface has 37
  distinct prefixes). Flagged rather than silently restated.

## Infrastructure finding (unchanged, re-stated for the record)

`/sites/...` URLs on `static.teamily.ai` are access-controlled: an anonymous
request is refused, so the CDN copy is not a public surface. The GitHub commit
is the canonical copy of this artifact.

## Verification performed

- Artifact in `origin/main` re-read and hashed: matches `f51d9045...` byte for byte.
- Artifact compared against the locally built and reviewed file: identical (`cmp`).
- Stale-count gate over the published artifact: `270 tools` present 4 times,
  zero occurrences of `268 tools`, `26 domains`, `~258`, `~260`, `257 tools`.
- HTML tag balance over the published artifact: no unclosed or mismatched tags.
- `published/MANIFEST.tsv` carries this artifact's path, byte size and SHA-256.

## Status at publication

Committed to `main` as `b908ba9`, on top of `412716b` (the one-shot job that
produced it). The job, and a temporary base64 probe file, were removed in that
same commit, so `main` carries no leftover CI scaffolding for this publish.

## Known remaining gap (owned elsewhere)

Live GitHub Pages (`https://bythewayz66-glitch.github.io/mem20/`, HTTP 200)
still serves **268 tools / 26 domains** because `docs/index.html` on `main`
still contains the old strings, despite commit `ff143c6` being described as
"268/26 -> 270/27 in README and docs/index.html" — that commit only modified
`README.md`. Until `docs/index.html` is corrected, the public site and this
republished artifact disagree.
