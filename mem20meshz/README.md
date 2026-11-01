# mem20 Mesh Gold Runtime

Six domain mesh engines are **vendored** under `mem20meshz.meshes`:

- crisis (ex `mem20crisisresponsemeshz`)
- crossdevice (ex `mem20crossdevicememorymeshz`)
- federated (ex `mem20federatedmodellearningmeshz`)
- nearby (ex `mem20nearbydevicemeshz`)
- offline (ex `mem20offlineresiliencemeshz`)
- selfhealing (ex `mem20selfhealingconnectormeshz`)

The old top-level packages are removed after consolidation.

## Admission control

Consolidating six subsystems into one dispatcher is exactly where a policy that
lived in one of them stops being enforced. `mem20meshz.governance` is that
policy, in one place, on the path every mesh execution takes. Six estate
modules are consulted, and each answers a question the mesh runtime cannot
answer for itself:

| Estate module | Question it answers | Refusal |
|---|---|---|
| `mem20liez.gates.check_prohibited_uses` | may this mesh be used for the declared purpose at all? | `prohibited_use` |
| `mem20ops.clicheck.classify_naming` | is the tool name an estate name, or a misroute? | `naming` |
| `mem20verify.linters.noop_bodies` | is the mesh's engine body real, or `pass`? | `stub_body` |
| `mem20temporaldatabasefabricz.temporal.interval.contains` | is this instant inside the mesh's operating window? | `outside_window` |
| `mem20ircz.filter.classify` + `NoiseMeter` | which wire lines are signal, and how much was swallowed? | (filters, never refuses) |
| `mem20dreamz.ledger.commit_raw` | where is this execution recorded, and was it committed? | (records, never refuses) |

A refusal raises `MeshRefused` and the mesh does not run. It is reported per
mesh, never silently skipped and never dispatched anyway.

## Usage

```bash
# list the six meshes
python3 -m mem20meshz list

# run one mesh through admission control
python3 -m mem20meshz execute '{"text": "pump 3 is down"}' --only crisis

# what admission control decided for the last execute
python3 -m mem20meshz admission

# where each execution was recorded, and whether braid committed it
python3 -m mem20meshz provenance
```

A refused execution is reported in the result, not raised out of the CLI:

```bash
python3 -m mem20meshz execute '{"intended_uses": ["automated_detention"]}' --only crisis
```

```json
{
  "mesh": "mem20meshz",
  "results": {
    "crisis": {
      "refused": true,
      "check": "prohibited_use",
      "reason": "prohibited_use: Automated detention or restraint decisions are prohibited."
    }
  }
}
```

Wire noise is dropped before a mesh sees it, and the saving is reported as
evidence rather than claimed:

```bash
python3 -m mem20meshz execute '{"wire": [{"command": "372", "text": "- motd"}, {"command": "PRIVMSG", "text": "pump 3 is down", "prefix": "ana!u@h", "params": ["#ops"]}]}' --only crisis
python3 -m mem20meshz admission
```

```json
{
  "crisis": {
    "mesh": "crisis",
    "tool": "mem20meshz_crisis",
    "naming": "mem20-native",
    "wire_kept": 1,
    "wire_swallowed": 1,
    "wire_waste_ratio": 0.5,
    "wire_reasons": {"numeric.motd": 1},
    "stub_issues": 0,
    "window_ok": true
  }
}
```

## Tests

```bash
python3 -m pytest mem20meshz/tests -q
```

`tests/test_governance.py` drives `MasterEngine.execute` -- the same entry point
the CLI and the MCP tool use -- and asserts on what the estate modules decided,
not on a mock of them.
