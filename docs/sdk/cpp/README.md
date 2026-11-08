# mem20 C++ SDK

> **Status:** first-class (`mem20_sdk` 0.1.0) · **Server baseline:** `mem20` 3.1.2  
> **Tool surface:** **311 tools across 39 domains** (`mem20::surface::summary()`)  
> **Implementation:** [`sdk/cpp/`](../../../sdk/cpp/) · **Canonical repo:** https://github.com/bythewayz66-glitch/mem20  
> **License:** MIT

Library headers, sources, CMake, and tests live under **`sdk/cpp/`**.  
This directory keeps protocol docs, API reference, and the `store_recall_audit` example.

The server this release was verified against advertises **311 tools across 39
domains** over `tools/list`. The figure is stated in exactly one place in code —
`include/mem20/surface.hpp`, where `static_assert`s pin it — and is
cross-checked against `docs/surface.json` (generated from a live `tools/list` by
`scripts/surface_manifest.py`). It is guarded by the `surface_docs` test (greps
this file and `sdk/cpp/README.md`) and the `live_surface` test (asserts the
count a real server returns). Retired figures are 257 tools / 26 domains,
268 tools / 26 domains, 270 tools / 27 domains, 272 tools / 27 domains and
306 tools / 38 domains — all retired; none is re-published here.

```bash
cmake -S sdk/cpp -B build/cpp -DCMAKE_BUILD_TYPE=Release
cmake --build build/cpp
ctest --test-dir build/cpp
MEM20_SERVER=/abs/path/to/mcp/mcp_server.py ./build/cpp/mem20_store_recall_audit
```

**Contamination** is guaranteed `0.0` at the store layer. Index drift is repaired via health/rebuild — not accepted as normal.

See also [SDKS.md](../../../SDKS.md).
