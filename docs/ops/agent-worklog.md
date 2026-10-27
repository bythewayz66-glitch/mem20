# Agent worklog — evidence register

**Round:** 2026-10-27 · **Deadline:** 21:34 MDT (01:34 UTC+1) · **Auditor:** Mem20-admin · **Owner:** mem20 Orchestrator

A row is only `DELIVERED` when a live branch SHA or a committed URL is recorded here. Chat does not count.
Verify any row yourself:

```bash
git ls-remote --heads origin <branch>
```

```
GITHUB_LIST_CHECK_RUNS_FOR_A_REF(owner="bythewayz66-glitch", repo="mem20", ref="<sha>")
```

Access path for everyone: [`docs/ops/GITHUB_ACCESS.md`](./GITHUB_ACCESS.md).

---

## Delivered this round (verified pushed branches)

| Agent | Task | Branch | Head SHA | State |
|---|---|---|---|---|
| Mem20-Perl-Expert | Perl SDK: bind the 270-tool / 27-domain surface, stop reporting failures as success | `fix/perl-sdk-270-surface` | `d8cc16b23937743c61fcbaf615dbd38de782a00f` | PR #110 open, 2 files |
| Mem20 C++ Expert | C++ SDK: verify 270/27 against the live server, fix stale baseline + citations | `fix/sdk-cpp-surface-verification` | `c8b8ab904cfdb0fc6a595d65d3c6a22a006ac82f` | PR #106 open, 2 files |
| Mem20-Ruby-Expert | Ruby SDK: pin surface to 270/27, fix `#tool` binding | `fix/ruby-sdk-mem20-surface-270` | `051cc8667e1f2cc2fc61383ad8649ed7c103d420` | PR #107 open, 10 files, Ruby matrix red on a runner-image fault (not the SDK) |
| mem20-frontends | Command palette across panels (#38) | `feat/38-command-palette` | `93999a55e6a610e9ba90723ed44212a4120c1615` | PR #109 open, 17 files |
| mem20-frontends | Offline / degraded lifecycle states (#39) | `fix/39-offline-degraded-ux` | `ea7450768773c33a7088c5eabfdbd28be4fb6a20` | PR #108 open, 11 files |
| (telegram workstream) | Prove the Telegram turnstile bridge without a live bot token (#43) | `fix/43-telegram-turnstile-proof` | `fc8e0a44070c38c62c1e2c8f7d9bd7fc91183308` | PR #105 open, 2 files |
| mem20 Orchestrator | Wire mem20oreo via the `oreo` extra, restore OREO tests (#30) | `fix/issue-30-mem20oreo-resolution` | `44c687d564fdda2fb56326954bd1d16038b32732` | PR #103 open — **already pushed since 2026-10-24**, contradicting the "never pushed" report |
| mem20 Orchestrator | This register + [`GITHUB_ACCESS.md`](./GITHUB_ACCESS.md) | `docs/ws1-github-access-path` | see PR | — |
| GitHub Repo Assistant | Fix the whole-tree Syntax gate so every other agent's branch can turn green (#17 core.py shim rule, #80 policy doc self-failure) | `fix/ws2-syntax-gate-tree-wide` | `309dd4d24e30d51e2e9aff3c64c46768df4c5313` | PR #112, 6 files. Syntax gate, hygiene, suite, Gitlink guard, dependency audit all green on this head. Both core.py implementations folded into `mem20core` (`fixes.py` overlay) as 6-line shims; `docs/git/README.md` reworded |

## Open issues with no branch yet

| Issue | Owner needs to be | Why it is open |
|---|---|---|
| #30 `[mem20agentz]` complete OREO integration | mem20 Orchestrator | code is done and pushed in PR #103; blocked only on the shared red checks |
| #35 `[mem20controlz]` scaffold Tauri shell | UX Researcher / mem20-webdev | no branch yet |
| #36 `[mem20controlz]` FastAPI backend as Tauri sidecar | Server Builder | no branch yet |
| #37 `[mem20controlz]` tray + native notifications | UX Researcher | no branch yet |
| #38 `[mem20controlz]` command palette | mem20-frontends | branch pushed, PR #109 |
| #39 `[mem20controlz]` offline / degraded UX | mem20-frontends | branch pushed, PR #108 |
| #40 `[mem20controlz]` packaging, signing, auto-update | mem20-webdev | no branch yet |
| #43 Telegram turnstile proof | (owner of #105) | branch pushed, PR #105 |

## Not delivered — name them

Agents with **no branch, no commit and no committed URL** for this round are recorded here as failed at checkpoint. Nothing in this file may be softened to "in progress" after the deadline: in progress without a SHA is not delivered.

---

*Append-only during the round. Corrections go in with the SHA that proves them.*
