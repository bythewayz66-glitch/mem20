---
issue: 392
agent: ChatGPT documentation steward (owner-authorized)
status: in-progress
branch: chatgpt/392-documentation-drift-remediation-r1
opened: 2026-11-07
updated: 2026-11-07
files:
  - docs/documentation-drift-audit-2026-11-07.md
  - docs/INDEX.md
  - mem20-sdk-ruby/docs/INSTALL.md
  - mem20-sdk-ruby/docs/USAGE.md
  - docs/sdk/cpp/protocol.md
  - sdk/perl/AUDIT.md
depends_on: []
---

## Intent
Audit current-facing documentation against the current MEM20 implementation and repair safe non-README drift without rewriting historical evidence or interfering with the active subsystem README run.

## State
- Confirmed current baseline: VERSION 3.1.2; live surface manifest and verifier expect 311 tools / 39 domains.
- Confirmed docs/README.md, docs/02-tools-reference.md, docs/05-complete-tools-reference.md, docs/surface.json, and docs/INDEX.md already report 311 / 39.
- Found current-facing docs that still present older tool surfaces, plus dated artifacts that must remain historical.
- Owner-authorized README drift window is active; README files are explicitly deferred.

## Next step
1. Publish the path-level audit and link it from docs/INDEX.md.
2. Correct the Ruby SDK install/usage docs to distinguish dynamic live tools/list discovery from the SDK's pinned 272/27 constants.
3. Expand the audit into controlled batches after checking active claims and agent branches.

## Verification
- Compare all live tool-count claims to VERSION, verify_mcp.py, and docs/surface.json.
- Inspect SDK client discovery code and its Surface constants before editing.
- Re-fetch every edited file and verify the resulting commit and diff.

## Blockers
- Do not update subsystem README.md files until the owner's active README-drift run is complete.
- MEM20 project-memory context was unavailable in this session; use repository governance docs and request owner confirmation where branch/agent identity is ambiguous.
