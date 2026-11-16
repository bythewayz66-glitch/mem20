# teamz orchestrator (`server/`)

FastAPI orchestrator for teamz providing:

- **Keyless-first LLM routing** across providers with an **observable fallback chain** (attempts, latency, reasons/errors, usage).
- Verified provider targets/integrations: **Pollinations**, **LLM7**, **OVHcloud AI Endpoints** (OpenAI-compatible), plus optional local OpenAI-compatible runtimes.
- Streaming and non-stream chat completions (`/v1/chat/completions`, OpenAI-compatible shape + teamz routing metadata).
- **Prompt optimization** using conversation/channel context and **mem20**-recalled memories (`/v1/optimize-prompt`).
- **Persistent channel memory/context** integration via mem20 MCP stdio client (recall/store; chat turns and relevant context are persisted/tagged by conversation).
- **Memory & tool** APIs backed by mem20 (`/v1/memory/recall`, `/v1/memory/store`, `/v1/tools`, `/v1/tools/call`).
- **Connectors**: GitHub (REST API), `gh` (GitHub CLI), and Google (`/v1/connectors/*`).
- **Runtime planning** for the lead agent to add/remove/program agents/channels and delegate/orchestrate (`/v1/runtime/plan`).
- **Chat opportunity scanner** for tools/skills/capabilities/reusable assets and portfolio updates (`/v1/opportunities/scan`).

## Setup

```bash
cd server
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Run

From the repo root:

```bash
PYTHONPATH=/opt/mem20/teamz server/.venv/bin/python -m uvicorn server.app.main:app --host 0.0.0.0 --port 8787
```

Or using the helper script:

```bash
cd server
./run.sh
```

## Tests

```bash
cd /opt/mem20/teamz
PYTHONPATH=/opt/mem20/teamz server/.venv/bin/python -m pytest server/tests -q
```

## Configuration (env vars)

### Server
- `TEAMZ_HOST` (default `0.0.0.0`)
- `TEAMZ_PORT` (default `8787`)
- `TEAMZ_CORS_ORIGINS` (comma-separated; defaults include localhost dev/preview origins)

### Routing
- `TEAMZ_KEYLESS_FIRST` (default `true`)
- `TEAMZ_MAX_ATTEMPTS` (default `6`) — real attempt budget; dead local runtimes are probed/skipped without consuming the whole budget
- `TEAMZ_REQUEST_TIMEOUT_S`, `TEAMZ_CONNECT_TIMEOUT_S`, `TEAMZ_PROBE_TIMEOUT_S`, `TEAMZ_DEAD_RUNTIME_TIMEOUT_S`

### Providers (keyless-first; keys optional)
- **Pollinations**: `POLLINATIONS_BASE_URL`, `POLLINATIONS_KEYED_BASE_URL`, `POLLINATIONS_API_KEY`
- **LLM7**: `LLM7_BASE_URL`, `LLM7_API_KEY`
- **OVHcloud**: `OVH_BASE_URL`, `OVH_API_KEY`
- **Local OpenAI-compatible runtimes** (optional): `TEAMZ_LOCAL_OPENAI_BASE_URLS` (comma-separated)

Routing behavior (intent):
- Keyless-first provider/model selection with observable fallback attempts.
- Dead local runtimes must not consume the whole attempt budget.
- Probe/learning must not route chat at whisper/pro-tier models.
- Agent/request model is treated as a preference/hint with fallback (not a hard filter causing total outage).
- Streaming must not produce an empty answer for non-SSE providers (synthesized stream/done as needed).
- Router must not close a caller-owned HTTP client.
- `extract_text` supports Anthropic-shaped content blocks.

### Mem20 (persistent memory & tools)
- `MEM20_ENABLED` (default `true`)
- `MEM20_MCP_COMMAND` (default `python3`)
- `MEM20_MCP_ARGS` (comma-separated; default `/opt/mem20/mcp/mcp_server.py`)
- `MEM20_TIMEOUT_S` (default `30`)

### Connectors
- **GitHub**: `GITHUB_TOKEN` or `GH_TOKEN` (for authenticated REST API access)
- **gh**: uses installed `gh` CLI from PATH (configure via `gh auth login` or `GH_TOKEN`)
- **Google**: `GOOGLE_ACCESS_TOKEN` (direct), or `GOOGLE_SERVICE_ACCOUNT_JSON` / `GOOGLE_APPLICATION_CREDENTIALS` (service account; RS256 JWT minted via `openssl` for real API calls). Optional per-request scopes supported.

## API (selected)

- `GET /health` — health, provider list, mem20 status
- `GET /v1/status` — provider/mem20/config status
- `POST /v1/chat/completions` — chat (stream or non-stream), memory-augmented, lead-agent runtime instructions when applicable; returns routing/usage metadata
- `POST /v1/optimize-prompt` — improve a draft prompt using history, agents, and mem20-recalled context
- `POST /v1/memory/recall`, `POST /v1/memory/store` — mem20 memory
- `GET /v1/tools`, `POST /v1/tools/call` — mem20 tools
- `GET /v1/connectors/status` and connector-specific status/request/exec endpoints for GitHub, gh, Google
- `POST /v1/runtime/plan` — plan structured runtime actions/delegations for lead-agent requests
- `POST /v1/opportunities/scan` — scan chats for opportunities and portfolio/skill updates

All behavior is implemented with real working code (no placeholders/fake implementations).
