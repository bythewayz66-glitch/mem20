# mem20 C++ SDK — API Reference

**Header-first C++17 / C++20.** `#include <mem20/client.hpp>` pulls the whole public
surface. Namespace: `mem20`. All fallible calls return `mem20::Result<T>`; no exceptions
cross the public boundary; no raw `new`/`delete` in the public API.

---

## Header map

| Header | Contents |
|---|---|
| `<mem20/client.hpp>` | `Session`, `ServerConfig`, `ServerInfo`, `CallResult`, `Result<T>` |
| `<mem20/memory.hpp>` | `MemoryScope`, `MemoryCategory`, `GroundedMemory`, `SimulatedMemory`, `RecallHit`, `PromotionRequest` |
| `<mem20/ledger.hpp>` | `LedgerEntry`, `LedgerFilter` (read-only views) |
| `<mem20/json_rpc.hpp>` | `Request`, `Response`, `RpcError`, framing codec |

---

## `Result<T>`

```cpp
namespace mem20 {

template <class T>
using Result = /* std::expected<T, Error> on C++23, compatible backport otherwise */;

struct Error {
    enum class Kind { Transport, Codec, Rpc, InvalidArgument, Timeout, Closed };
    Kind        kind;
    int         rpc_code   = 0;      // valid when kind == Rpc
    std::string message;
    std::string data;                // raw JSON-RPC error.data, if present
};

}
```

Usage:

```cpp
auto s = mem20::Session::spawn(cfg);
if (!s) { std::cerr << s.error().message << "\n"; return 1; }
auto& session = *s;
```

---

## `ServerConfig`

Describes how to reach a mem20 server.

```cpp
struct ServerConfig {
    // Absolute path to the mem20 MCP entry-point script, e.g. "<repo>/mcp/mcp_server.py".
    std::string script_path;

    // Interpreter (default "python3").
    std::string interpreter = "python3";

    // Extra argv appended after the script path.
    std::vector<std::string> extra_args;

    // Environment overrides for the child, e.g. {"MEM20_STORE_PATH", "/var/lib/mem20/store"}.
    std::vector<std::pair<std::string, std::string>> env;

    // Handshake timeout and per-call default timeout.
    std::chrono::milliseconds handshake_timeout = std::chrono::seconds(20);
    std::chrono::milliseconds call_timeout      = std::chrono::seconds(60);

    // Bounded graceful shutdown before SIGKILL.
    std::chrono::milliseconds shutdown_timeout  = std::chrono::seconds(5);

    static ServerConfig python_script(std::string path);   // convenience
};
```

The default `env` leaves `MEM20_STORE_PATH` unset so the server uses its own default
(`~/.mem20/store`).

---

## `Session`

RAII owner of the child process and of one MCP session.

```cpp
class Session {
public:
    // --- construction -------------------------------------------------------
    static Result<Session> spawn(const ServerConfig&);          // fork/exec + handshake
    Session(Session&&) noexcept;                                // movable
    Session& operator=(Session&&) noexcept;
    Session(const Session&) = delete;                           // non-copyable
    ~Session() noexcept;                                        // graceful teardown

    // --- handshake results --------------------------------------------------
    const ServerInfo& server_info() const noexcept;             // protocol_version, capabilities, server_info
    bool              initialized() const noexcept;

    // --- discovery ----------------------------------------------------------
    Result<std::vector<ToolDescriptor>> list_tools();
    Result<ToolDescriptor>              describe(std::string_view tool_name);

    // --- raw invocation -----------------------------------------------------
    Result<CallResult> call(std::string_view tool_name, const json& arguments = json::object());

    // --- typed grounded surface --------------------------------------------
    Result<StoreReceipt>  store(const GroundedMemory&);          // -> memory_store
    Result<std::vector<RecallHit>> recall(std::string_view query, RecallOptions = {});
    Result<std::vector<RecallHit>> recall_hybrid(std::string_view query, RecallOptions = {});
    Result<std::vector<RecallHit>> recall_semantic(std::string_view query, RecallOptions = {});

    // --- typed simulated surface -------------------------------------------
    Result<SimReceipt>    simulate(const SimulatedMemory&);      // -> memory_simulate_store
    Result<std::vector<SimulatedHit>> list_simulated();

    // --- promotion (the ONLY bridge) ---------------------------------------
    Result<PromotionReceipt> promote(const PromotionRequest&);// -> memory_promote

    // --- audit / provenance ------------------------------------------------
    Result<AuditReport>   audit_contamination();                 // -> memory_audit_contamination
    Result<EpistemicReceipt> set_epistemic_status(               // -> memory_set_epistemic_status
        std::string_view fact_id, EpistemicStatus status);

    // --- ledger (READ-ONLY) -------------------------------------------------
    std::vector<LedgerEntry> read_ledger(const LedgerFilter& = {}) const;

    // --- observability ------------------------------------------------------
    Result<HealthStatus> health();                               // :8080/health, outside JSON-RPC
};
```

### Notes

* **`store` vs `simulate` are different functions with different argument types.**
  There is no overload accepting a `SimulatedMemory` where a `GroundedMemory` is
  required — the partition is enforced at compile time.
* **`read_ledger` is `const` and returns a value copy.** There is no mutating or
  deleting counterpart anywhere in the public headers.
* `list_tools()` caches descriptors per session; call `describe(name)` to refresh one.

---

## `ServerInfo` / `ToolDescriptor` / `CallResult`

