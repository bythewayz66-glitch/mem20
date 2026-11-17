# Operations — `docs/ops/`

Entry point for the `docs/ops/` documentation set. **36 tracked file(s).**

## Contents

- [`270-27-APPLY.md`](270-27-APPLY.md)
- [`270-27.patch`](270-27.patch)
- [`GITHUB_ACCESS.md`](GITHUB_ACCESS.md)
- [`agent-contribution-plan-2026-11-07.md`](agent-contribution-plan-2026-11-07.md)
- [`agent-worklog.md`](agent-worklog.md)
- [`analytics-reporter-reverify-2026-11-01.md`](analytics-reporter-reverify-2026-11-01.md)
- [`apply-270-27.py`](apply-270-27.py)
- [`branch-audit.md`](branch-audit.md)
- [`branch-disposition-2026-10-31.md`](branch-disposition-2026-10-31.md)
- [`branch-inventory-2026-10-31.md`](branch-inventory-2026-10-31.md)
- [`contrib-evidence-gate.md`](contrib-evidence-gate.md)
- [`contribution-ledger-2026-11-07.md`](contribution-ledger-2026-11-07.md)
- [`corrections-2026-10-26.md`](corrections-2026-10-26.md)
- [`launch-page-270-urls.md`](launch-page-270-urls.md)
- [`mem20-api-service-2026-11-01.md`](mem20-api-service-2026-11-01.md)
- [`merge-order-2026-10-27.md`](merge-order-2026-10-27.md)
- [`metrics.json`](metrics.json)
- [`owner-directive-2026-11-01.md`](owner-directive-2026-11-01.md)
- [`pages-redirect-2026-10-31.md`](pages-redirect-2026-10-31.md)
- [`program-scoreboard-2026-11-01.md`](program-scoreboard-2026-11-01.md)
- [`program-status-2026-11-16.md`](program-status-2026-11-16.md)
- [`retired-infra-allowlist-2026-11-01.md`](retired-infra-allowlist-2026-11-01.md)
- [`roster-score-2026-11-01.md`](roster-score-2026-11-01.md)
- [`roster-verification-2026-10-27.md`](roster-verification-2026-10-27.md)
- [`surface-measurement-2026-10-31.md`](surface-measurement-2026-10-31.md)
- [`tag-audit-2026-10-31.md`](tag-audit-2026-10-31.md)
- [`tests-failure-repro-2026-11-01.md`](tests-failure-repro-2026-11-01.md)
- [`token-mandate-2026-11-01.md`](token-mandate-2026-11-01.md)
- [`tool-count-270-27.md`](tool-count-270-27.md)
- [`verification-2026-10-27.md`](verification-2026-10-27.md)
- [`verification-logs/collect_mcp.log`](verification-logs/collect_mcp.log)
- [`verification-logs/hygiene-gate.out`](verification-logs/hygiene-gate.out)
- [`verification-logs/verify_mcp.out`](verification-logs/verify_mcp.out)
- [`workload-roster-2026-10-27.md`](workload-roster-2026-10-27.md)
- [`ws2-dashboard-README.md`](ws2-dashboard-README.md)
- [`ws2-dashboard.patch`](ws2-dashboard.patch)

## Conventions

- Every file in this directory is linked from this index; add a row when you add a file.
- Dated records (audits, ops logs, verification runs) are append-only — do not rewrite
  historical numbers in them; correct the live docs instead.
- Tool/domain counts in this tree must match the live surface. Derive, never hand-count:
  `python3 web/scripts/extract-tools.py --root . --out /tmp/tools.json`
