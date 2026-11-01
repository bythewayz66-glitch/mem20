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

---

# PART II — Confirmation sweep and 4.0 working status

**Sweep window:** 2026-11-01, 18:56Z–19:12Z · **Roster at check time:** 26 members (25 agents + 1 human owner)
**Repo state at check time:** `main` = `48c241a1edff1fdc9f0d0b38f51796c3c8b88b2b` ("chore(release): cut 3.1.2 and land the owner directive"), 25 branches total (24 non-`main`), **7 open PRs (#150–#156)**, `teamz` `main` = `ca1e6c66c5bba61ce32834ae41a266823393a475`.

This part answers two separate questions the owner asked, and they are **not** the same question:

- **CONFIRMED** = the agent replied to the token mandate with a branch, a 40-character SHA, and a command form, and that SHA is real in the API.
- **WORKING** = the agent has a branch with commits ahead of `main` and a recent commit timestamp.

An agent can be working without having confirmed, and the reverse. Both are reported separately below.

---

## 8. Confirmation ledger — 2 of 25 confirmed (8%)

Every SHA in this table was re-read in this run from `GET /repos/bythewayz66-glitch/mem20/branches/<branch>`. **No chat claim was accepted as evidence.**

| # | Agent | Branch | 40-char SHA | Command form (redacted) | API check | Status |
|---|---|---|---|---|---|---|
| 1 | Mem20-admin | `docs/ws1-token-mandate-2026-11-01` | `fea166d8e51c5fae32de0fd6dd4abdab3e58390a` | `git clone https://x-access-token:$GITHUB_TOKEN@github.com/…` → `git push origin HEAD:refs/heads/…` | `MATCH` | **VERIFIED** |
| 2 | UX Researcher | `tmp/token-verify-uxresearcher` | `1668c5bcd7077a419e136757490990055cbb06d5` | `git push https://x-access-token:$GITHUB_TOKEN@github.com/…` | commit **exists** (`GET /commits/1668c5bc…` → 200); ref `404` (deleted by design) | **VERIFIED** (throwaway ref, correctly cleaned up) |
| 3 | Mem20-Ruby-Expert | `ruby-sdk-release-2026-11-01` | `a2354422d35beaa93efd100e75146a33b69c3a0b` | — | branch `MATCH`, but **no reply** | NOT CONFIRMED |
| 4 | Mem20 Content Creator | `docs/gtm-launch-copy-v5-2026-11-01` | `aaffc08b84291c82e7041ee0cbf28fc521f1eddc` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 5 | Growth Hacker | `content/ws3-launch-channels-2026-11-01` | `e6c429a4a795a638fce269a518dc41e13aaa54e4` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 6 | mem20-sybsystems | `docs/tests-failure-repro-2026-11-01` | `34ff99db1ba5f0bb242a169b58d972edbdb2d603` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 7 | Market Research | `chore/competitive-matrix-refresh-2026-11-01` | `3db9b2699aabc38a9ff844022240f5cb6d2b613a` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 8 | Super Agent | *(none)* | *(none)* | — | no branch | NOT CONFIRMED |
| 9 | Slides Assistant | `deck/ws3-rebuild-2026-11-01` | `6b587d2e0b9bd6582f0ee247149e8747df140cdb` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 10 | Mem20-Perl-Expert | `docs/perl-sdk-release-2026-11-01` | `813d5ac3d73e0fbaea6f60d416325efc071bc7db` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 11 | Webpage Developer | *(none)* | *(none)* | — | no branch | NOT CONFIRMED |
| 12 | Finance Assistant | `chore/finance-claims-check-rerun-2026-11-01` | `6389f7eed2c8fbf1e3715178ac07fe96dec05d28` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 13 | Mem20 C++ Expert | `sdk/cpp-install-export-2026-11-01` | `73ea1af49fa5ace66a3abacc8922b7e86e913967` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 14 | mem20 GTM Team Lead | `docs/gtm-claim-ledger-v7` | `6304bfa3b5d90f89fa27f9963bfb7b28982b2781` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 15 | mem20-webdev | *(none persistent)* | *(none)* | — | earlier `tmp/token-verify` deleted | NOT CONFIRMED |
| 16 | AI Engineer | *(none)* | *(none)* | — | no branch | NOT CONFIRMED |
| 17 | Mem20-naration | `docs/ws1-narrative-serial-2026-11-01-final` | `1376fb477675636aba846467e138318dd742b3a1` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 18 | Mem20 Benchmark Dataset Builder | `docs/retrieval-gap-analysis-2026-11-01` | `899123a8141406dcba03298c690583ea465a7241` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 19 | Experiment Tracker | `docs/ws-experiment-registry-scored-2026-11-01` | `75aa002e7e8846f3daca5d2821cf1eb1a1722412` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 20 | GitHub Repo Assistant | `chore/g8-purge-retired-infra-2026-11-01` | `b355c98828ab6af558f1f710f2dfd2588a148cf4` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 21 | mem20 Orchestrator | `docs/4.0-renovation-plan` | `0883eca3826daf5f3dcdc973c00256e126f0ef1b` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 22 | Pricing Analyst | `pricing/reconcile-acv-14000-270-27` | `050f581e44314974805d701cc2962d146c4c4aec` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 23 | Analytics Reporter | `docs/ws1-program-scoreboard-2026-11-01` | `ffc7aad181dae2c02d54680ca72a1239384a4aca` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 24 | mem20-frontends | `fix/frontend-drift-2026-11-01` | `29f3de9e966b2d4277d0c818bf21d7c92284e496` | — | branch `MATCH`, **no reply** | NOT CONFIRMED |
| 25 | Server Builder | *(none)* | *(none)* | — | earlier dry-run only, no ref | NOT CONFIRMED |

**Chase dispatched this run:** 23 of 23 unconfirmed agents @-mentioned individually (`send_at_message`, 23 items, 23 succeeded, 0 failed). Each message carried that agent's own verified branch + SHA so the reply is a one-line confirmation, not an investigation. Deadline **2026-11-01 20:00Z / 14:00 MDT**.

**Important distinction for the owner:** `NOT CONFIRMED` is **not** the same as `not working`. Nineteen of the 23 unconfirmed agents have a live branch with commits ahead of `main` — they are producing work but have not replied to the credential protocol. Only the confirmation step is outstanding for them.

---

## 9. 4.0 working status — 20 of 25 working (80%)

Rule applied: a branch that contains commits ahead of `main`, with a commit timestamp inside the current cycle. `zero commits` = **NOT WORKING**.

| # | Agent | Active branch | 40-char SHA | Last commit (UTC) | Ahead | Verdict |
|---|---|---|---|---|---|---|
| 1 | mem20 GTM Team Lead | `docs/gtm-claim-ledger-v7` | `6304bfa3b5d90f89fa27f9963bfb7b28982b2781` | 2026-11-01T18:06:09Z | 12 | **WORKING** |
| 2 | GitHub Repo Assistant | `chore/g8-purge-retired-infra-2026-11-01` | `b355c98828ab6af558f1f710f2dfd2588a148cf4` | 2026-11-01T17:50:58Z | 10 | **WORKING** |
| 3 | Mem20-Ruby-Expert | `ruby-sdk-release-2026-11-01` | `a2354422d35beaa93efd100e75146a33b69c3a0b` | 2026-11-01T17:37:20Z | 6 | **WORKING** |
| 4 | Mem20 C++ Expert | `sdk/cpp-install-export-2026-11-01` | `73ea1af49fa5ace66a3abacc8922b7e86e913967` | 2026-11-01T17:31:42Z | 5 | **WORKING** |
| 5 | Growth Hacker | `content/ws3-launch-channels-2026-11-01` | `e6c429a4a795a638fce269a518dc41e13aaa54e4` | 2026-11-01T17:35:19Z | 4 | **WORKING** |
| 6 | mem20 Orchestrator | `docs/4.0-renovation-plan` | `0883eca3826daf5f3dcdc973c00256e126f0ef1b` | 2026-11-01T18:58:00Z | 4 | **WORKING** |
| 7 | Analytics Reporter | `docs/ws1-program-scoreboard-2026-11-01` | `ffc7aad181dae2c02d54680ca72a1239384a4aca` | 2026-11-01T17:31:14Z | 4 | **WORKING** |
| 8 | Mem20-naration | `docs/ws1-narrative-serial-2026-11-01-final` | `1376fb477675636aba846467e138318dd742b3a1` | 2026-11-01T17:36:33Z | 3 | **WORKING** |
| 9 | Market Research | `chore/competitive-matrix-refresh-2026-11-01` | `3db9b2699aabc38a9ff844022240f5cb6d2b613a` | 2026-11-01T17:32:35Z | 2 | **WORKING** |
| 10 | Mem20-Perl-Expert | `docs/perl-sdk-release-2026-11-01` | `813d5ac3d73e0fbaea6f60d416325efc071bc7db` | 2026-11-01T17:31:17Z | 2 | **WORKING** |
| 11 | Experiment Tracker | `docs/ws-experiment-registry-scored-2026-11-01` | `75aa002e7e8846f3daca5d2821cf1eb1a1722412` | 2026-11-01T17:33:05Z | 2 | **WORKING** |
| 12 | mem20-frontends | `fix/frontend-drift-2026-11-01` | `29f3de9e966b2d4277d0c818bf21d7c92284e496` | 2026-11-01T17:32:15Z | 2 | **WORKING** |
| 13 | Finance Assistant | `chore/finance-claims-check-rerun-2026-11-01` | `6389f7eed2c8fbf1e3715178ac07fe96dec05d28` | 2026-11-01T17:31:45Z | 1 | **WORKING** |
| 14 | Slides Assistant | `deck/ws3-rebuild-2026-11-01` | `6b587d2e0b9bd6582f0ee247149e8747df140cdb` | 2026-11-01T17:30:34Z | 1 | **WORKING** |
| 15 | Mem20 Content Creator | `docs/gtm-launch-copy-v5-2026-11-01` | `aaffc08b84291c82e7041ee0cbf28fc521f1eddc` | 2026-11-01T17:30:13Z | 1 | **WORKING** |
| 16 | UX Researcher | `docs/mem20-desktop-ux-research-2026-11-01` | `b7c8659a8d7c86f95540d6aa0b4e3a4a8aa19bfd` | 2026-11-01T17:31:12Z | 1 | **WORKING** |
| 17 | Mem20 Benchmark Dataset Builder | `docs/retrieval-gap-analysis-2026-11-01` | `899123a8141406dcba03298c690583ea465a7241` | 2026-11-01T18:23:07Z | 1 | **WORKING** |
| 18 | mem20-sybsystems | `docs/tests-failure-repro-2026-11-01` | `34ff99db1ba5f0bb242a169b58d972edbdb2d603` | 2026-11-01T17:32:34Z | 1 | **WORKING** |
| 19 | Pricing Analyst | `pricing/reconcile-acv-14000-270-27` | `050f581e44314974805d701cc2962d146c4c4aec` | 2026-11-01T17:47:26Z | 1 | **WORKING** |
| 20 | Mem20-admin | `docs/ws1-token-mandate-2026-11-01` | `fea166d8e51c5fae32de0fd6dd4abdab3e58390a` | 2026-11-01T18:53:43Z | 1 | **WORKING** |
| 21 | Super Agent | *(none)* | — | — | **0** | **NOT WORKING** |
| 22 | Webpage Developer | *(none)* | — | — | **0** | **NOT WORKING** |
| 23 | mem20-webdev | *(none persistent)* | — | — | **0** | **NOT WORKING** |
| 24 | AI Engineer | *(none)* | — | — | **0** | **NOT WORKING** |
| 25 | Server Builder | *(none)* | — | — | **0** | **NOT WORKING** |

**Totals:** 24 non-`main` branches · **71 commits ahead of `main`** · 20 agents working · **5 agents with zero commits**.

---

## 10. Verdict

| Question | Answer |
|---|---|
| How many agents **confirmed** the token mandate? | **2 of 25 (8%)** — Mem20-admin, UX Researcher |
| How many agents are **working** (branch with commits ahead of `main`)? | **20 of 25 (80%)** |
| Token write access proven? | **YES** — real push to `tmp/token-verify-mem20admin` @ `8becac15b2b98c59770025e4071ff1754b0b2354`, deleted after (204 → 404) |

**Not working (zero commits) — 5 agents, named:**
1. **Super Agent** — CI/quality-gate lane; no branch.
2. **Webpage Developer** — published-surface lane; no branch. The launch-page rebuild is unowned in the repo.
3. **mem20-webdev** — frontend lane; verified the credential with a throwaway ref earlier but landed no deliverable.
4. **AI Engineer** — AI/engineering lane; no branch.
5. **Server Builder** — server/backend lane; dry-run proven, no branch, no deliverable.

**Not confirmed but working — 18 agents:** Mem20-Ruby-Expert, Mem20 Content Creator, Growth Hacker, mem20-sybsystems, Market Research, Slides Assistant, Mem20-Perl-Expert, Finance Assistant, Mem20 C++ Expert, mem20 GTM Team Lead, Mem20-naration, Mem20 Benchmark Dataset Builder, Experiment Tracker, GitHub Repo Assistant, mem20 Orchestrator, Pricing Analyst, Analytics Reporter, mem20-frontends. Their work exists; only the three-field reply is missing.

---

## 11. Method and caveats

1. **How the API check was run.** For each of the 24 non-`main` branches, `GET /repos/bythewayz66-glitch/mem20/branches/<branch>` was issued and its `commit.sha` compared to the recorded head. **24 of 24 matched.** `ahead`/`behind` came from `GET /repos/…/compare/main...<branch>`; timestamps from `GET /repos/…/commits/<sha>`.
2. **A deleted ref is not a fake claim.** UX Researcher's `tmp/token-verify-uxresearcher` returns `404` as a branch but `GET /commits/1668c5bcd7077a419e136757490990055cbb06d5` returns **200**. The push happened; the ref was then removed, which is the correct hygiene behaviour. It is scored VERIFIED on the commit, not on the ref.
3. **Attribution limitation (material).** Token-based pushes commit as the token owner, so the git author field reads `bythewayz66-glitch` on **414 of the commits inspected**. Agent attribution in the tables above therefore comes from **branch name + changed paths**, not from the author field. Of the 24 branches, only 6 carry any commit authored under an agent name (Mem20 C++ Expert ×5, Analytics Reporter ×4, Mem20-Perl-Expert ×2, Experiment Tracker ×1, Finance Assistant ×1, mem20-slides ×1, mem20-sybsystems ×1). A future run must not read `bythewayz66-glitch` as "the human did this work".
4. **What was not checked.** Whether any agent used a non-token credential cannot be determined from the repository — the remote is anonymous-readable and the push protocol leaves no credential trace in git metadata. This sweep verifies *that work is pushed and verifiable*, not *which credential performed each push*. Claims of token usage per agent remain UNVERIFIED until the agent reports its command form.
5. **PR state.** 7 open, all non-draft: #150 (program scoreboard), #151 (desktop UX research), #152 (cpp install/export), #153 (finance claims rerun), #154 (launch channels), #155 (retrieval gap analysis), #156 (4.0 renovation plan). One branch — `docs/4.0-renovation-plan` — accounts for the newest commit in the repo (18:58Z).
6. **Stranded-work total.** 71 commits across 24 branches are ahead of `main`. That is the real at-risk figure for this cycle, not the branch count.

---

## 12. Next actions

| Action | Owner | Evidence required |
|---|---|---|
| Reply with the three fields (branch, 40-char SHA, command form) | 23 unconfirmed agents | deadline 2026-11-01 20:00Z |
| Land a first branch with real content | Super Agent, Webpage Developer, mem20-webdev, AI Engineer, Server Builder | 40-char SHA on a pushed branch |
| Merge or close PRs #150–#156 | GitHub Repo Assistant | 0 open PRs, or a stated disposition per PR |
| Reduce the 71-commit stranded total | mem20 Orchestrator + branch owners | merge order with SHAs |
| Rotate the token if this transcript is ever exported | owner | new token issued, old one revoked |

---

## 13. House numbers (carried, unchanged)

- 257 tools across 26 domains (house figure; the direct count on `main` reads 270 / 27 — the discrepancy is a known open item, not resolved here)
- TAM $1.28B / SAM $282M / SOM $1.68M
- Blended ACV $14,000
