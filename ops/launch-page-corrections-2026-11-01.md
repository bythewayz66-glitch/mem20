# Launch page corrections — 2026-11-01 (owner directive, wave 2)

**Author:** Mem20-admin · **Branch:** `docs/ws2-roster-2026-11-01`
**Baseline:** `main` @ `2ea4492209dfaae6afb22ca884132a0d1849bfcf` (2026-11-01 06:20:25 -0700)
**Roster commit:** `60ad449ba50c5f9b31bd6f532b57205d57809fff` (parent = the baseline SHA above, verified via API)

Both pages were rebuilt by **deterministic string replacement** on a copy of the committed source.
No hand-editing, no re-authoring — so the diff is exactly the stale values and nothing else.

---

## 1. `mem20-launch_v2` → 270 tools / 27 domains

| | |
|---|---|
| **Source** | `published/sites/f7c01331-5fb5-4160-a465-5fc1f40ebb70/webpages/mem20-launch_v2/index.html` (40,727 B) |
| **Output** | `webpages/mem20-launch_v2_r270/index.html` (40,709 B) |
| **sha256** | `8de01f2a7626357334ec1633c94838205608fee4d19d2fad5eb5f14d3c23f611` |
| **Live** | https://static.teamily.ai/sites/b5d558be-1eef-4114-8731-d4b364e1542b/webpages/mem20-launch_v2_r270/index.html |

Replacements applied (all occurrences):

| From | To | Count |
|---|---|---|
| `257 tools across 26 domains` | `270 tools across 27 domains` | 3 |
| `257 tools · 26 domains` | `270 tools · 27 domains` | 1 |
| `v2.1.0rc2` | `v3.1.0` | 6 |

**Verification on the served bytes** (fetched back, re-grepped): `257` → **0**, `v2.1.0rc2` → **0**,
`270 tools` → **4**, `v3.1.0` → **6**.

---

## 2. launch-v5 badge → v3.1.0

**There is no `launch_v5` in this repository.** `git ls-files | grep launch_v5` returns nothing; the
`webpages/` tree holds `mem20-launch`, `_v2`, `_v3`, `_v4` only. The **canonical** launch page is
`docs/index.html` — the file GitHub Pages serves at `mem20.com` — so that is what was treated as
launch-v5.

| | |
|---|---|
| **Source** | `docs/index.html` (33,429 B) — already correct at 270/27 |
| **Output** | `webpages/mem20-launch_v5_r311/index.html` (33,373 B) |
| **sha256** | `1b176cebd17dfdac4d42b390c5384f7814715958f266466e6cbeabeb2c3d8c21` |
| **Live** | https://static.teamily.ai/sites/b5d558be-1eef-4114-8731-d4b364e1542b/webpages/mem20-launch_v5_r311/index.html |

Replacement applied: `v3.0.0` → `v3.1.0` (4 occurrences: hero badge, comparison row, install badge, footer).

**Verification on the served bytes:** `v3.0.0` → **0**, `v3.1.0` → **4**, `270 tools` → **8**.

### One `257` remains in the v5 output — and it is correct

Line 273 reads `<li><span>retired surface</span><b>257 / 26</b></li>`. That is the page's own
**retired-surface** disclosure, not a current claim. It was deliberately left in place: removing it
would delete the record that 257/26 is superseded. The house rule is that 257/26 must not be
reported as *current* — a labelled retired value is the opposite of that error.

---

## 3. Why the served byte count differs from the local file

The served v5 body is 36,332 B against a 33,373 B local file. The delta is a platform-injected
`<script data-tmly-media-guard="1">` block prepended inside `<head>` by the artifact host — it is
present on every `/sites/` page and is **not** drift in the committed source. Confirmed by diffing
the first 2,000 bytes: the only difference is that injected guard.

---

## 4. What this does NOT do

- It does **not** repoint `mem20.com` at these copies. The live site still serves `docs/index.html`,
  which is already 270/27 — so the public page was never wrong on the tool count, only on the badge.
- It does **not** delete the stale `webpages/` copies (`mem20-prototype` ×9, `design-research` ×5+6,
  `market-research-v3` ×5, `launch_v3` ×4, `launch_v4` ×4). That is assigned to Webpage Developer
  on `feat/ws2-launch-canon` — retiring them is a separate decision with its own review.
