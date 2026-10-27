# mem20 desktop merge order — 2026-10-27

**Owner of this document:** mem20 Orchestrator (roster row 5, branch `docs/ws1-merge-order`)
**Deadline:** 2026-10-27 09:44 UTC / 03:44 MDT
**Subject:** the single order that lands the mem20controlz desktop PRs without a `lib.rs` collision.

All paths below are relative to the repository checkout root.

---

## 0. Baseline and corrections (verified in this run, do not re-do)

| Fact | Value | How verified |
|---|---|---|
| Canonical repo | `github.com/bythewayz66-glitch/mem20` | `GITHUB_WHO_AM_I` + clone |
| Stated baseline commit | `1264076698a00878acc3adacf7bf1d51eea315cc` | exists (`git cat-file -t` = commit) |
| `main` at time of writing | `b9de9aa84b04341ac873689875a9bf8dd1cc3b7c` | `origin/main`, 2026-10-27 02:48:46 -0600 |
| Distance | `main` is **1 commit ahead** of the stated baseline | `git rev-list --count` = 1; `b9de9aa` = `fix(ci): restore the full 308-line ci.yml ... (#117)` |
| VERSION / tracked files | 3.0.0 / 7,974 | `cat VERSION`, `git ls-files \| wc -l` |

Two corrections carried from the dispatch, not re-litigated here:

1. **PR #112 (Syntax gate) is already merged** at `d3ec87699242e89830c66914e49763a352f4f25e` (08:28:34Z). Do not re-open.
2. **270 tools / 27 domains has already landed on `main`.** Do not re-sweep.

One correction to the dispatch itself, found by inspecting the branches rather than the issue text:

> The brief says `#35`, `#36` and `#37` all edit `mem20controlz/src-tauri/src/lib.rs`.
> **`#37` does not touch that file.** It adds `mem20controlz/src-tauri/src/tray_surface.rs` and edits the `mem20desktop` crate only.
> The file all three genuinely edit is `mem20controlz/src-tauri/mem20desktop/src/lib.rs`.

Because `main` moved, **re-base the order onto `main` at merge time**, not onto the baseline SHA quoted above. The merge-base the three branches share is `ee0ebc5e40794eb66acf16a15a4ec537deceaec5`.

### Branch heads at time of writing

| Issue | Branch | Head SHA | ahead/behind vs `main` (main/branch) |
|---|---|---|---|
| #35 | `feat/ws2-tauri-shell-35` | `0eae49153f94c07d736320ef5939ab50bd824a32` | 7 / 6 |
| #36 | `feat/ws2-tauri-sidecar-36` | `b7163284d6f8d6ba3cb137e53b0275f9ad84cd01` | 7 / 2 |
| #37 | `feat/ws2-tray-notifications-37` | `201c8315fc11a474df68fe4400b2b9517963289e` | 7 / 5 |
| #40 | *no branch exists* | — | roster row 1 (`mem20-webdev`) must create `feat/ws2-desktop-packaging-40` |

---

## 1. The merge order

```
main  ->  #35  ->  #36  ->  #37  ->  #40
```

### Why this order and no other

**Step 1 — #35 first, because it is the only branch that merges clean.**
Merging `feat/ws2-tauri-shell-35` onto `main` produced **0 conflicts** in a real simulation. It is also the branch that *creates* the `mem20desktop` crate (`Cargo.toml`, `health.rs`, `http/mod.rs`, `http/tests.rs`, `lib.rs`) and the icons. Everything after it is editing a crate that #35 owns, so #35 has to be the floor of the stack.

**Step 2 — #36 second, because it cannot exist without #35.**
`#36` adds only `sidecar.rs`, one line of module wiring, and app-level commands — but `sidecar.rs` calls `probe_port`, which returns `mem20desktop::ControlPlaneLiveness`, a type **defined in #35's `health.rs`**. #36 merged alone onto `main` fails to resolve `mem20desktop::*` entirely. Merging #36 onto #35 is what makes the crate whole: the merge succeeds mechanically (two predictable conflicts, resolved in §2) and produces the first tree where the shell both probes and owns a backend.

**Step 3 — #37 third, because it is file-disjoint but crate-coupled.**
#37 never touches `src-tauri/src/lib.rs`, so it looks independent. It is not: it appends `pub mod poller; pub mod tray;` **to the same `mem20desktop/src/lib.rs` that steps 1 and 2 were already rewriting**, and it re-declares `HEALTH_PATH`, which #35 also declares. Landing it before #36 would force #36 to resolve a three-way conflict instead of a two-way one. Landing it after #36 means each step resolves exactly one overlap.

