# RM-244 — Narrative, Dialogue and Localization Pipeline (#339)

**Outcome:** Drive story state, dialogue graphs, lore content generation, timing, and engine reintegration from one runtime.  
**Operation kind:** `graph` (also supports `pipeline`).

## 1st-class implementation
- **Domain:** `parse_dialogue/localize/validate_dialogue/word_count/export_script` (legacy) plus `build_narrative_graph`/`export_narrative` producing dialogue graph (nodes/edges), validation, localizations, word count, export.
- **Runtime:** `graph`/`pipeline` wired to domain + 6 peer signals.
- **Ecosystem (6 peers, unique set, different from #332):** `mem20leveldesignworldbuildingandnavigationpipelinez`, `mem20dynamicnarrativeenginez`, `mem20loreragcontentgeneratorz`, `mem20contextcompressionforgez`, `mem20episodicmemorygraphz`, `mem20eventstreamsuperhighwayz`.

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20narrativedialogueandlocalizationpipelinez execute '{"text":"NPC: Hello\nHERO: Ready","target_languages":["en","es"]}'
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20narrativedialogueandlocalizationpipelinez/mem20narrativedialogueandlocalizationpipelinez/tests/test_domain.py -q
```
Gateway `SUBSYSTEMS["mem20narrativedialogueandlocalizationpipelinez"]`; docs `docs/app/narrativedialogueandlocalizationpipelinez/index.html`; target 7/7.
