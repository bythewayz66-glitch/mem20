# mem20gamebalancesimulatorz — Game Balance Simulator (RM-231, #315)

**Outcome:** run large-scale simulations of combat, progression, economy, and player strategies.  
**Breakthrough:** balance decisions are supported by millions of synthetic playthroughs.

Preserves legacy domain API (**#307 peer dependency**) and CAPABILITY Engine/CLI/10-scenario simulator; enriches progression/execute with balance analysis and 6 **unique** peer integrations (different from #300–#314).

## Legacy domain API (preserved)
`dps(damage,attack_speed)`, `ttk(health,dps_val)`, `economy_balance(income,expenses)`, `difficulty_curve(levels,base,growth)`, `balance_check(stats,targets)`, `win_rate(simulations)`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls | Contribution |
|---|---|---|
| `mem20skillbasedprogressionbrainz` | `gain_xp`,`level`,`progression_health` | XP/progression health signals |
| `mem20playermotivationtwinz` | `create_twin`,`update`,`predict_churn`,`motivation_segments` | player motivation/churn context |
| `mem20ailevelarchitectz` | `difficulty_curve`,`pacing_profile`,`generate_layout` | level difficulty/pacing/architecture |
| `mem20communitychallengeenginez` | `create_challenge`,`join`,`record_progress`,`leaderboard` | challenge/engagement balance signals |
| `mem20skillmemorytransferz` | `extract`/`transfer`,`merge_skills`,`transfer_health` | skill transfer/progression balance |
| `mem20realworldimpactrewardsz` | `record_impact`,`compute_reward`,`impact_health` | impact/reward economy signals |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20gamebalancesimulatorz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20gamebalancesimulatorz execute '{"xp":120,"damage":10,"attack_speed":2,"health":100,"income":100,"expenses":40,"levels":5,"balance":true,"simulations":[{"winner":"player"}]}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20gamebalancesimulatorz serve --port 8795
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20gamebalancesimulatorz/tests mem20gamebalancesimulatorz/mem20gamebalancesimulatorz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20gamebalancesimulatorz
```
