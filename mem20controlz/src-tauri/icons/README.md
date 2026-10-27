# src-tauri/icons — required icon set (currently MISSING)

`tauri.conf.json` on `main` declares `"bundle": { "icon": [] }`, and no icon
files exist anywhere in the repository. Tauri's bundler embeds a platform icon
into the app binary **and** into every installer, so an empty icon list is a
packaging gap, not a cosmetic one.

See `docs/app/desktop-packaging.md` §2.3 for the analysis. It is recorded as an
**unverified precondition**: there is no Rust toolchain in the environment where
#40 was written, so the failure could not be reproduced — but it is expected to
block `dmg`, `msi` and `nsis`.

## Generate them

From `mem20controlz/src-tauri/`, against a 1024×1024 RGBA PNG source:

```sh
cargo tauri icon path/to/app-icon.png
```

That writes the five files Tauri expects:

```
icons/32x32.png
icons/128x128.png
icons/128x128@2x.png
icons/icon.icns      # macOS
icons/icon.ico       # Windows — 16/24/32/48/64/256 layers, 32px layer first
```

## Then wire them up

The icon list belongs in the **base** config (`tauri.conf.json`), not in the
`tauri.<platform>.conf.json` overlays — the #35 scaffold owns that file, and an
overlay that re-declared the list would silently override it.

```json
"bundle": {
  "icon": [
    "icons/32x32.png",
    "icons/128x128.png",
    "icons/128x128@2x.png",
    "icons/icon.icns",
    "icons/icon.ico"
  ]
}
```

Commit the generated binaries. They are build inputs, not build outputs.

## Why this file is a README and not the icons

Producing a valid `.icns` and `.ico` pair requires platform tooling (`iconutil`
on macOS, an ICO writer with the six required layers) that is not available in
the #40 environment, and a malformed binary that fails to embed is worse than a
documented gap. The placeholder names the exact gap and the one command that
closes it so it is not rediscovered later.
