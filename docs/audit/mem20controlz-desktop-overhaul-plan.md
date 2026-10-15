# mem20controlz - Full Desktop Overhaul Plan

**Date:** 2026-10-15 - **Scope:** `mem20controlz/` @ `main`
**Standing rule:** *features are never removed - they are fixed or completed.* This plan **adds** a desktop shell around the existing control plane. The current web surface and every existing route stay exactly as they are.

---

## 1. Current state assessment

`mem20controlz` is the most mature of the three surfaces. Measured this session:

| Aspect | State | Evidence |
|---|---|---|
| Package import | OK - Clean | `import mem20controlz` -> `0.1.0` |
| Backend | OK - FastAPI, single origin | `app.py` 496 LOC; serves API **and** built frontend |
| API surface | OK - Rich and honest | 24 documented routes (auth, registry, CLI coverage, websites/DNS/Pages, dreams) |
| Frontend | OK - Built and shipped | Vite + React 18; **5 tabs** (Overview, Subsystems, Websites, Dreams, CliCoverage) + **10 views**; built bundle in `static/assets/` |
| Auth | OK - Deliberate, fail-closed | CF Access header (opt-in) + HMAC session cookie; secrets-file-wins precedence |
| Status honesty | OK - Documented invariant | `ok/degraded/unreachable/no-health/unknown`; `cached`/`age_s`/`stale` on every response |
| Tests | BROKEN - Do not collect | 3 modules `ERROR` (`ModuleNotFoundError: mem20ops`); `test_auth_app.py` -> **68 errors** |
| Packaging into a desktop app | ABSENT | No Tauri/Electron/PyInstaller/pywebview spec anywhere in the repo |
| Runtime deps | PARTIAL - Undeclared siblings | `pyproject.toml` depends on `mem20ops`, `mem20dreamz` (in-tree, not installed by the control plane's own install) |

**One-line verdict:** an excellent *service*, with no *app*. The backend already exposes everything a desktop client needs; what's missing is the shell, the packaging, and a testable install.

### What exists / is broken / is missing

- **Exists:** backend, API, auth, honest status registry, React UI, static build pipeline.
- **Broken:** the test suite (collection blocked by the sibling-import gap).
- **Missing:** a native window, an offline-capable desktop bundle, a signed installer, a tray/notification surface, and a reproducible dependency manifest.

---

## 2. Target architecture

```
+---------------------------- mem20controlz desktop ----------------------------+
|  Tauri 2 shell (Rust host + system WebView)                                   |
|    - window / tray / notifications / auto-update / deep links                |
|    - sidecar: bundled FastAPI (uvicorn) on 127.0.0.1:<ephemeral port>        |
|         - serves the SAME React bundle already in mem20controlz/static/      |
|                                                                              |
|  No divergent state: the desktop client is a thin WebView over the existing  |
|  same-origin API. Every current route is reused verbatim.                    |
+------------------------------------------------------------------------------+
```

**Why Tauri over Electron:** the repo already ships Vite + React; Tauri reuses that bundle untouched, produces a **~10-15 MB** installer instead of ~120 MB, uses the OS WebView (no second Chromium), and gives native tray/updater out of the box. Electron is the fallback only if the WebView proves too limiting.

**Sidecar model:** bundle the existing FastAPI app as a Tauri sidecar bound to **`127.0.0.1` on an ephemeral port** chosen by the shell, passed to the WebView as the API base. This keeps the current "one origin, no second web server to operate" property and avoids a fixed port colliding with a systemd install on the same host.

### UI/UX direction

The existing React app is a competent operations console. The overhaul is about making it feel like a **desktop control room**, not a new product:

1. **Shell chrome** - native title bar, menu (File / Fleet / View / Help), keyboard shortcuts, and a **system tray** with a fleet-health glyph driven by `/api/registry`.
2. **Native notifications** - a desktop toast when a subsystem flips to `unreachable`/`degraded`, reusing the registry's own `stale`/`age_s` semantics so a cached panel never raises a false alarm.
3. **Command palette (Cmd-K)** - jump to any subsystem panel, run a CLI audit, or open a dream lineage without touching the mouse.
4. **Offline & degraded states** - an explicit banner when the sidecar is starting or the store is unreachable, echoing the backend's honesty vocabulary rather than a spinner.
5. **Density + theming** - the current dark palette, plus per-panel density and a "compact fleet" layout for >100 subsystems.

---

## 3. Work items

| ID | Work item | Labels | Prereq |
|---|---|---|---|
| C1 | **Make the test suite collect and pass**: install/resolve `mem20ops` + `mem20dreamz` for the control plane (declare them as dev/test deps), then get `test_auth_app.py` + `test_registry.py` + `test_dreams.py` + `test_websites.py` green | `bug`, `tech-debt`, `severity:high` | - |
| C2 | **Declare runtime + test dependencies** in `mem20controlz/pyproject.toml` so `pip install -e .[dev]` is reproducible (fastapi, uvicorn, httpx, pyyaml, pytest) | `tooling`, `severity:medium` | - |
| C3 | **Scaffold the Tauri desktop shell**: `src-tauri/`, window config, dev/build scripts, reusing the existing `web/` bundle | `tooling`, `enhancement`, `severity:high` | C2 |
| C4 | **Bundle the FastAPI app as a Tauri sidecar** on an ephemeral loopback port; pass the base URL to the WebView | `tooling`, `severity:high` | C3 |
| C5 | **System tray + fleet-health glyph + native notifications** wired to `/api/registry` (honour `stale`/`age_s`) | `enhancement`, `severity:medium` | C4 |
| C6 | **Command palette (Cmd-K)** over subsystem panels, CLI audit and dream lineages | `enhancement`, `severity:medium` | C3 |
| C7 | **Desktop packaging & signing**: produce `.dmg`/`.msi`/`.AppImage`, code-sign, wire the Tauri updater | `tooling`, `security`, `severity:high` | C4 |
| C8 | **Offline/degraded UX pass**: explicit starting/unreachable/store-missing states using the backend's existing status vocabulary | `enhancement`, `severity:medium` | C4 |
| C9 | **Docs**: a `docs/desktop.md` covering build, run, packaging and the sidecar contract; update `mem20controlz/README.md` (currently advertises a 165-test suite) | `documentation`, `severity:medium` | C1, C7 |

### Missing code that must be written

- `mem20controlz/src-tauri/` - Rust host, `tauri.conf.json`, sidecar spawn/health-wait, port handshake.
- `mem20controlz/src-tauri/src/tray.rs` - tray icon + health polling.
- A `desktop` CLI verb (`python -m mem20controlz desktop --dev|--build`).
- A test-dependency extra (`[project.optional-dependencies].dev`) resolving the two sibling subsystems.

---

## 4. Acceptance for the overhaul

1. `pytest tests` in `mem20controlz` collects and passes with no manual installs.
2. `npm run desktop:dev` opens a native window showing the live control plane.
3. `npm run desktop:build` emits a platform installer < 60 MB.
4. Killing the sidecar surfaces an explicit "backend unreachable" state - never a blank panel.
5. Every existing API route and UI tab is reachable from the desktop shell, unchanged.
