# mem20 C++ SDK

**First-class C++17 client** for the mem20 MCP server.

| | |
|--|--|
| Version | 0.1.0 |
| Protocol | JSON-RPC 2.0 / stdio, MCP `2025-06-18` |
| Server baseline | 3.1.2 |
| Tool surface | **272 tools across 27 domains** |
| Partition safety | `GroundedMemory` vs `SimulatedMemory` types |

## Tool surface

The server this release was verified against advertises **272 tools across 27
domains** over `tools/list`. That figure is stated in exactly one place in code
— `include/mem20/surface.hpp` — where `static_assert`s pin the derivation
(283 `Tool(name=...)` constructions − 1 duplicate `lie_status` = 282 defined,
minus 10 defined-but-never-registered in `lattice_tools.py` and
`eventstream_tools.py` = 272 on the wire; 28 `register_*_tools` groups − the
A2A transport layer = 27 domains).

```cpp
#include "mem20/surface.hpp"

mem20::surface::kToolCount;    // 272
mem20::surface::kDomainCount;  // 27
mem20::surface::summary();     // "272 tools across 27 domains"
```

Two guards keep it honest: `surface_docs` greps this README and
`docs/sdk/cpp/README.md` for the same string, and `live_surface` asserts the
count a real `mcp/mcp_server.py` returns. The count describes a *server build* —
the client never filters on it, it discovers the live surface with
`Session::list_tools()`. Retired figures are 257 tools / 26 domains,
268 tools / 26 domains, and 270 tools / 27 domains (the pre-wave-1 surface);
none is re-published here.

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
