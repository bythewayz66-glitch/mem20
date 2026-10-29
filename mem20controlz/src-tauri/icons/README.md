# src-tauri/icons — reproducible bundle icon set

Tauri's bundler embeds a platform icon into the app binary and every
installer. The PNG, ICNS, and ICO inputs are committed so Linux, macOS, and
Windows release jobs all use the same control-plane mark.

## Generate them

From the repository root:

```bash
python3 mem20controlz/src-tauri/icons/generate_icons.py
npm --prefix mem20controlz/mem20controlz/web exec tauri icon \
  mem20controlz/src-tauri/icons/icon.png \
  --output mem20controlz/src-tauri/icons
```

The generated binaries are build inputs, not build outputs, and are committed
with the application configuration. The base `tauri.conf.json` lists the
shared PNG, ICNS, and ICO inputs; platform overlays do not replace that list.
