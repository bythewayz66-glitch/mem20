# Contribution-Evidence Gate

**Status:** landed on `chore/contrib-evidence-gate-2026-11-07`
**Owner:** GitHub Repo Assistant (step 1 of the all-agent contribution plan)
**Rule enforced:** *a contribution is a commit on a pushed branch — nothing else counts.*

---

## 1. What this gate is

A pull-request check that **fails any PR whose body carries neither a
40-character commit SHA nor a URL that answers HTTP 200.**

It exists because the all-agent contribution plan
(`docs/ops/agent-contribution-plan-2026-11-07.md`) is only real if it is
mechanically enforced. Chat descriptions, plans and summaries are not
contributions; a commit on a pushed branch is. This gate makes that rule
checkable by a machine instead of by a reader.

It is **step 1** of the plan precisely because it makes every later step
verifiable: once it is a required check, no agent can land a PR that claims a
contribution without pointing at the commit that *is* the contribution.

## 2. The rule, exactly

A PR body **passes** when it contains at least one of:

| Kind | What counts | Example |
|---|---|---|
| Commit SHA | a bare 40-hex-character token, or a `github.com/<owner>/<repo>/commit/<sha>` URL | `e34963f3f1c5801a9fd45a424b168eb30d18c5ba` |
| Verified URL | any `http(s)://` URL in the body that answers **HTTP 200** | `https://github.com/bythewayz66-glitch/mem20` |

A PR body **fails** when it contains neither.

Notes on the matching:

- The SHA must be exactly 40 hex characters. A 40-hex slice of a longer hex run
  (e.g. a 64-character blob digest) does **not** count — the token must stand
  alone.
- The URL probe follows redirects and accepts only a final `200`. A `403`, `404`
  or a timeout does not count. Private artifact URLs that require an access
  token therefore do **not** satisfy the gate on their own — use a public URL or
  the commit SHA.
- The gate is **body-only**. It never inspects the diff, so it cannot be
  satisfied by the change itself, and it never needs a token or a secret.

## 3. Files

| File | Role |
|---|---|
| `.github/workflows/contrib-evidence.yml` | the workflow; runs on `pull_request` to `main` |
| `scripts/ops/verify-contrib-evidence.sh` | the gate itself; reads a body, exits 0/1 |
| `docs/ops/contrib-evidence-gate.md` | this document |

## 4. Running it locally

```bash
# fail: no evidence
printf 'adds a thing\n' > /tmp/body.txt
bash scripts/ops/verify-contrib-evidence.sh --body-file /tmp/body.txt   # exit 1

# pass: a 40-char SHA
printf 'evidence: e34963f3f1c5801a9fd45a424b168eb30d18c5ba\n' > /tmp/body.txt
bash scripts/ops/verify-contrib-evidence.sh --body-file /tmp/body.txt   # exit 0

# pass: a URL that answers 200
printf 'evidence: https://github.com/bythewayz66-glitch/mem20\n' > /tmp/body.txt
bash scripts/ops/verify-contrib-evidence.sh --body-file /tmp/body.txt   # exit 0
```

Options:

```
--body-file <path>   read the PR body from a file
--body <text>        read the PR body from the argument
--require-sha        also require a 40-char SHA
--require-url        also require a 200-verified URL
--timeout <seconds>  per-URL curl timeout (default 10)
--json               emit a one-line JSON verdict
```

Exit codes: `0` evidence present · `1` no evidence (or a required kind missing)
· `2` usage error.

Environment: `CONTRIB_EVIDENCE_TIMEOUT` (per-URL timeout),
`CONTRIB_EVIDENCE_OFFLINE=1` (skip the network probe; accept any well-formed
`http(s)` URL — used by the self-test).

## 5. How to satisfy it

Put the evidence in the PR body, not in the diff:

```
Contribution: <branch> @ <40-char head SHA>
Evidence: https://github.com/bythewayz66-glitch/mem20/commit/<40-char head SHA>
```

Read the SHA back from the remote — never from your own claim:

```bash
git ls-remote --heads origin <branch>   # must return a 40-char SHA
```

## 6. Making it a required check (flip procedure)

The workflow lands **advisory** first, exactly like `pr-gate.yml`'s Tier B, so
it cannot block the very PR that introduces it. To make it blocking:

1. Settings → Branches → branch protection for `main` → *Require status checks
   to pass* → add **`contribution evidence`**.
2. Confirm the check name matches the job's `name:` in the workflow.

Until then the check still runs on every PR and reports red/green; it simply is
not yet a merge blocker.

## 7. Evidence

The gate is proven by two runs of the same workflow on the same branch — one
seeded to fail, one compliant:

| Case | PR body | Expected | Run |
|---|---|---|---|
| Seeded no-evidence | no SHA, no 200 URL | **red** | _filled in below_ |
| Compliant | 40-char head SHA | **green** | _filled in below_ |

Branch head SHA (read back from the remote): _filled in below_.

## 8. Scope

This gate touches only the three files listed in §3. It does not read or write
any frozen path from the 4.0 conformance overhaul, and it does not inspect the
diff, so it cannot conflict with the live sweep.
