# PyO3 bindings for `braid_core` — `braid_python/`

Python extension module exposing the Rust `braid_core` engine (Ed25519 + BLAKE3
braided log, capability/policy evaluation, proven-node gate) to Python callers.

**3 tracked file(s).**

## Contents

- `Cargo.toml` — crate manifest, depends on `braid_core`
- `src/lib.rs` — the `pyo3` module: engine, capability, policy, and `node_is_proven` bindings
- `tests/prove_gate.rs` — Rust-side test of the proof gate

## Usage

```bash
cd braid_python && cargo test
```

## Notes

The Rust crate `braid/` is the source of truth for behaviour; this crate is a
binding layer and must not re-implement policy logic.

---

Part of the [mem20 monorepo](../README.md). See [`docs/INDEX.md`](../docs/INDEX.md) for the full documentation map.
