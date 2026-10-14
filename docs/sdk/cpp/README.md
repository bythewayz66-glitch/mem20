# mem20 C++ SDK

> **Status:** initial (`mem20_sdk` 0.1.0) · **Server baseline:** `mem20` 2.1.0rc2
> **Canonical repo:** https://github.com/bythewayz66-glitch/mem20 (branch `main`)
> **License:** MIT

A native C++17/C++20 client for the mem20 MCP server. It speaks **JSON-RPC 2.0 over
stdio** (the canonical transport), performs the MCP handshake, discovers tools with
`tools/list`, and invokes them with `tools/call` — with the grounded/simulated
partition and the append-only ledger baked into the type system.

Everything in this document is pinned to the mem20 server source in the canonical
repo. The exact commit and file paths each statement is drawn from are listed in
[`source-ledger.md`](source-ledger.md).

---

## 60-second quickstart

```bash
# 1. Get the mem20 server (the SDK talks to a real server process)
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 2. Build the C++ SDK + example
cmake -S sdk/cpp -B build/cpp -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build/cpp

# 3. Run the store -> recall -> audit walkthrough against the live server
MEM20_SERVER="/abs/path/to/mem20/mcp/mcp_server.py" \
  ./build/cpp/mem20_store_recall_audit
```

Minimal C++ usage:

```cpp
#include <mem20/client.hpp>

int main() {
    auto cfg = mem20::ServerConfig::python_script("/abs/path/to/mem20/mcp/mcp_server.py");
    auto session = mem20::Session::spawn(cfg).value();      // RAII: spawns + owns the child

    // Grounded write — goes to the grounded partition + grounded-only indexes.
    auto stored = session.store(mem20::GroundedMemory{
        .content  = "mem20's canonical repo is bythewayz66-glitch/mem20",
        .category = mem20::MemoryCategory::Project,
        .tags     = {"repo", "canonical"},
    });
    if (!stored) return 1;

    // Recall (hybrid retrieval on the server side).
    auto hits = session.recall("canonical repository", {.limit = 5});

    // Provenance audit; the ledger is read-only from the SDK.
    auto audit = session.audit_contamination();

    for (const auto& e : session.read_ledger({.action = "remember"})) {
        std::cout << e.ts << "  " << e.origin << "  " << e.content << "\n";
    }
}
```

---

## Requirements

| Item | Requirement | Source of truth |
|---|---|---|
| C++ standard | C++17 minimum; C++20 features auto-enabled when available | SDK design |
| Compiler | GCC 9+ / Clang 10+ / MSVC 19.29+ | SDK design |
| Build system | CMake ≥ 3.20 | SDK design |
| Dependencies | **None mandatory** — `nlohmann/json` is vendored (single header) | SDK design |
| mem20 server | Python ≥ 3.10, `mem20` 2.1.0rc2 | `pyproject.toml` (`requires-python`, `version`) |
| Server runtime deps | `mcp>=2.1.1`, `pydantic>=2.13.4`, `anyio>=4.14.2`, `numpy>=1.24`, `faiss-cpu>=1.7.4`, `sentence-transformers>=2.2.0` | `requirements.txt` |

The SDK deliberately adds **no mandatory third-party dependency** beyond the vendored
JSON layer, so it can be dropped into embedded/host-constrained builds.

---

## Starting the server

The canonical entry point is the script `mcp/mcp_server.py` — a thin shim that calls
`server.py:main`. `mcp/` is a *script directory*, not an importable package (it has no
`__init__.py`), which is why the server is launched as a script rather than imported.

```bash
# From a repo checkout
MEM20_STORE_PATH=~/.mem20/store .venv/bin/python mcp/mcp_server.py

# Or, after `pip install .`
mem20-mcp                       # console script via launcher.py — identical stdio behaviour
```

Health/observability endpoints are served on port **8080** (`MEM20_HEALTH_PORT`):

