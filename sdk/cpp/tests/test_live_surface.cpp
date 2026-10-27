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
constexpr std::size_t kExpectedToolCount = 270;

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
  std::cout << "mem20 C++ SDK live surface test\n"
            << "  sdk version      : " << mem20::kSdkVersion << "\n"
            << "  requested proto  : " << mem20::kProtocolVersion << "\n"
            << "  server script    : " << MEM20_TEST_SERVER_SCRIPT << "\n";

  // --- 0. Preconditions, each skip naming its own reason --------------------
  if (!has_python3()) {
    skip("no python3 on PATH; cannot spawn the mem20 MCP server");
  }
  if (!python3_has_mcp()) {
    skip("python3 on PATH cannot 'import mcp'; the mem20 server dependency is "
         "not installed (pip install 'mcp>=2.1.1' aiohttp)");
  }
  {
    const std::string script = MEM20_TEST_SERVER_SCRIPT;
    FILE* f = std::fopen(script.c_str(), "rb");
    if (f == nullptr) {
      skip("mem20 server entry point not found at " + script);
    }
    std::fclose(f);
  }

  // The grounded write blocks rather than failing if the store is unwritable,
  // so give the child a fresh private directory instead of the ~/.mem20 default.
  std::string store_dir;
  {
    char tmpl[] = "/tmp/mem20-live-surface-XXXXXX";
    const char* made = mkdtemp(tmpl);
    if (made == nullptr) {
      skip("could not create a scratch MEM20_STORE_PATH under /tmp");
    }
    store_dir = made;
  }

  // --- 1. Real MCP handshake ------------------------------------------------
  mem20::ServerConfig cfg = mem20::ServerConfig::python_script(MEM20_TEST_SERVER_SCRIPT);
  cfg.cwd = MEM20_TEST_REPO_ROOT;  // mcp_server.py imports its siblings
  cfg.protocol_version = mem20::kProtocolVersion;
  cfg.env.emplace_back("MEM20_STORE_PATH", store_dir);
  cfg.env.emplace_back("MEM20_LOG_LEVEL", "WARNING");

  auto spawned = mem20::Session::spawn(cfg);
  if (!spawned) {
    fail("initialize handshake failed: " + spawned.message());
  }
  mem20::Session session = std::move(*spawned);

  const mem20::ServerInfo info = session.server_info();
  if (info.server_info.empty()) {
    fail("initialize returned an empty reply (server did not hand-shake)");
  }
  if (info.server_info.find("\"protocolVersion\":\"") == std::string::npos) {
    fail("initialize reply carried no protocolVersion: " + info.server_info);
  }
  std::cout << "  initialize reply : " << info.server_info << "\n";

  // --- 2. tools/list: assert the live surface -------------------------------
  auto tools = session.list_tools();
  if (!tools) {
    fail("tools/list failed: " + tools.message());
  }

  const std::set<std::string> unique(tools->begin(), tools->end());
  std::cout << "  tools/list       : " << tools->size() << " entries, "
            << unique.size() << " unique\n";

  if (tools->size() != unique.size()) {
    fail("tools/list returned duplicate tool names (" +
         std::to_string(tools->size()) + " entries, " +
         std::to_string(unique.size()) + " unique)");
  }
  if (tools->size() != kExpectedToolCount) {
    fail("tools/list returned " + std::to_string(tools->size()) +
         " tools, expected " + std::to_string(kExpectedToolCount));
  }
  // Spot-check the two tools this test actually relies on are present.
  if (unique.count("memory_store") == 0 || unique.count("memory_recall") == 0) {
    fail("tools/list is missing memory_store and/or memory_recall");
  }

  // --- 3. Grounded write through the real server ----------------------------
  // The typed store() path cannot express epistemic_status, which the server
  // requires for a grounded write, so use the documented raw escape hatch.
  std::string store_args;
  store_args.reserve(320);
  store_args += "{\"content\":\"";
  store_args += kFactText;
  store_args += "\",\"category\":\"general\",\"tags\":\"sdk,live-surface\","
                "\"epistemic_status\":\"observed\"}";

  auto stored = session.tool("memory_store", store_args);
  if (!stored) {
    fail("memory_store transport error: " + stored.message());
  }
  if (reply_is_error(*stored)) {
    fail("memory_store returned isError:true -> " + reply_text(*stored));
  }
  const std::string store_prose = reply_text(*stored);
  if (store_prose.find("Record ID:") == std::string::npos) {
    fail("memory_store reply carried no record id -> " + store_prose);
  }
  std::cout << "  memory_store     : " << store_prose << "\n";

  // --- 4. Grounded read: the fact must come back ----------------------------
  auto recalled = session.tool(
      "memory_recall",
      std::string("{\"query\":\"") + kFactMarker + "\",\"limit\":5}");
  if (!recalled) {
    fail("memory_recall transport error: " + recalled.message());
  }
  if (reply_is_error(*recalled)) {
    fail("memory_recall returned isError:true -> " + reply_text(*recalled));
  }
  const std::string recall_prose = reply_text(*recalled);
  if (recall_prose.find(kFactMarker) == std::string::npos) {
    fail(std::string("recall did not return the stored fact (") + kFactMarker +
         ") -> " + recall_prose);
  }
  std::cout << "  memory_recall    : " << recall_prose << "\n";

  std::cout << "PASS: live initialize + tools/list (" << tools->size()
            << " unique tools) + grounded store/recall round trip\n";
  return kExitOk;
}
