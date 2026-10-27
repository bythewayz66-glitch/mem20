# Branch audit — 2026-10-26

Inventory of every non-`main` branch in `bythewayz66-glitch/mem20`, with the
disposition each one needs. Measured against `main` at `c64c113edb9ec4c0f41481900c56a9074469280b`
(2026-10-25).

Reproduce with:

```bash
git ls-remote --heads origin | sed 's#.*refs/heads/##' | grep -v '^main$'
# per branch:
git rev-list --count origin/main..origin/<branch>   # commits not on main
git merge-base --is-ancestor origin/<branch> origin/main && echo MERGED || echo UNMERGED
```

## Summary

| Measure | Value |
|---|---:|
| Branches total | 16 |
| `main` | 1 |
| Fully merged (0 unique commits) | 3 |
| Unmerged | 12 |
| **Orphan commits (unreachable from `main`)** | **60** |

The per-branch counts below sum to exactly 60, so the orphan population is fully
accounted for. Nothing is deleted until its commits are accounted for.

## Fully merged — safe to delete

These carry zero commits that `main` does not already contain. Deleting the ref
loses no work.

| Branch | Head | Unique commits | Disposition |
|---|---|---:|---|
| `ci/ws2-pr-gate` | `7e08ffe1be429e8c3f032f634245a2712a604bc3` | 0 | delete ref |
| `copilot/setup` | `d997a87f2c5dd9126555fabeff71c3be5585da19` | 0 | delete ref |
| `fix/issues-5-10-11-14-18` | `b69b7b653821d09d3dc79a052e7815d06cfde643` | 0 | delete ref |

## Unmerged — commits must be preserved

Disposition vocabulary:

- **rebase-and-PR** — content is wanted; rebase onto `main` and open a PR.
- **merge** — fast-forwardable / no conflict; merge directly.
- **archive-tag** — not wanted on `main` but the history is worth keeping; tag
  `archive/<branch>-2026-10-26` and delete the ref.
- **review** — needs a human decision on whether the work is still wanted.

| # | Branch | Head | Unique commits | Disposition |
|---:|---|---|---:|---|
| 1 | `fix/issues-5-18-complete` | `d25015a149ae7cc00138af3887f0df3e278579c6` | 21 | rebase-and-PR (largest single payload; tracked as its own job) |
| 2 | `chore/wave1-git-hygiene` | `8a038f697a446ffab8ca497abff0f024de475e1d` | 11 | rebase-and-PR |
| 3 | `feat/first-class-sdks-readme` | `e665bab9864aa2c062dd4a7e8d146903d3a609d5` | 6 | rebase-and-PR |
| 4 | `chore/merge-adapz-autoz` | `72b46985109faffd57333a6ea2e81f805a9efd24` | 6 | review |
| 5 | `fix/ws2-mcp-bootstrap-collect` | `b08576617344149477cbe324efef64b2e15d7f2a` | 4 | rebase-and-PR |
| 6 | `fix/issues-18-25` | `6e03e463f972b6f1d270bcf091767c8182434473` | 3 | rebase-and-PR |
| 7 | `fix/batch-13-47` | `e0100159fbd0bb2111aadcd15d11848a16fc280d` | 2 | rebase-and-PR |
| 8 | `feat/scale-corpus-2000` | `d0f21e2d040b5279dca36ae1f9c2b0baa8382064` | 2 | rebase-and-PR (benchmark corpus; tracked as its own job) |
| 9 | `chore/wave1-portable-paths` | `94a224341fd820fb47f6fc0626591cd35e0bc8c0` | 2 | rebase-and-PR |
| 10 | `fix/issues-5-18-safe` | `8babe092a56a1f83ae3c9aead08617b96ccbc12d` | 1 | review (subset of #1 — confirm before keeping both) |
| 11 | `fix/issue-30-mem20oreo-resolution` | `44c687d564fdda2fb56326954bd1d16038b32732` | 1 | rebase-and-PR |
| 12 | `dependabot/cargo/braid/ed25519-dalek-3` | `b0a3a6e19445da1454033833b387a1e0963a9d4f` | 1 | review (dependency bump; needs Rust braid CI green) |

## Tags

| Tag | State | Disposition |
|---|---|---|
| `v3.0.0` | points ~100 commits behind `main` | leave (historical release marker); a new tag is needed, not a move |
| `archive-mem20frontendz-2026-10-19` | 15 commits off `main` | **remove** — superseded archive; its history is already reachable if those commits are accounted for |

## What this run did and did not do

- **Recorded** the full disposition table above from live `git ls-remote` +
  `rev-list` output, so every number here is reproducible.
- **Did not delete refs or tags.** The sandbox has no git credentials, and the
  connected GitHub integration exposes no delete-reference or delete-tag
  operation — only create/commit/read. Deleting a remote ref is therefore not
  possible from this agent, and no claim is made that it happened. The three
  fully-merged refs remain on the remote; they are inert (0 unique commits) and
  carry no risk while they wait for someone with ref-delete access.
- The dispositions are proposals with reasons, not merged state. Merging 60
  orphan commits is real work with real conflicts; recording the table is the
  prerequisite, not the substitute.
