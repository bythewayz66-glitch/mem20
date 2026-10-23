# Spec authority paths (issues #14 / #15)

## Rule
Do not use `/opt/mem20/...` (or any personal absolute path) as a **required**
default. Defaults must be:
- relative to the repo / package, or
- `Path.home()`-based with an env override, or
- fail fast with a clear message when unset.

## Spec inputs
Commit canonical copies under `specs/` when a pipeline needs fixed inputs.
Override with `MEM20_SPEC_SOURCE` for local layouts.

## Env overrides
| Variable | Purpose |
|----------|--------|
| `MEM20_ENGINE_PATH` | Cognitive engine / repo root override |
| `MEM20_SPEC_SOURCE` | Spec authority directory |
| `UNITY_EDITOR` | Unity editor binary |
| `MEM20_STORE_PATH` | Memory store path |