**Step 4 — #40 last, because it has nothing to merge onto yet.**
There is no `feat/ws2-desktop-packaging-40` branch. Packaging/signing/auto-update touches `tauri.conf.json` and the bundle config — files #35 already modifies (20 lines) and which #36/#37 leave alone. It must land after the crate compiles so the signing config wraps a working binary, and it must not be used to mask a compile failure earlier in the stack.

> **Do not merge #36 before #35 under any circumstances**, including "it says it only adds two files." That is the exact trap the roster flagged: `git diff --stat main...feat/ws2-tauri-sidecar-36` shows 3 files and looks self-contained, while the types it references live 13 files away on #35.

---

## 2. The literal union

### 2a. The three-line union for `mem20controlz/src-tauri/src/lib.rs`

After merging #35 and then #36, the only thing that must survive from **both** sides in this file is the command registration. These are the literal three lines:

```rust
        .manage(Mutex::new(Backend::default()))
        .invoke_handler(tauri::generate_handler![
            probe_control_plane, start_backend, backend_status
        ])
```

The resulting `run()` in full — this is the exact text to commit:

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(Mutex::new(Backend::default()))
        .invoke_handler(tauri::generate_handler![
            probe_control_plane,
            start_backend,
            backend_status
        ])
        .run(tauri::generate_context!())
        .expect("error while running the mem20controlz desktop shell");
}
```

**Resolution rule for the whole file: take #36's side, not #35's.** #36's version is a strict superset — it carries #35's `ProbeReport`, `state_name`, and a *rewritten* `probe_control_plane` that prefers the owned sidecar port and falls back to the documented one. `git checkout --theirs` is correct here.

Do **not** instead try to keep both `probe_control_plane` definitions. They differ in signature (the #36 one takes `tauri::State<'_, Mutex<Backend>>`) and taking #35's would leave `Backend` unmanaged while `backend_status` still demands it.

### 2b. The literal union for `mem20controlz/src-tauri/mem20desktop/src/lib.rs`

The module block becomes the union — the two #36 lines are added, nothing from #35 is removed:

```rust
pub mod health;
pub mod http;
pub mod sidecar;

pub use health::{
    assess, parse_health_body, Assessment, ControlPlaneLiveness, HealthBody, HealthError,
    CONTROL_PLANE_SERVICE,
};
pub use http::{http_get, HttpError, Response};
pub use sidecar::{Endpoint, LaunchSpec, SidecarError, SidecarState};
```

And in the constants region, keep #35's constants, keep #36's doc note, and drop #37's duplicate `HEALTH_PATH` when #37 lands:

```rust
/// Where a locally installed control plane listens by default.
///
/// The systemd unit and `mem20controlz/README.md` both document `8890`; the
/// shell uses the same number so a desktop launch and a service launch are
/// describing the same thing.
///
/// Since #36 the sidecar prefers an ephemeral port and this is only the
/// fallback for attaching to an already-running service.
pub const DEFAULT_CONTROL_HOST: &str = "127.0.0.1";
pub const DEFAULT_CONTROL_PORT: u16 = 8890;

/// The unauthenticated liveness route. The only route the shell may call
/// before a session exists.
pub const HEALTH_PATH: &str = "/api/health";
```

### 2c. What #37 adds on top (step 3)

After #37, the module block gains two lines and one re-export, and `HEALTH_PATH` **must stay declared exactly once**:

```rust
pub mod health;
pub mod http;
pub mod poller;
pub mod sidecar;
pub mod tray;
```

#37's own `lib.rs` declares `HEALTH_PATH` at its line 31 and also declares `REGISTRY_PATH`. Since #35 already owns `HEALTH_PATH`, the merged file keeps #35's declaration and adds only:

```rust
/// The authenticated fleet route.
pub const REGISTRY_PATH: &str = "/api/registry";
```

---

## 3. Conflict map

### 3a. Files each branch touches (three-dot diff from the shared merge-base)

