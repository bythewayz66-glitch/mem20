# mem20 — Agent State Board

> Living board. One row per in-flight item. Update it when your claim changes
> state. Keep it to the current week; move finished rows to `archive/`.
>
> **Last updated:** 2026-10-15 by Teamily (repo audit).

## In progress

| Issue | Agent | Layer | Status | Branch | Next step |
|---|---|---|---|---|---|
| #1 | Teamily | hygiene | review | `audit/mem20-2026-10` | Owner review of the audit branch; merge or request changes |

## Blocked — needs the human owner

| Issue | Agent | Blocked on |
|---|---|---|
| — | — | — |

## Ready and unclaimed (claim one)

| Issue | Severity | Layer | Title |
|---|---|---|---|
| see `issues?label=severity:critical` | critical | OpenCode | Quarantine or remove `mcp_server_dir/` (25 unparseable files) |
| see `issues?label=ci` | high | Teamily | CI: land the syntax gate and green it on `main` |
| see `issues?label=tech-debt` | high | Teamily | Stop tracking `build/` and `__pycache__` in git |
| see `issues?label=bug` | medium | OpenCode | `install_tracker.py` `try:` is commented out |
| see `issues?label=documentation` | medium | Teamily | README version/ tool-count skew |

> This table is refreshed from the live issue list; when it and the issues
disagree, **the issues win**.

## Recently done (last 7 days)

| Issue | Agent | Landed |
|---|---|---|
| #1 | Teamily | Issue tracking enabled; labels, milestone, templates, CI, protocol |
| — | Teamily | Fixed unterminated f-string in `mem20agentz/gateway_web.py` (branch `audit/mem20-2026-10`) |
