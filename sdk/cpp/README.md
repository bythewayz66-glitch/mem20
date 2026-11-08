# mem20 C++ SDK

**First-class C++17 client** for the mem20 MCP server.

| | |
|--|--|
| Version | 0.1.0 |
| Protocol | JSON-RPC 2.0 / stdio, MCP `2025-06-18` |
| Server baseline | 3.1.2 |
| Tool surface | **311 tools across 39 domains** |
| Partition safety | `GroundedMemory` vs `SimulatedMemory` types |

## Tool surface

The server this release was verified against advertises **311 tools across 39
domains** over `tools/list`. That figure is stated in exactly one place in code
— `include/mem20/surface.hpp` — where `static_assert`s pin it, and it is
cross-checked against `docs/surface.json`, which `scripts/surface_manifest.py`
generates from a live `tools/list` response and the AST catalog in
`web/src/data/tools.json` (the two must be identical or the generator refuses
to emit).

```cpp
#include "mem20/surface.hpp"

mem20::surface::kToolCount;    // 311
mem20::surface::kDomainCount;  // 39
mem20::surface::summary();     // "311 tools across 39 domains"
```

Two guards keep it honest: `surface_docs` greps this README and
`docs/sdk/cpp/README.md` for the same string, and `live_surface` asserts the
count a real `mcp/mcp_server.py` returns. The count describes a *server build* —
the client never filters on it, it discovers the live surface with
`Session::list_tools()`. Retired figures are 257 tools / 26 domains,
268 tools / 26 domains, 270 tools / 27 domains, 272 tools / 27 domains and
306 tools / 38 domains — all retired; none is re-published here.

## Build

```bash
cmake -S sdk/cpp -B build/cpp -DCMAKE_BUILD_TYPE=Release
cmake --build build/cpp
ctest --test-dir build/cpp
```

## Example

```bash
MEM20_SERVER=/abs/path/to/mem20/mcp/mcp_server.py ./build/cpp/mem20_store_recall_audit
```

See `docs/sdk/cpp/examples/store_recall_audit.cpp`.

## Contamination

The engine **guarantees** `contamination_rate == 0.0`. `Session::audit_contamination()` surfaces that invariant. Promotion without evidence is refused.

## Layout

```
sdk/cpp/
  include/mem20/   # public headers (surface.hpp = the tool/domain count)
  src/             # transport + session
  tests/           # unit, docs-drift and live-surface tests
  CMakeLists.txt
```

## License

MIT.
