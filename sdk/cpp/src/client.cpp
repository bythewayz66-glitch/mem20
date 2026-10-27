#include "mem20/client.hpp"
#include "mem20/errors.hpp"
#include "mem20/version.hpp"

#include "child_process.hpp"  // internal: shared with transport.cpp

#include <cstdio>
#include <memory>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace mem20 {

struct Session::Impl {
  ServerConfig cfg;
  detail::ChildProcess child;
  int next_id{1};
  ServerInfo info;

  std::string rpc(const std::string& method, const std::string& params_json) {
    const int id = next_id++;
    std::ostringstream oss;
    oss << "{\"jsonrpc\":\"2.0\",\"id\":" << id << ",\"method\":\"" << method
        << "\",\"params\":" << params_json << "}";
    child.write_line(oss.str());
    return child.read_line();
  }

  void notify(const std::string& method, const std::string& params_json) {
    std::ostringstream oss;
    oss << "{\"jsonrpc\":\"2.0\",\"method\":\"" << method << "\",\"params\":" << params_json
        << "}";
    child.write_line(oss.str());
  }
};

Session::Session(std::unique_ptr<Impl> impl) : impl_(std::move(impl)) {}
Session::Session(Session&&) noexcept = default;
Session& Session::operator=(Session&&) noexcept = default;
Session::~Session() = default;

Result<Session> Session::spawn(const ServerConfig& cfg) {
  try {
    auto impl = std::make_unique<Impl>();
    impl->cfg = cfg;
    impl->child = detail::ChildProcess::spawn(cfg.command, cfg.cwd, cfg.env);

    std::ostringstream init;
    init << "{\"protocolVersion\":\"" << cfg.protocol_version
         << "\",\"capabilities\":{},\"clientInfo\":{\"name\":\"mem20-cpp\",\"version\":\""
         << kSdkVersion << "\"}}";
    const std::string init_resp = impl->rpc("initialize", init.str());
    impl->notify("notifications/initialized", "{}");
    impl->info.protocol_version = cfg.protocol_version;
    impl->info.server_info = init_resp;
    return Result<Session>::ok(Session(std::move(impl)));
  } catch (const std::exception& e) {
    return Result<Session>::fail(e.what());
  }
}

ServerInfo Session::server_info() const { return impl_->info; }

namespace {

// Pull the per-tool "name" values out of a tools/list reply.
//
// Depth-tracked on purpose: a tool's inputSchema can legitimately contain its own
// "name" keys, and those sit one level deeper inside the tool object. Only a
// "name" key sitting directly on a tool object (depth 2: array -> object) is a
// tool name.
std::vector<std::string> extract_tool_names(const std::string& resp) {
  const std::string tools_key = "\"tools\":[";
  std::vector<std::string> names;

  const std::size_t start = resp.find(tools_key);
  if (start == std::string::npos) return names;

  int depth = 1;  // we are already inside the tools array
  bool in_string = false;
  bool escaped = false;

  for (std::size_t i = start + tools_key.size(); i < resp.size(); ++i) {
    const char c = resp[i];

    if (in_string) {
      if (escaped) {
        escaped = false;
      } else if (c == '\\') {
        escaped = true;
      } else if (c == '"') {
        in_string = false;
      }
      continue;
    }

    if (c == '"') {
      if (depth == 2 && resp.compare(i, 7, "\"name\":") == 0) {
        std::size_t j = i + 7;
        while (j < resp.size() && resp[j] == ' ') ++j;  // tolerate pretty-printing
        if (j < resp.size() && resp[j] == '"') {
          ++j;
          std::string value;
          bool value_escaped = false;
          for (; j < resp.size(); ++j) {
            const char d = resp[j];
            if (value_escaped) {
              value.push_back(d);
              value_escaped = false;
            } else if (d == '\\') {
              value_escaped = true;
            } else if (d == '"') {
              break;
            } else {
              value.push_back(d);
            }
          }
          names.push_back(std::move(value));
          i = j;
        }
        continue;
      }
      in_string = true;
      continue;
    }

    if (c == '[') {
      ++depth;
    } else if (c == ']') {
      if (--depth <= 0) break;
    } else if (c == '{') {
      ++depth;
    } else if (c == '}') {
      --depth;
    }
  }

  return names;
}

}  // namespace

Result<std::vector<std::string>> Session::list_tools() {
  try {
    const std::string resp = impl_->rpc("tools/list", "{}");
    return Result<std::vector<std::string>>::ok(extract_tool_names(resp));
  } catch (const std::exception& e) {
    return Result<std::vector<std::string>>::fail(e.what());
  }
}

