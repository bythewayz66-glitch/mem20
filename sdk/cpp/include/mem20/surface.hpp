#pragma once

// mem20/surface.hpp -- the single place in the C++ SDK where the size of the
// mem20 MCP tool surface is stated.
//
// WHY THIS FILE EXISTS
// --------------------
// The SDK used to state no tool count anywhere in its headers, and the live
// surface test buried `270` in an anonymous namespace inside a .cpp file. A
// consumer (or a release note) therefore had no compile-time constant to quote,
// and nothing stopped the SDK from publishing a stale figure -- the same failure
// mode that produced three different published values (257 / 268 / 270) in
// earlier revisions of the project.
//
// The numbers here are cross-checked by three independent guards:
//   1. static_assert  -- the derivation arithmetic below cannot ship inconsistent.
//   2. CMake test     -- surface_docs greps this header, README.md and
//                        docs/sdk/cpp/README.md, and fails on any disagreement.
//   3. Live test      -- live_surface asserts the count the running
//                        mcp/mcp_server.py advertises over `tools/list`.
//
// GROUND TRUTH
// ------------
// docs/TOOL-DOMAINS.md is the authoritative mapping, generated from the registry
// itself. Both derivations below reproduce exactly that document:
//
//   registration sites in mcp/**/*.py       271
//   minus the one duplicate (`lie_status` is assigned twice in
//                             mcp/tools/lie_tools.py)
//   = distinct tools                        270   -> kToolCount
//
//   28 `register_*_tools` groups
//   minus `register_a2a_tools` (an inter-agent transport, not a tool domain)
//   = domains                                27   -> kDomainCount
//   of which 265 tools, plus 5 `a2a_*` =   270   -> kToolCount
//
// The count is a property of a *server build*, not of this client: mcp20's
// client discovers the real surface via `tools/list` (see
// Session::list_tools()). These constants describe the server version this SDK
// release was verified against and are what the guards assert -- they are never
// used to filter or reject tools that a server actually sent.

#include <cstddef>
#include <string>

namespace mem20 {
namespace surface {

// --- server version this surface was verified against ------------------------
inline constexpr const char* kServerVersion = "3.1.0";

// --- tool count -------------------------------------------------------------
// Distinct tool names a fresh `tools/list` returns: 270.
inline constexpr std::size_t kToolCount = 270;

// The two halves. Conflating them is what produced the retired numbers, so the
// split is explicit here and the identity is enforced below.
inline constexpr std::size_t kDomainTools = 265;  // registered by the 27 domains
inline constexpr std::size_t kA2aLayerTools = 5;  // transport layer, not a domain
inline constexpr std::size_t kInfraTools = 0;     // in v3.1.0 job_* is a domain

// --- domain count -----------------------------------------------------------
// 28 `register_*_tools` groups minus the A2A transport layer = 27 domains.
inline constexpr std::size_t kRegisterGroups = 28;
inline constexpr std::size_t kA2aIsTransportNotDomain = 1;
inline constexpr std::size_t kDomainCount =
    kRegisterGroups - kA2aIsTransportNotDomain;  // 27

// --- source-level derivation facts (what the live test recounts) -------------
inline constexpr std::size_t kRegistrationSites = 271;  // raw assignments
inline constexpr std::size_t kDuplicateSites = 1;       // `lie_status`, twice

// --- retired figures --------------------------------------------------------
// Kept only so the guards can prove the SDK never re-publishes them. 257/26
// predates the lie_* domain; 268/26 counted mcp/tools/ modules only and missed
// the three root-level domain modules.
inline constexpr std::size_t kRetiredToolCount = 257;
inline constexpr std::size_t kRetiredDomainCount = 26;

// --- invariants -------------------------------------------------------------
// The two derivations must reconcile with each other, and the source-level
// recount must land on the same total. If any number above is edited without
// its counterpart, this stops the build instead of shipping a drifting figure.
static_assert(kDomainCount == 27, "28 register groups - 1 A2A layer = 27 domains");
static_assert(kToolCount == 270, "distinct tools advertised by tools/list");
static_assert(kDomainTools + kA2aLayerTools + kInfraTools == kToolCount,
              "265 domain tools + 5 a2a_* tools = 270");
static_assert(kRegistrationSites - kDuplicateSites == kToolCount,
              "271 registration sites - 1 duplicate = 270 distinct tools");
static_assert(kToolCount != kRetiredToolCount,
              "257 is retired; do not re-publish it");
static_assert(kDomainCount != kRetiredDomainCount,
              "26 is retired; do not re-publish it");

// "270 tools across 27 domains" -- the one-line form the docs must match.
inline std::string summary() {
  return std::to_string(kToolCount) + " tools across " +
         std::to_string(kDomainCount) + " domains";
}

}  // namespace surface
}  // namespace mem20
