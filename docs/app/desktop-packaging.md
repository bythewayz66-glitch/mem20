# mem20controlz — desktop packaging, code-signing and auto-update (#40)

Status of the **desktop distribution** layer: which installer artefacts CI can
actually reproduce from this repository, and which require signing material that
is **not** in this repository and **not** available to the agents that wrote this
file.

Read this before quoting any download to a user. An artefact that exists but is
unsigned is not the same product as a signed, notarized one, and the tables below
do not conflate them. **No signed build exists. No `cargo tauri build` has been
run against this branch** — see §3.

Upstream context: the Tauri 2 shell scaffold is issue #35
(`mem20controlz/docs/desktop.md`); the loopback sidecar is #36; tray presence is
#37. This document covers only packaging, signing and the update channel.

Baseline: rebased onto `main` @ `45445f4850377814cd95b7fa50c0a9153f76c163`.
`mem20controlz/` is byte-identical between this branch's original base
(`b9de9aa8`) and `45445f48`, so the merge validation in §2 was re-run against the
current base tree, not carried over.

---

## 1. What was added

Six files exist for this issue. The four configs are **overlays**: Tauri 2 merges
a platform config over the base config at build time, so none of them edits
`mem20controlz/src-tauri/tauri.conf.json`. That keeps this branch textually
independent of #35 / #36 / #37, all of which edit the base config or
`src/lib.rs`.

| File | Kind | What it sets |
|---|---|---|
| `mem20controlz/src-tauri/tauri.macos.conf.json` | platform overlay | `bundle.targets` = `app`, `dmg`; `bundle.macOS.minimumSystemVersion` 10.15; `hardenedRuntime: true`; a 660×400 DMG window with fixed icon positions |
| `mem20controlz/src-tauri/tauri.windows.conf.json` | platform overlay | `bundle.targets` = `msi`, `nsis`; WebView2 `downloadBootstrapper`; NSIS `installMode: both` (per-user and per-machine), `lzma` compression; WiX `en-US` |
| `mem20controlz/src-tauri/tauri.linux.conf.json` | platform overlay | `bundle.targets` = `deb`, `appimage`; `category: DeveloperTool`; deb depends on `libwebkit2gtk-4.1-0` and `libgtk-3-0`; AppImage does not bundle a media framework |
| `mem20controlz/src-tauri/tauri.updater.conf.json` | opt-in overlay | `bundle.createUpdaterArtifacts: false`; `plugins.updater` block with the GitHub Releases `latest.json` endpoint, `dialog: true`, `active: false`, and an **empty** `pubkey` |
| `mem20controlz/src-tauri/icons/README.md` | placeholder + instructions | names the exact icon files the bundler needs and the one command that generates them; see §2.1 |
| `docs/app/desktop-packaging.md` | this document | the reproducibility and credential matrix |

