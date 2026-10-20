# Sidney Deployment Runbook — mem20 @ c274404

Target host: `sidney` = `root@216.198.115.91:2222` (per GABE_SPEC.md line 5)
Source: `https://github.com/bythewayz66-glitch/mem20` @ `main` / `c274404a116f203b0ed99ab7156e3752f0953ea8`
Method: rsync over SSH, **routed through gabe** (GABE_SPEC.md §8)

## Blocking constraint: everything goes through gabe

GABE_SPEC.md is explicit:

> §8 — "No code reaches sidney except through Gabe. **No manual scp, no exceptions.**"

Therefore the command shape requested in the task:

```
rsync -avz --delete <clone>/ gabe@sidney:<deploy_path>/
```

must **not** be run as a raw file push. Doing so would violate **G1** (single authorized
publish path), **G10** (no second writer to the live surface) and **G11** (authority does
not transfer). A direct rsync of ~9,859 files into the live tree is, by the spec's own
definition, the bypass lane the gate exists to close.

The correct route is: stage the payload, then let **gabe** own the commit into the live
surface. `--delete` is also dangerous here — the spec records an `optwatch.service` that
watches `/opt` and `/srv` for deletions, and any deletion under a watched tree trips the
watcher. Use `--delete` only inside a staging dir, never against the live tree.

## Prerequisites (owner action)

The sandbox has **no working credential** for the target. Provide ONE of:

- password for `root@216.198.115.91` (port 2222) — export `SSHPASS`, or
- an SSH private key with access — place at `~/.ssh/id_ed25519` (chmod 600), or
- the gabe-side ingress endpoint (S/FTP, rsync daemon, or web hook) that the gate exposes.

Bounded facts already established:

| Check | Result |
|---|---|
| DNS `sidney` | no record (host is only reachable by IP) |
| TCP `216.198.115.91:2222` | **open** |
| SSH `gabe@216.198.115.91:2222` | `Permission denied (publickey,password)` |
| SSH `root@216.198.115.91:2222` | `Permission denied, please try again.` (password auth is enabled, credential rejected) |
| keys / `~/.ssh/config` / `SSHPASS` in sandbox | none |

## Step 1 — stage the payload

```bash
# payload already built and hashed
tar czf mem20-c274404.tar.gz --exclude=.git -C <clone> .
sha256sum mem20-c274404.tar.gz
# ac645714ee2120a93d4669044e519c6889aee231b9e79876a857a4f315226680
```

## Step 2 — put the payload where gabe can pick it up, then hand off

```bash
# stage only. NOT the live tree.
timeout 600 rsync -avz --partial \
  -e "ssh -p 2222 -o StrictHostKeyChecking=accept-new" \
  mem20-c274404.tar.gz root@216.198.115.91:/tmp/gabe-ingress/
```

Then have **gabe** validate and commit it into the live surface (§8, G6, G14):

```bash
ssh -p 2222 root@216.198.115.91
sha256sum /tmp/gabe-ingress/mem20-c274404.tar.gz   # must equal the value above
/opt/mem20/gabe/bin/gabe publish --producer mem20 --artifact /tmp/gabe-ingress/mem20-c274404.tar.gz
/opt/mem20/gabe/bin/gabe status                    # expect: halted=false, chain ok
```

Gate responses to expect (armed v8 state):

- `halts=false`, chain integrity ok, refusals exit **1**, halts exit **2**
- a refusal is double-logged (durable hash-chained manifest entry + human-readable audit line)

## Step 3 — build / install on the host

Recon first, then install. Host profile from prior recon: Kali GNU/Linux Rolling 2026.3,
kernel 7.1.5+kali-amd64, `/usr/bin/python3.14` (3.14.7), cryptography 49.0.0, systemd 262,
~822 G free on `/`.

```bash
cd /opt/mem20
tar xzf /tmp/gabe-ingress/mem20-c274404.tar.gz -C /opt/mem20/mem20
cd /opt/mem20/mem20

# repo-provided installer: venv + requirements.txt + systemd unit, then enable/start
sudo ./install.sh --dir /opt/mem20/mem20 --venv /opt/mem20/mem20/.venv
```

Repo build entry points (inspected in the clone):

- `install.sh` — generates a venv, installs `requirements.txt`, renders
  `systemd/mem20.service.template`, enables + starts the unit (`--no-systemd` to skip)
- `Makefile` targets: `sync venv install dev docker deb npm dashboard test clean`
- `docker-compose.yml` — services `mem20` and `mem20-store`
- `pyproject.toml` + `requirements.txt` + `requirements-optional.txt` (Blender/Unity optional)

## Step 4 — verify with real output

```bash
systemctl status mem20 --no-pager
journalctl -u mem20 -n 80 --no-pager
python3 -c "import mem20_runtime, sys; print(mem20_runtime.__file__)"
curl -sS --max-time 10 http://127.0.0.1:8642/health || true    # gateway default port 8642
/opt/mem20/gabe/bin/gabe status
```

Snapshot the deployed tree immediately after extraction and keep the checksums — a
concurrent writer can swap files between deploy and verify:

```bash
find /opt/mem20/mem20 -name '*.py' -not -path '*/.venv/*' -exec md5sum {} + > /opt/mem20/mem20.deployed.md5
md5sum -c /opt/mem20/mem20.deployed.md5 | grep -v OK | head
```

## Rollback

```bash
cp -a /opt/mem20/mem20 /opt/mem20/mem20.bak.$(date +%Y%m%d-%H%M%S)   # take BEFORE overwriting
# restore:
# rsync -a --delete /opt/mem20/mem20.bak.<stamp>/ /opt/mem20/mem20/
```

Never delete under `/opt` or `/srv` while `optwatch.service` is active.
