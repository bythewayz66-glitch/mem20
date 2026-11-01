# mem20 C++ SDK — release note 2026-11-01

**Roster row:** #12 (Mem20 C++ Expert) · **Gap:** G5 (PyPI 404s — SDK distribution)
**Directive:** `docs/ops/owner-directive-2026-11-01.md` @ `06fa1220e964f84aabac78127fc18463dfa6798d`
**Base commit:** `2ea4492209dfaae6afb22ca884132a0d1849bfcf` (`main`, 2026-11-01T13:21:47Z)
**Branch:** `sdk/cpp-install-export-2026-11-01` (pushed to `bythewayz66-glitch/mem20`)
**Remote commits:** `ab46fb56` (types.hpp + cmake config templates) → `1e90945d`
(example fix, consumer project, install-export driver) → `99f37bcc` (CMakeLists
install/export) → `5385ecf0` (evidence transcripts) → this document.
**Local commit range:** `00fd06d9` → `23a704b4` on the same branch name.
**Patch:** `git format-patch 2 --stdout` from `2ea44922`, 1204 lines.

---

## 1. What the directive asked for

> **12. Mem20 C++ Expert** — G5
> C++ SDK (`sdk/cpp/**`) — CMake install/export config and a green `ctest` run;
> `test_surface_docs.cpp` must pass.
> **Acceptance:** branch SHA; committed `ctest` output; `docs/sdk/cpp-release-2026-11-01.md`.

## 2. State found at `2ea44922`

| Item | State on arrival |
|---|---|
| `sdk/cpp/CMakeLists.txt` | Builds the library and 3 tests. **No `install()`, no export set, no package config, no `.pc` file.** `find_package(mem20)` was impossible. |
| Default build | **BROKEN.** `docs/sdk/cpp/examples/store_recall_audit.cpp` is an unconditional target and did not compile, so `cmake --build` failed and `ctest` could not run at all. |
| `test_surface_docs.cpp` | Present and correct, but unreachable — the suite never built. |
| `test_live_surface.cpp` | Present; needs `python3` + the `mcp` package + `mcp/mcp_server.py`. |

The build blocker was a real API defect, not a typo: `Result<T>` exposed
`const auto& error() const { return *this; }` alongside a zero-argument
`std::string message() const`, so the documented `r.error().message` parsed as a
member-function pointer and could never compile. `server_info().server_info.dump()`
was a second defect — `ServerInfo::server_info` is a `std::string`, not a JSON value.

## 3. What changed

### 3.1 Build repair (unblocks the suite)

| File | Change |
|---|---|
| `sdk/cpp/include/mem20/types.hpp` | Replaced the contradictory `error()` accessor with `detail()`; kept `message()` as a value accessor. Both return the error string. |
| `docs/sdk/cpp/examples/store_recall_audit.cpp` | `r.error().message` → `r.detail()` (7 sites); dropped `.dump()`; `print_ledger` now checks the `Result` before iterating instead of range-for over a `Result`. |

### 3.2 Install / export packaging (the actual deliverable)

| File | Purpose |
|---|---|
| `sdk/cpp/CMakeLists.txt` | Rewritten. `install(TARGETS … EXPORT mem20Targets)`, `install(EXPORT … NAMESPACE mem20::)`, `configure_package_config_file`, `write_basic_package_version_file` (`SameMajorVersion`), `mem20.pc`, build-tree `export()`. Adds `MEM20_BUILD_TESTS` / `MEM20_BUILD_EXAMPLES` / `MEM20_WARNINGS_AS_ERRORS` / `MEM20_ENABLE_SANITIZERS` / `MEM20_CXX_STANDARD`. |
| `sdk/cpp/cmake/mem20Config.cmake.in` | Package config; `find_dependency(Threads)` because the static library's pthread dependency is `PUBLIC` and must reach the consumer. |
| `sdk/cpp/cmake/mem20.pc.in` | pkg-config metadata (`pkg-config --cflags --libs mem20`). |
| `sdk/cpp/tests/consumer/{CMakeLists.txt,main.cpp}` | A **separate project** that knows mem20 only through `find_package(mem20 CONFIG REQUIRED)`. Odr-uses `Session::spawn` so the link actually pulls `client.o`/`transport.o` out of the archive. |
| `sdk/cpp/tests/test_install_export.cmake` | ctest driver: install → configure consumer → build → **run**. |

