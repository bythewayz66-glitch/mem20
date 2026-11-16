## 2. Surface of record

| Ref | Claim | Verified value | Status | Command (settles it) | Adversarial |
|---|---|---|---|---|---|
| S1 | Surface of record | **487 tools / 129 domains** | **VERIFIED** | `python3 -c "import json;d=json.load(open('docs/surface.json'));print(d['tools'],d['domains'])"` | `n/a: surface count` |
| S2 | Doc-count gate agrees | `live pin: 487 tools / 129 domains`; `OK: no retired tool/domain band in any live doc`; exit 0 | **VERIFIED** | `python3 scripts/ops/check-doc-counts.py` | `n/a: gate output` |
| S3 | GTM claim gate agrees | `surface of record: 487 <- MEM20_EXPECTED_TOOLS in .github/workflows/mcp-verify.yml`; `RESULT: PASS` | **VERIFIED** | `python3 scripts/check_gtm_claims.py` | `n/a: gate output` |
| S4 | `docs/02-tools-reference.md` | prints **487 tools across 129 domains** in its header | **VERIFIED** | `sed -n '1,8p' docs/02-tools-reference.md` | `n/a: doc state` |
| S5 | `README.md` | `\| MCP tools \| **487** \|` | **VERIFIED** | `grep -n '487' README.md` | `n/a: doc state` |
| S6 | `docs/gtm/README.md` | still prints **270 tools across 27 domains** | **STALE** | `grep -n '270 tools' docs/gtm/README.md` | `n/a: doc state` |
| S7 | `docs/gtm/mem20-sales-one-pager.md` | still prints **270 tools / 27 domains** and **MIT** | **STALE** | `grep -n '270 tools\|MIT' docs/gtm/mem20-sales-one-pager.md` | `n/a: doc state` |
