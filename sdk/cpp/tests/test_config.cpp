#include "mem20/config.hpp"
#include "mem20/version.hpp"

#include <cassert>
#include <iostream>

int main() {
  mem20::ServerConfig c = mem20::ServerConfig::python_script("/opt/mem20/mcp/mcp_server.py");
  assert(c.command.size() == 2);
  assert(c.command[0] == "python3");
  assert(c.health_port == 8080);
  assert(std::string(mem20::kProtocolVersion) == "2025-06-18");
  assert(std::string(mem20::kServerBaseline) == "3.1.0");
  std::cout << "ok\n";
  return 0;
}
