# candy

Quarantine for **long-name** `mem20*z` subsystems (`len(name) > 15`).

This folder **is tracked in git**. The estate must **not** import, discover,
test, or register MCP tools from here.

## Rule

| Location | Estate? |
|----------|---------|
| Root `mem20*z` with `len(name) <= 15` | Yes — consolidation boxes |
| `candy/**` | **No** — quarantine only |

## Layout

- `candy/<pkg>/` — former top-level long packages
- `candy/absorbed/<host>__<pkg>/` — former absorbed long packages
- `candy/mcp_tools/` — MCP tool modules for long packages

## Dewire

`mem20verify.testrun.discover_packages` skips `candy/` and any long `mem20*z` name.
`.mem20-absorbed-map.json` has no long-package entries.
`mcp/tools/` has no long-package tool modules.
MCP admission code does not import packages from `candy/`.

Do **not** put `candy/` on `PYTHONPATH` for boot.
