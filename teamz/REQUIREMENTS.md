# Teamz requirements note

Captured from user requests for the current build/fix pass. This note records requested behavior and scope; implementation and docs elsewhere must reflect reality.

## Full fix/build scope (do thoroughly)

- Fix everything previously identified as missing in `bythewayz66-glitch/teamz`:
  - Implement the missing FastAPI orchestrator in `server/` with keyless-first LLM routing across providers and an observable fallback chain (matching intended behavior/commit intent).
  - Add server tests and run/config docs/spec for the orchestrator.
  - Implement required frontend transport integration and a live provider/usage panel/UI updates.
  - Add/update frontend tests (unit/integration/UI flow) to cover new behavior.
  - Remove sidebar agent duplication (agents currently appear in both Agents and Direct).
  - Align package manager/lock/workflows (`yarn.lock`/`package-lock.json`, `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`) consistently.
  - Install Playwright browsers and add working E2E/visual-flow coverage for existing scripts/tests.
  - Update hygiene/docs: `.gitignore` (e.g. venv/cache artifacts), document orchestrator API/config/run steps, and reflect reality in `README.md` and related docs.
  - Ensure services/build/test commands run cleanly end-to-end.
- Use `https://gamut.so` and `https://teamily.ai` for product/UX inspiration.
- Do it the right/thorough way (research each section); no placeholders/stubs/fake implementations.

## Product behavior requirements

- **Channel responses (relevance, not blind fan-out):** When a user talks in a channel, the same request must **not** be sent to every agent in sequence. Only the relevant agents should answer, whether they are @mentioned or not. (@mentions remain an explicit way to direct a message; unmentioned messages should still route only to relevant agents.)
- **Lead agent (orchestration/control):** Provide a lead agent the user can speak to who can add, remove, and program agents and the runtime itself. When asked, the lead agent should be able to make new channels, make agents, and program/configure current ones. The lead agent must have the knowledge to orchestrate and delegate work to groups of agents that match the task.
- **HTML presentation replies:** Agents should be able to create HTML presentations as replies when they complete a job (Teamily-like presentation/artifact replies).
- **Prompt improve button:** Provide a button to make/improve the user’s prompt after typing it. Prompt optimization must use memory for context (conversation/channel context and relevant memories).
- **Message actions (long press / context actions):** Users should be able to long-press a message and **unsend**, **delete**, or **bring attention to** it (and related useful actions as appropriate).
- **Agent portfolio & skill learning:** Anytime an agent learns a new skill or capability, it must be added to the agent’s portfolio along with a skill level.
- **Chat opportunity scanner (backend):** Provide a backend process/capability that scans chats for opportunities to create tools, skills, capabilities, and other reusable assets.
- **Persistent channel memory:** Each channel should have persistent memory for context.

## Platform integration

- **Mem20:** The system should be directly connected to mem20 for memory and tools.
- **Connectors:** Add connectors for GitHub and `gh` (GitHub CLI), and for Google.

## Orchestrator intent / regression areas to satisfy

- FastAPI orchestrator with keyless-first LLM routing and an observable fallback chain.
- Frontend transport and a live provider/usage panel.
- Provider verification targets referenced: OVHcloud, Pollinations, LLM7.
- Regression/behavior cases to handle with real tests/implementation:
  - Dead local runtimes must not consume the whole attempt budget.
  - Probe/learning must not route chat at whisper/pro-tier models.
  - An agent’s model string must not be a hard filter that causes total outage (preference/hint with fallback).
  - Streaming must not produce an empty answer for non-SSE providers.
  - Router must not close a caller-owned HTTP client.
  - `extract_text` must not drop Anthropic-shaped content blocks.