Consumer contract:

```cmake
find_package(mem20 CONFIG REQUIRED)
target_link_libraries(app PRIVATE mem20::mem20)
```

`EXPORT_NAME mem20` is set on the target so the imported name is `mem20::mem20`
rather than `mem20::mem20_sdk`. The same name works in-tree via
`add_subdirectory(sdk/cpp)` / FetchContent, so there is one spelling everywhere.

A configure-time guard fails the build if `project(VERSION)` and
`kSdkVersion` in `include/mem20/version.hpp` disagree.

### 3.3 New test: `install_export`

The packaging claim is now self-verifying. `install_export` installs into a
scratch prefix, asserts the expected files exist, configures the standalone
consumer with **only** `CMAKE_PREFIX_PATH`, builds it, and runs it. A wrong
export set, a missing install rule, or a dropped `Threads` dependency fails the
suite instead of shipping.

## 4. Test results

Command (from the repo root):

```bash
cmake -S sdk/cpp -B build/cpp -G Ninja -DCMAKE_BUILD_TYPE=Release -DMEM20_WARNINGS_AS_ERRORS=ON
cmake --build build/cpp
ctest --test-dir build/cpp --output-on-failure
```

```
1/4 Test #1: mem20_sdk_tests ..................   Passed    0.00 sec
2/4 Test #2: live_surface .....................   Passed    1.75 sec
3/4 Test #3: surface_docs .....................   Passed    0.00 sec
4/4 Test #4: install_export ...................   Passed    1.04 sec

100% tests passed, 0 tests failed out of 4
```

`surface_docs` — the docs-drift guard the directive names — **passes**:

```
mem20 C++ SDK surface docs test
  expected surface : 270 tools across 27 domains
PASS: surface.hpp, version.hpp and both READMEs agree on 270 tools across 27 domains
```

`live_surface` ran against a **real** `mcp/mcp_server.py` (not a skip): real
`initialize` handshake, real `tools/list`, and a grounded `memory_store` →
`memory_recall` round trip.

Committed transcripts:

| Evidence | File |
|---|---|
| Release configure + build + ctest | `docs/sdk/evidence/ctest-release-2026-11-01.txt` |
| ASan + UBSan configure + build + ctest | `docs/sdk/evidence/ctest-asan-2026-11-01.txt` |
| `cmake --install`, installed tree, pkg-config, `find_package` consumer | `docs/sdk/evidence/install-export-2026-11-01.txt` |

### 4.1 Sanitizers

`-DMEM20_ENABLE_SANITIZERS=ON` (ASan + UBSan, `-fno-sanitize-recover=all`),
`RelWithDebInfo`, `-Werror`: **4/4 passed**. Run under `setarch -R` because this
container's kernel has `vm.mmap_rnd_bits` set incompatibly with ASan shadow
memory and the sysctl is not writable — an environment workaround, not a code
change.

### 4.2 Negative controls (the tests are not vacuous)

| Control | Expected | Observed |
|---|---|---|
| `sdk/cpp/README.md` states `269 tools across 27 domains` | `surface_docs` fails | exit `1`, `FAIL: sdk/cpp/README.md: does not state "270 tools across 27 domains"`; ctest `Failed` |
| `EXPORT_NAME` changed to `mem20_sdk` | `install_export` fails | consumer configure fails, ctest `Failed` |
| `python3` on `PATH` cannot `import mcp` | `live_surface` skips | exit `77`, `SKIP: python3 on PATH cannot 'import mcp'…`; ctest `Skipped` |

## 5. Installed layout

