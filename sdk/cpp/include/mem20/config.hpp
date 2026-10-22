#pragma once

#include <string>
#include <utility>
#include <vector>

namespace mem20 {

struct ServerConfig {
  std::vector<std::string> command{"python3", "mcp/mcp_server.py"};
  std::string cwd;
  std::vector<std::pair<std::string, std::string>> env;
  std::string health_host{"127.0.0.1"};
  int health_port{8080};
  int timeout_ms{30000};
  std::string protocol_version{"2025-06-18"};

  static ServerConfig python_script(const std::string& server_path) {
    ServerConfig c;
    c.command = {"python3", server_path};
    return c;
  }
};

}  // namespace mem20
