# mem20 C++ SDK

> **Status:** first-class (`mem20_sdk` 0.1.0) · **Server baseline:** `mem20` 3.0.0  
> **Implementation:** [`sdk/cpp/`](../../../sdk/cpp/) · **Canonical repo:** https://github.com/bythewayz66-glitch/mem20  
> **License:** MIT

Library headers, sources, CMake, and tests live under **`sdk/cpp/`**.  
This directory keeps protocol docs, API reference, and the `store_recall_audit` example.

```bash
cmake -S sdk/cpp -B build/cpp -DCMAKE_BUILD_TYPE=Release
cmake --build build/cpp
ctest --test-dir build/cpp
MEM20_SERVER=/abs/path/to/mcp/mcp_server.py ./build/cpp/mem20_store_recall_audit
```

**Contamination** is guaranteed `0.0` at the store layer. Index drift is repaired via health/rebuild — not accepted as normal.

See also [SDKS.md](../../../SDKS.md).
