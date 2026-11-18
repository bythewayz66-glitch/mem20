# mem20 Program Status & Work-Assignment — 2026-11-16

**Owner:** mem20 Orchestrator · **Repo:** `github.com/bythewayz66-glitch/mem20`
**Baseline `main`:** `0224a64946a2c00313a9872515893157adcbc47e` (2026-11-16 06:55:07 +0000,
*"docs: Update DIARY/failures with MCP server startup fix"*) · **`VERSION`:** 4.0.0
**Measured:** 2026-11-16, fresh clone, `git fetch --prune --tags` rc=0. Every figure is emitted
by a command run in this push or a GitHub REST call. A row is DELIVERED only when a pushed
branch SHA or committed URL backs it.

## 1. Still open — blockers and decisions needed

| # | Blocker | Owner |
|---|---|---|
| B1 | `main` not release-clean: 3 of 13 checks red on `0224a649` (`Tests`, `MCP handshake (shallow clone)`, `artifact evidence`). Root cause is issue **#229**: `mem20kilnz/engine/` dropped with a gitlink in `71939ee0`, so ~200 tests fail loudly by design. Restore the engine source or retire the package — do not paper over it with a skip. Not an agent call. | GitHub Repo Assistant / mem20-sybsystems |
| B2 | **50 at-risk commits on 12 branches**, unmerged, **no PR open for any of them** — they will rot. Triage order in §3. | Orchestrator → branch owners |
| B3 | `main` untagged at 4.0.0 — no `v4.0.0`; newest semver `v4.0.0` is **683 commits behind**. Cutting a tag is an owner call. | owner (release cut) |
| B4 | PyPI absent — `mem20` / `mem20-mcp` / `mem20-sdk` all 404. Needs a token or trusted publisher. | owner (credentials) |
| B5 | Live surface is **487 tools / 129 domains**, not the house 257 / 26 — positioning line is stale (§6). | owner (positioning) |

**Snapshot:** 10/13 checks green (76.9%); 103 remote heads; 12 ahead; 0 open PRs; 1 open issue;
132 tags; 11,439 tracked files; 1,158 commits on main; `mem20.com` HTTP 200 stating v4.0.0.
**Composite: 4 green, 2 amber, 5 red.** Not release-clean.

## 2. Who owns what

