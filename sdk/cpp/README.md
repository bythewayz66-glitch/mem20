# mem20 C++ SDK

**First-class C++17 client** for the mem20 MCP server.

| | |
|--|--|
| Version | 0.1.0 |
| Protocol | JSON-RPC 2.0 / stdio, MCP `2025-06-18` |
| Server baseline | 3.0.0 |
| Partition safety | `GroundedMemory` vs `SimulatedMemory` types |

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
  include/mem20/   # public headers
  src/             # transport + session
  tests/
  CMakeLists.txt
```

## License

MIT.
