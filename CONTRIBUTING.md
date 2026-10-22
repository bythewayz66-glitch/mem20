# Contributing to mem20

mem20 is a large multi-package Python monorepo (1,700+ modules across many
`mem20*z` packages). Small, verifiable changes beat large clever ones.

## Before you start

- **Python >= 3.10** (see `pyproject.toml`). CI runs 3.11.
- **Check out with symlinks enabled.** `git config --get core.symlinks` must
  return `true`. A checkout without symlink support wedges `git status` on the
  model-cache paths and is the most common cause of a "broken tree".
- **Never commit generated output:** `build/`, `__pycache__/`, `node_modules/`,
  `*.faiss`, `ledger.jsonl`, `entries/*.json`, HuggingFace caches. They are in
  `.gitignore` for a reason; run `git status` before every commit.
- **Optional but recommended:** `pip install pre-commit && pre-commit install`
  (see `.pre-commit-config.yaml` — issue #23).

## Working on a change

1. Branch from `main`: `fix/<topic>`, `feat/<topic>`, or `docs/<topic>`.
2. Keep the change small and scoped to one package where possible.
3. Verify:

   ```bash
   python3 -m compileall -q <paths you touched>
   pip install -e '.[dev]'   # provides pytest
   python3 -m pytest <package> -q
   # markers (issue #5 / #18):
   #   pytest -m unit          # CI-safe, no optional native deps
   #   pytest -m integration   # needs torch/blender/network as applicable
   ```

   A bare `pytest` runs the whole estate; the top-level `test/` scratch dir is
   excluded via `norecursedirs` so it cannot break collection (issue #18).
4. Open a PR and fill in `.github/PULL_REQUEST_TEMPLATE.md`.

## Rust (`braid/`)

- Commit `Cargo.lock` for the braid workspace (issue #20). CI runs
  `cargo check` / `cargo test` on `braid/` (issue #21).

## What gets a PR rejected

- A file that fails `python3 -m compileall`.
- Committed build artefacts, runtime state, or `.pyc` / `__pycache__`.
- A moved entry point (e.g. `mcp/mcp_server.py`, a systemd `ExecStart` target)
  without updating the unit file and the docs that reference it.
- Docs that contradict the code. If you change tool counts, ports, or versions,
  grep the affected `README.md` / `docs/` files **in the same PR**.

## Reporting bugs and proposing features

Use the issue forms in `.github/ISSUE_TEMPLATE/`. Every issue should carry a
`severity:*` label and, where known, a component label (`mcp`, `ci`, `tooling`,
`tech-debt`, `security`).

## Security

Do **not** open a public issue for a vulnerability. See `SECURITY.md`.

## Working as an agent

If you are an AI agent (Teamily, Hermes, OpenCode), read
`docs/handoff/AGENT-OPERATING-PROTOCOL.md` **before** touching a file, and claim
your work in `docs/handoff/claims/`. One writer per file at a time.
