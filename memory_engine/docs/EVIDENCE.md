# M0 EVIDENCE — memory_engine importable core contract

Baseline commit: d99ab5d8e9c5c45a1fb3d02d3b65b2f9a96b5110
Date: 2026-11-01T22:27:36Z
Python: Python 3.11.15

## 1. Baseline state (before M0)

$ wc -c memory_engine/__init__.py
0 memory_engine/__init__.py

$ grep -c "^version" pyproject.toml; cat VERSION
version = "3.0.0"  (pyproject.toml:7)
3.1.2  (VERSION)

## 2. New tests pass

$ python3 -m pytest memory_engine/tests/test_contract.py memory_engine/tests/test_error_model.py memory_engine/tests/test_properties.py -q

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
60 passed, 4 warnings in 2.11s

## 3. Full memory_engine suite (pre-existing tests included)

$ python3 -m pytest memory_engine/tests -q --ignore=memory_engine/tests/test_pii_non_destructive.py
=========================== short test summary info ============================
FAILED memory_engine/tests/test_fact_fiction_labeling.py::TestLabelSurvivesEveryRetrievalSurface::test_recall_semantic_returns_the_label
FAILED memory_engine/tests/test_fact_fiction_labeling.py::TestLabelSurvivesEveryRetrievalSurface::test_recall_hybrid_returns_the_label
2 failed, 150 passed, 4 warnings in 3.36s

## 4. Public surface

$ python3 -c "import memory_engine; print(len(memory_engine.__all__), memory_engine.__version__)"
names: 50
version: 3.1.2

## 5. Health report on a fresh store

$ MEM20_STORE_PATH=$(mktemp -d) python3 -c "from memory_engine import MemoryEngine; print(MemoryEngine().health().to_dict())"
{'healthy': False, 'store_path': '/tmp/tmp.wbZBdIU29l', 'ledger_records': 0, 'indexes': {'vector': {'index': 'vector', 'present': False, 'healthy': False}, 'bm25': {'index': 'bm25', 'present': False, 'healthy': False}, 'graph': {'index': 'graph', 'present': False, 'healthy': False}}, 'config': {'store_path': '/tmp/tmp.wbZBdIU29l', 'sim_ttl_days': 30, 'rerank_enabled': True, 'rerank_model': 'cross-encoder/ms-marco-MiniLM-L-6-v2', 'mem_cap': 2200, 'user_cap': 1375}}

## 6. Import cost — package import does not pull native deps

$ python3 -c "import sys, memory_engine; print([m for m in (\"numpy\",\"faiss\",\"sentence_transformers\") if m in sys.modules])"
[]

## 7. No regression in pre-existing tests (git stash comparison)

tests/test_retrieval_graph.py  BEFORE M0: 7 failed, 20 passed
tests/test_retrieval_graph.py  AFTER  M0: 7 failed, 20 passed

## 8. Files added

 M memory_engine/__init__.py
?? memory_engine/api.py
?? memory_engine/config.py
?? memory_engine/docs/
?? memory_engine/errors.py
?? memory_engine/tests/test_contract.py
?? memory_engine/tests/test_error_model.py
?? memory_engine/tests/test_properties.py