```bash
curl http://localhost:8080/health     # {"status":"ok", ...}
curl http://localhost:8080/ready      # readiness probe
curl http://localhost:8080/metrics    # tool counters + contamination_rate
```

The stdio JSON-RPC channel is the one the SDK uses; the `:8080` endpoints are
side-channel observability, not the protocol.

---

## Building & installing the SDK

### Option A — in the repo (this tree)

```bash
cmake -S sdk/cpp -B build/cpp -DCMAKE_BUILD_TYPE=Release
cmake --build build/cpp -j
ctest --test-dir build/cpp --output-on-failure
```

### Option B — `find_package` (installed / exported)

```bash
cmake -S sdk/cpp -B build/cpp -DMEM20_SDK_INSTALL=ON
cmake --build build/cpp -j
cmake --install build/cpp --prefix /usr/local
```

Consumer:

```cmake
find_package(mem20_sdk 0.1 REQUIRED)
target_link_libraries(my_app PRIVATE mem20::mem20_sdk)
```

Exported targets: `mem20::mem20_sdk` (library) and `mem20::mem20_sdk_headers`
(interface-only, for header-first use).

### Option C — `FetchContent`

```cmake
include(FetchContent)
FetchContent_Declare(mem20_sdk
  GIT_REPOSITORY https://github.com/bythewayz66-glitch/mem20.git
  GIT_TAG        main          # pin a commit SHA for reproducible builds
  SOURCE_SUBDIR  sdk/cpp)
FetchContent_MakeAvailable(mem20_sdk)
target_link_libraries(my_app PRIVATE mem20::mem20_sdk)
```

### Option D — vcpkg / Conan

Not yet published to a registry. Until then, use FetchContent with a pinned commit
SHA, or vendor the header tree. (Tracked in the SDK roadmap; no registry coordinates
are claimed here.)

> **Reproducible builds:** always pin `GIT_TAG` to a commit SHA rather than `main`.
> The canonical repo's current `main` head at the time of writing is
> `c274404a116f203b0ed99ab7156e3752f0953ea8`.

---

## Repository layout (SDK)

```
sdk/cpp/
  CMakeLists.txt
  cmake/mem20_sdk-config.cmake.in
  include/mem20/
    client.hpp          # Session, ServerConfig, Result<T>
    memory.hpp          # MemoryScope, GroundedMemory, SimulatedMemory, MemoryCategory
    ledger.hpp          # LedgerEntry (read-only view)
    json_rpc.hpp        # JSON-RPC 2.0 codec
  src/
    client.cpp
    json_rpc.cpp
    stdio_transport.cpp
  tests/
    test_json_rpc.cpp
    test_client_integration.cpp
  examples/
    store_recall_audit.cpp
```

---

## The grounded / simulated partition in the type system

mem20 keeps two logical partitions and enforces a hard separation. The SDK mirrors it
with **distinct types**, so a caller cannot silently mix them:

```cpp
enum class MemoryScope { Grounded, Simulated };

struct GroundedMemory  { std::string content; MemoryCategory category; std::vector<std::string> tags; };
struct SimulatedMemory { std::string topic; std::string content; std::vector<std::string> tags; };
```

They are mapped to **different server tools** and are never interchangeable:

| SDK call | Server tool | Partition |
|---|---|---|
| `Session::store(GroundedMemory)` | `memory_store` | grounded |
| `Session::simulate(SimulatedMemory)` | `memory_simulate_store` | simulated |
| `Session::recall(query, …)` | `memory_recall` (also `_hybrid`, `_semantic`, `_graph`) | grounded-only indexes |
| `Session::list_simulated()` | `memory_list_simulated` | simulated |
| `Session::audit_contamination()` | `memory_audit_contamination` | provenance audit |

There is no overload that accepts a `SimulatedMemory` where a `GroundedMemory` is
expected. Promotion is the **only** bridge and it is a separate, explicit call
(`Session::promote(...)` → `memory_promote`).

