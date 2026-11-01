# gateway

The fleet relay. One place where a message crosses from one agent to another —
and the one place where a message can be posted **as a human**.

## Admission control

A relay that will carry anything is a relay that will carry an impersonation,
and a relay with no audit trail cannot tell you afterwards what it carried.
`relay.py` is the policy, on the path every message takes. Six estate modules
are consulted, and each answers a question the relay cannot answer for itself:

| Estate module | Question it answers | Refusal |
|---|---|---|
| `mem20liez.gates.check_prohibited_uses` | may this message be sent for the declared purpose at all? | `prohibited_use` |
| `mem20ops.clicheck.classify_naming` | is the agent name an estate address, or an unroutable string? | `naming` |
| `mem20verify.linters.noop_bodies` | is the relay's handler body real, or `pass`? | `stub_body` |
| `mem20temporaldatabasefabricz.temporal.interval.contains` | is this timestamp inside its validity window, or a replay? | `outside_window` |
| `mem20ircz.filter.classify` + `NoiseMeter` | which transport lines are signal, and how much was swallowed? | (filters, never refuses) |
| `mem20dreamz.ledger.commit_raw` | where is this message recorded, and was it committed? | (records, never refuses) |

A refusal raises `RelayRefused` and the message is **not written**. A relay that
writes first and validates later has already relayed it.

`send_human_message` is the estate's impersonation surface, so it is the one
tool that *requires* a declared intended use. Without one it returns
`check: undeclared_use` rather than posting.

## Usage

```bash
# register this agent — the generated name is an estate address
python3 gateway/hermes_gateway.py register --location sidney

# list registered agents
python3 gateway/hermes_gateway.py list

# broadcast, declaring what the message is for
python3 gateway/hermes_gateway.py broadcast "pump 3 is down" \
    --agent-name mem20-sidney-abc12345 --intended-use fleet_status

# read back what the fleet actually said
python3 gateway/hermes_gateway.py read --limit 10
```

A prohibited use is refused and nothing is written:

```bash
python3 gateway/hermes_gateway.py broadcast "hold them" \
    --agent-name mem20-sidney-abc12345 --intended-use automated_detention
```

```json
{
  "refused": true,
  "check": "prohibited_use",
  "reason": "prohibited_use: Automated detention or restraint decisions are prohibited."
}
```

Every accepted message carries its admission record and its provenance:

```json
{
  "agent_name": "mem20-sidney-abc12345",
  "message": "pump 3 is down",
  "admission": {
    "naming": "mem20-native",
    "intended_uses": ["fleet_status"],
    "wire_kept": 1,
    "wire_swallowed": 1,
    "wire_reasons": {"numeric.motd": 1},
    "stub_issues": 0,
    "window_ok": true
  },
  "provenance": {"committed": false, "reason": "braid unreachable"}
}
```

## Tool catalog

`gateway_tools.py` exposes the same operations to the MCP server via
`get_gateway_tools()` / `call_gateway_tool()`. `broadcast`, `send_to_agent` and
`send_human_message` all go through `relay.admit`.

## Tests

```bash
python3 -m pytest gateway/tests -q
```

## Defects fixed in this pass

- `read_messages` filtered on `m["agent"]` and printed `m['agent']`, but every
  entry written by `broadcast` carries `agent_name`. Any call with `--agent`
  raised `KeyError`, and any call at all raised `KeyError` on the print.
- `MEM20_DIR` was hardcoded to `/opt/mem20` in both modules, so the gateway only
  worked on one box and silently imported a *different* gateway elsewhere.
- `hermes_gateway.py` and `mem20_gateway.py` were 218-line near-duplicates that
  had already drifted: the `hermes-` prefix produced agent names that classify
  as `other`, so agents registered through that copy had addresses no other
  subsystem recognised. There is now one implementation; `mem20_gateway.py`
  re-exports it.
- `send_human_message` wrote an entry with no admission at all.
