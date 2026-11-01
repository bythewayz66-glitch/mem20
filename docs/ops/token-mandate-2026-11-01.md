# Owner directive — 2026-11-01: GitHub token mandate for all repo writes

**Issued by:** bythewayz66 (owner) · **Executed and verified by:** Mem20-admin
**Repo of record:** `bythewayz66-glitch/mem20` (public). `JaysonAIOnline/mem20` returns **404** — not the live repo.
**Second repo in scope:** `bythewayz66-glitch/teamz`.
**Verification window:** 2026-11-01, 18:50Z–19:05Z.

> **Standing rule (owner, restated):** every push and every API write to `mem20` and `teamz` uses the
> owner-supplied fine-grained personal access token. The sandbox has no git CLI credentials of its own.
> A deliverable exists only as a **commit SHA on a pushed branch** or a **permanent URL committed under
> `docs/`**. Chat-only claims do not count.

---

## 1. The three sanctioned mechanics

The token is supplied **only** through one of these three channels. Nothing else is acceptable.

| # | Mechanic | Form | Use for |
|---|---|---|---|
| 1 | Remote URL | `git remote add origin https://x-access-token:$GITHUB_TOKEN@github.com/OWNER/REPO.git` | `git clone`, `git push`, `git fetch` |
| 2 | Environment | `export GITHUB_TOKEN=…` or `export GH_TOKEN=…` | any tool that reads the standard env var |
| 3 | Bearer header | `curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/…` | REST API reads and writes, MCP calls |

**Redaction rule for every report:** show the token as its first 12 characters followed by an ellipsis.
Never paste the full value into a chat message, a commit message, a PR body, or a document.

---

## 2. Prohibitions (hard)

The token must **never** be written into:

1. **Any tracked file** — source, docs, fixtures, test data, notebooks, or this document.
2. **Workflow YAML** — `.github/workflows/**` is owner-review-only and must reference
   `${{ secrets.GITHUB_TOKEN }}` or a repository secret, never a literal.
3. **A committed `.git/config`** — the remote URL form is for the working copy only. Before any
   commit or archive, reset the remote to the credential-free URL:
   `git remote set-url origin https://github.com/OWNER/REPO.git`.
4. **Commit messages, branch names, tag names, or PR titles/bodies.**

A token that reaches any of the four is treated as compromised and must be rotated by the owner.

---

## 3. Write-access verification performed this run

| Check | Command form (redacted) | Result |
|---|---|---|
| Token identity | `curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user` | `bythewayz66-glitch`, id `330751727`, type `User` |
| `mem20` permissions | `GET /repos/bythewayz66-glitch/mem20` | `admin: true, maintain: true, push: true, triage: true, pull: true` |
| `teamz` permissions | `GET /repos/bythewayz66-glitch/teamz` | `admin: true, maintain: true, push: true, triage: true, pull: true` |
| Real push event | `git push origin HEAD:refs/heads/tmp/token-verify-mem20admin` | `* [new branch] HEAD -> tmp/token-verify-mem20admin` |
| Push confirmed via API | `GET /repos/…/branches/tmp/token-verify-mem20admin` | `8becac15b2b98c59770025e4071ff1754b0b2354` |
| Throwaway ref removed | `DELETE /repos/…/git/refs/heads/tmp/token-verify-mem20admin` | `204`, then `404` on re-read |

**Conclusion: the token has verified write access to both repositories.** The proof is a real
`[new branch]` push line plus an API read of the same 40-character SHA — not a permission field alone.

---

## 4. Leak scan of the tracked tree

| Scan | Scope | Result |
|---|---|---|
| Token prefix grep | full tracked tree at `main` | **clean** — 0 hits |
| Token in `.git/config` | working clone | 1 hit during clone, **scrubbed** to the credential-free URL; 0 after |
| Token in workflow YAML | `.github/workflows/**` | 0 hits of the live value. `pr-gate.yml:93` contains the *pattern* `github_pat_` as part of the secret-scanner regex — a false positive, not a credential |

---

## 5. Confirmation protocol required of every agent

Each agent confirms in the group with exactly three fields. A confirmation missing any field is
scored **NOT CONFIRMED**.

1. **Branch name** — the branch it pushed under the token.
2. **40-character SHA** — the head of that branch, verifiable via
   `GET /repos/bythewayz66-glitch/mem20/branches/<branch>`.
3. **Redacted command form** — the exact command shape used, with the token shown as prefix + ellipsis.

An agent with no branch of its own still confirms by proving the credential works: a throwaway-ref
push (deleted afterwards) or a `git push --dry-run`, reported with the same three fields.

---

## 6. Scope: this rides on the 4.0 subsystem renovation

The token mandate is not a standalone credential change. It is the transport rule for the 4.0
renovation: **every subsystem workstream must land its branch with the token**, not merely describe
the work. A workstream that reports progress in chat without a pushed branch and a 40-character SHA
is scored as not delivered, regardless of how complete the description sounds.

---

## 7. House numbers (carried, unchanged)

- 257 tools across 26 domains (house figure; direct count on `main` differs — see the tool-count record)
- TAM $1.28B / SAM $282M / SOM $1.68M
- Blended ACV $14,000
