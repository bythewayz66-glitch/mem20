# Client SDKs — `sdk/`

Language SDKs for talking to the mem20 MCP server. Each language has its own
subdirectory with its own README.

**38 tracked file(s).**

## Contents

- `cpp/` — C++ SDK (CMake, headers under `include/mem20/`, `pkg-config` and CMake package files)
- `perl/` — Perl SDK (`Makefile.PL`, `cpanfile`, examples, `AUDIT.md`)

## Usage

```bash
# C++
cmake -S sdk/cpp -B build && cmake --build build
# Perl
cd sdk/perl && perl Makefile.PL && make && make test
```

## Notes

See `sdk/cpp/README.md` and `sdk/perl/README.md` for language-specific usage.
Both SDKs speak the same JSON-RPC 2.0 stdio protocol as the server.

---

Part of the [mem20 monorepo](../README.md). See [`docs/INDEX.md`](../docs/INDEX.md) for the full documentation map.
