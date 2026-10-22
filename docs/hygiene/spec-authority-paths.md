# Spec authority paths (issues #14 / #15)

## Rule
No personal absolute path (`/home/jayson/...`) as a required default.

Use:
- paths under `specs/` in-repo, or
- `Path.home()` / env overrides, or
- fail with a clear message.

## Env
| Variable | Purpose |
|----------|--------|
| `MEM20_ENGINE_PATH` | Repo / engine root |
| `MEM20_SPEC_SOURCE` | Spec authority directory (default `specs`) |
| `UNITY_EDITOR` | Unity editor binary |
| `MEM20_STORE_PATH` | Memory store |
| `MEM20_PACKAGE` | owebz package path |
| `MEM20_OWEBZ_ROOT` / `MEM20_OWEBZ_ART` | Project roots |
| `MEM20_AUDIT_OUT` | Audit output path |
