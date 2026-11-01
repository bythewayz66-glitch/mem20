// sdk/cpp/tests/test_live_surface.cpp
//
// Live surface test for the mem20 C++ SDK.
//
// Every other test in this directory asserts the SDK's surface against
// documentation or a fake transport. This one asserts it against a REAL server:
// it spawns mcp/mcp_server.py, performs a real MCP handshake (initialize +
// notifications/initialized), reads a real tools/list, and then does one
// memory_store -> memory_recall round trip through the grounded partition and
// checks that the stored fact comes back.
//
// Contract: this test never passes silently.
//   exit  0  -> the live surface matched, with the evidence printed
//   exit 77  -> SKIPPED, always with a named reason on stderr (no python3 on
//               PATH, no server script, etc). CMakeLists.txt sets
//               SKIP_RETURN_CODE 77, so ctest reports a skip, not a pass.
//   exit 1   -> a real assertion failed
//
// Requires C++17.

#include "mem20/client.hpp"
#include "mem20/config.hpp"
#include "mem20/types.hpp"
#include "mem20/version.hpp"

#include <stdio.h>   // fopen / fclose
#include <stdlib.h>  // mkdtemp, std::system

#include <cstdlib>
#include <iostream>
#include <set>
#include <string>
#include <utility>
#include <vector>

#ifndef MEM20_TEST_SERVER_SCRIPT
#error "MEM20_TEST_SERVER_SCRIPT must be defined by CMakeLists.txt"
#endif
#ifndef MEM20_TEST_REPO_ROOT
#error "MEM20_TEST_REPO_ROOT must be defined by CMakeLists.txt"
#endif

namespace {

// Live tools/list surface captured from mcp/mcp_server.py on the canonical
// repository (bythewayz66-glitch/mem20, main). If the server's registered tool
// table changes, this number must change with it — that is the point of the
// assertion.
constexpr std::size_t kExpectedToolCount = 272;

constexpr int kExitOk = 0;
constexpr int kExitFail = 1;
constexpr int kExitSkip = 77;

// The fact this test stores. Distinctive so a recall hit cannot be a
// false positive from anything already in the store.
const char* const kFactMarker = "CADENCE-LIVE-SURFACE-91";
const char* const kFactText =
    "CADENCE-LIVE-SURFACE-91: the mem20 C++ SDK live surface test stored this "
    "exact sentence.";

void skip(const std::string& reason) {
  std::cerr << "SKIP: " << reason << "\n";
  std::exit(kExitSkip);
}

void fail(const std::string& what) {
  std::cerr << "FAIL: " << what << "\n";
  std::exit(kExitFail);
}

// Best-effort check that an interpreter is spawnable. Without it the child exits
// 127 and the handshake would otherwise look like an empty-but-successful reply,
// which is exactly the silent pass this test exists to prevent.
bool has_python3() {
  const int rc = std::system("command -v python3 >/dev/null 2>&1");
  return rc == 0;
}

// The server needs the `mcp` package. A python3 that is present but missing it
// cannot run the server either, and that is a missing-dependency skip, not a
// surface defect -- so check it rather than reporting a bogus FAIL.
bool python3_has_mcp() {
  const int rc = std::system("python3 -c 'import mcp' >/dev/null 2>&1");
  return rc == 0;
}

// The server answers tools/call with prose in content[0].text and
// (on failure) "isError":true. It never sends structuredContent.
bool reply_is_error(const std::string& reply) {
  return reply.find("\"isError\":true") != std::string::npos;
}

std::string reply_text(const std::string& reply) {
  // Pull the first content[].text value without a JSON dependency.
  const std::string key = "\"text\":\"";
  const std::size_t at = reply.find(key);
  if (at == std::string::npos) return std::string();
  std::string out;
  bool escaped = false;
  for (std::size_t i = at + key.size(); i < reply.size(); ++i) {
    const char c = reply[i];
    if (escaped) {
      // Keep it readable: real newlines/tabs in the prose, not the escapes.
      if (c == 'n') out.push_back('\n');
      else if (c == 't') out.push_back('\t');
      else out.push_back(c);
      escaped = false;
      continue;
    }
    if (c == '\\') { escaped = true; continue; }
    if (c == '"') break;
    out.push_back(c);
  }
  return out;
}

}  // namespace

int main() {