# mem20controlz desktop shell (issues #35 / #40)

## Scaffold (#35)
Tauri 2 shell lives under `src-tauri/`. It reuses the existing static/React
bundle under `mem20controlz/static/` (or `mem20controlz/web` build output).

### Dev
1. Install Tauri prerequisites (Rust stable, system WebView).
2. Ensure the web UI is built into the frontend dist path in `tauri.conf.json`.
3. `cd src-tauri && cargo tauri dev`

### Build
`cd src-tauri && cargo tauri build`

## Packaging (#40)
Full platform installers (`.dmg` / `.msi` / `.AppImage`), code-signing, and the
Tauri updater channel are **follow-on work**: they require platform certs and
release infrastructure not stored in this repo.

Until then:
- `cargo tauri build` produces unsigned artifacts for local testing.
- Sidecar wiring (ephemeral FastAPI on loopback) is issue #36.
