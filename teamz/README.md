# teamz

A Teamily-style workspace for managing and collaborating with **your own** AI agents: channels, 1:1 chats, a lead/orchestrator agent, persistent memory, and a FastAPI orchestrator with keyless-first LLM routing.

- **Channels + DMs:** multi-agent channels with relevance-based responses (not blind fan-out) and explicit `@mentions`; 1:1 chats with each agent.
- **Lead agent / runtime control:** a lead agent can be asked to add/remove/program agents and the runtime itself, create/manage channels, configure agents, and orchestrate/delegate work to groups matching the task (via runtime actions/planning).
- **Prompt improve:** improve a draft prompt using conversation, channel, agent, and mem20 memory context.
- **Message actions:** long-press/right-click to reply/bring attention, unsend (your sent message), or delete locally.
- **HTML presentation replies:** agents can deliver completed work as sandboxed HTML presentations (` ```presentation ` / `:::presentation` blocks).
- **Persistent channel memory:** mem20-backed memory per conversation/channel used for context and prompt optimization.
- **Agent portfolio & skill learning:** skills/capabilities tracked with levels; portfolio updates can be applied (including from opportunity scans).
- **Connectors:** GitHub (REST), `gh` (GitHub CLI), and Google via the orchestrator.
- **Chat opportunity scanner (backend):** scans chats for tools/skills/capabilities/reusable assets and portfolio updates.

## Quick start (frontend)

```bash
corepack enable
yarn install --frozen-lockfile --ignore-scripts
yarn dev        # http://localhost:5173
```

```bash
yarn run typecheck
yarn run test
yarn run build  # typecheck + production bundle into dist/
yarn preview    # serve dist/
```

Requires Node 18+ (developed/tested on Node 20). Package manager: **Yarn 1** (`yarn.lock`).

## Quick start (orchestrator / server)

```bash
cd server
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cd ..
PYTHONPATH=$PWD server/.venv/bin/python -m uvicorn server.app.main:app --host 0.0.0.0 --port 8787
# or: server/run.sh
```

In the app, open **Workspace & API** and select **Teamz orchestrator** (default `http://localhost:8787`).

See [`server/README.md`](server/README.md) for full run/config docs, env vars, provider targets (Pollinations/LLM7/OVHcloud + optional local runtimes), mem20 integration, connectors, and API details.

## AI providers

Configured in **Workspace & API** (stored in browser `localStorage`, never in the build/repo):

| Provider | What it does |
| --- | --- |
| **Teamz orchestrator** (recommended) | FastAPI server with keyless-first routing + observable fallback chain, mem20 persistent memory/tools, prompt optimization, connectors, runtime planning, opportunity scanning |
| **Pollinations** | Direct browser → Pollinations OpenAI-compatible chat (streaming) |
| **Own endpoints** | POST to each agent’s `endpointUrl` (custom contract) |
| **Mock** | Offline canned replies (labelled) |

The composer/provider pill and the live provider/usage panel show last selected provider/model, usage, and fallback attempts when using the orchestrator.

## Key behavior

### Channel routing (relevance, not blind fan-out)
- In channels, messages **without** `@mentions` are routed to **relevant** agents (not every member in sequence).
- `@mentions` explicitly direct a message to specific agents.
- The composer shows likely responders for unmentioned channel messages (use `@` to direct explicitly).

### Lead agent & runtime orchestration
- Agents can be marked **Lead** (see Agent settings). Seed workspace includes a lead agent (Atlas).
- Talk to the lead agent to add/remove/program agents and the runtime, create channels, configure agents, and orchestrate/delegate work to groups matching the task.
- Lead-agent replies can include runtime actions (parsed/applied by the frontend) and the orchestrator provides `/v1/runtime/plan` plus lead-aware context/memory.

### Prompt improve
- Use the ✨ **Improve prompt** button in the composer to rewrite your draft using conversation/channel history, agent roster/skills/roles, and mem20-recalled persistent memory (via orchestrator).

### Message actions
- Long-press (touch) or right-click a message: **Reply/bring attention**, **Bring/remove attention**, **Unsend** (your sent message), **Delete** (local).
- Attention and reply context are reflected in the thread and composer.

### HTML presentation replies
- Agents can return completed deliverables as sandboxed HTML presentations using a fenced block:
  - ` ```presentation ... ``` ` (or `html:presentation` / `slides`), or
  - `:::presentation` ... `:::` markers.

### Persistent channel memory (mem20)
- The orchestrator stores and recalls conversation-tagged memories in mem20 and augments chat/prompt optimization with relevant persistent context. Each channel/conversation has persistent memory for context when mem20 is enabled/configured.

### Agent portfolio & skill learning
- Each agent has a portfolio of skills/capabilities with levels (1–5). Skills can be added/updated in Agent settings.
- Opportunity scans can produce portfolio updates; runtime/lead workflows can add skills as agents learn capabilities.

### Connectors (orchestrator)
- **GitHub** (REST, token-configured), **`gh`** (CLI exec/status), **Google** (access token or service-account based) exposed via `/v1/connectors/*` with real, configurable integrations.

### Opportunity scanner (backend)
- `POST /v1/opportunities/scan` analyzes chats for opportunities to create tools/skills/capabilities/reusable assets and suggests portfolio updates.

## Own endpoints contract (custom provider)

`src/api/agents.ts` POSTs to `agent.endpointUrl`:

```jsonc
{
  "agent":    { "id", "name", "model", "systemPrompt" },
  "messages": [ { "role": "user" | "assistant", "content": "...", "authorName": "..." } ],
  "channel":  { "id", "name", "members": [ { "id", "name" } ] },
  "directed": true // optional, when explicitly @mentioned
}
```

Accepted reply shapes include `{ "reply": "..." }`, `{ "text": "..." }`, OpenAI-style `choices[0].message.content`, and Anthropic-style content blocks.

## Visual/E2E scripts (Playwright)

Install browsers once:

```bash
yarn playwright install chromium
```

Run the app (preview or dev), then run scripts (default `BASE_URL=http://localhost:4173/teamz/`):

```bash
yarn build && yarn preview --host 0.0.0.0 --port 4173 &
node scripts/shot-picker.mjs
node scripts/shot-channel.mjs
```

Scripts capture screenshots to `screenshots/` and print JSON diagnostics (filter/invite/picker measurements).

## Project layout

```
src/
  api/                 agents, orchestrator, pollinations, settings
  components/          Sidebar, ChatPane, AgentSettings, dialogs, RichText (presentations), etc.
  data/                mock seed data + template catalogue
  lib/                 mentions, relevance routing, formatting
  store/               workspace state (persistence, relevance routing, message/runtime actions)
  styles.css
server/
  app/                 FastAPI orchestrator (routing, providers, mem20, connectors, runtime/scan APIs)
  tests/               server tests
scripts/               Playwright visual-flow scripts (shot-picker, shot-channel)
```

## Tests & verification

```bash
# Frontend
yarn run typecheck
yarn run test
yarn run build

# Server
PYTHONPATH=$PWD server/.venv/bin/python -m pytest server/tests -q
```

CI/deploy workflows are aligned to Yarn (`yarn.lock`, `corepack enable`, `yarn install --frozen-lockfile`).

## License

MIT
