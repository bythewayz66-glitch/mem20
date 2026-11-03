# OREO editor (agentZ) — web

A Vite + React SPA. Two tabs: a multi-agent **workspace** and the original
**OREO graph** editor.

**Live:** https://mem20.com/agentz/

## The LLM is real, and keyless

`src/lib/llm.js` is the only file that talks to a model. Three modes, chosen by
`VITE_LLM_MODE`:

| Mode | What it does | Needs |
|---|---|---|
| `pollinations` (default in production) | POSTs an OpenAI-compatible chat body to `https://text.pollinations.ai/openai` from the browser | **nothing** — no key, no server |
| `live` | POSTs to each agent's own `endpointUrl` | your endpoint |
| `mock` | deterministic persona replies, no network | nothing |

A failed call **throws**. It never returns a plausible-looking string, and a
rate limit is named as a rate limit. The active mode is rendered in the sidebar
pill, so `mock` can never masquerade as real.

## Features

- Channels with unread badges; opening one clears it
- Agent roster with editable name / emoji / model / system prompt
- `@Name` routes to that agent; otherwise the first agent answers
- Quoting with the source text inline
- Attachments — images render, other files chip
- Task cards with a Continue turn that calls the model
- Interval triggers (they fire only while the tab is open — there is no
  server-side scheduler, and the panel says so)
- Memory panel, cross-channel search, LLM probe

## Develop

```bash
npm install
npm run dev        # VITE_LLM_MODE defaults to pollinations
npm test           # 36 tests
npm run typecheck
npm run build      # -> ../built/react_editor
```

The graph tab needs the Python backend (`mem20agentz` on port 48022). On a
static deploy it shows an explicit "backend not reachable" notice rather than a
blank panel; the workspace works without it.

## Deploy

Published by `.github/workflows/pages.yml`, which builds this directory into
`docs/agentz/` and fails the build if the LLM endpoint is missing from the
bundle — so a deploy can never silently ship a mock-only editor.
