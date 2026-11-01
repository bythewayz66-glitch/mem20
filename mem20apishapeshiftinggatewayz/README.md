# RM-075 - API Shape-Shifting Gateway

Outcome: Translate between incompatible schemas, pagination styles, auth flows, and interaction patterns

Breakthrough: One stable internal API can face thousands of external services

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `route` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Admission control

This gateway's whole job is to rewrite payloads before they reach a service, and
a rewrite is exactly where a field silently disappears. `governance.py` is the
policy, on the path every translation takes. Six estate modules are consulted,
and each answers a question the gateway cannot answer for itself:

| Estate module | Question it answers | Refusal |
|---|---|---|
| `mem20ops.clicheck.classify_naming` | is the route an estate address, or one no upstream will match? | `naming` |
| `mem20liez.gates.check_prohibited_uses` | may this payload be translated for the declared purpose? | `prohibited_use` |
| `mem20verify.linters.noop_bodies` | is the transform body real, or `pass`? | `stub_body` |
| `mem20temporaldatabasefabricz.temporal.interval.contains` | is this API version live at that instant? | `outside_window` |
| `mem20ircz.filter.classify` + `NoiseMeter` | which upstream lines are signal, and how much was swallowed? | (filters, never refuses) |
| `mem20dreamz.ledger.commit_raw` | what did this gateway actually send upstream? | (records, never refuses) |

Plus a round-trip check on the transform itself: a mapping that collapses two
fields onto one key is refused as `lossy_transform`, because the translation
would report success and the value would be gone.

A refusal raises `GatewayRefused` and the payload is **not** transformed.

Note that payload keys are domain data, not addresses - `goal` and `candidates`
are ordinary words. Only the route is held to the naming convention.

## Usage

```bash
# route a payload through admission control
python3 -m mem20apishapeshiftinggatewayz execute '{"goal": "route this", "candidates": [{"id": "a", "utility": 0.9}]}'

# what admission control decided for the last translation of each route
python3 -m mem20apishapeshiftinggatewayz admission

# where each translation was recorded, and whether braid committed it
python3 -m mem20apishapeshiftinggatewayz provenance

# the HTTP console and API
python3 -m mem20apishapeshiftinggatewayz serve --port 8080
```

A prohibited use is refused and nothing is transformed:

```bash
python3 -m mem20apishapeshiftinggatewayz execute '{"goal": "x", "intended_uses": ["automated_detention"]}'
```

```
mem20apishapeshiftinggatewayz.governance.GatewayRefused: prohibited_use: Automated detention or restraint decisions are prohibited.
```

A lossy mapping is refused rather than shipped:

```bash
python3 -m mem20apishapeshiftinggatewayz execute '{"goal": "x", "a": 1, "b": 2, "mapping": {"a": "same", "b": "same"}}'
```

```
mem20apishapeshiftinggatewayz.governance.GatewayRefused: lossy_transform: mapping collapses 3 fields into 2; a translated field would silently disappear
```

Every accepted translation carries its admission record:

```json
{
  "route": "mem20_rm-075",
  "naming": "mem20-native",
  "round_trip": {"mapping": {}, "fields_in": 2, "fields_out": 2},
  "intended_uses": ["schema_translation"],
  "wire_kept": 1,
  "wire_swallowed": 1,
  "wire_reasons": {"numeric.motd": 1},
  "stub_issues": 0,
  "window_ok": true
}
```

## Tests

```bash
python3 -m pytest mem20apishapeshiftinggatewayz/tests -q
```

## Defect fixed in this pass

The default route was the roadmap id (`RM-075`), which classifies as `other` -
no upstream would match it. It is now the estate-prefixed form (`mem20_rm-075`),
which is the address the rest of the estate resolves.
