#pragma once

// mem20/surface.hpp -- the single place in the C++ SDK where the size of the
// mem20 MCP tool surface is stated.
//
// WHY THIS FILE EXISTS
// --------------------
// The SDK used to state no tool count anywhere in its headers, and the live
// surface test buried the number in an anonymous namespace inside a .cpp file.
// A consumer (or a release note) therefore had no compile-time constant to
// quote, and nothing stopped the SDK from publishing a stale figure -- the same
// failure mode that produced several different published values (257 / 268 /
// 270 / 272) in earlier revisions of the project.
//
// The numbers here are cross-checked by three independent guards:
//   1. static_assert  -- the derivation arithmetic below cannot ship inconsistent.
//   2. CMake test     -- surface_docs greps this header, README.md and
//                        docs/sdk/cpp/README.md, and fails on any disagreement.
//   3. Live test      -- live_surface asserts the count the running
//                        mcp/mcp_server.py advertises over `tools/list`.
//
// GROUND TRUTH (from docs/surface.json, generated from the live tools/list)
// ------------------------------------------------------------------------
// The count is measured from a live `tools/list` response and cross-checked
// against the AST catalog in web/src/data/tools.json by
// scripts/surface_manifest.py; the two collections must be identical or the
// generator refuses to emit. Both land on 311 tools across 39 domains.
//
//   live `tools/list` distinct names                        311   -> kToolCount
//   distinct owning domain modules (after documented folds)  39   -> kDomainCount
//
// Every tool belongs to exactly one domain, so the domain half is the whole
// surface: kDomainTools == kToolCount and there is no separate infra layer.
// (`job_status` / `job_wait` are the `job` domain; `a2a_*` is the `a2a`
// domain -- neither is a transport-only layer any more.)
//
// The count is a property of a *server build*, not of this client: the client
// discovers the real surface via `tools/list` (see Session::list_tools()).
// These constants describe the server version this SDK release was verified
// against and are what the guards assert -- they are never used to filter or
// reject tools that a server actually sent.

#include <cstddef>
#include <string>

namespace mem20 {
namespace surface {

// --- server version this surface was verified against ------------------------
inline constexpr const char* kServerVersion = "3.1.2";

// --- tool count -------------------------------------------------------------
// Distinct tool names a fresh `tools/list` returns: 311.
inline constexpr std::size_t kToolCount = 311;

// The two halves. Every tool belongs to a domain, so the domain half is the
// whole surface and the transport/infra layer is empty.
inline constexpr std::size_t kDomainTools = 311;  // registered by the 39 domains
inline constexpr std::size_t kA2aLayerTools = 0;  // a2a is a domain in v3.1.2
inline constexpr std::size_t kInfraTools = 0;     // job_* is a domain in v3.1.2

// --- domain count -----------------------------------------------------------
// Distinct owning domain modules after the documented folds = 39.
inline constexpr std::size_t kDomainCount = 39;

// --- retired figures --------------------------------------------------------
// Kept only so the guards can prove the SDK never re-publishes them. 257/26
// predates the lie_* domain; 268/26 counted mcp/tools/ modules only and missed
// the root-level domain modules; 270/27 was the pre-temporal surface; 272/27
// was the wave-1 surface before the temporal_* tools and the domain split;
// 306/38 was the pre-temporal count.
inline constexpr std::size_t kRetiredToolCount = 257;
inline constexpr std::size_t kRetiredDomainCount = 26;
inline constexpr std::size_t kRetiredToolCountV3 = 270;
inline constexpr std::size_t kRetiredToolCountV4 = 272;
inline constexpr std::size_t kRetiredToolCountV5 = 306;

// --- invariants -------------------------------------------------------------
// The derivation must reconcile, and the source-level recount must land on the
// same total. If any number above is edited without its counterpart, this stops
// the build instead of shipping a drifting figure.
static_assert(kDomainCount == 39, "39 distinct owning domain modules");
static_assert(kToolCount == 311, "distinct tools advertised by tools/list");
static_assert(kDomainTools + kA2aLayerTools + kInfraTools == kToolCount,
              "311 domain tools + 0 a2a + 0 infra = 311");
static_assert(kToolCount != kRetiredToolCount,
              "257 is retired; do not re-publish it");
static_assert(kToolCount != kRetiredToolCountV3,
              "270 is retired; do not re-publish it");
static_assert(kToolCount != kRetiredToolCountV4,
              "272 is retired; do not re-publish it");
static_assert(kToolCount != kRetiredToolCountV5,
              "306 is retired; do not re-publish it");
static_assert(kDomainCount != kRetiredDomainCount,
              "26 is retired; do not re-publish it");

// "311 tools across 39 domains" -- the one-line form the docs must match.
inline std::string summary() {
  return std::to_string(kToolCount) + " tools across " +
         std::to_string(kDomainCount) + " domains";
}

}  // namespace surface
}  // namespace mem20
