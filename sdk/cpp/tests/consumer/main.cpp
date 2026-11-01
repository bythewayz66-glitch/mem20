// sdk/cpp/tests/consumer/main.cpp
//
// Standalone consumer of the INSTALLED mem20 C++ SDK. Built by `install_export`
// against a scratch prefix with nothing but find_package(mem20 CONFIG REQUIRED).
//
// What it proves:
//   1. The public headers are installed and on the imported target's include path.
//   2. The static library is installed and its symbol chain resolves. Session::spawn
//      is odr-used (its address is taken) because the linker only pulls
//      client.o/transport.o out of the archive when a real symbol is required --
//      printing a header-only constant would link fine against an empty archive.
//   3. The version the package advertises, the version the headers declare, and
//      the SDK surface constant agree.
//
// It deliberately does NOT spawn a server: that is `live_surface`'s job, and the
// consumer test must stay runnable on a machine with no python3 at all.
//
// Exit: 0 = the installed package works, 1 = a check failed.

#include <mem20/client.hpp>
#include <mem20/config.hpp>
#include <mem20/surface.hpp>
#include <mem20/types.hpp>
#include <mem20/version.hpp>

#include <iostream>
#include <string>
#include <vector>

namespace {

constexpr const char* kExpectedSurface = "272 tools across 27 domains";

int g_failures = 0;

void check(bool ok, const std::string& what) {
  if (!ok) {
    std::cerr << "FAIL: " << what << "\n";
    ++g_failures;
  }
}

}  // namespace

int main() {
  std::cout << "mem20 installed-package consumer\n"
            << "  sdk version   : " << mem20::kSdkVersion << "\n"
            << "  protocol      : " << mem20::kProtocolVersion << "\n"
            << "  server baseline: " << mem20::kServerBaseline << "\n"
            << "  surface       : " << mem20::surface::summary() << "\n";

  // --- 1. headers + constants ----------------------------------------------
  check(std::string(mem20::surface::summary()) == kExpectedSurface,
        "surface::summary() != \"" + std::string(kExpectedSurface) + "\"");
  check(mem20::surface::kToolCount == 272, "kToolCount != 272");
  check(mem20::surface::kDomainCount == 27, "kDomainCount != 27");
  check(std::string(mem20::surface::kServerVersion) ==
            std::string(mem20::kServerBaseline),
        "surface.hpp and version.hpp disagree on the server baseline");

  // --- 2. link proof -------------------------------------------------------
  // Odr-use the transport entry point. If the archive were installed without
  // client.o/transport.o (or the two TUs disagreed on ChildProcess), this is
  // where the link fails instead of at the consumer's first real call.
  using SpawnFn = mem20::Result<mem20::Session> (*)(const mem20::ServerConfig&);
  SpawnFn spawn_fn = &mem20::Session::spawn;
  check(spawn_fn != nullptr, "Session::spawn did not resolve");

  // --- 3. the value types behave as documented -----------------------------
  mem20::ServerConfig cfg =
      mem20::ServerConfig::python_script("/opt/mem20/mcp/mcp_server.py");
  check(cfg.command.size() == 2 && cfg.command[0] == "python3",
        "ServerConfig::python_script did not build {python3, <path>}");
  check(cfg.protocol_version == mem20::kProtocolVersion,
        "ServerConfig default protocol_version disagrees with kProtocolVersion");

  mem20::Result<std::string> ok = mem20::Result<std::string>::ok("ready");
  check(static_cast<bool>(ok), "Result::ok did not report success");
  check(*ok == "ready", "Result value did not round-trip");
  check(ok.detail().empty(), "a successful Result carried an error detail");

  mem20::Result<std::string> bad =
      mem20::Result<std::string>::fail("server refused the write");
  check(!static_cast<bool>(bad), "Result::fail did not report failure");
  check(bad.detail() == "server refused the write",
        "Result error detail did not round-trip");

  // Moved payloads must survive: Session is move-only and only reachable
  // through Result<Session>, so this is the documented extraction path.
  mem20::Result<std::string> moved = std::move(ok);
  check(static_cast<bool>(moved) && *moved == "ready",
        "moving a Result dropped its payload");

  if (g_failures != 0) {
    std::cerr << "FAIL: " << g_failures << " consumer check(s) failed\n";
    return 1;
  }
  std::cout << "PASS: find_package(mem20 CONFIG REQUIRED) -> mem20::mem20 links "
               "and behaves\n";
  return 0;
}