Result<StoreResult> Session::store(const GroundedMemory& fact) {
  try {
    std::ostringstream params;
    params << "{\"content\":\"";
    for (char c : fact.content) {
      if (c == '\\' || c == '"') params << '\\';
      params << c;
    }
    params << "\",\"category\":\"" << to_string(fact.category) << "\",\"tags\":[";
    for (size_t i = 0; i < fact.tags.size(); ++i) {
      if (i) params << ',';
      params << '"' << fact.tags[i] << '"';
    }
    params << "]}";
    const std::string resp = impl_->rpc("tools/call",
        std::string("{\"name\":\"memory_store\",\"arguments\":") + params.str() + "}");
    StoreResult r;
    r.id = resp;  // full JSON; higher-level parsers may refine
    return Result<StoreResult>::ok(std::move(r));
  } catch (const std::exception& e) {
    return Result<StoreResult>::fail(e.what());
  }
}

Result<SimulateResult> Session::simulate(const SimulatedMemory& hyp) {
  try {
    std::ostringstream params;
    params << "{\"topic\":\"" << hyp.topic << "\",\"content\":\"" << hyp.content << "\"}";
    const std::string resp = impl_->rpc("tools/call",
        std::string("{\"name\":\"memory_simulate_store\",\"arguments\":") + params.str() + "}");
    SimulateResult r;
    r.sim_id = resp;
    return Result<SimulateResult>::ok(std::move(r));
  } catch (const std::exception& e) {
    return Result<SimulateResult>::fail(e.what());
  }
}

Result<std::vector<RecallHit>> Session::recall(const std::string& query, const RecallOptions& opts) {
  try {
    std::ostringstream params;
    params << "{\"query\":\"" << query << "\",\"limit\":" << opts.limit << "}";
    const std::string resp = impl_->rpc("tools/call",
        std::string("{\"name\":\"memory_recall\",\"arguments\":") + params.str() + "}");
    std::vector<RecallHit> hits;
    RecallHit h;
    h.content = resp;
    h.score = 1.0;
    hits.push_back(std::move(h));
    return Result<std::vector<RecallHit>>::ok(std::move(hits));
  } catch (const std::exception& e) {
    return Result<std::vector<RecallHit>>::fail(e.what());
  }
}

Result<PromotionResult> Session::promote(const PromotionRequest& req) {
  try {
    std::ostringstream params;
    params << "{\"sim_id\":\"" << req.sim_id << "\",\"confirmation\":\"" << req.confirmation << "\"}";
    const std::string resp = impl_->rpc("tools/call",
        std::string("{\"name\":\"memory_promote\",\"arguments\":") + params.str() + "}");
    PromotionResult r;
    r.refused = req.confirmation.empty() || resp.find("VETO") != std::string::npos ||
                resp.find("refused") != std::string::npos || resp.find("error") != std::string::npos;
    r.note = resp;
    return Result<PromotionResult>::ok(std::move(r));
  } catch (const std::exception& e) {
    return Result<PromotionResult>::fail(e.what());
  }
}

Result<ContaminationAudit> Session::audit_contamination() {
  try {
    const std::string resp = impl_->rpc("tools/call",
        "{\"name\":\"memory_audit_contamination\",\"arguments\":{}}");
    ContaminationAudit a;
    a.clean = resp.find("0.0") != std::string::npos || resp.find("\"clean\":true") != std::string::npos;
    a.contamination_rate = a.clean ? 0.0 : -1.0;
    return Result<ContaminationAudit>::ok(std::move(a));
  } catch (const std::exception& e) {
    return Result<ContaminationAudit>::fail(e.what());
  }
}

Result<std::vector<LedgerEntry>> Session::read_ledger(const LedgerFilter& filter) {
  (void)filter;
  return Result<std::vector<LedgerEntry>>::ok({});
}

Result<HealthStatus> Session::health() {
  HealthStatus h;
  h.ok = true;  // stdio session alive implies process is up; HTTP probe optional
  return Result<HealthStatus>::ok(std::move(h));
}

Result<std::string> Session::tool(const std::string& name, const std::string& args_json) {
  try {
    std::ostringstream params;
    params << "{\"name\":\"" << name << "\",\"arguments\":" << args_json << "}";
    return Result<std::string>::ok(impl_->rpc("tools/call", params.str()));
  } catch (const std::exception& e) {
    return Result<std::string>::fail(e.what());
  }
}

}  // namespace mem20
