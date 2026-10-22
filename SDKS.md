# mem20 SDKs — first-class clients

All clients talk to the same mem20 MCP server (JSON-RPC 2.0 over stdio, protocol **2025-06-18**) unless noted. Server baseline: **3.0.0**.

## Product invariants (all clients)

- **Contamination rate is guaranteed `0.0`.** Simulated content cannot enter grounded vector/BM25 indexes. This is enforced in the store engine, not by client convention.
- **Index drift is a defect, not a feature.** The engine reports health and supports rebuild; we fix drift rather than marketing “admission” of a broken index as a product strength.
- **Promotion is evidence-based.** Simulated → grounded requires evidence; a bare flag is refused.

## First-class SDKs

| SDK | Path | Language | Role | Version |
|-----|------|----------|------|---------|
| **Python API** | `mem20api/` | Python | In-process engine API | ships with 3.0 |
| **Ruby** | `mem20-sdk-ruby/` | Ruby ≥ 3.1 | MCP client gem | 0.2.0 |
| **Perl** | `sdk/perl/` | Perl ≥ 5.20 | MCP client (core-only) | 0.1.0 |
| **TypeScript** | `mem20-sdk-typescript/` | Node ≥ 18 | MCP client (`@mem20/sdk`) | 0.1.0 |
| **Godot** | `mem20-sdk-godot/` | GDScript / Godot 4 | Editor/game addon | 0.1.0 |
| **C++** | `sdk/cpp/` | C++17 | MCP client library | 0.1.0 |

Docs-only protocol notes remain under `docs/sdk/cpp/` for the C++ walkthrough example.

## Quick links

- TypeScript: `mem20-sdk-typescript/README.md`
- Godot: `mem20-sdk-godot/README.md`
- C++: `sdk/cpp/README.md`
- Ruby: `mem20-sdk-ruby/README.md`
- Perl: `sdk/perl/README.md`
- Python: `mem20api/README.md`
