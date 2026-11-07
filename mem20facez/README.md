# mem20facez — Interface & Workspace Crew Runtime (#312)

First-class interface/workspace runtime for 8 reviewed member systems. Preserves compatibility (`MEMBERS`, `__version__`, `mem20facez.cli:main`, `--version`, `--members`) and adds real member probing, composition planning, 6 unique cross-subsystem peer integrations, JSON CLI, HTTP API, and a static cockpit.

## Members (8, preserved)
`mem20adaptiveinterfacecomposerz`, `mem20musicvisualsynchronizerz`, `mem20parallelworkstreamcomposerz`, `mem20spatialcommanduniversez`, `mem20spatialexperiencedesignerz`, `mem20visualagentblackboardz`, `mem20visualdataflowcomposerz`, `mem20voicetoactionswitchboardz`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls | Contribution |
|---|---|---|
| `mem20multimodaltaskcapturez` | `capture`,`merge_captures`,`extract_action_items`,`capture_health` | multimodal task capture |
| `mem20visualdataflowcomposerz` | `create_pipeline`,`add_node`,`connect` | visual dataflow composition |
| `mem20intenttomissioncompilerz` | `compile_mission`,`validate_mission`,`mission_progress` | intent→mission compilation |
| `mem20personalautomationcanvasz` | `create_canvas`,`add_workflow`,`add_trigger` | workspace automation canvas |
| `mem20multiworldsandboxz` | `create_world`,`branch`,`step` | sandboxed layout/world branching |
| `mem20visualagentblackboardz` | `create_blackboard`,`post`,`read` | visual agent coordination board |

## Runnable example (verified)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20facez --version
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20facez --members
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20facez doctor
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20facez compose --intent "visual workspace" --payload '{"mode":"visual"}'
```

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20facez serve --port 8792
```

HTTP: `/health`, `/status`, `/doctor`, `/compose` (POST), cockpit at `/`.

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20facez/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20facez
```
