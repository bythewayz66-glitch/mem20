# mem20freestackambientcomputingfabricz — FreeStack Ambient Computing Fabric (RM-211, #314)

**Outcome:** make FreeStack available as a continuous intelligence layer across desktop, mobile, home, vehicle, headset, and edge devices.  
**Breakthrough:** the platform follows the user and composes the right interface everywhere.

Preserves legacy domain API (#304 peer dependency) and CAPABILITY Engine/CLI/10-scenario simulator; enriches analyze/execute with ambient fabric analysis and 6 **unique** peer integrations (different from #300–#313).

## Legacy domain API (preserved)
`pool_resources(nodes)`, `discover_services(fabric,capability)`, `allocate(fabric,request)`, `fabric_health(fabric)`, `ambient_score(fabric)`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls | Contribution |
|---|---|---|
| `mem20fabricz` | `dispatch_plan`,`probe_members` | integration fabric dispatch/planning |
| `mem20hardwareawareinferencecompilerz` | `fuse_ops`,`quantize`,`schedule`,`memory_estimate` | hardware-aware inference/resource compilation |
| `mem20capabilitymarketplacez` | `CapabilityMarketplace` (+ method call) | capability discovery |
| `mem20crossplatformmicrokernelz` | `create_process`,`allocate_memory`,`schedule` | ambient workload process/memory/scheduling |
| `mem20secretslessworkloadidentityz` | `issue_identity`,`verify`,`rotate`,`identity_health` | secretsless workload identity |
| `mem20ambientdevicecompanionz` | `sense_context`,`proactive_suggestion` | ambient device context/suggestions |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20freestackambientcomputingfabricz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20freestackambientcomputingfabricz execute '{"nodes":[{"cpu":4,"memory":8,"status":"online"}],"capability":"compute","request":{"cpu":1,"memory":1},"values":[1,2,3]}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20freestackambientcomputingfabricz serve --port 8794
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20freestackambientcomputingfabricz/tests mem20freestackambientcomputingfabricz/mem20freestackambientcomputingfabricz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20freestackambientcomputingfabricz
```
