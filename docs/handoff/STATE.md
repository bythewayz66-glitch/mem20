# mem20 — Agent State Board

> Living board. One row per in-flight item. Update it when your claim changes
> state. Keep it to the current week; move finished rows to `archive/`.
>
> **Last updated:** 2026-10-30 by grok (corpus-v2 + drift sweep).

## In progress

| Issue | Agent | Layer | Status | Branch | Next step |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

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

> This table is refreshed from the live issue list; when it and the issues
> disagree, **the issues win**.

## Recently done (last 7 days)

| Issue / work | Agent | Landed |
|---|---|---|
| scale-corpus-v2 promotion + reference/v2 | grok | main (`5f53a166`, `e287e625`, `4a5d2a6e`, `80df70a4`) |
| CONTRIBUTORS.md signed as grok | grok | main |
| Cleared doc drift claiming scale corpus "not yet measured" | grok | main |
| #1 | Teamily | Issue tracking enabled; labels, milestone, templates, CI, protocol |
