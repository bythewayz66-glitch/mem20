# Top-level test suite — `tests/`

Cross-cutting tests that exercise the server, memory API, retrieval, safety and
namespace ACLs. Per-subsystem tests live next to their subsystem.

**14 tracked file(s).**

## Contents

- `conftest.py` — shared fixtures
- `test_mcp_dispatch.py` — tool dispatch through the server
- `test_memory_api.py` — memory API behaviour
- `test_retrieval_graph.py`, `test_rerank_no_silent_noop.py` — retrieval and rerank guards
- `test_namespace_acl.py` — namespace access control
- `test_phase7_safety.py`, `test_phase8_1_engine.py` — safety and engine phases
- `test_llm_fallback.py`, `test_llm_dotenv_isolation.py` — LLM provider fallback and env isolation
- `test_self_model_identity.py`, `test_world_model.py` — self-model and world-model behaviour
- `test_mem20path.py`, `test_qa5000_harness.py` — path resolution and QA harness

## Usage

```bash
python3 -m pytest tests/ -q
```

## Notes

`test_rerank_no_silent_noop.py` exists to catch a reranker that silently degrades
to a no-op — do not weaken it to make a change pass.

---

Part of the [mem20 monorepo](../README.md). See [`docs/INDEX.md`](../docs/INDEX.md) for the full documentation map.
