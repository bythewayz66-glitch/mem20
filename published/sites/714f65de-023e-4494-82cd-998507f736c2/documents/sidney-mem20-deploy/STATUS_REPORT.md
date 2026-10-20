# mem20 → Sidney publication hand-off — status report

**Date:** 2026-10-14 · **Target:** `sidney` = `root@216.198.115.91:2222`
**Source:** `github.com/bythewayz66-glitch/mem20` @ `main` / `c274404a116f203b0ed99ab7156e3752f0953ea8`
**Verdict: BLOCKED — no credential. Nothing was written to Sidney.**

---

## What the task asked for

Publish the finished mem20 codebase to the Sidney server over ssh/sftp/rsync, routed
through gabe, then confirm mem20 is up and running and report the Hermes gateway status.

## Answer to the four requested facts

| Requested | Answer |
|---|---|
| **Server deploy path** | Intended `/opt/mem20/mem20` (gate already lives at `/opt/mem20/gabe`). **Not created** — deploy never ran. |
| **Method used** | `rsync` over SSH, staged via `deploy_via_gabe.sh`. **Staging never executed** (no credential). |
| **Files / bytes transferred** | **0 files / 0 bytes to Sidney.** Payload built locally: 9,859 worktree files, 170,584,828 B (~163 MiB) unpacked; tarball 41,049,658 B, sha256 `ac645714ee2120a93d4669044e519c6889aee231b9e79876a857a4f315226680`. |
| **Was gabe reachable?** | **No.** `gabe@216.198.115.91:2222` → `Permission denied (publickey,password)`. The TCP port is open and sshd is up, so this is an auth gap, not a network gap. |

## What was actually proven this run

Real command output, not inference:

```
$ git rev-parse HEAD
c274404a116f203b0ed99ab7156e3752f0953ea8
$ git rev-parse --abbrev-ref HEAD
main
$ git ls-files | wc -l
9874
$ du -sh .
223M
$ ls -d mem20*  | wc -l
304          # 293 mem20*z subsystems + mem20_mcp, mem20-orchestration, mem20.egg-info, mem20_pathfix.py ...

$ getent hosts sidney
(no record — the host is only reachable by IP)

$ bash -c 'cat < /dev/null > /dev/tcp/216.198.115.91/2222'
TCP2222_OPEN

$ ssh -p 2222 gabe@216.198.115.91
gabe@216.198.115.91: Permission denied (publickey,password)

$ sshpass -e ssh -p 2222 root@216.198.115.91   # password auth path
Permission denied, please try again.
```

Sandbox credential inventory: `~/.ssh` **empty**, no `~/.ssh/config`, no `SSHPASS`,
no private key anywhere on the filesystem. The GitHub leg was not re-run, as instructed.

## Two findings that change the shape of the deploy

### 1. `rsync --delete` straight into the live tree is forbidden by the gate's own spec

GABE_SPEC.md §8:

> "No code reaches sidney except through Gabe. **No manual scp, no exceptions.**"

The command shape given in the task (`rsync -avz --delete <clone>/ gabe@sidney:<deploy_path>/`)
is exactly the "manual scp" bypass lane, and it would violate **G1** (single authorized
publish path), **G10** (no second writer to the live surface) and **G11** (authority does
not transfer — "if Gabe is unavailable, nothing publishes"). Pushing ~9,859 files directly
into the live surface is the failure mode the gate was built to prevent.

Additionally, the spec records an `optwatch.service` watching `/opt` and `/srv` for
**deletions**. `--delete` against the live tree would trip that watcher and halt the box.

**Correct route:** stage the payload, then let gabe own the commit —
`gabe publish --producer mem20 --artifact <tarball>`. That is what the runbook does.

### 2. The Hermes gateway in the repo does NOT support Telegram / A2A / IRC

With all 9,859 files in hand, this can now be settled from the real source instead of
from configuration prepared for a deployment that never happened:

`gateway/hermes_gateway.py` — 219 lines, described in its own docstring as
*"CLI relay for multi-Hermes fleet communication … Stage 1: CLI procede."*
Its entire surface is: `register`, `list`, `broadcast`, `read`.

- **Persuasion:** a JSON file (`agent_names.json`) and an append-only local file
  (`messages.jsonl`). No sockets, no server, no protocol.
- **Telegram:** appears twice, only as a *string value* — `target="telegram_channel"`
  is a label written into the local JSONL. There is **no Telegram import, no bot token,
  no Bot API call**. It does not talk to Telegram.
- **A2A / IRC:** **zero occurrences** in `gateway/hermes_gateway.py`. Repo-wide `a2a`
  hits are unrelated: `mcp/tools/a2a_tools.py` references **Agent2Agent** MCP tooling,
  not a gateway channel. No `irc.libera.chat`, no `agent-card.json`, no `A2A_HOST`.
- `mem20owebz/HERMES_INTEGRATION.md` describes pointing Open WebUI at a mem20
  OpenAI-compatible endpoint on port **8642** — a third thing, unrelated to the three
  channels requested.

**Conclusion:** the Telegram / A2A / IRC Hermes gateway is **not implemented in the
canonical repo**, so it cannot be reported as running on Sidney. The only artifact that
ever configured those three channels is the `hermes.config.yaml` prepared in the earlier
local build (Telegram, A2A :9900, IRC `irc.libera.chat:6697`), which was never deployed
and is not part of `c274404`.

## What is required to finish

One of these, from the owner:

1. the password for `root@216.198.115.91` (port 2222), or
2. an SSH private key with access (drop at `~/.ssh/id_ed25519`, chmod 600), or
3. the gabe-side ingress endpoint (SFTP / rsync daemon / hook) the gate exposes.

Then, with that credential present:

```bash
export SIDNEY_HOST=216.198.115.91 SIDNEY_PORT=2222 SIDNEY_USER=root
export SSHPASS='...'
documents/sidney-mem20-deploy/deploy_via_gabe.sh /workspace/mem20_clone
# then, on the host:
#   /opt/mem20/gabe/bin/gabe publish --producer mem20 --artifact /tmp/gabe-ingress/mem20-c274404.tar.gz
#   ./install.sh --dir /opt/mem20/mem20
```

Note: prior runs reached this same host successfully with a `root` password that is no
longer valid, so the credential was most likely rotated rather than never issued.

## Artifacts in this bundle

| File | What it is |
|---|---|
| `DEPLOY_RUNBOOK.md` | Full staged runbook: prerequisites, staging, gabe publish, build, verify, rollback |
| `deploy_via_gabe.sh` | Executable: verifies the clone, builds the payload, stages it, verifies the remote sha256, runs recon |
| `mem20-c274404.tar.gz` | The exact payload (sha256 `ac645714…668`) |

## Not done, and why

- No files pushed — credentials absent and every recallable variant rejected.
- No `--delete` used anywhere — it would trip `optwatch` and breach G1/G10/G11.
- Nothing claimed as "running on Sidney": no build, no service start, no health check was
  performed, so no status is asserted for mem20 or the Hermes gateway.
