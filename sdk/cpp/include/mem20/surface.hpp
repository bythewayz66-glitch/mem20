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
// failure mode that produced three different published values (257 / 268 / 270)
// in earlier revisions of the project.
//
// The numbers here are cross-checked by three independent guards:
//   1. static_assert  -- the derivation arithmetic below cannot ship inconsistent.
//   2. CMake test     -- surface_docs greps this header, README.md and
//                        docs/sdk/cpp/README.md, and fails on any disagreement.
//   3. Live test      -- live_surface asserts the count the running
//                        mcp/mcp_server.py advertises over `tools/list`.
//
// GROUND TRUTH (re-derived on main @ d99ab5d8, 2026-11-01)
// --------------------------------------------------------
// The count is measured two ways that must agree: a source recount and a live
// `tools/list` from a booted server. Both land on 272.
//
//   registration sites in mcp/**/*.py                    284
//   minus sites in modules server.py never registers        -10
//         (mcp/tools/lattice_tools.py and
//          mcp/tools/eventstream_tools.py each define a
//          register_*_tools function that _setup_tools()
//          does not call, so their 5+5 tools never reach
//          the wire)
//   = sites in registered modules                          274
//   minus duplicate names                                   -2
//         (`lie_status` is assigned twice in
//          mcp/tools/lie_tools.py; `vcs_asset_release_audit`
//          is assigned twice in mcp/tools/rm239_tools.py)
//   = distinct tools                                       272   -> kToolCount
//
//   mcp/server.py::_setup_tools() makes 28 `register_*_tools` calls
//   minus `register_a2a_tools` (an inter-agent transport, not a tool domain)
//   = domains                                               27   -> kDomainCount
//   of which 267 tools, plus 5 `a2a_*` =                   272   -> kToolCount
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
inline constexpr const char* kServerVersion = "3.1.0";

// --- tool count -------------------------------------------------------------
// Distinct tool names a fresh `tools/list` returns: 272.
inline constexpr std::size_t kToolCount = 272;

// The two halves. Conflating them is what produced the retired numbers, so the
// split is explicit here and the identity is enforced below.
inline constexpr std::size_t kDomainTools = 267;  // registered by the 27 domains
inline constexpr std::size_t kA2aLayerTools = 5;  // transport layer, not a domain
inline constexpr std::size_t kInfraTools = 0;     // in v3.1.0 job_* is a domain

// --- domain count -----------------------------------------------------------
// 28 `register_*_tools` calls in server.py minus the A2A transport layer = 27.
inline constexpr std::size_t kRegisterGroups = 28;
inline constexpr std::size_t kA2aIsTransportNotDomain = 1;
inline constexpr std::size_t kDomainCount =
    kRegisterGroups - kA2aIsTransportNotDomain;  // 27

// --- source-level derivation facts (what the live test recounts) -------------
inline constexpr std::size_t kRegistrationSites = 284;  // raw assignments
// Sites in modules that define a register_*_tools function but are never
// called from server.py::_setup_tools(): lattice_tools.py (5) and
// eventstream_tools.py (5). Their tools are not on the wire.
inline constexpr std::size_t kUnregisteredSites = 10;
inline constexpr std::size_t kDuplicateSites = 2;  // lie_status, vcs_asset_release_audit

// --- retired figures --------------------------------------------------------
// Kept only so the guards can prove the SDK never re-publishes them. 257/26
// predates the lie_* domain; 268/26 counted mcp/tools/ modules only and missed
// the three root-level domain modules; 270/27 was correct before the wave-1
// merges added `vcs_asset_release_audit` and `graph_execute_reversible_plan`.
inline constexpr std::size_t kRetiredToolCount = 257;
inline constexpr std::size_t kRetiredDomainCount = 26;
inline constexpr std::size_t kRetiredToolCountV3 = 270;

// --- invariants -------------------------------------------------------------
// The two derivations must reconcile with each other, and the source-level
// recount must land on the same total. If any number above is edited without
// its counterpart, this stops the build instead of shipping a drifting figure.
static_assert(kDomainCount == 27, "28 register groups - 1 A2A layer = 27 domains");
static_assert(kToolCount == 272, "distinct tools advertised by tools/list");
static_assert(kDomainTools + kA2aLayerTools + kInfraTools == kToolCount,
              "267 domain tools + 5 a2a_* tools = 272");
static_assert(kRegistrationSites - kUnregisteredSites - kDuplicateSites ==
                  kToolCount,
              "284 registration sites - 10 unregistered - 2 duplicates = 272");
static_assert(kToolCount != kRetiredToolCount,
              "257 is retired; do not re-publish it");
static_assert(kToolCount != kRetiredToolCountV3,
              "270 is retired; do not re-publish it");
static_assert(kDomainCount != kRetiredDomainCount,
              "26 is retired; do not re-publish it");

// "272 tools across 27 domains" -- the one-line form the docs must match.
inline std::string summary() {
  return std::to_string(kToolCount) + " tools across " +
         std::to_string(kDomainCount) + " domains";
}

}  // namespace surface
}  // namespace mem20
