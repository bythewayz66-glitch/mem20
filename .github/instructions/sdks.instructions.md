---
applyTo: "sdk/**,mem20-sdk-ruby/**,mem20-sdk-typescript/**,mem20-sdk-godot/**"
---

# SDK rules

All clients speak JSON-RPC 2.0 over stdio, protocol **2025-06-18**, server
baseline **3.0.0**. See `SDKS.md` for the authoritative matrix.

| SDK | Path | Floor |
| --- | --- | --- |
| Perl | `sdk/perl/` | Perl >= 5.20, core modules only |
| C++ | `sdk/cpp/` | C++17 |
| Ruby | `mem20-sdk-ruby/` | Ruby >= 3.1 |
| TypeScript | `mem20-sdk-typescript/` | Node >= 18 |
| Godot | `mem20-sdk-godot/` | Godot 4 (GDScript) |

- Perl is **core-only** — do not add a CPAN dependency to `cpanfile` without a
  strong reason. Tests run with `prove -Isdk/perl/lib sdk/perl/t/*.t`.
- C++: keep the public headers in `sdk/cpp/include/mem20/` and the compile check
  passing via `make cpp-example`.
- The SDKs are clients, not enforcement points: the contamination guarantee lives
  in the server's store engine. Do not reimplement invariant checks client-side.
- Any protocol or version change must be reflected in `SDKS.md` in the same PR.
