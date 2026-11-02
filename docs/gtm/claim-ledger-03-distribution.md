# §3 — Distribution state

Part 3 of 7. Index: `claim-ledger.md`. Measured at `2ea44922`.

| # | Question | Measured result | Status | Command (settles it) | Adversarial |
|---|---|---|---|---|---|
| **D1** | PyPI package? | **No.** `mem20`, `mem20-ai`, `mem20oreo`, `mem20-mcp`, `mem20-sdk` → **all 404** | **VERIFIED** | `for p in mem20 mem20-ai mem20oreo mem20-mcp mem20-sdk; do curl -s -o /dev/null -w "$p %{http_code}\n" https://pypi.org/pypi/$p/json; done` | `n/a: packaging` |
| **D2** | Documented install path | `git clone https://github.com/bythewayz66-glitch/mem20.git` → `pip install -r requirements.txt`. Pins **eight**: `mcp>=2.1.1`, `mcp-types>=2.3.0`, `aiohttp>=3.14.5`, `pydantic>=2.13.4`, `anyio>=4.14.2`, `numpy>=1.24`, `faiss-cpu>=1.7.4`, `sentence-transformers>=2.2.0` | **VERIFIED** | `cat requirements.txt` | `n/a: install path` |
| **D2b** | Is that path complete? | **Yes** — a clean install boots the server: `TOOL_COUNT: 270`, `RESULT: PASS` | **VERIFIED** | `pip install -r requirements.txt && python3 verify_mcp.py` | `n/a: install path` |
| **D4** | Canonical public URL | **`mem20.com`** → 200, **33,429 bytes**. The GitHub Pages host → 200, same size. Both **byte-identical to the committed `docs/index.html`** (digest recorded in §3.1). | **VERIFIED** | `md5sum /tmp/a.html docs/index.html` after fetching the host | `n/a: hosting` |
| **D5** | CNAME host resolves? | **Yes.** `docs/CNAME` = exactly **`mem20.com`**; `getent hosts mem20.com` → four GitHub Pages A-records (`185.199.108–111.153`) | **VERIFIED** | `cat docs/CNAME; getent hosts mem20.com` | `n/a: DNS` |