```cpp
struct ServerInfo {
    std::string protocol_version;     // as returned by the server — echoed, never assumed
    json        capabilities;
    json        server_info;          // {name, version, ...}
};

struct ToolDescriptor {
    std::string name;
    std::string title;
    std::string description;
    json        input_schema;         // kept raw so unknown fields survive
};

class CallResult {
public:
    bool                 is_error() const noexcept;   // MCP isError OR refusal prefix
    const std::string&   text() const noexcept;       // concatenated content[].text
    const json&          raw() const noexcept;        // full JSON-RPC result
private:
    bool        is_error_;
    std::string text_;
    json        raw_;
};
```

`is_error()` is true when the server set `isError`, **or** when the text begins with a
refusal marker the mem20 handlers emit (e.g. `Error:`, `VETO / BLOCKED:`). Branch on
`is_error()` rather than string-matching in caller code.

---

## Memory types (`<mem20/memory.hpp>`)

```cpp
enum class MemoryScope { Grounded, Simulated };

enum class MemoryCategory { UserPref, Project, Tool, General };   // wire: "user_pref","project","tool","general"

struct GroundedMemory {
    std::string              content;                 // required
    MemoryCategory           category = MemoryCategory::General;
    std::vector<std::string> tags;                    // joined to comma-separated string on the wire
};

struct SimulatedMemory {
    std::string              topic;                   // required
    std::string              content;                 // required
    std::vector<std::string> tags;
};

struct RecallOptions {
    std::optional<MemoryCategory> category;           // omit -> all
    int limit = 10;                                   // server bounds 1..50
    std::optional<std::chrono::system_clock::time_point> as_of;   // time-scoped recall
};

struct RecallHit {
    std::string id;
    std::string content;
    double      score = 0.0;
    MemoryScope scope = MemoryScope::Grounded;        // hits are grounded by construction
    json        raw;
};

struct StoreReceipt  { std::string id; std::string text; };
struct SimReceipt    { std::string sim_id; std::string text; };
struct SimulatedHit  { std::string sim_id; std::string topic; std::string content; json raw; };
```

### `EpistemicStatus`

```cpp
enum class EpistemicStatus {
    Observed, Inferred, Imagined, UserStated, Hypothesis, AgentGenerated
};
// wire values: "observed","inferred","imagined","user_stated","hypothesis","agent_generated"
```

### Promotion

```cpp
struct PromotionRequest {
    std::string sim_id;                                  // required
    // Provide ONE of the two evidence paths, matching the server's gate:
    std::optional<std::string> confirmation;              // external confirmation text
    bool resolved_via_prediction_error = false;           // plus a note:
    std::string resolution_note;
    std::optional<json> prediction_error_evidence;        // linked prior prediction, if any
};

struct PromotionReceipt {
    std::string grounded_id;
    std::string note;
    bool        refused = false;                          // true when server returned VETO / BLOCKED
};
```

A `PromotionRequest` with neither `confirmation` nor a resolved prediction error is
rejected by the server; the SDK returns `PromotionReceipt{ .refused = true }` with the
server's message in `note`, and `Result` still succeeds (the refusal is a valid tool
outcome). Callers should check `refused`.

`promote` documents the mem20 rule precisely: promotion is **evidence-based with an
append-only audit trail** — an auditable record, not a security guarantee.

---

## Ledger (`<mem20/ledger.hpp>`)

```cpp
struct LedgerFilter {
    std::optional<std::string> id;
    std::optional<std::string> action;     // e.g. "remember"
    std::optional<std::string> actor;      // e.g. "gateway"
    std::optional<std::string> origin;     // e.g. "grounded"
    std::optional<std::string> store;      // "grounded" | "simulated" | ...
    std::optional<std::string> epistemic_status;   // e.g. "observed"
    std::optional<std::string> since_ts;   // ISO-8601 lower bound
    std::size_t limit = 100;
};

struct LedgerEntry {                       // read-only view of one append-only line
    std::string id;
    std::string ts;               // ISO-8601
    std::string actor;
    std::string action;
    std::string topic;
    std::string content;
    std::string origin;           // origin tag
    std::string store;            // store tag
    std::string epistemic_status;
    json        raw;              // the complete original line
};
```

The ledger is **append-only**; `LedgerEntry` is a *view*. The SDK exposes **no
`delete`, `update`, `erase`, or `rewrite`** for ledger history — by design, and by the
absence of such a function in the headers.

---

## Audit types

```cpp
struct ContaminationFinding {
    std::string memory_id;
    std::string reason;           // e.g. provenance is simulation
    json        raw;
};

struct AuditReport {
    bool                             clean = false;
    std::vector<ContaminationFinding> findings;
    std::string                      text;      // server's human-readable report
    json                             raw;
};

struct EpistemicReceipt { std::string fact_id; EpistemicStatus status; std::string text; };
```

`audit_contamination()` asks the server to detect (a) any high-confidence memory whose
ultimate provenance is simulation, and (b) any simulated content leaking into grounded
indexes.

---

## Thread-safety

A `Session` is **not** thread-safe. Concurrent callers must either serialize calls or
hold one `Session` per thread. `ServerInfo` and `ToolDescriptor` values are plain data
and may be shared once obtained.

---

## What is intentionally absent

| Absent API | Why |
|---|---|
| `delete_memory`, `erase_ledger`, `update_ledger` | ledger is append-only; no mutation surface is offered |
| `store(SimulatedMemory)` on a grounded call | the partition is a *type* boundary, not a flag |
| Any implicit promotion | promotion requires an explicit `PromotionRequest` with evidence |
| Hard-coded `protocolVersion` | negotiated in the handshake and echoed from `ServerInfo` |
