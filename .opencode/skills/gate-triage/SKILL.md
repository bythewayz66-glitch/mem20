---
name: gate-triage
description: Diagnose a red mem20 CI check and decide whether it is a real regression or pre-existing debt, using the repo's own gate scripts as the source of truth
---

# Gate triage (mem20)

Use this when a check on `main` or on a pull request is red and you need to know
**whether the change caused it** before you touch anything. The mem20 gates are
diff-scoped on purpose, so "red on main" and "red because of this PR" are
different questions and must be answered separately.

## Rule zero: reproduce the gate locally, do not guess

Every gate in this repo is a script you can run. Run the script, read its exit
code, and quote the output. A check name in the GitHub UI is not evidence; the
script's own log is.

| Check (GitHub) | Workflow | Local command |
|---|---|---|
| `hygiene` | `.github/workflows/pr-gate.yml` | `git diff --name-only --diff-filter=ACMR origin/main...HEAD` then apply the Tier A greps |
| `suite` | `.github/workflows/pr-gate.yml` | `python3 -m pytest --collect-only -q` |
| `MCP handshake (shallow clone)` | `.github/workflows/mcp-verify.yml` | `python3 verify_mcp.py` with `MEM20_EXPECTED_TOOLS` set |
| `artifact evidence` | `.github/workflows/artifact-evidence.yml` | `python3 scripts/check_artifact_evidence.py --range origin/main...HEAD --repo .` |
| `doc-count drift gate` | `.github/workflows/doc-counts.yml` | `python3 scripts/ops/check-doc-counts.py` |
| surface / version drift | `scripts/surface_manifest.py` | `python3 scripts/surface_manifest.py --check-docs` |
| `Syntax gate` | `.github/workflows/ci.yml` | `python3 -m py_compile <changed .py files>` |

## The three questions, in order

1. **Is it red on `main` too?** Check out `main` at the merge base and run the
   same command. If it fails there, it is pre-existing debt and your PR is not
   the cause. Say so with the command and the exit code — do not "fix" it as
   part of an unrelated change.
2. **Is it diff-scoped?** `pr-gate.yml` and `artifact-evidence.yml` only inspect
   files the PR adds or changes. A legacy violation already on `main` cannot
   fail a clean PR. If a diff-scoped gate is red, the offending path is in your
   own diff — find it in the gate's printed file list.
3. **Is it a real regression?** Only then change code. Fix the root cause; never
   skip, xfail, or mock a test to make a gate green (conformance rule 5).

## Artifact evidence specifically

`scripts/check_artifact_evidence.py` fails a **delivery** that carries no
committed artifact. Two things satisfy it:

* a **40-character SHA** of a pushed branch, verified as a real commit object
  (`git cat-file --batch-check`), or
* a permanent URL (`https://static.teamily.ai/sites/...` or `/files/...`)
  committed **under `docs/`** — a URL outside `docs/` is ignored with a warning.

It is exempt when the range authors nothing on the trunk line (a pure merge
convergence), when the authored commits change no file, or when the change is
the gate's own machinery (`.github/workflows/`, `scripts/check_artifact_evidence.py`).
An exempt pass prints `EXEMPT` and the reason — a green log is not proof of a
verified delivery, so read which branch of the gate you hit.

Self-check before pushing:

```bash
python3 scripts/check_artifact_evidence.py --self-test
python3 scripts/check_artifact_evidence.py --range origin/main...HEAD --repo .
```

## Reporting

State, per red check: the command you ran, its exit code, whether it also fails
on `main`, and the one-line cause. Never report a check as fixed without the
command output that shows it passing.
