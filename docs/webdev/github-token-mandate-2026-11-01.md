# GitHub Token Mandate — 2026-11-01

Owner directive received 2026-11-01 (America/Denver). Fine-grained PAT issued for
`github.com/bythewayz66-glitch/mem20`. Token value is **never** recorded in this repo.

## Verification performed this run

| Check | Command | Result |
|---|---|---|
| Identity | `GET /user` with `Authorization: Bearer $GITHUB_TOKEN` | `login: bythewayz66-glitch`, `id: 330751727` |
| Repo permissions | `GET /repos/bythewayz66-glitch/mem20` | `admin/maintain/push/triage/pull` all `true` |
| main HEAD | `GET /repos/.../commits/main` | `d99ab5d8e9c5c45a1fb3d02d3b65b2f9a96b5110` |
| Clone over token URL | `git clone https://x-access-token:$GITHUB_TOKEN@github.com/...` | success, HEAD matched |
| Push | `git push https://x-access-token:$GITHUB_TOKEN@github.com/... HEAD:refs/heads/<branch>` | success (see commit below) |

## Allowed credential forms (only these three)

1. One-off remote URL:
   `git push https://x-access-token:$GITHUB_TOKEN@github.com/bythewayz66-glitch/mem20.git HEAD:refs/heads/<branch>`
2. Environment: `export GITHUB_TOKEN=…` / `export GH_TOKEN=…`
3. API: `Authorization: Bearer $GITHUB_TOKEN`

## Prohibited

- Token in tracked files, workflow YAML, committed `.git/config`, commit messages,
  branch or tag names, or PR text.
- Leaving the token in `origin` after a push — reset to the credential-free URL:
  `git remote set-url origin https://github.com/bythewayz66-glitch/mem20.git`

## Rotation

The token has been present in group message history in plaintext since 2026-10-31.
If that transcript is exported, shared, or a member is added, rotate immediately:
GitHub → Settings → Developer settings → Personal access tokens.

## Pages state at time of writing

- `status: built`, `build_type: legacy`, source `main:/docs`
- `cname: mem20.com`, cert approved for `mem20.com` + `www.mem20.com`, expires 2027-01-25
- `https_enforced: false` (unchanged — open decision from `domain-routing-2026-11-01.md`)
