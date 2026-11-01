// docs/sdk/cpp/examples/store_recall_audit.cpp
//
// mem20 C++ SDK — end-to-end walkthrough: store -> recall -> audit.
//
// Requires the built mem20_sdk headers (include/mem20/*.hpp) and a running mem20
// server entry point (mcp/mcp_server.py in the canonical repo).
//
// Build (from the repo root, using the SDK's own CMake target):
//     cmake -S sdk/cpp -B build/cpp -G Ninja -DCMAKE_BUILD_TYPE=Release
//     cmake --build build/cpp
//     MEM20_SERVER=/abs/path/to/mem20/mcp/mcp_server.py ./build/cpp/mem20_store_recall_audit
//
// Requires C++17 (uses C++17 structured bindings / std::optional); the SDK enables
// C++20 features opportunistically when the toolchain provides them.

#include <mem20/client.hpp>

#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

namespace {

void print_ledger(mem20::Session& session) {
    // The ledger is append-only and exposed READ-ONLY. This function only reads.
    mem20::LedgerFilter filter;
    filter.action = "remember";
    filter.limit  = 10;

    auto entries = session.read_ledger(filter);
    if (!entries) {
        std::cerr << "read_ledger failed: " << entries.detail() << "\n";
        return;
    }
    for (const auto& e : *entries) {
        std::cout << "  " << e.ts
                  << "  origin=" << e.origin
                  << "  store="  << e.store
                  << "  status=" << e.epistemic_status
                  << "  " << e.content.substr(0, 72) << "\n";
    }
}

}  // namespace

int main() {
    const char* server_path = std::getenv("MEM20_SERVER");
    if (server_path == nullptr || *server_path == '\0') {
        std::cerr << "MEM20_SERVER is not set.\n"
                     "Point it at the mem20 entry point, e.g.\n"
                     "  MEM20_SERVER=/abs/path/to/mem20/mcp/mcp_server.py "
                     "./build/cpp/mem20_store_recall_audit\n";
        return 2;
    }

    // --- 1. Configure + spawn -------------------------------------------------
    // Session is RAII: it owns the child process and tears it down in its destructor.
    auto cfg = mem20::ServerConfig::python_script(server_path);
    cfg.env.emplace_back("MEM20_STORE_PATH", "/tmp/mem20-cpp-sdk-demo/store");

    auto spawned = mem20::Session::spawn(cfg);
    if (!spawned) {
        std::cerr << "spawn failed: " << spawned.detail() << "\n";
        return 1;
    }
    mem20::Session session = std::move(*spawned);

    std::cout << "handshake ok\n"
              << "  protocolVersion=" << session.server_info().protocol_version
              << "  serverInfo="     << session.server_info().server_info
              << "\n";

    // --- 2. Discovery --------------------------------------------------------
    auto tools = session.list_tools();
    if (!tools) {
        std::cerr << "tools/list failed: " << tools.detail() << "\n";
        return 1;
    }
    std::cout << "discovered " << tools->size() << " tools\n";

    // --- 3. STORE a grounded fact -------------------------------------------
    // GroundedMemory maps to memory_store. There is no overload that accepts a
    // SimulatedMemory here: the partition is enforced by the type system.
    mem20::GroundedMemory fact;
    fact.content  = "mem20's canonical repository is bythewayz66-glitch/mem20 (branch main)";
    fact.category = mem20::MemoryCategory::Project;
    fact.tags     = {"canonical", "repo"};

    auto stored = session.store(fact);
    if (!stored) {
        std::cerr << "memory_store failed: " << stored.detail() << "\n";
        return 1;
    }
    std::cout << "stored grounded id=" << stored->id << "\n";

    // --- 4. SIMULATE a counterfactual (separate partition) -------------------
    mem20::SimulatedMemory whatif;
    whatif.topic   = "repo-hosting";
    whatif.content = "Suppose the canonical repo later moved to another org.";
    whatif.tags    = {"hypothetical"};

    auto simulated = session.simulate(whatif);
    if (simulated) {
        std::cout << "stored simulated sim_id=" << simulated->sim_id << "\n";
    } else {
        std::cerr << "warning: memory_simulate_store failed: "
                  << simulated.detail() << "\n";
    }

    // --- 5. RECALL (grounded-only indexes) ----------------------------------
    mem20::RecallOptions opts;
    opts.category = mem20::MemoryCategory::Project;
    opts.limit    = 5;

    auto hits = session.recall("canonical repository", opts);
    if (!hits) {
        std::cerr << "memory_recall failed: " << hits.detail() << "\n";
        return 1;
    }
    std::cout << "recall returned " << hits->size() << " hit(s)\n";
    for (const auto& h : *hits) {
        std::cout << "  [" << h.score << "] " << h.id << "  "
                  << h.content.substr(0, 72) << "\n";
    }

    // --- 6. PROMOTION requires evidence -------------------------------------
    // A request with no confirmation and no resolved prediction error is refused
    // by the server ("VETO / BLOCKED"). Promotion is evidence-based, with an
    // append-only audit trail — we surface the refusal rather than hiding it.
    if (simulated) {
        mem20::PromotionRequest bad;
        bad.sim_id = simulated->sim_id;   // no confirmation, no prediction error

        auto refused = session.promote(bad);
        if (refused && refused->refused) {
            std::cout << "promotion correctly refused: " << refused->note << "\n";
        } else if (refused) {
            std::cout << "unexpected: promoted -> " << refused->grounded_id << "\n";
        }

        // The evidence-backed path (uncomment with a real external confirmation):
        // mem20::PromotionRequest ok;
        // ok.sim_id        = simulated->sim_id;
        // ok.confirmation  = "verified against the live repository listing";
        // auto promoted    = session.promote(ok);
    }

    // --- 7. AUDIT provenance -------------------------------------------------
    auto audit = session.audit_contamination();
    if (audit) {
        std::cout << "contamination audit: "
                  << (audit->clean ? "clean" : "findings present")
                  << " (" << audit->findings.size() << " finding(s))\n";
    } else {
        std::cerr << "memory_audit_contamination failed: "
                  << audit.detail() << "\n";
    }

    // --- 8. Read the append-only ledger (read-only by construction) ----------
    std::cout << "ledger tail:\n";
    print_ledger(session);

    // --- 9. Observability (outside the JSON-RPC session) ---------------------
    auto health = session.health();
    if (health) {
        std::cout << "health: " << (health->ok ? "ok" : "degraded") << "\n";
    }

    // session is destroyed here: the child process is shut down gracefully.
    std::cout << "done\n";
    return 0;
}
