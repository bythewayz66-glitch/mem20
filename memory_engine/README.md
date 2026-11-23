# memory_engine

The mem20 memory engine: a grounded, epistemically-labelled ledger with hybrid
retrieval, plus the **4.0 substrate** — the stable public API the rest of the
estate wires against.

## Install

mem20 is **source-only** — it is not published on PyPI.

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
# optional vector retrieval
pip install -e ".[vector]"
```

## Quick start

```bash
export MEM20_STORE_PATH=$(mktemp -d)
python3 -m memory_engine remember --topic demo --content "the sky is blue" --epistemic-status observed
python3 -m memory_engine recall --topic demo
python3 -m memory_engine health
```

```python
from memory_engine import MemoryEngine, EngineConfig
# or free functions:
from memory_engine import remember, recall, predict_next, as_of, create_episode, ingest
```

## What is stable

| Group | Names |
|---|---|
| Facade | `MemoryEngine`, `Fact`, `HealthReport` |
| Config | `EngineConfig`, `DEFAULT_STORE_PATH` |
| Errors | `MemoryEngineError` and subclasses |
| Engine functions | `remember`, `remember_simulated`, `recall`, `recall_at`, `recall_semantic`, `recall_hybrid`, `recall_graph`, `supersede`, `rebuild_*`, `index_health`, `status`, `ledger_view`, `backup`, secrets/gaps/audit helpers |
| Predictive | `predict_next`, `prefetch`, `record_recall_outcome`, `predictive_health` |
| Temporal | `as_of`, `timeline`, `diff`, `snapshot`, `temporal_health` |
| Episodic | `create_episode`, `add_event`, `link_episodes`, `recall_episodes`, `episode_graph`, `forget_episode`, `list_episodes` |
| Ingest | `ingest`, `ingest_batch`, `ingest_health` |
| Skills | `export_skill`, `import_skill`, `transfer_skill`, `list_transferred_skills` |
| Search | `cognitive_search`, `search_health` |
| Session | `save_session`, `load_session`, `list_sessions` |
| Verify | `verify_claim`, `verify_prediction`, `verify_batch` |
| Containment | `MemoryCircuit`, `quarantine_topic`, `is_quarantined`, `safe_recall` |

Everything named in package `__all__` is the contract. Import is lazy: `import memory_engine` does not load numpy/faiss/sentence-transformers until needed.

## Trust model

`remember()` requires an explicit `epistemic_status` (`observed | inferred | imagined | user_stated | hypothesis | agent_generated | unlabeled`). Simulated content cannot enter the grounded ledger — use `remember_simulated()` (separate partition, TTL).

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `MEM20_STORE_PATH` | `~/.mem20/store` | Store root (absolute) |
| `MEM20_SIM_TTL_DAYS` | `30` | Simulated-fact decay |
| `MEM20_RERANK` | `1` | Cross-encoder rerank on/off |

Set `MEM20_STORE_PATH` before the first engine access.

## First-class capabilities (absorbed into the engine)

These used to be separate `mem20*z` packages. They are now modules under
`memory_engine` and write/read the **grounded ledger** (firewall defaults to
grounded-only). Import them from `memory_engine` — do not depend on the old
package trees.

### Predictive recall (`memory_engine.predictive`)

Was `mem20predictiverecallenginez` / `mem20prez`.

Learns topic transitions and decayed access from real recall traffic, ranks
likely next topics, and prefetches via grounded `recall`.

```python
from memory_engine import predict_next, prefetch, record_recall_outcome

print(predict_next(context_topic="auth", k=5))
result = prefetch(context_topic="auth", k=3)  # grounded facts only by default
record_recall_outcome(result.event_id, used_fact_ids=[], useful=True)
```

### Temporal memory (`memory_engine.temporal`)

Was `mem20memorytimemachinez`.

`as_of` is a public name over `recall_at`. Timeline, diff, and snapshot operate
on ledger validity windows.

```python
from memory_engine import as_of, timeline, diff, snapshot

as_of("2026-11-01T00:00:00+00:00", topic="auth")
timeline("auth")
diff("2026-10-01T00:00:00+00:00", "2026-11-01T00:00:00+00:00", topic="auth")
snapshot(topic="auth")
```

### Episodic graph (`memory_engine.episodic`)

Was `mem20episodicmemorygraphz`.

Episodes and links are persisted as grounded facts (`episode:…`,
`episode_link:…`), not process-local lists.

```python
from memory_engine import create_episode, add_event, link_episodes, recall_episodes

ep = create_episode("login flow", events=[{"action": "open", "person": "alice"}])
add_event(ep, {"action": "token_issued"})
link_episodes(ep["id"], other_id, relation="follows")
recall_episodes("alice")
```

### Sensory / batch ingest (`memory_engine.ingest`)

Was `mem20sensorymemoryingestz`.

Normalizes text/image/audio/sensor payloads and writes grounded memories.

```python
from memory_engine import ingest, ingest_batch

ingest("button click at 12:01", modality="sensor", topic="ui.events")
ingest_batch([{"content": "hello", "modality": "text"}, {"content": {"px": 1}, "modality": "image"}])
```

### Skill transfer (`memory_engine.skills`)

Was `mem20skillmemorytransferz`.

Export/import procedural skills and mirror them onto the ledger as `skill:…` facts.

```python
from memory_engine import export_skill, import_skill, transfer_skill

transfer_skill("deploy")
import_skill({"name": "deploy", "description": "ship it", "steps": ["build", "push"]})
```

### Cognitive search (`memory_engine.search`)

Was `mem20personalcognitivesearchz`.

Ranked search over memory: hybrid (default), semantic, or keyword.

```python
from memory_engine import cognitive_search

cognitive_search("session token lifetime", k=10, mode="hybrid")
```

### Session continuity (`memory_engine.session`)

Was `mem20crossdevicesessioncontinuityz`.

Session state is a superseding grounded fact per `session_id` (optional `device_id` tags).

```python
from memory_engine import save_session, load_session

save_session("s-1", {"cursor": 12}, device_id="laptop")
load_session("s-1")
```

### Outcome verification (`memory_engine.verify`)

Was `mem20outcomeverificationruntimez`.

Check claims against the grounded ledger; record prediction usefulness via the predictive store.

```python
from memory_engine import verify_claim, verify_prediction, verify_batch

verify_claim("auth", expected_content="token")
verify_batch([{"topic": "auth"}, {"topic": "billing"}])
```

### Fault containment (`memory_engine.containment`)

Was `mem20faultcontainmentcellsz`.

Circuit breaker (closed → open → half-open, fail-fast) plus topic quarantine markers that `safe_recall` respects.

```python
from memory_engine import MemoryCircuit, quarantine_topic, is_quarantined, safe_recall

cell = MemoryCircuit(threshold=5, cool_down=30.0)
cell.call(lambda: "ok")
quarantine_topic("noisy.topic", reason="spam")
safe_recall(topic="noisy.topic")  # [] while quarantined
```

### Removed packages

Do not import or install the old package directories for the names above. The only supported API is `memory_engine`. See also `memory_engine/MEMBERS.md`.

## CLI

```bash
python3 -m memory_engine.memory remember --topic t --content "..." --epistemic-status observed
python3 -m memory_engine.memory recall --topic t --k 5
python3 -m memory_engine.memory status
python3 -m memory_engine.memory rebuild
```

## Tests

```bash
python3 -m pytest memory_engine/tests -q
```
