# mem20executablegameconceptandscopepipelinez — Executable Game Concept & Scope Pipeline (RM-237, #309)

**Outcome:** turn a game concept into measurable mechanics, dependency graphs, prototypes, and scope simulations.  
**Breakthrough:** scope is validated through running systems rather than documents.

First-class `graph` operation (CAPABILITY/Engine preserved) that enriches concept/scope analysis with real domain evaluation (`concept_score`, `scope_estimate`, `feasibility_check`, `risk_assessment`, `pipeline_stage`) and, for explicit scope requests, 6 **unique** peer integrations (different from #300–#308). Legacy domain API is preserved (used as a peer by #307).

## Legacy domain API (preserved)
`concept_score(concept)`, `scope_estimate(concept)`, `feasibility_check(concept, budget_weeks=24)`, `risk_assessment(concept)`, `pipeline_stage(concept)`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls | Contribution |
|---|---|---|
| `mem20gameproductioncontrolcenterz` | `sprint_plan`,`burndown`,`milestone_status`,`risk_score`,`production_health` | sprint/milestone/risk planning |
| `mem20aiproductionstudiooperatingsystemz` | `schedule_projects`,`resource_allocation`,`milestone_progress`,`critical_path`,`studio_health` | studio scheduling/resource/milestone ops |
| `mem20productledgrowthsimulatorz` | `funnel`,`viral_coefficient`,`retention_curve`,`growth_score`,`simulate` | growth/retention feasibility signal |
| `mem20autonomoussoftwarefoundryz` | `spec_to_tasks`,`code_quality`,`deploy_decision`,`estimate_effort`,`build_artifact`,`foundry_report` | spec-to-tasks/effort/build feasibility |
| `mem20aigamestudiobuilderz` | `scaffold_project`,`asset_pipeline`,`build_config`,`estimate_size`,`validate_project` | game project scaffold/asset/build validation |
| `mem20autonomousmicrosaasfoundryz` | `score_idea`,`mvp_spec`,`launch_plan`,`revenue_projection`,`idea_ranking`,`foundry_report` | idea/MVP/launch/revenue feasibility |

## Runnable example (verified)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20executablegameconceptandscopepipelinez simulate
```

Observed: 10 Engine simulator scenarios `ok=true` (`success`, `malformed`, `disconnection`, `overload`, `provider_loss`, `restart_recovery`, `adversarial_payload`, `privacy_guard`, `misuse_guard`, `replica_conflict`).

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20executablegameconceptandscopepipelinez execute '{"concept":{"name":"demo","innovation":7,"market_fit":6,"feasibility":6,"features":["core-loop","ui","save"],"complexity":"medium"},"budget_weeks":24}'
```

Returns legacy graph fields (`nodes/edges/degree/hubs`) plus `concept_score`, `scope`, `feasibility`, `risk_assessment`, `pipeline_stage`, and 6 peer `signals` (all `ok:true`) for explicit scope requests.

HTTP: `/health`, `/spec`, `/metrics`, `/events`, `/objects`, `/doctor` (peer probe), `/execute`, `/feedback`, `/replica/merge`, `/jobs/<id>/cancel`, cockpit at `/`.

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20executablegameconceptandscopepipelinez serve --port 8789
```

## Tests / conformance

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20executablegameconceptandscopepipelinez/tests/test_scope_pipeline.py mem20executablegameconceptandscopepipelinez/mem20executablegameconceptandscopepipelinez/tests/test_domain.py mem20executablegameconceptandscopepipelinez/tests/test_concept.py --noconftest -q
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20executablegameconceptandscopepipelinez
```

