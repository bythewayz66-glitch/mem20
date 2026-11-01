#pragma once

#include <optional>
#include <string>
#include <vector>

namespace mem20 {

enum class MemoryCategory { General, Project, Personal, System };

inline const char* to_string(MemoryCategory c) {
  switch (c) {
    case MemoryCategory::Project: return "project";
    case MemoryCategory::Personal: return "personal";
    case MemoryCategory::System: return "system";
    default: return "general";
  }
}

/** Grounded facts only — maps to memory_store. Partition enforced by type. */
struct GroundedMemory {
  std::string content;
  MemoryCategory category{MemoryCategory::General};
  std::vector<std::string> tags;
};

/** Simulated / hypothetical — maps to memory_simulate_store. Never indexed as grounded. */
struct SimulatedMemory {
  std::string topic;
  std::string content;
  std::vector<std::string> tags;
};

struct StoreResult {
  std::string id;
};

struct SimulateResult {
  std::string sim_id;
};

struct RecallHit {
  std::string id;
  std::string content;
  double score{0.0};
};

struct RecallOptions {
  MemoryCategory category{MemoryCategory::General};
  int limit{5};
};

struct PromotionRequest {
  std::string sim_id;
  std::string confirmation;  // required for success; empty → server refuses
};

struct PromotionResult {
  bool refused{false};
  std::string note;
  std::string grounded_id;
};

struct ContaminationAudit {
  bool clean{true};
  std::vector<std::string> findings;
  double contamination_rate{0.0};
};

struct LedgerEntry {
  std::string ts;
  std::string origin;
  std::string store;
  std::string epistemic_status;
  std::string content;
};

struct LedgerFilter {
  std::string action;
  int limit{10};
};

struct ServerInfo {
  std::string protocol_version;
  std::string server_info;  // raw JSON fragment
};

struct HealthStatus {
  bool ok{false};
};

template <typename T>
struct Result {
  std::optional<T> value;
  std::optional<std::string> error_message;

  explicit operator bool() const { return value.has_value(); }
  // Non-const overload is required to move a payload (e.g. Session) out of a
  // Result; without it every `std::move(*r)` binds to the const overload.
  T& operator*() { return *value; }
  const T& operator*() const { return *value; }
  T* operator->() { return &*value; }
  const T* operator->() const { return &*value; }

  static Result ok(T v) {
    Result r;
    r.value = std::move(v);
    return r;
  }
  static Result fail(std::string msg) {
    Result r;
    r.error_message = std::move(msg);
    return r;
  }
  // Two unambiguous accessors. `error()` used to return *this while `message()`
  // was a zero-argument member function, so the documented
  // `r.error().message` could never compile -- it read as a member pointer.
  // `detail()` is the string form; `message()` is kept as a value accessor so
  // either spelling works.
  std::string detail() const { return error_message.value_or(""); }
  std::string message() const { return error_message.value_or(""); }
};

}  // namespace mem20
