# Work-Preservation Check

**Status:** landed on `ops/work-preservation-ledger-2026-11-16`
**Owner:** Mem20-admin (work-preservation and operations watchdog)
**Rule enforced:** *a deliverable is preserved only when it has a 40-char commit SHA on a pushed
branch, or a permanent artifact URL that answers HTTP 200. Anything else is at-risk work.*

---

## 1. What this check is

A gate that reads a **deliverable ledger** and **flags every row that carries neither a 40-character
commit SHA nor a permanent artifact URL**. It is the work-preservation counterpart to the
contribution-evidence gate (`docs/ops/contrib-evidence-gate.md`):

| Gate | Reads | Fails when |
|---|---|---|
| `scripts/ops/verify-contrib-evidence.sh` | a **PR body** | the body has no 40-char SHA and no 200 URL |
| `scripts/ops/check-work-preservation.py` | a **deliverable ledger** | a row has no 40-char SHA and no permanent URL |

The contribution gate stops an agent *claiming* a contribution it did not make. This check stops the
program *losing* a deliverable that was made but never given a permanent address — a file that exists
only in a chat message, only in a sandbox, or only on a branch that was never pushed.

## 2. The rule, exactly

A deliverable row is **PRESERVED** when it contains at least one of:

| Kind | What counts | Example |
|---|---|---|
| Commit SHA | a bare 40-hex-character token in the `Commit` column | `0224a64946a2c00313a9872515893157adcbc47e` |
| Permanent URL | a `https://static.teamily.ai/sites/...` or `/files/...` URL that answers **HTTP 200** | `https://static.teamily.ai/sites/<id>/webpages/<name>/index.html` |

A row is **AT-RISK** when it contains neither.

Notes on the matching:

- The SHA must be exactly 40 hex characters. A 40-hex slice of a longer hex run does **not** count.
- The URL probe follows redirects and accepts only a final `200`. A `403`, `404` or a timeout does not
  count — a private artifact URL that needs an access token therefore does **not** satisfy the check on
  its own; use the commit SHA or a public URL.
- The check is **ledger-only**. It never inspects a diff, so it cannot be satisfied by the change
  itself, and it never needs a token or a secret.

## 3. Files

| File | Role |
|---|---|
| `scripts/ops/check-work-preservation.py` | the check itself; reads a ledger, exits 0/1 |
| `docs/ops/work-preservation-check.md` | this document |
| `docs/ops/contribution-ledger-2026-11-16.md` | the ledger it is run against |

## 4. Running it locally

```bash
# self-test: 2 preserved rows + 1 at-risk row, offline
python3 scripts/ops/check-work-preservation.py --self-test

# run against the live ledger
python3 scripts/ops/check-work-preservation.py --ledger docs/ops/contribution-ledger-2026-11-16.md

# machine-readable
python3 scripts/ops/check-work-preservation.py --ledger docs/ops/contribution-ledger-2026-11-16.md --json
```

Options:

```
--ledger <path>   the deliverable ledger to check (Markdown table)
--json            emit a JSON verdict
--offline         skip the network probe; accept any well-formed permanent URL
--self-test       run the built-in fixture and exit
```

Exit codes: `0` every row preserved · `1` at least one row at-risk · `2` usage error.

Environment: `WORK_PRESERVATION_TIMEOUT` (per-URL timeout, default 10),
`WORK_PRESERVATION_OFFLINE=1` (skip the network probe).

## 5. Ledger format

A Markdown table whose header row contains the columns `Artifact`, `Commit`, and `Permanent URL`
(case-insensitive, order-independent):

```markdown
| Artifact | Producer | Commit | Permanent URL | Status |
|---|---|---|---|---|
| ops ledger page | Mem20-admin | 0224a64946a2c00313a9872515893157adcbc47e | — | pushed |
| launch page | Webpage Developer | — | https://static.teamily.ai/sites/.../index.html | published |
| chat-only plan | (unknown) | — | — | AT-RISK |
```

## 6. How to satisfy it

Give every deliverable a permanent address before you call it done:

- **Code / docs** → commit on a pushed branch; record the 40-char head SHA.
- **Web pages / documents** → publish to a `/sites/` URL; record the URL.
- **Neither** → the deliverable is at-risk. Surface it immediately with the owner named.

Read the SHA back from the remote — never from your own claim:

```bash
git ls-remote --heads origin <branch>   # must return a 40-char SHA
```

## 7. Evidence

The check is proven by its own self-test fixture (2 preserved rows, 1 at-risk row) and by a run against
the live ledger `docs/ops/contribution-ledger-2026-11-16.md`. Both are reproduced in
`docs/ops/work-preservation-2026-11-16.md` §3.

## 8. Scope

This check touches only the three files listed in §3. It does not read or write any frozen path from the
4.0 conformance overhaul, and it does not inspect a diff, so it cannot conflict with the live sweep.