```
<prefix>/include/mem20/{client,config,errors,surface,types,version}.hpp
<prefix>/lib/libmem20_sdk.a
<prefix>/lib/cmake/mem20/{mem20Config,mem20ConfigVersion,mem20Targets,mem20Targets-release}.cmake
<prefix>/lib/pkgconfig/mem20.pc
```

`pkg-config --modversion mem20` → `0.1.0`.

## 6. Surface statement

The SDK states the surface in exactly one place in code —
`include/mem20/surface.hpp` — with `static_assert`s pinning the derivation
(271 registration sites − 1 duplicate `lie_status` = 270 distinct tools;
28 `register_*_tools` groups − the A2A transport layer = 27 domains).

**270 tools across 27 domains**, server baseline **3.1.0**, MCP protocol
`2025-06-18`. The client never filters on these constants — it discovers the
live surface with `Session::list_tools()`.

## 7. Domain rules honoured

- **Grounded / simulated partition is in the type system**: distinct
  `GroundedMemory` and `SimulatedMemory` types with separate write paths
  (`memory_store` / `memory_simulate_store`). No overload accepts one where the
  other is expected.
- **Promotion is evidence-based with an append-only audit trail.** The example
  demonstrates the refusal path for an evidence-free promotion rather than
  hiding it.
- **The ledger is append-only and origin-tagged.** `read_ledger()` is the only
  ledger API; no append, update or delete method exists.
- **No benchmark figures are cited in this document.** Nothing here claims
  LoCoMo or LongMemEval results.
- Banned-phrase scan run over the changed files: 0 hits.

## 8. Known gaps

| Gap | Detail |
|---|---|
| **Five commits, not one** | No push credential in this environment (`GIT_TERMINAL_PROMPT=0` → `could not read Username`), so the branch was replayed through the GitHub API in batches. The tree is byte-identical to the locally-built, locally-tested commit — every `blob_sha` returned by the API for the code files matches `git rev-parse HEAD:<path>`. The three evidence transcripts were expanded while committing and are therefore **not** blob-identical to the local originals; their content is the same runs, written out in full. Squash-merge is fine. |
| **No CI workflow for `sdk/cpp/`** | `.github/workflows/` has no C++ job, so none of this runs on push. Out of scope for this row; needs a separate `cpp-sdk.yml` slice. |
| **POSIX only** | `src/transport.cpp` `#error`s on `_WIN32`. Windows stdio transport is not implemented. |
| **No HTTP/SSE transport** | stdio only. |
| **Synchronous client** | No async API. |
| **`read_ledger()` returns an empty vector** | The typed ledger reader is a stub; the raw `tool()` escape hatch is the working path. Pre-existing, not introduced here. |
| **`store()`/`recall()` return raw reply text** | `StoreResult::id` and `RecallHit::content` carry the full JSON reply rather than a parsed field. Pre-existing; `test_live_surface` uses `tool()` for the parsed path. |
| **`pkg-config` not present in the base image** | Installed for verification; the `.pc` file itself is correct. |

## 9. Reproduce

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git && cd mem20
git checkout sdk/cpp-install-export-2026-11-01

# toolchain (Debian/Ubuntu)
apt-get update -q && apt-get install -y cmake ninja-build g++ pkg-config

# server deps, only needed for live_surface (otherwise it SKIPs with a reason)
pip install "mcp>=2.1.1" mcp-types aiohttp

cmake -S sdk/cpp -B build/cpp -G Ninja -DCMAKE_BUILD_TYPE=Release -DMEM20_WARNINGS_AS_ERRORS=ON
cmake --build build/cpp
ctest --test-dir build/cpp --output-on-failure

# install + consume
cmake --install build/cpp --prefix /tmp/mem20-prefix
cmake -S sdk/cpp/tests/consumer -B /tmp/consumer -G Ninja -DCMAKE_PREFIX_PATH=/tmp/mem20-prefix
cmake --build /tmp/consumer && /tmp/consumer/mem20_consumer
```

---

*Every figure in this document was produced by a command in this run. The
transcripts under `docs/sdk/evidence/` record those same runs; see §8 for the
one caveat about how they were committed.*
