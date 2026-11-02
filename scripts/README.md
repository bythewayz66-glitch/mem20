# Repository scripts — `scripts/`

Operational and maintenance scripts. None of these are imported by the server;
they are run by hand or by CI.

**8 tracked file(s).**

## Contents

- `sweep-tool-counts.py` — converge frontend surfaces on the live tool/domain count
- `check_launch_gate.py` — launch-gate assertions
- `audit_market_claims.py` — check market claims against their sources
- `validate_controlz_desktop.py` — desktop control-surface validation
- `vendor_into_members.sh` — vendor shared code into member packages
- `ops/scoreboard_signals.sh` — ops scoreboard signals
- `renovation/build_inventory.py`, `renovation/conformance.py` — renovation inventory and conformance checks

## Usage

```bash
python3 scripts/sweep-tool-counts.py          # dry run
python3 scripts/sweep-tool-counts.py --apply  # write
```

## Notes

`sweep-tool-counts.py` carries the canonical tool/domain numbers in `TOOLS` and
`DOMAINS`. When the surface changes, update those two constants first, then sweep —
otherwise the script will rewrite docs to a stale number.

---

Part of the [mem20 monorepo](../README.md). See [`docs/INDEX.md`](../docs/INDEX.md) for the full documentation map.
