# mem20liez Integration Notes

## MCP server recovery (if mcp/server.py was truncated)

```bash
cd /path/to/mem20
git show 6a2bdaab2434611a2edee5d26b93bcc500edb87b:mcp/server.py > mem20liez/_server_impl.py
# mcp/server.py is a thin loader that subclasses and registers lie_* tools
```

Or restore the original file entirely:

```bash
git checkout 6a2bdaab2434611a2edee5d26b93bcc500edb87b -- mcp/server.py
# then manually add LieToolsMixin import, base class, register_lie_tools(), and dispatch
```

## What is already integrated

| Item | Location | Status |
|------|----------|--------|
| Voice-stress detector (real, numpy) | `mem20liez/detectors/voice_stress.py` | Done |
| MCP tool handlers + schemas | `mcp/tools/lie_tools.py` | Done |
| Grounded memory write on seal | `lie_seal_session` → `remember()` | Done |
| Braid journal on seal | `lie_seal_session` → `braid_commit` | Done |
| Government dual-control | `lie_dual_acknowledge` | Done |
| Use-case docs | `docs/use-cases/UC-MEM-AV-*.md` | Done |
| Server wiring | loader subclass in `mcp/server.py` | Done (needs `_server_impl.py`) |

## Quick verify

```python
from mem20liez import LieDetector, LiveLieSession
d = LieDetector()
r = d.process_audio(open("sample.pcm","rb").read())
print(r.value, r.confidence)
```

MCP tools: `lie_status`, `lie_start_session`, `lie_set_baseline`, `lie_feed_audio`, `lie_get_cues`, `lie_seal_session`, `lie_dual_acknowledge`, ...
