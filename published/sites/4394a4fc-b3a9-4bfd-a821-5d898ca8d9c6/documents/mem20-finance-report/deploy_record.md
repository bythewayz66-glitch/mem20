# mem20 Finance Report — Sidney publish record

**As of:** 2026-10-14 · leg: transport/publish (Server Builder)
**Script run:** `documents/mem20-finance-report/deploy_finance_to_sidney.sh` (the shipped script, unmodified)
**Target:** `root@216.198.115.91:2222` (host `sidney`, Kali GNU/Linux Rolling)

---

## 1. Transport (ssh/rsync) — SUCCESS

The shipped script read its destination from the environment (`SIDNEY_HOST=216.198.115.91`,
`SIDNEY_PORT=2222`, `SIDNEY_USER=root`, `GABE_HOST`/`GABE_USER`/`GABE_PORT=2222`, `GABE_BIN=/opt/mem20/gabe/bin/gabe`).
No secret was written into the payload — authentication travelled as an `SSH_KEY`
(`/root/.ssh/id_sidney`) / `SSHPASS` environment value only.

Script output (verbatim):

```
[deploy] staged report page from .../payload-report/index.html
[deploy] generating SHA256SUMS
[deploy] payload: 9 file(s)
[deploy] routing through gabe at 216.198.115.91
[deploy] ensuring remote directory /opt/mem20/finance
[deploy] dry-run transfer
[deploy] transferring
sent 28,091 bytes  received 743 bytes  19,222.67 bytes/sec
total size is 151,261  speedup is 5.25
```

Landed on Sidney: 9 regular files, 91,880 bytes of payload content, at
`/opt/mem20/finance/` — report page at
`/opt/mem20/finance/webpages/mem20-finance-report/index.html`
(sha256 `a0a904614c9672aaa9a2872d9e9c30e6f6ea3d154dc0cd88a26b4055792d92fe`, 59,178 bytes).

## 2. gabe gate — RAN, verdict captured

The script's step‑4 gate check and step‑5 publish were executed by the deployed gate
(`/opt/mem20/gabe/bin/gabe`, made executable this run — sha unchanged at `d87c5014dc55ec94…`).

Step 4 (the script's own gabe check) returned, verbatim:

```json
{ "halted": false, "chain": "chain ok (124 entries)", "chain_ok": true,
  "published_artifacts": 22, "rule_bundle_sha256": "4192add05f09722f",
  "live_root": "/opt/mem20/live" }
```

`gabe verify` → `OK: chain ok (124 entries)`.

Step 5 (the script's publish step) — **documented failure, fail-closed**:

```
[deploy] publishing under gabe control
usage: gabe publish [-h] --requirement REQUIREMENT --producer PRODUCER
                    --producer-session PRODUCER_SESSION
                    [--claims [CLAIMS ...]] [--evidence EVIDENCE] artifact
gabe publish: error: the following arguments are required: --requirement, --producer, --producer-session
```

The deployed gate's `publish` verb takes a **single artifact** plus its written
requirement, producer and session — the script passes only a directory, so gabe takes
none of it and **nothing was published through gabe** and **nothing bypassed it**.
The finance bundle therefore has no gabe manifest entry; the live surface is unchanged
by this leg.

## 3. Verification (script step 6) — PASS

Target-side, on Sidney:

```
$ cd /opt/mem20/finance/documents/mem20-finance-report && sha256sum -c SHA256SUMS
./README.md: OK
./data/corrections_register.csv: OK
./data/market_sizing.csv: OK
./data/repo_dependencies.csv: OK
./data/unit_economics.csv: OK
./deploy_finance_to_sidney.sh: OK
./model/compute_model.py: OK
TARGET_SHA_EXIT=0
```

**7 / 7 files OK, exit 0** — the published bundle matches the checksums Finance Assistant
shipped. The report page was verified separately (above); it is intentionally not in
`SHA256SUMS`, which covers the document bundle.

## 4. Notes

- The gate is a live, stressed, multi-writer surface: during this leg other lanes
  (pricing-analyst, campaign-ops-agent, mem20-content) were being **refused** by the
  same judge on comparable requirements, and the chain grew from 12 → 124 entries.
  Any further finance publish must re-run through gabe at a quiet moment.
- The official script's gate step, as written, does not gate this bundle (single-artifact
  `publish` signature vs directory argument) — recorded here as the leg's finding, not patched.
- No off-spec patches were made to `compute_model.py` and no argument was had with the judge.
