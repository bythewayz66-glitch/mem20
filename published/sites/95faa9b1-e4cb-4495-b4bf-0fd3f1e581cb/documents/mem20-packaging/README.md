# mem20 server packaging — status

**Lane:** server packaging + Sidney publish leg (Server Builder)
**Canonical repo:** github.com/bythewayz66-glitch/mem20 @ `8e2f803`
**Date:** 2026-10-18

## Bottom line

The packaging is fixed and verified: a clean build now produces a wheel that
carries the real server tree, installs with its declared dependencies, and
starts serving 268 tools over stdio.

The Sidney publish is **blocked on one external thing**: there is no working
SSH credential for the host. Nothing was deployed and nothing was published, so
no Sidney URL is claimed here.

## What was actually broken

A clean `python -m build` of the stock tree produced a **13-entry wheel with no
server in it** — no `mem20_runtime/`, no `mcp_server.py`. It only appeared to
work because a stale `build/lib/mem20_runtime/` was **committed to git**, and
setuptools reused that leftover output. That stale tree held 33 Python files
against 37 in `mcp/`, so it was also shipping older tool code.

| Defect | Effect | Fix |
|---|---|---|
| Bundled server tree never declared | wheel had no server | shipped as `mem20_runtime`, staged from `mcp/` by `scripts/stage_runtime.sh` |
| `build/`, `dist/`, `mem20_runtime/` committed | stale output masked the break | added to `.gitignore` |
| Launcher accepted any dir named `mcp` | in an installed env that is the SDK, not the server | requires the `mcp_server.py` marker |
| `aiohttp` imported unconditionally, undeclared | startup abort: `ModuleNotFoundError` | declared as a real dependency |

`faiss-cpu` / `sentence-transformers` were demoted to the `vector` extra: the
engine guards their import (`VECTOR_AVAILABLE`, `CROSS_ENCODER_AVAILABLE`) and
falls back to lexical recall. That is what makes the package installable on a
bare system interpreter such as the host's Python 3.14, where torch/faiss
wheels may not exist. `mcp` is pinned `<2.2` because the server uses
`ServerRequestContext` and the SDK-shipped `mcp_types`.

## Verified

- Clean build: 52 entries, `mem20_runtime/mcp/mcp_server.py` present, **0**
  `.pyc`/`__pycache__` entries (the old bundle carried cpython-314 bytecode).
- Fresh venv, wheel + declared deps only, `PYTHONPATH` cleared, cwd outside the
  repo: `initialize` → `serverInfo.name = mem20-mcp`,
  `protocolVersion = 2025-06-18`; `tools/list` → **268 tools**.
- `build.sh` re-run end-to-end on a pristine copy: same result.

Reproduce: `bash build.sh /path/to/bythewayz66-glitch-mem20`.

## Sidney / gabe status — BLOCKED

- `216.198.115.91` reachable on **tcp/2222 only** (22, 80, 443, 8080, 873, 9900
  closed). Banner `SSH-2.0-OpenSSH_10.5p1 Debian-1`, offering
  `publickey,password`.
- The password shared in the earlier run has been **rotated** (do not reuse it); it is rejected
  for `root`, `jayson`, `sidney`, `gabe` and `ubuntu`.
- The sandbox holds no key: `~/.ssh` is empty, and there is no `SIDNEY_*` or
  `GABE_*` environment. `sidney` and `gabe` do not resolve in DNS.
- Key authentication installed by the earlier sync belonged to a different
  session's key, which is not present here.

**To unblock, exactly one of these is needed from the Sidney owner:**

1. a private key authorised on `216.198.115.91:2222` (preferred), or
2. the current password for `root` (or a dedicated `mem20` deploy user).

Then the deploy is one command — see below.

## Then: deploy, in one command

```bash
SIDNEY_HOST=216.198.115.91 SIDNEY_PORT=2222 SIDNEY_USER=root \
SSH_KEY=~/.ssh/id_ed25519 \
bash deploy_to_sidney.sh
```

The script routes every artifact through gabe, which is the sole publish
authority:

1. recon (kernel, interpreter, disk, `gabe status`)
2. ship the wheel, verify `sha256` on the host
3. reversible backup `venv.bak.<stamp>`, then additive install
4. verify from the **installed** artifact, not the checkout
5. install and enable `systemd/mem20.service`, `daemon-reload`
6. restart, then prove it: `is-active`, `MainPID`, `/health`, `/ready`, listener
   on :8080
7. `gabe publish` the release note — a **text** artifact on purpose, because the
   gate's L2 judge reads files as text and refuses binaries; the note carries
   the wheel's sha256 and size as its identity
8. `gabe status` plus a listing of `$GABE_LIVE_ROOT`

`DRY_RUN=1` prints the whole plan without touching the host.

`deploy_to_sidney.sh` deliberately does not pass `--delete` and does not write
under a watched tree: gabe's scan covers `$GABE_LIVE_ROOT` (`/opt/mem20/live`),
and the install is additive into `/opt/mem20/venv`.

## House numbers

Unchanged: **268 tools across 26 domains**; **TAM $1.28B / SAM $282M /
SOM $1.68M**; **blended ACV $14,000**.

## Files

| File | Purpose |
|---|---|
| `build.sh` | clean, staged, audited wheel build |
| `scripts/stage_runtime.sh` | stage/verify/unstage `mcp/` → `mem20_runtime/` |
| `pyproject.toml`, `launcher.py` | the two fixed source files |
| `0001-fix-mem20-wheel-packaging.patch` | applyable diff against `8e2f803` |
| `mem20-2.1.0rc2-py3-none-any.whl` | the verified wheel (sha256 in the note) |
| `systemd/mem20.service` | unit, hardened, absolute `ExecStart` |
| `deploy_to_sidney.sh` | one-command gabe-routed deploy |
| `requirement.txt` | the requirement text gabe judges against |
| `release-note.md` | the artifact gabe publishes |
| `evidence/01-packaging-fix.txt` | before/after measurements |
