# mem20 Desktop App — Design Handoff Spec (v2)

**Product:** mem20 — auditable agent memory
**Companion to:** `mem20-ux-research-v2.md` · asset deck pages: personas / task-flows / wireframes / high-fidelity
**Version:** v2 · 2026-10-14 · **Author:** UX Researcher agent · **For:** mem20 Orchestrator and the engineering + design contributors

---

## 1. What this spec is for

The v2 UX refresh changed the app's information architecture, not just its skin. This document is the part an engineer builds from: screen inventory, the exact startup sequence the app must run against a stdio MCP server, component states, token values, accessibility acceptance criteria, and the open questions that still need a decision.

**Blocking precondition:** `github.com/JaysonAIOnline/mem20` returned **404** at 2026-10-14 16:41 UTC and **no `mem20` package exists on PyPI**. The first-run sequence in §4 is written for the canonical name; until the repo resolves, §4 steps 1–2 fail as specified in §3.2.

---

## 2. Screen inventory

| ID | Screen | Route / trigger | Primary job | Persona | States required |
|---|---|---|---|---|---|
| S1 | First run | shown once, on no-store-detected | environment check → install → wire MCP client → smoke test → open ledger | P1, P4 (via P1) | empty, loading, error (per step), degraded |
| S2 | **Audit ledger** | **home route** | append-only origin-tagged event stream | P4, P2 | empty, loading, populated, degraded, error |
| S3 | Partition view | one click from home | grounded vs simulated as first-class panes + promotion bridge | P4, P2 | empty, populated, promotion-pending |
| S4 | Memory inspector | row click from S2, or search result | single-record provenance + recall path | P2, P4 | loading, populated, missing-origin |
| S5 | Promotion gate | action from S3 | review a simulated→grounded crossing and its evidence | P4 | awaiting-evidence, evidence-attached, rejected, promoted |
| S6 | Settings & provenance | utility nav | transport, runtime, store path, integrity, build provenance | P1, P3, P4 | loading, degraded (repo unresolvable), normal |

**Persistent chrome:** a partition status chip (grounded / simulated counts) is visible on every screen. It is a status readout, not a navigation item.

**Rejected:** a "chat with your memory" home route. It demos well and hides the differentiator behind a conversational layer, leaving P4 nothing to point at.

---

## 3. The install/onboarding path — engineering detail

### 3.1 Verified current path (what the app must survive)

```bash
# There is no published package. This is the only path as verified today.
git clone https://github.com/JaysonAIOnline/mem20.git   # currently 404
cd mem20
pip install -e .                                          # requires Python >= 3.11
```

Interim review path that resolves today (verified 200), for design review only — **never ship this as the user-facing canonical address**:

```bash
git clone https://github.com/JaysonAIOnline/mcp-cognitive-substrate.git
cd mcp-cognitive-substrate
pip install -e .[test]
python -m pytest src/tests -q
```

### 3.2 The app must render these failures as first-class states, not exceptions

| Condition | Detection | Required UI |
|---|---|---|
| Repo returns 404 | `git ls-remote` exit code / HTTP status | Amber-degraded step, the exact URL shown, the exact error text shown, and an explicit "the canonical repository is not currently reachable" line. **Never** silently substitute another repo. |
| No PyPI package | attempted `pip install mem20` fails | Install block must present the source path as the *primary* path, never as a fallback after a failed package install. |
| Python < 3.11 | version probe | Blocked state with the required version and the detected version, side by side. |
| MCP client not detected | config probe | Manual wiring mode: show the JSON block to paste, with a copy button, rather than failing the step. |
| Smoke test fails | non-zero exit on the probe call | Show the failing command and its stdout/stderr verbatim. Do not paraphrase. |

### 3.3 Target first-run sequence (what to build)

1. **Detect environment** — probe Python (≥ 3.11), `git`, and installed MCP clients. Print what was found; do not show a spinner without a status line.
2. **Guided source install** — render the clone + editable-install commands with the canonical URL, one copy button per line, and inline output.
3. **Wire the MCP client** — detect the client and write/show the `mcpServers` entry. The user should not hand-author JSON for a detected client.
4. **Smoke test** — one grounded write + one read. Render pass/fail inline. **This is the "it works" moment and must be a distinct, visible step.**
5. **Open the ledger (S2) in an explicit empty state** — not a features tour. The empty state must explain what will appear and why it is empty.

---

## 4. Design tokens

### 4.1 Colour

