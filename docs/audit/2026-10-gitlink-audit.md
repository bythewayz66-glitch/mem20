# Nested-repo / gitlink audit - 2026-10

Scope: `bythewayz66-glitch/mem20` only. Follow-up to the Pages build failure (#54).

## Summary

Three **dangling gitlinks** (index mode `160000`) exist on **5 of 6 branches**. Each was
created by a bare `git add` of a nested working tree, which records a commit pointer but
writes no URL. `.gitmodules` has **never existed** in this repository (absent at HEAD and
in every commit of every branch). All three pointer commits are **absent from mem20**, and
all three target repositories return **HTTP 404** - so the pointers are fully dangling.

This is the exact defect that aborts `git submodule update --init --recursive` (exit 128)
in the legacy Pages builder and fails the build before Jekyll runs.

## Findings table

| Path | Branches | Mode | Pointer SHA | Target repo | Target commit | Status |
|---|---|---|---|---|---|---|
| `kanban-mcp` | main, audit/mem20-2026-10, gtm-optionc-conversion, fix/mem20agentz-hygiene, fix/mem20crewz-hygiene | 160000 | `834bdb3994942374e1ec9ebe197a6d48442b0ef1` | 404 | absent | **DANGLING** |
| `mem20oreo` | same 5 | 160000 | `c688f7b573c104b0e28abbe4d0381b863aceabb0` (main/audit/agentz/crewz); `51876daba59cd68932fa57b50fbdade0fb3703c2` (gtm) | 404 | absent | **DANGLING** |
| `mem20kilnz/engine` | same 5 | 160000 | `f28e6597ee23b6a576c8fe53555a889673c52796` (main/audit/agentz/crewz); `f306c6cd39306a69e8a3963f9c98c11039eaf9a6` (gtm) | 404 | absent | **DANGLING** |

`fix/pages-submodule-checkout` (PR #55) is the only branch with **zero** gitlinks.

## Other accident classes checked

| Check | Result |
|---|---|
| Nested `.git` directories or `.git` files tracked | **None** - clean |
| Symlinks (mode `120000`) | 12, all `dashboard/node_modules/.bin/*` npm shims; every target resolves **inside** the repo - benign |
| `.gitmodules` present / entries matching a real gitlink | **Absent** at HEAD and in all history - no orphan entries |
| Vendored repos tracked as content | `mem20kilnz/` (43 files, real content incl. `mem20kilnz/mem20kilnz/engine.py`), `mcp_server_dir/` (70), `mem20officez/src_harvest/` (614, carries its own `.github/workflows/` - a vendored repo) |
| Directories tracked as pointer only (no content) | `kanban-mcp` (0 files), `mem20oreo` (0 files), `mem20kilnz/engine` (0 files) - the three gitlinks |
| Empty dirs meant to be submodules | The three gitlinks above |

## Per-finding fix

1. **`kanban-mcp`** - pointer only, target 404. If the kanban MCP code is needed, restore it as a
   proper submodule (`.gitmodules` entry with a reachable URL) or vendor the content as plain
   tracked files. Do **not** drop the feature.
2. **`mem20oreo`** - pointer only, target 404. Same treatment as `kanban-mcp`.
3. **`mem20kilnz/engine`** - pointer only, target 404, **and redundant**: the engine source already
   exists as tracked content at `mem20kilnz/mem20kilnz/engine.py`. The gitlink adds nothing; the
   fix is to drop the pointer (no content is lost) or, if a separate engine repo is intended,
   re-add it with a real URL.

## Recommended fix order

1. **Done (PR #55)** - drop the three gitlinks on `fix/pages-submodule-checkout`; Pages publishes
   `docs/` via the Actions source with `submodules: false`.
2. **This commit** - CI guard: fail the `syntax` job if any mode-`160000` entry reappears.
3. Decide per path whether the code is needed; if so, re-add as a real submodule or vendor it.
4. **Propagate** - the other four branches (`audit/mem20-2026-10`, `gtm-optionc-conversion`,
   `fix/mem20agentz-hygiene`, `fix/mem20crewz-hygiene`) still carry the gitlinks and will fail
   the same way once merged.

## Commands used

```bash
git ls-tree -r origin/<branch> | awk '$2=="commit"{print $1,$2,$3,$4}'
git ls-files --stage | awk '$1=="160000"'
git log --all --oneline -- .gitmodules
git ls-files | grep -E '(^|/)\.git($|/)'
git ls-files --stage | awk '$1=="120000"{print $4}'
curl -s -o /dev/null -w '%{http_code}' https://api.github.com/repos/bythewayz66-glitch/<repo>
```
