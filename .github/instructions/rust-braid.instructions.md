---
applyTo: "braid/**"
---

# Rust `braid` workspace rules

`braid/` is a Cargo workspace: `braid_core`, `braid_drive`, `braid_her`,
`braid_keys`, `braid_sonic`, `braid_ui_bridge`, `braid_cli`.

- **Commit `Cargo.lock` for the braid workspace** (CONTRIBUTING issue #20). CI
  runs `cargo test --locked` when the lockfile is present.
- Standard edition/toolchain: stable (`dtolnay/rust-toolchain@stable` in CI).
- Check with `cargo check --manifest-path braid/Cargo.toml`; test with
  `cargo test --manifest-path braid/Cargo.toml`.
- `braid_core` holds the append-only cryptographic ledger. Changes there affect
  audit guarantees — add a test in `braid_core/tests/` for any behaviour change.
- Do not add a new crate unless the functionality genuinely does not belong in an
  existing one; the workspace is already split along clear lines.
- Keep `Cargo.toml` dependency versions consistent across the workspace.
