# mem20controlz desktop shell (issue #35)

The native window for the control plane. Tauri 2, reusing the existing React
console as-is -- **no UI rewrite**.

```
mem20controlz/
├── package.json          # desktop:dev / desktop:build / web:build
├── src-tauri/
│   ├── Cargo.toml        # the Tauri app crate (thin glue)
│   ├── tauri.conf.json   # window, CSP, bundle targets
│   ├── icons/            # bundle icons + generate_icons.py
│   ├── src/
│   │   ├── main.rs       # calls mem20controlz_desktop_lib::run()
│   │   └── lib.rs        # window + `probe_control_plane` command
│   └── mem20desktop/     # decision logic; no Tauri, fully unit-tested
└── mem20controlz/static/ # `npm run web:build` output -- what the window loads
```

## Run it

Prerequisites: Rust stable, and the WebKit/GTK dev packages for your platform
(`libwebkit2gtk-4.1-dev libgtk-3-dev librsvg2-dev` on Debian/Ubuntu).

```bash
# from mem20controlz/
npm install                 # @tauri-apps/cli
npm run web:build           # vite -> mem20controlz/static/
python3 -m mem20controlz --host 127.0.0.1 --port 8890 &   # backend, separately
npm run desktop:dev         # native window over the built bundle
```

`desktop:dev` needs the backend already running: issue #35 is the shell only,
and **spawning the backend is issue #36**. If nothing is listening on 8890 the
window still opens; it just renders the console's own signed-out/degraded state
rather than live data.

`npm run desktop:build` produces the platform bundle. Signing, installers and
the update channel are issue #40.

## The decision logic is a separate crate, on purpose

`src-tauri/mem20desktop/` has **no Tauri dependency** and no async runtime, so
`cargo test` runs it on a machine with no WebView, no display and no network:

```bash
npm run desktop:core:test    # 28 tests, ~2 s
```

It owns the three things in this issue that can actually be wrong:

1. **Identity.** `GET /api/health` is unauthenticated and its `status` is a
   hard-coded `"ok"`, so the body proves only that *something* answered. The
   shell therefore checks `service == "mem20-control"` **before** it looks at
   `status`. A dev server, a proxy or a stale build that answers
   `{"status":"ok"}` is reported as `foreign`, not as a healthy control plane.
2. **Liveness vs. health.** The verdict vocabulary is
   `unknown | starting | up | not-ok | foreign | unreachable` -- deliberately not
   the fleet-panel vocabulary (`ok/degraded/unreachable/no-health/unknown`),
   because reusing those words for one process invites reading "up" as "the
   fleet is fine". Fleet health is `/api/registry`, and belongs to #37.
3. **Freshness.** Every verdict carries `age_s` and `stale` in the type, so a
   cached reading cannot be rendered as a live one.

The `probe_control_plane` Tauri command is the only bridge: it calls that crate
and returns `{state, up, needs_attention, age_s, stale, summary, probed_url}`.
`summary` is rendered in Rust so the status strip and any future tray tooltip
cannot drift apart.

Transport is a small `std::net` HTTP/1.1 GET rather than a full client: the
shell asks one question of one loopback port, and `https` is rejected by name
with a readable reason instead of failing obscurely. Connect and read budgets
are separate (2 s / 5 s) because "nothing is listening" and "it accepted and
then wedged" need different remedies. Non-2xx statuses are returned as
responses, not turned into transport errors.

## What this branch does not do

| Issue | Scope | Status here |
|---|---|---|
| #36 | FastAPI sidecar, ephemeral port, lifecycle | **not implemented** -- `probe_control_plane(port)` already takes a port, so #36 only changes the caller |
| #37 | Tray, fleet-health glyph, notifications | **not implemented** -- contract in `docs/ux/issue-37-tray-and-notifications.md` |
| #40 | Installers, code-signing, auto-update | **not implemented** -- bundle targets are configured, signing is not |

No `tauri-plugin-*` dependencies are declared for those, and no placeholder
tray/notification code is committed: an unimplemented feature that looks
implemented is worse than an absent one.

## Known limitation of this scaffold

`cargo check --all-targets` passes (exit 0) and `cargo test` passes 28/28, but
a full `cargo build` of the GUI binary was not completed in the authoring
sandbox -- the build aborted with `No space left on device` partway through
transitive dependencies (`x11-dl`), not on an error in this code. The first
full build on a machine with normal disk headroom is the real end-to-end check
and should be run before this is called done.