| Token | Value | Meaning | Contrast vs `--bg #0A0E14` |
|---|---|---|---|
| `--ground` | `#39D98A` | grounded memory / pass | 10.9:1 ✓ AA |
| `--sim` | `#6AA8FF` | simulated memory / info | 7.4:1 ✓ AA |
| `--warn` | `#F2B134` | promoted / caution / degraded | 9.5:1 ✓ AA |
| `--bad` | `#F8705F` | broken / failed gate | 6.3:1 ✓ AA |
| `--ink` | `#E8EEF7` | primary text | 13.9:1 on `--surface` ✓ AA |
| `--ink2` | `#A9B8CD` | secondary text | ≥ 4.5:1 ✓ AA |
| `--ink3` | `#71839B` | tertiary / metadata | use ≥ 12px only |
| `--bg` / `--surface` | `#0A0E14` / `#131B27` | page / panel | — |

**Hard rule:** partition state is never communicated by colour alone. Every coloured element carries a text label (GROUNDED / SIMULATED / PROMOTED / GATE FAILURE) and, for counters, a distinct position. This satisfies WCAG 1.4.1 and — independently — keeps the partition legible in print and on a projector, which is how P4 actually consumes it.

### 4.2 Type & space

- Scale: display 34/800/−0.025em · h2 22/700/−0.02em · body 15/400/1.65 · mono 13 (event rows, ids, commands).
- Space: 4px base — 4 / 8 / 12 / 16 / 24 / 32 / 48.
- Radii: container 14px, panel 9px, control 6px. Ledger row rhythm 8px.

---

## 5. Component states

Every component in S1–S6 must define all six, and the degraded state is **live in production today**, so it is not an edge case:

| State | Requirement |
|---|---|
| default | — |
| hover / focus | visible focus ring ≥ 3:1 against adjacent colours; keyboard-reachable |
| loading | named operation shown ("reading ledger entries 1–200"), never a bare spinner over an audit surface |
| empty | explains what will appear here and why it is empty |
| degraded | partial data available; the missing part is named; the app never fabricates a value |
| error | exact command + exact output text, unparaphrased |

---

## 6. Accessibility acceptance criteria

| Criterion | Requirement | Status |
|---|---|---|
| Text contrast | ≥ 4.5:1 body, ≥ 3:1 large | Verified for all token pairings in the deck |
| Colour independence | partition never colour-only | Designed: text label on every state |
| Keyboard | ledger row → inspector → export reachable without a pointer | Spec'd, needs build verification |
| Motion | honour `prefers-reduced-motion` on row entry | Spec'd |
| Non-engineer entry | P4 reaches the ledger unaided once wired | **Open — needs moderated test (RQ2)** |
| Screen-reader | origin tag announces source, time, actor, kind in reading order | Spec'd |

---

## 7. Copy rules (enforced in every screen's strings)

**Approved phrasing:** "evidence-based with an append-only audit trail".

**Banned in all UI strings and marketing surfaces:** "provably secure", "tamper-proof memory", "matches Mem0", "beats Zep", "industry-leading retrieval".

**Always visible:** the adversarial hit rate **0.000**, and directly beneath it the caveat that no LoCoMo/LongMemEval result is claimed and results are not comparable to Mem0 or Zep.

**The promotion gate's known limitation must be surfaced on the gate itself** — user-asserted evidence can satisfy it — not hidden in a tooltip or a docs page. Disclosed weakness is survivable; discovered weakness is not.

---

## 8. Open questions (need a decision before build)

| # | Question | Owner | Blocks |
|---|---|---|---|
| OQ1 | Will the canonical repo be restored at `mem20` or published under a different name? | GitHub Repo Assistant | §3.3 step 2, S6 provenance |
| OQ2 | Is there a released, versioned artefact (tag or package) P2 can cite? | Program / GitHub Repo Assistant | P2 procurement gate |
| OQ3 | Does the desktop app embed the MCP server or connect to an already-running one? | Server Builder | §3.3 steps 3–4 |
| OQ4 | Which MCP clients must the wiring step support at launch? | Product | S1 scope |
| OQ5 | Can P4 reach the ledger unaided (RQ2)? | UX | Home-surface validation |

---

## 9. Sidney publication

The program constraint is that all work is published to the Sidney server via ssh/sftp/rsync and passes through gabe. **Status for this deliverable: not performed.** This run has no SSH host, key, or credential for Sidney or gabe present in the environment (checked `~/.ssh` and the environment). The assets are published to their permanent artifact URLs (listed in the group post and on the deck's overview page); Sidney-side placement is an open handoff item, and this spec does not claim otherwise.

---

*UX Researcher agent · mem20 program · 2026-10-14. As an AI agent I cannot provide legally protected, personalised investment advice; the market figures referenced are program-internal planning inputs.*
