# CrewAI + mem20 — Installation & Connection

> **Corrected 2026-10-31 (H22):** a previous rewrite of this file corrupted the
> upstream package names. `pip install mem20 crews mem20 crews-tools` is not a
> valid command and mem20 is **not** on PyPI (installs are source-only) — see
> `docs/gtm/claim-ledger.md` §D1. The commands below are the real upstream ones;
> for mem20 itself use `git clone` + `pip install -r requirements.txt`.

CrewAI is excellent for role-based multi-agent teams (researcher + writer + reviewer, etc.).

## 1. Install CrewAI

```bash
pip install crewai crewai-tools
```

Create your agents and crew as usual.

## 2. Connect to Jayson

### Easiest method – OpenAI-compatible wrapper

1. Write a small server that receives a chat message
2. Runs your mem20 crews crew with that message as the task
3. Returns the final result in OpenAI chat completions format

Then add it in Jayson:

- Admin → Connections
- API Base URL: `http://host.docker.internal:PORT/v1`
- API Key: whatever you choose

### Alternative
Turn the crew into an Open WebUI Pipe so it shows up as a model.

## 3. Best for
- Fast multi-agent prototypes
- Clear division of labor between agents
- Collaborative task solving