The overlays deliberately do **not** set `bundle.icon`. The icon list lives in
the base config so a single owner (the #35 scaffold) controls it; an overlay that
re-declared icon paths would silently override it and break the moment the two
lists diverged.

---

## 2. Verification performed — and its two limits

### 2.1 Schema validation (done, re-run against the current base)

Each overlay was deep-merged over `tauri.conf.json` as it exists on
`main` @ `45445f48`, and validated against the published Tauri v2 JSON schema
(`https://schema.tauri.app/config/2`, snapshot 172,879 bytes) with
`jsonschema.Draft7Validator` (jsonschema 4.26.0). All four merged documents are
**schema-valid**, and the merge produces the intended fields:

```
tauri.macos.conf.json        VALID  targets=['app', 'dmg']
    macOS keys: ['dmg', 'hardenedRuntime', 'minimumSystemVersion']
tauri.windows.conf.json      VALID  targets=['msi', 'nsis']
tauri.linux.conf.json        VALID  targets=['deb', 'appimage']
    category: DeveloperTool | deb.depends: ['libwebkit2gtk-4.1-0', 'libgtk-3-0']
tauri.updater.conf.json      VALID  targets=all
    updater active=False pubkey='' createUpdaterArtifacts=False
```

### 2.2 Limit one — no build was performed

There is no Rust toolchain, no `cargo-tauri` and no cross-platform SDK in the
environment where this was written (`cargo: command not found`). **No installer
was produced and no `cargo tauri build` was executed.** The first real compile
happens in CI (§3). Schema validity proves the config is well-formed; it proves
nothing about whether the bundler succeeds.

### 2.3 Limit two — the icon set is missing, which blocks two of the six targets

This is the finding that matters most in this document, and it was *not* visible
from the config alone:

* `mem20controlz/src-tauri/tauri.conf.json` on `main` @ `45445f48` declares
  `"bundle": { "icon": [] }` — an **empty** icon array.
* There are **no icon assets in the repository at all**. A tree-wide search for
  `icons/`, `*.icns` and `*.ico` finds exactly one match, and it is unrelated
  (`mem20officez/src_harvest/src/app/favicon.ico`).

Tauri's bundler embeds platform icons into the app binary and the installers:
`icon.icns` for macOS, `icon.ico` for Windows, PNGs for Linux. With an empty
array and no files on disk there is nothing to embed. Tauri's documentation and
its issue tracker both describe the macOS bundle as **failing** when `icon.icns`
cannot be resolved.

**I could not test this**, because of limit one. So it is recorded as a
**precondition, unverified**: it is highly likely that `dmg`, `msi` and `nsis`
fail at the icon stage today, and that `app` produces an icon-less bundle. The
`deb` and `appimage` targets are the least likely to be affected.

The fix is one command, run from `mem20controlz/src-tauri/` against a
1024×1024 RGBA source image, and belongs to the #35 scaffold owner because it
writes into the base config:

```
cargo tauri icon path/to/app-icon.png     # writes icons/32x32.png, 128x128.png,
                                          # 128x128@2x.png, icon.icns, icon.ico
```

then set `bundle.icon` to the five generated paths. `icons/README.md` in this
branch records that, so the gap is one step from closed rather than
rediscovered. **I did not write the icon binaries**: nothing in this environment
can produce a valid `.icns`/`.ico` pair, and a hand-rolled binary that fails to
embed is worse than a documented gap.

---

## 3. Reproducibility matrix — what CI can produce

"Reproducible" means: given the same commit, a hosted runner rebuilds the
artefact with no secret material, and the result installs on the target OS.

| Target | OS | Reproducible in CI now? | Signed? | Notarized? | Notes |
|---|---|---|---|---|---|
| `deb` | Linux x86_64 | **Yes** | No | n/a | `depends` resolves against the distro's WebKitGTK 4.1. Trust surface is the checksum, not a signature. |
| `appimage` | Linux x86_64 | **Yes** | No | n/a | Self-contained. Same trust surface. |
| `app` (`.app` bundle) | macOS | **Only after the icon set lands** (§2.3) | No | No | Builds; Gatekeeper quarantines it on download. Intermediate artefact, not a deliverable. |
| `dmg` | macOS | **Only after the icon set lands** (§2.3) | **No** | **No** | The `.dmg` container itself needs no Apple credentials. A *signed* or *notarized* `.dmg` needs §4.1 and is **not** producible here. |
| `msi` | Windows x64 | **Only after the icon set lands** (§2.3) | **No** | n/a | WiX bundle. SmartScreen warns on first run. |
| `nsis` (`.exe`) | Windows x64 | **Only after the icon set lands** (§2.3) | **No** | n/a | Same. `installMode: both` is what lets a user install without admin. |
| updater signature (`.sig`) | all | **No** — needs credentials (§4.3) | — | — | Requires the Tauri minisign keypair. |

So the honest count is: **two artefacts reproducible today, six once the icon set
exists, and zero that are signed.**

### The CI shape, when it is time to add it

| Runner | Command | Artefacts |
|---|---|---|
| `ubuntu-22.04` | `cargo tauri build --config tauri.linux.conf.json` | `*.deb`, `*.AppImage` |
| `macos-latest` | `cargo tauri build --config tauri.macos.conf.json --target aarch64-apple-darwin` (and `x86_64-apple-darwin`) | `mem20controlz.app`, `*.dmg` |
| `windows-latest` | `cargo tauri build --config tauri.windows.conf.json` | `*.msi`, `*-setup.exe` |

Linux needs `libwebkit2gtk-4.1-dev`, `libappindicator3-dev`, `librsvg2-dev` and
`patchelf` on the runner before the build. Rust needs the two
`*-apple-darwin` targets added for the macOS matrix entries.

**Do not add this workflow to the default branch yet.** Two reasons: `src/lib.rs`
does not compile standalone until #36 is fixed (recorded as a roster defect in
`docs/ops/workload-roster-2026-10-27.md`), and the icon set in §2.3 above is
missing. A packaging workflow on `main` today would fail on every push for
reasons unrelated to packaging, which trains people to ignore it.

If a workflow is added, it must publish **unsigned** artefacts explicitly
labelled as such — never a `latest` release that a user could mistake for a
signed build. That is the failure mode this document exists to prevent.

---