### Promotion is evidence-based, with an append-only audit trail

`memory_promote` accepts a simulated record **only** when it carries evidence: either a
non-empty `confirmation`, or `resolved_via_prediction_error=true` together with a
`resolution_note` (the store additionally accepts linked `prediction_error_evidence`).
Otherwise the server refuses the promotion. The SDK surfaces the refusal rather than
papering over it.

> We describe this exactly as **"evidence-based with an append-only audit trail."**
> We make no security-guarantee claim — the audit
> trail makes provenance *reviewable*, not *unforgeable*.

### The ledger is append-only and read-only from the SDK

`Session::read_ledger(filter)` returns `std::vector<LedgerEntry>` — a **read-only
view**. Each entry carries `origin` and `store` tags plus `epistemic_status`.

The SDK **offers no API that mutates or deletes ledger history**: there is no
`delete_ledger`, no `update_ledger`, no `erase`. This is enforced by absence of the
surface, not by a runtime flag. (The server's own `set_epistemic_status` stamps status
onto the original ledger line; it does not rewrite or remove the entry.)

---

## Compatibility matrix

| SDK | mem20 server | MCP transport | Status |
|---|---|---|---|
| `mem20_sdk` 0.1.x | **2.1.0rc2** (`pyproject.toml`) | stdio (canonical), HTTP/SSE | **Supported** — documented baseline |
| `mem20_sdk` 0.1.x | 2.2.0-dev (`CHANGELOG.md`, unreleased) | stdio, HTTP/SSE | Expected compatible; the JSON-RPC surface is unchanged. Not yet CI-verified. |
| `mem20_sdk` 0.1.x | ≤ 2.0.x | stdio | Not tested. Tool surface and counts differ. |

Tool surface of the documented baseline: **257 tools across 26 domains** (counted by
instantiating `Mem20MCPServer` and reading `server.tools` — see `README.md`).
Note the docs' bare-prefix domains: `memory_*` (52), `world_model_*` (15), `vcs_*` (11),
`cloud_*` (10), `db_*` (10), `prod_*` (10), `fs_*` (10), … plus optional `blender_*` (7)
and `unity_*` (5), which degrade gracefully when the external app is absent.

The MCP `protocolVersion` is negotiated during the handshake; the SDK echoes the
server's value rather than hard-coding one.

---

## Transport notes

* **stdio** — canonical, always available. `stdio_server()` in `server.py`.
* **Streamable HTTP + SSE** — optional; the server mounts a
  `StreamableHTTPSessionManager` at `/` under uvicorn (`POST initialize` and `GET SSE`
  both live under `/`). Enabled by the server's HTTP mode; not required by the SDK.

See [`protocol.md`](protocol.md) for the exact wire frames.

---

## Documentation map

| Document | Contents |
|---|---|
| [`README.md`](README.md) | this file — quickstart, build, install, compatibility |
| [`protocol.md`](protocol.md) | JSON-RPC 2.0 frames, MCP handshake, `tools/list`, `tools/call` |
| [`api-reference.md`](api-reference.md) | complete typed C++ surface |
| [`source-ledger.md`](source-ledger.md) | every claim mapped to a repo path + commit |
| [`examples/store_recall_audit.cpp`](examples/store_recall_audit.cpp) | runnable store → recall → audit |

---

## Benchmarks

Published mem20 benchmark numbers (hit rate **1.000** direct, **0.800** multi-hop,
**0.000** adversarial; leak rate **0.000**) are cited **only** from the repo's own
claim ledger, and the adversarial **0.000** row is kept visible alongside them. No
third-party conversational-memory benchmark results are claimed or implied for the C++ SDK. The SDK itself
publishes no retrieval benchmark numbers.

---

## License

MIT — see [LICENSE](https://github.com/bythewayz66-glitch/mem20/blob/main/LICENSE).
