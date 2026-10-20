# mem20 launch page — Sidney/gabe publish bundle

Canonical repo: `https://github.com/bythewayz66-glitch/mem20` (main, MIT, Python).
Source page (fixed, verified): `webpages/mem20-launch_v3/index.html`
CDN: `https://static.teamily.ai/sites/fb74dacb-26d1-429a-98ff-2765e0e7b61a/webpages/mem20-launch_v3/index.html`

## What changed in v3 (vs v2)

| # | Item | Was | Now |
|---|------|-----|-----|
| 1 | Install snippet | `git clone .../mem20` (no `.git`) · `pip install -e .` · `python -m mem20 --stdio` | `git clone .../mem20.git` · `python3 -m venv .venv` · `.venv/bin/pip install -r requirements.txt` · run `MEM20_STORE_PATH=~/.mem20/store .venv/bin/python mcp/mcp_server.py` |

The old `pip install -e .` / `python -m mem20 --stdio` did **not** match the canonical
repo's authoritative source install (README.md L186–L194 and CANONICAL.md). The new
block matches it exactly. No other content changed.

## Verification (already run, all PASS)

- HTML tags balanced (all paired); CSS braces 143/143; embedded JS `node --check` OK.
- 7 canonical `bythewayz66-glitch/mem20` references; **0** stale `JaysonAIOnline` references.
- `git clone .../mem20.git` ×1, `python3 -m venv .venv` ×1, `mcp/mcp_server.py` ×1.
- Old `pip install -e .` = 0; old `python -m mem20 --stdio` = 0.
- House numbers intact: `257 tools across 26 domains` ×3, `v2.1.0rc2` ×6.
- CDN reachability: HTTP 200, 40,821 B.

## Publish to Sidney via gabe (BLOCKED on credentials)

Route per CANONICAL.md: Sidney via ssh/sftp/rsync, **routed through gabe**
(gabe is a local runtime on the Sidney server, not an agent).

Current state of the leg (verified live):
- Sidney SSH endpoint reachable: `216.198.115.91:2222` — banner `SSH-2.0-OpenSSH_10.5p1 Debian-1`.
- Auth: `Permission denied (publickey,password)` for every attempt. Sandbox has no SSH
  key, no ssh-agent, no sshpass, no `SIDNEY_*`/`GABE_*`/`SSHPASS` env vars; DNS for
  `sidney`/`gabe` is NXDOMAIN.

To unblock, supply ONE of:
1. An SSH private key for `216.198.115.91:2222` (preferred), or
2. a valid password via `SSHPASS`, or
3. gabe-side ingress details (host/port/user + credential).

Then run `deploy_launch.sh` (this directory) — it copies `index.html` to Sidney and
invokes gabe there to place it in the live root.