| File | #35 | #36 | #37 | Overlap |
|---|---|---|---|---|
| `mem20controlz/src-tauri/mem20desktop/src/lib.rs` | +46 | +51 | +34 | **all three** |
| `mem20controlz/src-tauri/src/lib.rs` | +101/−2 | +176/−1 | — | **#35 × #36** |
| `mem20controlz/src-tauri/mem20desktop/Cargo.toml` | +7 | — | +13 | **#35 × #37** |
| `mem20controlz/src-tauri/Cargo.toml` | +7 | — | — | none |
| `mem20controlz/src-tauri/tauri.conf.json` | +20 | — | — | none (#40 will collide here) |
| `mem20controlz/src-tauri/src/main.rs` | +12 | — | — | none |
| `mem20controlz/src-tauri/mem20desktop/src/health.rs` | +481 (new) | — | — | none |
| `mem20controlz/src-tauri/mem20desktop/src/http/mod.rs` | +323 (new) | — | — | none |
| `mem20controlz/src-tauri/mem20desktop/src/http/tests.rs` | +188 (new) | — | — | none |
| `mem20controlz/src-tauri/mem20desktop/src/sidecar.rs` | — | +407 (new) | — | none |
| `mem20controlz/src-tauri/mem20desktop/src/poller.rs` | — | — | +190 (new) | none |
| `mem20controlz/src-tauri/mem20desktop/src/tray.rs` | — | — | +918 (new) | none |
| `mem20controlz/src-tauri/src/tray_surface.rs` | — | — | +180 (new) | **orphan — see 3c** |
| `mem20controlz/docs/desktop.md` | +108 | — | — | none |
| `mem20controlz/package.json` | +11 | — | — | none |
| `mem20controlz/src-tauri/icons/*` | 2 new | — | — | none |
| `mem20controlz/mem20controlz/web/src/status.js` | — | — | +63 (new) | none |
| `mem20controlz/mem20controlz/web/test/status.test.js` | — | — | +87 (new) | none |
| `mem20controlz/mem20controlz/web/package.json` | — | — | +3 | none |

### 3b. Overlaps and their resolution

| # | Overlap | What actually happens | Resolution |
|---|---|---|---|
| 1 | `mem20desktop/src/lib.rs` — #35 × #36, **add/add** | Git reports `CONFLICT (add/add)` because both branches create the file from nothing at the merge-base. Three hunks: `pub mod sidecar;`, the `pub use sidecar::{...}` line, and #36's ephemeral-port doc note on `DEFAULT_CONTROL_PORT`. | **Union.** Keep every #35 module and re-export, add the two #36 lines verbatim (§2b). Accept #36's doc note. Nothing is deleted. |
| 2 | `src-tauri/src/lib.rs` — #35 × #36, content | `CONFLICT (content)`, 4 hunks: the crate doc-comment, the `summary` example string, the `ControlPlaneLiveness` match arms, and the whole body of `probe_control_plane` vs #36's `Backend` + `start_backend` + `backend_status`. | **Take #36 wholesale** (`git checkout --theirs`). #36 is a superset; its doc comment already claims both issues. Confirmed by inspection: #36 defines `report_from`, `Backend`, `start_backend`, `backend_status`, and all three `generate_handler!` entries. |
| 3 | `mem20desktop/Cargo.toml` — #35 × #37 | Different regions of the same `[dependencies]` table; git usually auto-merges. | Keep #35's set, apply #37's 13 added lines on top. **Check what they are:** this crate's design contract is "no Tauri types, no async runtime, no TLS". If #37 added a Tauri or async dependency here, push it back to the shell crate instead of accepting it. |
| 4 | `HEALTH_PATH` declared twice (#35 and #37) | Not a git conflict — a **compile error** (`E0428: the name HEALTH_PATH is defined multiple times`) once both land in one file. | Keep one declaration (#35's, with its doc comment). Add only `REGISTRY_PATH` from #37 (§2c). |
| 5 | `ControlPlaneLiveness` variant shapes | #35 uses `Unreachable { reason }`, `Foreign { service }`, `NotOk { reported }`; #36's match writes `L::Unreachable` and `L::Foreign` without fields. | Irrelevant once #36 is taken wholesale — its own `health.rs` is the same file #35 ships, and the compiled form is field-bearing. If you ever hand-merge instead of `--theirs`, you must use the braces form or it will not compile. |
| 6 | `tauri.conf.json` — reserved for #40 | #35 changes it 20 lines; #40 is expected to change bundle/signing blocks. | Not a conflict today (no #40 branch). When #40 lands, resolve by keeping #35's window config and layering #40's `bundle`/`updater` keys. |

### 3c. Defects this order exposes — fix, do not paper over

1. **`src-tauri/src/tray_surface.rs` is orphaned on #37.** `git grep tray_surface` on `feat/ws2-tray-notifications-37` finds **no `mod tray_surface;` declaration and no caller** of `install`, `apply`, or `load_muted` anywhere in `mem20controlz/src-tauri`. #37's `main.rs` is still the 2-line #35-era stub. **If #37 merges as-is, the tray compiles into nothing and the feature is silently absent.** Step 3 must therefore also add the declaration and the call:

   ```rust
   mod tray_surface;
   ```

   and, in `run()`, install it from `setup` (the function signature is `install<R: Runtime>(app: &AppHandle<R>, muted_at_startup: bool) -> tauri::Result<()>`, so it cannot be chained like a builder method):

   ```rust
   .setup(|app| {
       tray_surface::install(&app.handle(), tray_surface::load_muted(&app.handle()))?;
       Ok(())
   })
   ```

   Wire `tray_surface::apply(...)` to the poller's next tick in the same commit. **Acceptance for #37 is not "it merged" — it is `tray_surface` being reachable.**

2. **`#36` ships no `Cargo.toml` change of its own.** It depends on `serde`/`serde_json` for `ProbeReport` and on the `mem20desktop` path dependency, all of which #35 declares. So #36 is only buildable **on top of** #35 — further proof of the ordering, and a reason never to cherry-pick #36's `lib.rs` onto `main` alone.

---

## 4. Verification — one command per merge

Run these in order. Each step's command must pass **before** you start the next merge; a failure at step *n* is never fixed by step *n+1*.

### After #35

```bash
cargo test --manifest-path mem20controlz/src-tauri/mem20desktop/Cargo.toml
```

**Expected:** `test result: ok.` for the `health`, `http`, and `lib` unit tests — no failures, and in particular `default_probe_target_matches_the_documented_service_port` passes (`8890` / `127.0.0.1` / `/api/health`). This crate has no Tauri and no async runtime, so it runs headless with no WebView and no display.

### After #36

```bash
cargo check --manifest-path mem20controlz/src-tauri/Cargo.toml
```

**Expected:** `Finished` with `0 errors`. Zero unresolved `mem20desktop::*` symbols — that specific failure means the `pub mod sidecar;` union line is missing from `mem20desktop/src/lib.rs`. `warning:` lines are acceptable; `error[E0432]`/`E0433]` (unresolved import) are not.

### After #37

```bash
cargo test  --manifest-path mem20controlz/src-tauri/mem20desktop/Cargo.toml \
  && cargo check --manifest-path mem20controlz/src-tauri/Cargo.toml \
  && (cd mem20controlz/mem20controlz/web && npm test)
```

**Expected:** the `mem20desktop` suite still green (now including `tray` and `poller` table tests), `cargo check` still `Finished` with 0 errors, and the new `web/test/status.test.js` passing. A duplicate-`HEALTH_PATH` `E0428` here means §2c was applied as a copy instead of a merge.

Then, separately, prove the tray is actually reachable:

```bash
cargo check --manifest-path mem20controlz/src-tauri/Cargo.toml 2>&1 | grep -c "never used"
```

**Expected:** `0` — an orphaned `tray_surface` shows up as dead code, which is the defect in §3c and not an acceptable end state.

### After #40

```bash
cargo check --manifest-path mem20controlz/src-tauri/Cargo.toml && cargo tauri build --debug
```

**Expected:** `Finished` then a bundle under the configured `target/debug/bundle`. Anything requiring signing credentials may fail on a runner without them — record which artefacts are reproducible in CI and which need secrets, rather than marking the step green.

### Honest status of this verification

**These commands have not been run to green in the run that produced this document.** The container had no Rust toolchain; one was installed (`cargo 1.99.1`, `rustc 1.99.1`), the #35+#36 merge was resolved locally with the exact text in §2, and `cargo test` then failed at **dependency resolution**, not compilation:

```
error: no matching package named `serde_json` found
location searched: crates.io index
required by package `mem20desktop v0.1.0`
```

So the union in §2 is *conflict-resolved and marker-free* (verified by grep: zero `<<<<<<<` / `>>>>>>>` left under `mem20controlz/src-tauri/`), but **not yet compile-proven**. The next agent must run the four commands above on a machine with crate registry access and treat any failure as a real finding — not as a documentation problem.

---

## 5. One-paragraph handoff

Merge `#35` (`0eae4915`), resolve nothing — it is clean. Merge `#36` (`b7163284`); resolve `mem20desktop/src/lib.rs` as the union in §2b and take #36's `src-tauri/src/lib.rs` wholesale, then `cargo check` must print `Finished`. Merge `#37` (`201c8315`); keep a **single** `HEALTH_PATH`, add `REGISTRY_PATH`, declare `mod tray_surface;` and call `tray_surface::install(...)` from `setup` or the tray does not exist. Then `#40`, which has no branch yet. Do not merge #36 before #35, and do not accept "#37 is independent" — it edits the same crate file and collides on a constant.

---

## 6. Provenance

- Branch heads, three-dot diff-stats, merge-bases, and the ahead/behind counts: `git fetch origin` + `git rev-list --left-right --count` + `git diff --stat origin/main...origin/<branch>` against a full clone of `bythewayz66-glitch/mem20`.
- Conflict classes and hunk counts: an actual `git merge` simulation on a scratch branch seeded at `1264076698a00878acc3adacf7bf1d51eea315cc` — #35 fast-forwarded clean, #36 produced `CONFLICT (add/add)` on `mem20desktop/src/lib.rs` and `CONFLICT (content)` on `src-tauri/src/lib.rs`.
- `HEALTH_PATH` duplication and the orphaned `tray_surface.rs`: `git grep` / `git show <branch>:<path>` on the three heads.
- `main` HEAD and #117: `origin/main` after fetch.
