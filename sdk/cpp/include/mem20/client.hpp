#pragma once

#include "mem20/config.hpp"
#include "mem20/types.hpp"

#include <memory>
#include <string>
#include <vector>

namespace mem20 {

class Session {
 public:
  Session(Session&&) noexcept;
  Session& operator=(Session&&) noexcept;
  ~Session();

  Session(const Session&) = delete;
  Session& operator=(const Session&) = delete;

  static Result<Session> spawn(const ServerConfig& cfg);

  ServerInfo server_info() const;

  Result<std::vector<std::string>> list_tools();
  Result<StoreResult> store(const GroundedMemory& fact);
  Result<SimulateResult> simulate(const SimulatedMemory& hyp);
  Result<std::vector<RecallHit>> recall(const std::string& query, const RecallOptions& opts = {});
  Result<PromotionResult> promote(const PromotionRequest& req);
  Result<ContaminationAudit> audit_contamination();
  Result<std::vector<LedgerEntry>> read_ledger(const LedgerFilter& filter = {});
  Result<HealthStatus> health();

  Result<std::string> tool(const std::string& name, const std::string& args_json = "{}");

 private:
  struct Impl;
  explicit Session(std::unique_ptr<Impl> impl);
  std::unique_ptr<Impl> impl_;
};

}  // namespace mem20
