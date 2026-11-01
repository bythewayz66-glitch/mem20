# §3 — Distribution state

Part 3 of 7. Index: `claim-ledger.md`. Measured at `2ea44922`.

| # | Question | Measured result | Status | Command (settles it) | Adversarial |
|---|---|---|---|---|---|
| **D1** | PyPI package? | **No.** `mem20`, `mem20-ai`, `mem20oreo`, `mem20-mcp`, `mem20-sdk` → **all 404** | **VERIFIED** | `for p in mem20 mem20-ai mem20oreo mem20-mcp mem20-sdk; do curl -s -o /dev/null -w "$p %{http_code}\n" https://pypi.org/pypi/$p/json; done` | `n/a: packaging` |