## 4. What is blocked, and on exactly what

Each row is one credential that must be supplied by the repository owner. None of
these are present in this repository, in the CI secrets, or in the environment
where this document was written. **No signed build exists.**

### 4.1 macOS — Developer ID signing + notarization

Needs a paid Apple Developer Program membership and all of:

| Secret | Content |
|---|---|
| `APPLE_CERTIFICATE` | base64 of the exported Developer ID Application `.p12` |
| `APPLE_CERTIFICATE_PASSWORD` | password set when exporting that `.p12` |
| `APPLE_SIGNING_IDENTITY` | e.g. `Developer ID Application: <legal name> (TEAMID)` |
| `APPLE_TEAM_ID` | 10-character team identifier |
| `APPLE_ID` + `APPLE_PASSWORD` | Apple ID and an **app-specific** password, for notarization |
| *or* `APPLE_API_KEY` + `APPLE_API_ISSUER` | App Store Connect API key, the preferred alternative |

`bundle.macOS.hardenedRuntime` is already `true` in the overlay because
notarization rejects a non-hardened binary — but hardened runtime without a
signing identity does not make the build notarized. A hardened, unsigned binary
is still an unsigned binary.

Owner action: export the certificate once, add the six (or five) secrets, then
the same `cargo tauri build` on `macos-latest` signs and notarizes with no config
change.

### 4.2 Windows — code-signing certificate

Needs one of:

* an OV/EV code-signing certificate with its private key, imported into the
  runner's certificate store, with `bundle.windows.certificateThumbprint` set to
  its thumbprint and `bundle.windows.digestAlgorithm` set to `sha256`; or
* a cloud HSM / eSigner-style service, wired in through
  `bundle.windows.signCommand` with `%1` as the file placeholder, e.g.
  `artifact-signing-cli -e <endpoint> -a <account> -c <profile> -d mem20controlz %1`.

Tauri calls `signCommand` for the main binary, the NSIS plugins and the final
installers, so a cloud signer needs enough quota for several calls per build.

SmartScreen reputation accrues to the certificate, not to the file — expect
warnings on the first releases even once signed, unless the certificate is EV.

### 4.3 Auto-update — Tauri minisign keypair

`tauri.updater.conf.json` ships **`active: false` and an empty `pubkey`**. That is
deliberate: an updater endpoint with no public key cannot verify a payload, and
an `active: true` block with a placeholder key would be a config that looks
shipped but cannot possibly update — worse than an honest off switch.

To enable, in this order:

1. Generate the keypair once, offline: `cargo tauri signer generate -w mem20controlz.key`.
2. Put the **private** key in `TAURI_SIGNING_PRIVATE_KEY` and its password in
   `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` as CI secrets. Never commit either.
3. Paste the **public** key (`mem20controlz.key.pub`) into `plugins.updater.pubkey`
   and flip `active` to `true`.
4. Flip `bundle.createUpdaterArtifacts` to `true` so the bundler emits `.sig`
   files alongside each artefact.
5. Publish a `latest.json` manifest next to the release assets at the endpoint
   already configured:
   `https://github.com/bythewayz66-glitch/mem20/releases/latest/download/latest.json`
   containing, per platform, the `url`, `signature` and `version`.
6. Add the `updater:default` permission to the app's capability set, or the
   window cannot call `check()` / `install()`.

Endpoint templating (`{{current_version}}`, `{{target}}`, `{{arch}}`) is available
if the static manifest is replaced by a dynamic one later.

**Losing the private key means every installed copy is stranded** — it can never
verify a future release. Back it up outside the repository before step 2.

---

## 5. Summary

* **Bundle targets added:** `dmg` (+ `.app`) on macOS, `msi` + `nsis` on Windows,
  `deb` + `appimage` on Linux — as three platform overlays that do not touch the
  shared base config.
* **Updater config added:** a complete `plugins.updater` block, present but
  switched **off** (`active: false`, empty `pubkey`), with the endpoint and
  Windows install mode already correct.
* **Reproducible in CI, no credentials:** `deb` and `appimage` today; `.app`,
  `dmg`, `msi` and `nsis` once the icon set from §2.3 exists — all six unsigned.
* **Needs credentials I do not have:** any signed macOS build, any notarized
  build, any signed Windows build, and any updater signature.
* **Not verified here:** a successful `cargo tauri build`. No Rust toolchain
  existed in the environment that wrote this; the configs are schema-validated,
  the compile is CI's first job.
* **Misleading if quoted out of context:** the phrase "six installers build".
  Two build today; four are waiting on one icon set; none are signed.
