# mem20officez/src_harvest (issue #24)

## Status

`mem20officez/src_harvest/` is a **vendored first-class tree** committed into the
monorepo. It is not a git submodule. Nested `.github/workflows/` under this path
are **not executed** by GitHub (only root workflows run).

## Decision

- **Keep** the directory (standing rule: do not remove functionality).
- Treat it as vendored / harvested source owned by the mem20 monorepo.
- Root CI and Dependabot do not inherit nested workflow configs.
- Licence/provenance: follow the parent `mem20officez` package licence unless a
  file-level notice says otherwise.

## Follow-ups

- Prefer root workflows for any automation that must run on this tree.
- Optional: strip nested `.github/workflows` if they cause confusion (content can
  be moved to root under a distinct job name).
