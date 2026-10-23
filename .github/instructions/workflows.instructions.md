---
applyTo: ".github/workflows/**,.github/**"
---

# Workflow and `.github/` rules

Existing workflows: `ci.yml`, `pages.yml`, `release.yml`, `mem20-web.yml`,
`ruby-sdk.yml`, and `copilot-setup-steps.yml`.

## Conventions already in use

- Pin actions to a major tag (`actions/checkout@v4`, `actions/setup-python@v5`,,
  `actions/setup-node@v4`, `dtolnay/rust-toolchain@stable`). Keep that style.
- Declare `permissions:` explicitly. `mem20-web.yml` needs `contents: write`
  because it publishes; everything else should default to read.
- Use `concurrency:` with `cancel-in-progress: false` for publish jobs so a
  Pages deploy is never cancelled mid-flight.
- Failures are surfaced with `::error::` annotations — keep that idiom when adding
  a guard.

## `copilot-setup-steps.yml` contract

This workflow prepares the environment for the Copilot coding agent. It is
special: the job **must** be named `copilot-setup-steps`, and the file must stay
at `.github/workflows/copilot-setup-steps.yml`. It only runs on
`workflow_dispatch` plus the agent's internal trigger — it does not run on push,
so it costs nothing on normal PRs. If you rename the job or the file, the coding
agent silently falls back to a bare environment.

## CI guards you must not remove

- `gitlink-guard` / dangling-gitlink checks (mode 160000) — these prevent checkouts
  that break Pages.
- `Guard against tracked bytecode` — fails on tracked `*.pyc` / `__pycache__`.
- `dependency-audit` — `pip-audit -r requirements.txt`, non-blocking by design
  (`|| exit 0`); it warns rather than fails.
- The green-set count assertion (`-ne 22`).

## Editing the green set

`ci.yml`'s `tests` job runs a fixed list of 22 packages and asserts the count. If
you add or drop a package, update both the `GREEN` list and the `-ne 22` guard in
the same commit, or CI fails on the count check.
