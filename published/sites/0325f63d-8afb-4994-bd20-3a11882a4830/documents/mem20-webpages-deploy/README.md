# mem20 webpages — repo update + Sidney publish bundle

**Task:** Update the mem20 webpages (launch page, launch dashboard) to reference the new canonical
repo and correct every repo-dependent link, then publish to the **Sidney** server via
ssh/sftp/rsync **routed through gabe**.

**Canonical repo:** https://github.com/bythewayz66-glitch/mem20 · default branch `main`
**Old (dead) repo:** `github.com/JaysonAIOnline/mem20` → returns **404** (confirmed via GitHub API).

---

## 1. What changed (v2)

Both pages were re-versioned (`_v2`) from the live v1 files and every repo-dependent reference was
repointed from `JaysonAIOnline/mem20` → `bythewayz66-glitch/mem20`.

### Launch page — `webpages/mem20-launch/`
| Line | Element | v1 (old) | v2 (new) |
|------|---------|----------|----------|
| nav CTA | "GitHub" button | `github.com/JaysonAIOnline/mem20` | `github.com/bythewayz66-glitch/mem20` |
| hero CTA | "Get started on GitHub" | same old repo | new repo |
| hero | repo hint text | `github.com/JaysonAIOnline/mem20` | `github.com/bythewayz66-glitch/mem20` |
| install | `git clone …` snippet | `git clone https://github.com/JaysonAIOnline/mem20` | `git clone https://github.com/bythewayz66-glitch/mem20` |
| final CTA | button label + href | old repo | new repo |
| footer | "GitHub repository" | old repo | new repo |

7 occurrences replaced. `cd mem20` (directory name) intentionally unchanged.

### Launch dashboard — `webpages/mem20-launch-dashboard/`
| Line | Element | v1 (old) | v2 (new) |
|------|---------|----------|----------|
| card | source label | `api.github.com/repos/JaysonAIOnline/mem20` | `api.github.com/repos/bythewayz66-glitch/mem20` |
| table | "GitHub stars" endpoint row | old repo | new repo |
| footer | repo link | old repo | new repo |
| JS | `var REPO` (drives `api.github.com/repos/…`) | `"JaysonAIOnline/mem20"` | `"bythewayz66-glitch/mem20"` |
| JS | 404 message copy | "not publicly resolvable under this name yet" | "the canonical repo is public, so this indicates an API/name mismatch or GitHub unavailability" |
| section 08 | "To make stars & clones live" bullet | "If the repo is not yet public…" | "The canonical repo `bythewayz66-glitch/mem20` is public, so the star card resolves live…" |

5 occurrences replaced. **Verified live effect:** the dashboard's GitHub status dot now reports
**`live`** (it read "repo not resolvable (404)" in v1).

### Unchanged by design
Every `/sites/…` link to the launch page, copy pack and campaign plan, the `utm_campaign=mem20_launch_2026q4`
tracking contract, the 12-row UTM table, benchmark figures and the guardrail copy are all preserved.

---

## 2. Quality gate (passed)

- **Structure:** zero unclosed/anomalous tags on both pages; CSS braces 143/143 (launch) and 116/116 (dashboard).
- **JS:** `node --check` OK on both pages' inline scripts.
- **Guardrails:** adversarial hit rate `0.000` still visible (amber); no-LoCoMo caveat intact;
  "evidence-based" promotion wording intact; zero hits for banned phrases
  (`provably secure`, `tamper-proof memory`, `matches Mem0`, `beats Zep`, `industry-leading retrieval`).
- **Reachability:** both pages HTTP **200**, bytes match local files (40,749 / 52,053).
- **Visual:** rendered in real Chromium — no overlap, no cut-off text, all sections laid out;
  launch page shows `github.com/bythewayz66-glitch/mem20`, dashboard shows the new API endpoint.

---

## 3. Publish targets (permanent URLs already live)

| Page | Permanent URL |
|------|---------------|
| Launch page (v2) | https://static.teamily.ai/sites/0325f63d-8afb-4994-bd20-3a11882a4830/webpages/mem20-launch_v2/index.html |
| Launch dashboard (v2) | https://static.teamily.ai/sites/0325f63d-8afb-4994-bd20-3a11882a4830/webpages/mem20-launch-dashboard_v2/index.html |

> Note: the v2 pages are hosted under a **different project id** (`0325f63d…`) than the v1 pages
> (`f7c01331…`). When publishing to Sidney, place the v1-named paths below so existing links keep working.

---

## 4. Sidney publish leg — BLOCKED on credentials (this is the one open item)

**Status: not executed.** As in the earlier Server Builder pass, this sandbox has **no SSH
host/key/password/jump-host for `sidney` or `gabe`**:

```
$ ls ~/.ssh          → empty (no keys, no config)
$ getent hosts sidney / gabe → no DNS
$ env | grep -i 'sidney|gabe' → (nothing)
```

`ssh`, `sftp` and `rsync` are all installed — only the access details are missing.

### Payload (ready to ship)
```
payload/webpages/mem20-launch/index.html            40,749 B   ← v2 launch page, new repo
payload/webpages/mem20-launch-dashboard/index.html  52,053 B   ← v2 dashboard, new repo
```

### Run once the credentials exist
```bash
export SIDNEY_HOST=<host>   SIDNEY_PORT=22   SIDNEY_USER=<user>
export GABE_HOST=<host>     GABE_PORT=22     GABE_USER=<user>      # jump host (all traffic routed through gabe)
export SIDNEY_SSH_KEY=~/.ssh/id_ed25519                            # or use sshpass + SSHPASS
export REMOTE_WEBROOT=/var/www/mem20                               # web root on Sidney

bash deploy_webpages.sh            # rsync over ssh, proxied through gabe
```

`deploy_webpages.sh` builds `ssh -J <gabe_user>@<gabe_host>` and rsyncs the payload into
`$REMOTE_WEBROOT/webpages/…`, then prints the remote file listing for confirmation.
No secrets are stored in this bundle.

### Finish condition
The two HTML files present under `$REMOTE_WEBROOT/webpages/` on Sidney, each serving the new
`bythewayz66-glitch/mem20` reference, with `gabe` as the routing hop.
