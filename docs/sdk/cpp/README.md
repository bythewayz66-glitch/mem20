# mem20 C++ SDK

> **Status:** first-class (`mem20_sdk` 0.1.0) · **Server baseline:** `mem20` 3.1.0  
> **Tool surface:** **270 tools across 27 domains** (`mem20::surface::summary()`)  
> **Implementation:** [`sdk/cpp/`](../../../sdk/cpp/) · **Canonical repo:** https://github.com/bythewayz66-glitch/mem20  
> **License:** MIT

Library headers, sources, CMake, and tests live under **`sdk/cpp/`**.  
This directory keeps protocol docs, API reference, and the `store_recall_audit` example.

The server this release was verified against advertises **270 tools across 27
domains** over `tools/list`. The figure is stated in exactly one place in code —
`include/mem20/surface.hpp`, where `static_assert`s pin the derivation — and is
guarded by the `surface_docs` test (greps this file and `sdk/cpp/README.md`) and
the `live_surface` test (asserts the count a real server returns). Retired
figures are 257 tools / 26 domains and 268 tools / 26 domains; neither is
re-published here.

```bash
cmake -S sdk/cpp -B build/cpp -DCMAKE_BUILD_TYPE=Release
cmake --build build/cpp
ctest --test-dir build/cpp
MEM20_SERVER=/abs/path/to/mcp/mcp_server.py ./build/cpp/mem20_store_recall_audit
```

**Contamination** is guaranteed `0.0` at the store layer. Index drift is repaired via health/rebuild — not accepted as normal.

See also [SDKS.md](../../../SDKS.md).
