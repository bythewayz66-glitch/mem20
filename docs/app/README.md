# App / product narrative — `docs/app/`

Entry point for the `docs/app/` documentation set. **25 tracked file(s).**

## Contents

- [`.nojekyll`](.nojekyll)
- [`assets/index-BMgU54DU.css`](assets/index-BMgU54DU.css)
- [`assets/index-DCqPYDUE.js`](assets/index-DCqPYDUE.js)
- [`continuum/index.html`](continuum/index.html)
- [`deck/PERMANENT_URL.md`](deck/PERMANENT_URL.md)
- [`transport/index.html`](transport/index.html)
- [`deck/index.html`](deck/index.html)
- [`deck/slides/README.md`](deck/slides/README.md)
- [`deck/slides/slide_01.html`](deck/slides/slide_01.html)
- [`deck/slides/slide_02.html`](deck/slides/slide_02.html)
- [`deck/slides/slide_03.html`](deck/slides/slide_03.html)
- [`deck/slides/slide_04.html`](deck/slides/slide_04.html)
- [`deck/slides/slide_05.html`](deck/slides/slide_05.html)
- [`deck/slides/slide_06.html`](deck/slides/slide_06.html)
- [`deck/slides/slide_07.html`](deck/slides/slide_07.html)
- [`deck/slides/slide_08.html`](deck/slides/slide_08.html)
- [`deck/slides/slide_09.html`](deck/slides/slide_09.html)
- [`deck/slides/slide_10.html`](deck/slides/slide_10.html)
- [`deck/slides/slide_11.html`](deck/slides/slide_11.html)
- [`deck/slides/slide_12.html`](deck/slides/slide_12.html)
- [`deck/slides/slide_13.html`](deck/slides/slide_13.html)
- [`desktop-packaging.md`](desktop-packaging.md)
- [`fleet/index.html`](fleet/index.html)
- [`index.html`](index.html)
- [`narrative/serial-2026-10-27.md`](narrative/serial-2026-10-27.md)

## Continuum monitor (`continuum/`)

[`continuum/index.html`](continuum/index.html) is the estate-shell view of the
Edge-to-Cloud Intelligence Continuum (RM-214). Static page, reads the
subsystem's JSON API (`?api=http://host:port`), shows health/targets/workloads
and can run `doctor`. It owns no state.

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20edgetocloudintelligencecontinuumz serve --port 8791
# -> http://127.0.0.1:8000/continuum/?api=http://127.0.0.1:8791
```


## Transport fabric monitor (`transport/`)

[`transport/index.html`](transport/index.html) is the estate-shell view of the
Edge Transport Fabric (RM-077). Static page, reads the subsystem JSON API
(`?api=http://host:port`), shows fabric health/nodes/links/flows and can run
`doctor`. It owns no state.

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20edgetransportfabricz serve --port 8782
# -> http://127.0.0.1:8000/transport/?api=http://127.0.0.1:8782
```

## Fleet monitor (`fleet/`)

[`fleet/index.html`](fleet/index.html) is the estate-shell view of the Edge Fleet
Brain (RM-041). It is a static page: it owns no state and reads the subsystem's
own JSON API, so the operator cockpit served by the fleet process and this page
cannot drift apart.

```bash
# start the subsystem that owns the state plane
PYTHONPATH=/opt/mem20 python3 -m mem20edgefleetbrainz --store /tmp/fleet.db serve --port 8771

# open the monitor against it (also accepts ?api=http://host:port)
python3 -m http.server 8000 --directory docs/app
# -> http://127.0.0.1:8000/fleet/?api=http://127.0.0.1:8771
```

The page shows fleet health, node load, the workload queue, the fault forecast,
the 24 h energy projection and the live event stream, and it can run the six
scenario simulator, probe all six ecosystem peers and plan a rebalance. The
`API` field persists in `localStorage`; `?api=` overrides it for the session.
The full operator cockpit (node registration, dispatch, drain/evacuate) is
served by the fleet process itself at its root URL.

## Conventions

- Every file in this directory is linked from this index; add a row when you add a file.
- Dated records (audits, ops logs, verification runs) are append-only — do not rewrite
  historical numbers in them; correct the live docs instead.
- Tool/domain counts in this tree must match the live surface. Derive, never hand-count:
  `python3 web/scripts/extract-tools.py --root . --out /tmp/tools.json`

- [Audio/Voice/Music Pipeline monitor](audiovoiceandmusicpipelinez/index.html) — run `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20audiovoiceandmusicpipelinez serve --port 8781` and connect the estate monitor to its API.
- [Autonomous Deal Desk monitor](autonomousdealdeskz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz serve --port 8782`
- [Autonomous Micro-SaaS Foundry monitor](autonomousmicrosaasfoundryz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousmicrosaasfoundryz serve --port 8783`
- [Autonomous Recovery Director monitor](autonomousrecoverydirectorz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousrecoverydirectorz serve --port 8784`
- [Autonomous Sales Laboratory monitor](autonomoussaleslaboratoryz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussaleslaboratoryz serve --port 8785`
- [Autonomous Software Foundry monitor](autonomoussoftwarefoundryz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussoftwarefoundryz serve --port 8786`
- [Autonomous Workcells monitor](autonomousworkcellsz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousworkcellsz serve --port 8787`
- [Business Model Simulator monitor](businessmodelsimulatorz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20businessmodelsimulatorz serve --port 8788`