| Agent | Current assignment | Status |
|---|---|---|
| **mem20 Orchestrator** | This record; triage of the 12 at-risk branches (§3) | GREEN (in progress) |
| **GitHub Repo Assistant** | Close B1; open PRs for the 12 at-risk branches | RED (blocked on #229) |
| **mem20-sybsystems** | Own issue **#229** (`mem20kilnz` engine deleted with gitlink) | RED (open) |
| **Mem20 Benchmark Dataset Builder** | Publish scored adversarial_hard + unanswerable rows (carried from 2026-11-01, still ABSENT) | RED (not delivered) |
| **AI Engineer** | `docs/benchmarks/retrieval-gap-analysis-2026-11-01.md` never pushed — re-assign | RED (ABSENT) |
| **Mem20-Perl-Expert** | `fix/perl-sdk-surface-272` @ `d5c4af64` — surface 270→272 + guard hole | AMBER (no PR) |
| **Mem20-Ruby-Expert** | `ruby-sdk-release-2026-11-01` @ `a2354422` — release docs + gemspec | AMBER (no PR) |
| **Mem20 C++ Expert** | `…cpp-expert-braid` @ `5a63ed53`; `…mem20wasmz` @ `925d10af` | AMBER (no PR) |
| **Server Builder** | `…server-builder-gateway` @ `40cf6c56`; `…mem20meshz` @ `abc3a111` | AMBER (no PR) |
| **mem20 GTM Team Lead** | `gtm/claim-ledger-v7-rebase` @ `ac929c4e` — 14 ahead, largest at-risk branch | AMBER (no PR) |
| **mem20-frontends** | `feat/4.0-super-agent-memory-engine` @ `638ee427` | AMBER (no PR) |
| **Mem20-naration** | `docs/ws1-narrative-serial-2026-11-01` @ `2d2e6212` | AMBER (no PR) |
| **mem20-webdev** | Live site green at v4.0.0; `/sites/` anonymous-403 (G10) still open | AMBER |

**Produced nothing this push (named, not padded):** UX Researcher, Analytics Reporter, Content
crew (mem20-\*), Short-video crew, Message-board agents, Beta tester agent, QA agents.

## 3. At-risk branches — 50 commits, 12 branches, 0 PRs

`git rev-list --count origin/main..origin/<branch>`; all unmerged, all with **no open PR**.

```
ahead branch                                              head SHA
14    gtm/claim-ledger-v7-rebase                          ac929c4e3e5f27669bb92f576c5b2ee265415277
 9    fix/post20-defects                                  a267eaa39e9ceee77281d5aff24035040f582963
 6    ruby-sdk-release-2026-11-01                         a2354422d35beaa93efd100e75146a33b69c3a0b
 6    feat/4.0-mem20-cpp-expert-braid                    5a63ed5322ba9fe8833d426a7693f9724155f3c8
 4    feat/4.0-server-builder-mem20meshz                  abc3a111dbf690b598cf0345c583238b91210098
 3    feat/4.0-server-builder-gateway                     40cf6c5675f5b16228b8b0ea9e09921e017f2ef7
 2    feat/4.0-mem20-cpp-expert-mem20wasmz                925d10aff3516a09c21c32e2b69d5f3215beff0b
 2    docs/ws1-narrative-serial-2026-11-01                2d2e6212eb5d4b3570121cdc3c7b1f55353e6e56
 1    fix/perl-sdk-surface-272                            d5c4af64001000bcc1bfc11297b414072c94f3f7
 1    fix/open-issues-5                                   dafe65024e3539ef401ebbb65d3941e33736a39d
 1    feat/4.0-super-agent-memory-engine                   638ee427113c3de10c7e3515af5f144c0eb472dc
 1    feat/4.0-conformance-gate-language-aware-discovery   d4b04e661f7cf3d47542f5cb27e3b250fc6504df
50    12 branches
```

**Triage order:** `fix/open-issues-5` → `fix/post20-defects` (9) → the three SDK branches
(Perl/Ruby/C++) → the two Server Builder 4.0 branches → `gtm/claim-ledger-v7-rebase` (largest;
needs a rebase against a 683-commits-newer `main`) → rest.

## 4. Red checks on `main` `0224a649` (10 green / 3 red)

| Check | Annotations | Job |
|---|---|---|
| `MCP handshake (shallow clone)` | 3 | [43820093477](https://github.com/bythewayz66-glitch/mem20/actions/runs/43820093477/job/133141021916) |
| `Tests` | 4 | [43820093439](https://github.com/bythewayz66-glitch/mem20/actions/runs/43820093439/job/133140960132) |
| `artifact evidence` | 8 | [43820093456](https://github.com/bythewayz66-glitch/mem20/actions/runs/43820093456/job/133140960033) |

Green: `hygiene`, `suite`, `Syntax gate`, `Gitlink guard`, `Dependency audit (issue`,
`Rust braid (issue`, `controlz desktop wiring`, `mem20api HTTP service`, `doc-count drift gate`,
`mem20agentz OREO integration`. `Tests` root cause is #229 above; `build-engine` returns
`{"ok": false, "returncode": 2}`.

## 5. What landed in this push

| Artifact | Path | Owner |
|---|---|---|
| This program status & work-assignment record | `docs/ops/program-status-2026-11-16.md` | mem20 Orchestrator |
| `docs/ops/` index refresh (28 stale entries → 36 tracked files) | `docs/ops/README.md` | mem20 Orchestrator |

Branch `docs/ops/program-status-2026-11-16`, cut from `main`
`0224a64946a2c00313a9872515893157adcbc47e`. The 40-char head SHA is recorded in the PR body
opened from this branch; that PR is the evidence of record for this push.

## 6. Corrections to house numbers

| Carried claim | Live measurement |
|---|---|
| "257 tools across 26 domains" | **487 / 129** (`docs/surface.json`, cross-checked against the AST catalog); 19 tools unwired — house line is several surface moves stale |
| "`v4.0.0` is the newest tag" | newest by creatordate is `archive-ops-daily-report-2026-11-14` (`9670699`, 23 behind / 1 ahead); newest semver is `v4.0.0` (683 behind). Both true; `main` is untagged at 4.0.0 |
| TAM $1.28B / SAM $282M / SOM $1.68M; ACV $14,000 | not re-measured here; carried unchanged, not verified |

## 7. Reproduce

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git && cd mem20 && git fetch --prune --tags
git rev-parse origin/main && git log -1 --format='%ci %s' origin/main
for b in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin | grep -v 'origin/HEAD' | grep -v 'origin/main$'); do
  n=$(git rev-list --count origin/main..$b); [ "$n" -gt 0 ] && echo "$n $b"; done | sort -rn
git rev-list --left-right --count v4.0.0...origin/main
git ls-tree -r --name-only origin/main | wc -l
```

**Not measured here:** historical trend (one snapshot); test-case-level pass rate (check runs
expose job conclusions only); benchmark quality (rows carried ABSENT, not re-scored);
revenue/funnel; anonymous reachability of `/sites/` (G10 is mem20-webdev's).

---

*mem20 Orchestrator · 2026-11-16 · baseline `0224a64946a2c00313a9872515893157adcbc47e`*

**Disclaimer:** As an AI Agent, I cannot provide legally protected, personalized investment
advice. This analysis is for informational purposes only and does not constitute investment
advice or recommendations. Consult a licensed financial advisor before making investment
decisions.
