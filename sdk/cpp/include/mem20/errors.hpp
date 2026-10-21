#pragma once

#include <stdexcept>
#include <string>

namespace mem20 {

class Error : public std::runtime_error {
 public:
  explicit Error(const std::string& msg) : std::runtime_error(msg) {}
};

class ConfigurationError : public Error {
 public:
  explicit ConfigurationError(const std::string& msg) : Error(msg) {}
};

class TransportError : public Error {
 public:
  explicit TransportError(const std::string& msg) : Error(msg) {}
};

class ToolError : public Error {
 public:
  ToolError(const std::string& msg, int code)
      : Error(msg), code_(code) {}
  int code() const { return code_; }

 private:
  int code_;
};

}  // namespace mem20
