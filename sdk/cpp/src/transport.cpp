#include "mem20/errors.hpp"

#include <cerrno>
#include <cstring>
#include <string>
#include <utility>
#include <vector>

#if defined(_WIN32)
#error "mem20 C++ SDK stdio transport targets POSIX in 0.1.0"
#else
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

namespace mem20 {
namespace detail {

class ChildProcess {
 public:
  int pid{-1};
  int to_child{-1};
  int from_child{-1};

  ChildProcess() = default;
  ChildProcess(ChildProcess&& o) noexcept { *this = std::move(o); }
  ChildProcess& operator=(ChildProcess&& o) noexcept {
    if (this != &o) {
      close_all();
      pid = o.pid;
      to_child = o.to_child;
      from_child = o.from_child;
      o.pid = -1;
      o.to_child = -1;
      o.from_child = -1;
    }
    return *this;
  }
  ChildProcess(const ChildProcess&) = delete;
  ChildProcess& operator=(const ChildProcess&) = delete;

  ~ChildProcess() { close_all(); }

  void close_all() {
    if (to_child >= 0) {
      ::close(to_child);
      to_child = -1;
    }
    if (from_child >= 0) {
      ::close(from_child);
      from_child = -1;
    }
    if (pid > 0) {
      ::kill(pid, SIGTERM);
      int st = 0;
      ::waitpid(pid, &st, 0);
      pid = -1;
    }
  }

  static ChildProcess spawn(const std::vector<std::string>& cmd,
                            const std::string& cwd,
                            const std::vector<std::pair<std::string, std::string>>& env) {
    int in_pipe[2];
    int out_pipe[2];
    if (pipe(in_pipe) != 0 || pipe(out_pipe) != 0) {
      throw TransportError(std::string("pipe failed: ") + std::strerror(errno));
    }
    pid_t child = fork();
    if (child < 0) {
      throw TransportError(std::string("fork failed: ") + std::strerror(errno));
    }
    if (child == 0) {
      dup2(in_pipe[0], STDIN_FILENO);
      dup2(out_pipe[1], STDOUT_FILENO);
      close(in_pipe[0]);
      close(in_pipe[1]);
      close(out_pipe[0]);
      close(out_pipe[1]);
      if (!cwd.empty()) {
        if (chdir(cwd.c_str()) != 0) _exit(127);
      }
      for (const auto& kv : env) {
        setenv(kv.first.c_str(), kv.second.c_str(), 1);
      }
      std::vector<char*> argv;
      for (const auto& s : cmd) argv.push_back(const_cast<char*>(s.c_str()));
      argv.push_back(nullptr);
      execvp(argv[0], argv.data());
      _exit(127);
    }
    close(in_pipe[0]);
    close(out_pipe[1]);
    ChildProcess cp;
    cp.pid = static_cast<int>(child);
    cp.to_child = in_pipe[1];
    cp.from_child = out_pipe[0];
    return cp;
  }

  void write_line(const std::string& line) {
    std::string buf = line;
    if (buf.empty() || buf.back() != '\n') buf.push_back('\n');
    const char* p = buf.data();
    size_t left = buf.size();
    while (left) {
      ssize_t n = ::write(to_child, p, left);
      if (n < 0) {
        if (errno == EINTR) continue;
        throw TransportError(std::string("write failed: ") + std::strerror(errno));
      }
      p += n;
      left -= static_cast<size_t>(n);
    }
  }

  std::string read_line() {
    std::string out;
    char c;
    while (true) {
      ssize_t n = ::read(from_child, &c, 1);
      if (n < 0) {
        if (errno == EINTR) continue;
        throw TransportError(std::string("read failed: ") + std::strerror(errno));
      }
      if (n == 0) break;
      if (c == '\n') break;
      out.push_back(c);
    }
    return out;
  }
};

}  // namespace detail
}  // namespace mem20
