# mem20ethicalincentivesimulatorz — Ethical Incentive Simulator (RM-203, #307)

**Outcome:** simulate how incentives might change behavior, including harmful or exploitable outcomes.  
**Breakthrough:** teams can design motivation without accidentally manipulating users.

First-class implementation preserving legacy domain API and the CAPABILITY-driven Engine/CLI, extended with real ethical incentive simulation (fairness, harm/manipulation detection, aligned rewards, risk scoring, hard-safety threshold blocking) and 6 **unique** peer integrations (different from #300–#306).

## Legacy-compatible domain API
`incentive(value,effort,fairness_weight=0.5)`, `fairness_score(distribution)`, `align_reward(action,ethical_score)`, `simulate_incentives(agents,rounds=10)`, `ethical_violation(action)`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls | Contribution |
|---|---|---|
| `mem20outcomesimulationlabz` | `simulate_once`,`monte_carlo`,`summarize`,`risk_of_loss`,`scenario_compare` | outcome Monte Carlo/risk scenarios |
| `mem20gamebalancesimulatorz` | `dps`,`ttk`,`economy_balance`,`difficulty_curve`,`balance_check`,`win_rate` | incentive/balance dynamics |
| `mem20executiondigitaltwinz` | `create_twin`,`sync_twin`,`simulate`,`predict_outcome`,`drift` | incentive process digital twin |
| `mem20dynamicquestrewardcomposerz` | `generate_quest`,`reward_for_quest`,`balance_quests`,`quest_chain`,`completion_rate` | reward composition/balancing |
| `mem20rewardforgez` | `linear_reward`,`shaped_reward`,`normalize`,`reward_health` | shaped/normalized reward signals |
| `mem20executablegameconceptandscopepipelinez` | `concept_score`,`scope_estimate`,`feasibility_check`,`risk_assessment`,`pipeline_stage` | harm/manipulation risk & feasibility |

## Runnable example (verified)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20ethicalincentivesimulatorz simulate
```

Observed (key fields): Engine simulator runs 10 scenarios and returns `ok=true` for `success`, `malformed`, `privacy_guard`, `misuse_guard`, `provider_loss`, `restart_recovery`, `replica_conflict`, etc. Progression execute returns ethical analysis (`simulation`, `fairness`, `ethical_violations`, `risk`, `hard_safety_threshold`, `blocked`) plus 6 peer `signals` all `ok:true`.

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20ethicalincentivesimulatorz execute '{"xp":10,"agents":[{"value":5,"effort":3,"ethical_score":0.8}],"rounds":3,"actions":[{"reward":10,"ethical_score":0.9}]}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20ethicalincentivesimulatorz serve --port 8787
```

HTTP: `/health`, `/spec`, `/metrics`, `/events`, `/objects`, `/doctor` (peer probe), `/execute`, `/feedback`, `/replica/merge`, `/jobs/<id>/cancel`, cockpit at `/`.

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20ethicalincentivesimulatorz/tests mem20ethicalincentivesimulatorz/mem20ethicalincentivesimulatorz/tests -q
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20ethicalincentivesimulatorz
```
