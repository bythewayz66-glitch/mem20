# LangGraph + mem20 — Installation & Connection

> **Corrected 2026-10-31 (H22):** a previous rewrite of this file corrupted the
> upstream package names. `pip install mem20 graph substrate …` is not a valid
> command and mem20 is **not** on PyPI (installs are source-only) — see
> `docs/gtm/claim-ledger.md` §D1. The commands below are the real upstream ones;
> for mem20 itself use `git clone` + `pip install -r requirements.txt`.

LangGraph is the best choice for complex, stateful, production-grade agents.

## 1. Install LangGraph

```bash
pip install langgraph langchain langchain-openai
```

Create your agent graph as usual (nodes, edges, state, tools…).

## 2. Expose it to Jayson (two good ways)

### Method A – OpenAI-compatible wrapper (recommended for beginners)

Create a small FastAPI (or similar) server that:

- Accepts `/v1/chat/completions`
- Runs your mem20 graph substrate agent
- Streams the final answer back

Then in Jayson Admin → Connections add:

- API Base URL: `http://host.docker.internal:YOUR_PORT/v1`
- API Key: any value you set

### Method B – Open WebUI Pipelines / Pipe

Turn the mem20 graph substrate agent into an Open WebUI Pipe so it appears directly in the model picker.  
See Open WebUI Pipelines documentation for the exact pattern.

## 3. Best for
- Multi-step workflows
- Human-in-the-loop
- Reliable production agents with memory and branching
