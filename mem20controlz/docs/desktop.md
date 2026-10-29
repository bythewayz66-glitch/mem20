# mem20controlz desktop shell (issues #35 / #40)

The native window for the control plane. Tauri 2 reuses the existing React
console as-is—**no UI rewrite**.

## Scaffold (#35)

```
mem20controlz/
├── package.json          # desktop:dev / desktop:build / web:build
├── src-tauri/
│   ├── Cargo.toml        # the Tauri app crate (thin glue)
│   ├── tauri.conf.json   # window, CSP, bundle targets
│   ├── icons/            # bundle icons + generate_icons.py
│   ├── src/
│   │   ├── main.rs       # calls mem20controlz_desktop_lib::run()
│   │   ├── lib.rs        # window + `probe_control_plane` command
│   │   └── mem20desktop/ # decision logic; no Tauri, fully unit-tested
│   └── ...
└── mem20controlz/static/ # `npm run web:build` output
```

## Run it

### Dev

1. Install Tauri prerequisites (Rust stable, system WebView).
2. From `mem20controlz/mem20controlz/web`, run `npm ci`.
3. Run `npm run desktop:dev`. Tauri starts Vite on `127.0.0.1:5173` and opens
   the existing React application in a native window.

### Build

From `mem20controlz/mem20controlz/web`, run `npm run desktop:build`. The
`beforeBuildCommand` produces the same `mem20controlz/static/` bundle used by
FastAPI, so the web serve path remains unchanged. The command emits the
platform bundle and the signed updater artifact when
`TAURI_SIGNING_PRIVATE_KEY` is present.

Prerequisites: Rust stable, and the WebKit/GTK development packages for your
platform (`libwebkit2gtk-4.1-dev libgtk-3-dev librsvg2-dev` on Debian/Ubuntu).

```bash
# from mem20controlz/
npm install
npm run web:build
python3 -m mem20controlz --host 127.0.0.1 --port 8890 &
npm run desktop:dev
```

`desktop:dev` starts the bundled backend sidecar and waits for its health
endpoint before loading the console. If startup fails, the window still opens
and renders the console's degraded state.

`npm run desktop:build` produces the platform bundle. The release workflow
`.github/workflows/controlz-desktop.yml` builds Linux AppImage/deb, Windows
MSI/NSIS, and macOS DMG artifacts, signs updater payloads, and publishes the
GitHub Release `latest.json` consumed by existing installations.

Release setup requires these GitHub Actions secrets:

- `TAURI_SIGNING_PRIVATE_KEY` and optional `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`
  for the updater key whose public half is committed in `tauri.conf.json`.
- `APPLE_CERTIFICATE`, `APPLE_CERTIFICATE_PASSWORD`, and `KEYCHAIN_PASSWORD`
  for macOS signing.
- `WINDOWS_CERTIFICATE` and `WINDOWS_CERTIFICATE_PASSWORD` for Authenticode.

Create a release by pushing a `controlz-v<version>` tag matching the Tauri
version, such as `controlz-v0.1.0`. The workflow keeps the GitHub Release as a
draft until its assets and signatures are reviewed.

## The decision logic is a separate crate

`src-tauri/mem20desktop/` has no Tauri dependency and no async runtime, so
`cargo test` runs without a WebView, display or network:

```bash
npm run desktop:core:test
```

It owns identity, liveness-vs-health vocabulary, and freshness. The
`probe_control_plane` Tauri command is the only bridge and returns
`{state, up, needs_attention, age_s, stale, summary, probed_url}`. Transport is
a small loopback HTTP/1.1 GET with separate connect/read budgets; HTTPS is
rejected explicitly and non-2xx responses remain inspectable responses.

## Implemented desktop scope

| Issue | Scope | Status here |
|---|---|---|
| #36 | FastAPI sidecar, ephemeral port, lifecycle | **implemented** |
| #37 | Tray, fleet-health glyph, notifications | **implemented** |
| #40 | Installers, code-signing, auto-update | **implemented** |

No placeholder tray/notification code is committed: an unimplemented feature
that looks implemented is worse than an absent one.

## Known limitation of local verification

`cargo check --all-targets` and the core Rust tests are the appropriate
headless checks. A full GUI build requires normal disk headroom and platform
WebView dependencies; the release workflow supplies those dependencies on each
target runner.
