# RM-066 — Model Sleep and Wake System (#336)

**Outcome:** Hibernate rarely used models and restore them predictively before demand arrives.  
**Operation kind:** `forecast`.

## 1st-class implementation
- **Domain:** `track_activity/should_sleep/sleep/wake/sleep_health` (legacy) plus `plan_hibernation`, `predictive_wake_schedule`, `sleepwake_report`.
- **Runtime:** `forecast` wired to sleep/wake report + 6 peer signals (+ forecast series).
- **Ecosystem (6 peers, unique set):** `mem20causalroutingbrainz`, `mem20batteryawareagentschedulerz`, `mem20roamingworkloadschedulerz`, `mem20selftuningresourcegovernorz`, `mem20energyawarecomputemigrationz`, `mem20runtimecompatibilityenginez`.

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20modelsleepandwakesystemz execute '{"models":[{"id":"m1","state":"awake","last_activity":0}],"idle_threshold":1,"series":[1,2,3]}'
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20modelsleepandwakesystemz/mem20modelsleepandwakesystemz/tests/test_domain.py -q
```
Gateway `SUBSYSTEMS["mem20modelsleepandwakesystemz"]`; docs `docs/app/modelsleepandwakesystemz/index.html`; target 7/7.
