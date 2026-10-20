# mem20 Sidney deploy — credential update run report

**Date:** 2026-10-18 (UTC)
**Target host:** `root@216.198.115.91:2222` (Sidney) — the ONLY host this credential was applied to
**Producer:** sidney-credential-update
**Artifact:** `mem20-2.1.0rc2-py3-none-any.whl`
**sha256:** `c433f9780595acce811a443d2c16036a3376176b81273d41811e614dd553c3fc` (189868 B)

---

## 1. Credential verification — PASS

The new root password authenticates on `216.198.115.91:2222`:

```
AUTH_OK
uid=0(root) gid=0(root) groups=0(root)
sidney
Linux 7.1.5+kali-amd64
Python 3.14.7
```

**Transport note:** this sshd only behaves with a PTY. Plain `ssh host cmd` and `scp`
hang after authentication (the session never returns output). All work was therefore
driven through a paramiko client with `get_pty=True` (exec + SFTP). The credential was
used on this host only.

## 2. Wheel shipped and verified — PASS

Transferred by SFTP to `/opt/mem20/staging/mem20-2.1.0rc2-py3-none-any.whl`; the remote
sha256 matches the published artifact byte-for-byte:

```
c433f9780595acce811a443d2c16036a3376176b81273d41811e614dd553c3fc  /opt/mem20/staging/mem20-2.1.0rc2-py3-none-any.whl
```

## 3. Reversible backup + additive install — PASS

- Backup retained: `/opt/mem20/venv.bak.20261018-144547` (plus earlier peer backups).
- venv created with `--system-site-packages` (Sidney has **no outbound internet**, so
  dependencies cannot be fetched; all of mem20's runtime deps — mcp, pydantic, anyio,
  aiohttp, httpx, starlette, uvicorn, sse_starlette — are already present system-wide).
- Wheel installed with `--no-deps` from the staged artifact:

```
Name: mem20
Version: 2.1.0rc2
/opt/mem20/venv/lib/python3.14/site-packages/mem20_runtime
```

## 4. Service proof — PASS

`mem20.service` is active and serving from the venv:

```
is-active: active
MainPID:   50904
NRestarts: 0
LISTEN 0.0.0.0:8082  users:(("mem20-mcp",pid=50904,fd=7))
LISTEN 0.0.0.0:8080  users:(("mem20-mcp",pid=50904,fd=3))
/health -> {"status": "ok", "service": "mem20-mcp", "uptime_seconds": 207.214}
/ready  -> {"ready": true, "tools": 257}
```

The unit runs the long-lived HTTP transport (`MEM20_TRANSPORT=http`, MCP on :8082) with
the health/ready endpoint on :8080. The earlier ad-hoc `python3 .../mcp_server.py`
process that had been squatting on :8080 is gone; the port is now owned by the systemd
service.

## 5. gabe publish — REFUSED (blocker)

`gabe publish` on the release note was executed and **refused**:

```
REFUSED 994177f57f35: see owner decision log
  recorded as manifest seq 368
```

Reason (manifest + audit log):

```
REFUSED [G11] producer=sidney-credential-update artifact=/opt/mem20/live/release-note.md
  :: L2 adversarial judge unavailable - failing closed:
     URLError: <urlopen error [Errno 111] Connection refused>
```

`gabe status`:

```json
{
  "halted": false,
  "chain": "chain ok (374 entries)",
  "chain_ok": true,
  "published_artifacts": 48,
  "rule_bundle_sha256": "4192add05f09722f",
  "live_root": "/opt/mem20/live"
}
```

### Root cause

gabe's L2 layer is a **real adversarial LLM call** (spec §4) with **no deterministic
substitute** — if the call cannot be made it fails closed under clause G11 and nothing
publishes. The judge calls NVIDIA NIM at `https://integrate.api.nvidia.com/v1`
(model `openai/gpt-oss-20b`), credential read from the root-only `/etc/gabe/llm.env`.

From Sidney that endpoint is unreachable:

```
curl -m 35 https://integrate.api.nvidia.com/v1/models
  -> curl: (28) Operation timed out after 35001 ms with 0 bytes received
```

DNS resolves and TCP/443 connects, but the TLS/HTTP exchange never completes — Sidney
has no usable egress to the LLM endpoint. No local LLM endpoint exists on the host
(nothing on :11434/:8000/:1234/:5000). This is the same class of failure recorded in
earlier manifest entries (seq 360–365, 372).

## 6. Remaining blockers

1. **gabe L2 judge cannot reach its LLM.** Publishing is blocked until Sidney can reach
   an OpenAI-compatible `/chat/completions` endpoint. Options:
   - restore outbound egress from Sidney to `integrate.api.nvidia.com`, **or**
   - point gabe at a reachable endpoint via `GABE_LLM_BASE_URL` + `GABE_LLM_API_KEY`
     (a deliberate operator override the client honours), **or**
   - run a local OpenAI-compatible model on Sidney and set `GABE_LLM_BASE_URL` to it.
2. **No SSH key on Sidney.** Deploy currently depends on the shared root password; a
   dedicated key would remove that dependency.

## 7. House numbers (unchanged)

257 tools across 26 domains; TAM 1.28B USD, SAM 282M USD, SOM 1.68M USD; blended ACV
14,000 USD.
