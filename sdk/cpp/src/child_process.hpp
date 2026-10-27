// sdk/cpp/src/child_process.hpp
//
// INTERNAL header - not installed, not part of the public API.
//
// Declares the stdio child process used by the transport. The declaration lives
// here and the member definitions live out-of-line in transport.cpp so that
// client.cpp and transport.cpp agree on one class layout and emit the symbols
// exactly once.

#pragma once

#include <string>
#include <utility>
#include <vector>

namespace mem20 {
namespace detail {

class ChildProcess {
 public:
  int pid{-1};
  int to_child{-1};
  int from_child{-1};

  ChildProcess() = default;
  ChildProcess(ChildProcess&& o) noexcept;
  ChildProcess& operator=(ChildProcess&& o) noexcept;
  ChildProcess(const ChildProcess&) = delete;
  ChildProcess& operator=(const ChildProcess&) = delete;
  ~ChildProcess();

  void close_all();

  static ChildProcess spawn(const std::vector<std::string>& cmd,
                            const std::string& cwd,
                            const std::vector<std::pair<std::string, std::string>>& env);

  void write_line(const std::string& line);
  std::string read_line();
};

}  // namespace detail
}  // namespace mem20
