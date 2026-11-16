# teamz Roadmap: 20 Phases × 10 Subphases

Each phase builds on the previous; subphases are ordered by dependency.  
✅ = done in this session. 🎯 = high leverage next step.

---

## Phase 0 — Foundation (Done)
| # | Subphase | Status |
|---|----------|--------|
| 0.1 | FastAPI orchestrator with keyless-first routing | ✅ |
| 0.2 | Observable fallback chain (attempts, latency, reasons) | ✅ |
| 0.3 | mem20 MCP stdio client (tools, memory recall/store) | ✅ |
| 0.4 | Connectors: GitHub REST, `gh` CLI, Google OAuth | ✅ |
| 0.5 | Runtime planner `/v1/runtime/plan` (lead agent) | ✅ |
| 0.6 | Opportunity scanner `/v1/opportunities/scan` | ✅ |
| 0.7 | Frontend: relevance routing, @mentions, message actions | ✅ |
| 0.8 | HTML presentation replies (fenced `presentation` blocks) | ✅ |
| 0.9 | Prompt improve button (orchestrator + local fallback) | ✅ |
| 0.10 | Yarn 1 lockfile, CI/deploy aligned, .gitignore hardened | ✅ |

---

## Phase 1 — Autonomous Worker Hardening
| # | Subphase |
|---|----------|
| 1.1 | Worker tick cadence configurable per-room (`goal.tick_s`) |
| 1.2 | Per-room step budget + global cap; persist step count in goal |
| 1.3 | Exponential backoff on model errors; dead-letter queue for failed steps |
| 1.4 | Structured step schema validation (Zod/Pydantic) before tool execution |
| 1.5 | Worker logs queryable via `/v1/worker/log?room=` with filters |
| 1.6 | Agent selection scoring: include recency, success rate, token cost |
| 1.7 | "Worker paused" banner with resume ETA; manual tick button in UI |
| 1.8 | Goal templates (PRD → spec → scaffold → test → CI → deploy) |
| 1.9 | Auto-split large goals into ordered sub-goals with dependencies |
| 1.10 | Export/import goal runs (JSON) for replay and audit |

---

## Phase 2 — Terminal & Shell UX
| # | Subphase |
|---|----------|
| 2.1 | Interactive PTY sessions (xterm.js) — agents can run `vim`, `python -i` |
| 2.2 | Terminal output streaming (SSE) to chat pane in real time |
| 2.3 | Command history per agent; `!!` / `!n` expansion |
| 2.4 | Allow-list / deny-list with glob patterns (`TEAMZ_TERMINAL_DENY_GLOBS`) |
| 2.5 | Sandbox mode: containerized exec (Firecracker / gVisor / podman) |
| 2.6 | Resource limits per command (CPU, RAM, wall time, pids) |
| 2.7 | Secret redaction in stdout/stderr (API keys, tokens) |
| 2.8 | Session recording (asciicast) + replay in UI |
| 2.9 | Multi-agent shared tmux session for pair programming |
| 2.10 | `terminal` tool returns structured `{exit, stdout, stderr, cwd, duration}` |

---

## Phase 3 — File System as Agent Workspace
| # | Subphase |
|---|----------|
| 3.1 | Git-aware write/edit: auto-stage, commit messages from step summary |
| 3.2 | Diff preview before `edit_file` applies (side-by-side in chat) |
| 3.3 | Workspace snapshots (git commit + state) per goal step |
| 3.4 | `glob` / `grep` / `find` tools with streaming results |
| 3.5 | Binary file handling (images, PDFs) via base64 + MIME detection |
| 3.6 | Language-aware edits (AST-based) for TS/Python/Go/Rust |
| 3.7 | Auto-format on write (Prettier, Black, gofmt, rustfmt) |
| 3.8 | Workspace index (ripgrep + ctags) for LSP-style "go to definition" |
| 3.9 | File watchers → push events to agents ("test file changed") |
| 3.10 | Per-agent virtual filesystem views (chroot per agent) |

---

## Phase 4 — GitHub / Git Integration
| # | Subphase |
|---|----------|
| 4.1 | `gh` tool: full CRUD for issues, PRs, releases, actions, repos |
| 4.2 | GitHub REST tool: GraphQL + REST with pagination helpers |
| 4.3 | Auto-create PR from goal branch; description from step log |
| 4.4 | CI status polling → agent sees pass/fail and reacts |
| 4.5 | Code review agent: posts review comments via API |
| 4.6 | Branch protection: agent cannot force-push to `main` |
| 4.7 | GitHub Projects / Issues sync: goal ↔ epic ↔ task mapping |
| 4.8 | Dependabot / Renovate PR auto-merge (if tests pass) |
| 4.9 | Release drafter: agent cuts releases from merged PRs |
| 4.10 | Self-hosted runner registration for private repos |

---

## Phase 5 — Skill System & Agent Growth
| # | Subphase |
|---|----------|
| 5.1 | Skill XP: agents earn XP per successful tool use; level up at thresholds |
| 5.2 | Skill tree UI: prerequisites, branching specializations |
| 5.3 | Agent teaches skill to another agent (pair session → both gain XP) |
| 5.4 | Skill certificates: export/import portable skill profiles |
| 5.5 | Dynamic skill discovery: agent proposes new skill from repeated patterns |
| 5.6 | Skill marketplace: share/install skill packs across workspaces |
| 5.7 | Proficiency decay: unused skills slowly decay; refresher tasks |
| 5.8 | Skill-based routing: worker prefers agents with relevant high-level skills |
| 5.9 | Agent resume: auto-generated from skills + completed goals + code |
| 5.10 | Mentor mode: lead agent assigns skill-learning sub-goals |

---

## Phase 6 — Multi-Room Orchestration
| # | Subphase |
|---|----------|
| 6.1 | Project room: parent goal with child rooms (frontend, backend, infra) |
| 6.2 | Cross-room message bus (Redis / NATS) for inter-room coordination |
| 6.3 | Dependency graph: room A blocks room B → worker respects ordering |
| 6.4 | Shared artifact store (S3 / MinIO) for build outputs, test reports |
| 6.5 | Global worker pool: agents can be loaned across rooms |
| 6.6 | Portfolio view: all active goals across rooms with health bars |
| 6.7 | Resource quotas per room (CPU, tokens, API calls) |
| 6.8 | Room templates (monorepo, microservice, docs, research) |
| 6.9 | Room cloning + forking for experiment branches |
| 6.10 | Org-level dashboard: teams, agents, goals, velocity |

---

## Phase 7 — Testing & Quality Gates
| # | Subphase |
|---|----------|
| 7.1 | Agent writes tests as part of goal steps (TDD loop) |
| 7.2 | Coverage gate: goal not "done" until coverage ≥ threshold |
| 7.3 | Mutation testing agent: survives mutants → confident |
| 7.3 | Property-based testing (fast-check / Hypothesis) generation |
| 7.4 | Contract testing: agent verifies API schemas against OpenAPI |
| 7.5 | Visual regression: agent runs Playwright, compares screenshots |
| 7.6 | Performance budgets: agent profiles, fails if regression > 10% |
| 7.7 | Security scanning agent (Semgrep, Trivy, OWASP ZAP) |
| 7.8 | Dependency audit agent: updates deps, runs tests, opens PR |
| 7.9 | Flaky test detection: agent re-runs, quarantines, files issue |
| 7.10 | Quality dashboard: per-room test health, coverage trends |

---

## Phase 8 — Observability & Debugging
| # | Subphase |
|---|----------|
| 8.1 | Structured JSON logs (OpenTelemetry) for every tool call |
| 8.2 | Distributed tracing: goal → step → tool → LLM call |
| 8.3 | Live token/cost meter per room in sidebar |
| 8.4 | Step timeline view (Gantt) with agent swimlanes |
| 8.5 | "Why did agent do that?" — click step → see prompt + context |
| 8.6 | Replay any goal run with same seed (deterministic) |
| 8.7 | Alerting: goal stalled, agent error rate high, budget exceeded |
| 8.8 | Export traces to Jaeger / Zipkin / Grafana Tempo |
| 8.9 | Custom dashboards per team (Grafana / custom React) |
| 8.10 | Audit log: immutable, signed, queryable |

---

## Phase 9 — LLM Provider Ecosystem
| # | Subphase |
|---|----------|
| 9.1 | Local model runners: Ollama, llama.cpp, vLLM, TGI |
| 9.2 | Provider health scoring: latency, error rate, cost/1k tokens |
| 9.3 | Automatic failover with cost-aware routing |
| 9.4 | Prompt caching (Anthropic / OpenAI) for repeated context |
| 9.5 | Structured output enforcement (JSON Schema → Pydantic) |
| 9.6 | Function calling shim for non-OpenAI models |
| 9.7 | Model-specific prompt templates (system prompts per provider) |
| 9.8 | Cost budgets per room/project/org with hard stops |
| 9.9 | BYOK (bring your own key) per agent |
| 9.10 | Provider marketplace: install new providers as plugins |

---

## Phase 10 — Memory & Knowledge
| # | Subphase |
|---|----------|
| 10.1 | Vector memory (pgvector / Qdrant / Weaviate) for code + docs |
| 10.2 | Episodic memory: agent recalls "how I solved X last time" |
| 10.3 | Semantic memory: project glossary, architecture decisions (ADRs) |
| 10.4 | Memory consolidation: nightly summarization + embedding |
| 10.5 | Cross-agent memory sharing (with privacy controls) |
| 10.6 | Memory TTL + importance scoring; auto-prune noise |
| 10.7 | "Remember this" button in chat → pins to long-term memory |
| 10.8 | Knowledge graph: entities (files, functions, APIs) + relations |
| 10.9 | RAG over git history: "why was this function added?" |
| 10.10 | Export/import memory packs for onboarding new agents |

---

## Phase 11 — Planning & Reasoning
| # | Subphase |
|---|----------|
| 11.1 | Hierarchical task networks (HTN) for complex goal decomposition |
| 11.2 | Monte Carlo tree search for step selection (simulate outcomes) |
| 11.3 | Counterfactual reasoning: "what if I used library Y instead?" |
| 11.4 | Plan verification: dry-run in sandbox before committing |
| 11.5 | Goal negotiation: agent asks clarifying questions before starting |
| 11.6 | Risk assessment per step (blast radius, reversibility) |
| 11.7 | Contingency planning: auto-generate fallback steps |
| 11.8 | Time-boxed steps with deadline-aware scheduling |
| 11.9 | Multi-agent consensus for high-stakes decisions |
| 11.10 | Explainable AI: natural-language rationale for every decision |

---

## Phase 12 — Collaboration & Human-in-the-Loop
| # | Subphase |
|---|----------|
| 12.1 | Approval gates: agent pauses for human ✅/❌ on sensitive steps |
| 12.2 | Pair programming mode: human + agent share terminal + editor |
| 12.3 | Code review UI: inline comments, suggestions, approve/request changes |
| 12.4 | Voice/chat handoff: "take over" / "resume autonomous" |
| 12.5 | Shared whiteboard (Excalidraw) for architecture diagrams |
| 12.6 | Meeting agent: joins calls, transcribes, extracts action items |
| 12.7 | Stakeholder digest: daily/weekly summary email/Slack |
| 12.8 | Guest access: read-only links for PMs, designers, execs |
| 12.9 | Conflict resolution: two agents disagree → mediator agent |
| 12.10 | Social features: agent kudos, streaks, team velocity |

---

## Phase 13 — Editor & IDE Integration
| # | Subphase |
|---|----------|
| 13.1 | VS Code extension: chat pane, inline edits, terminal sync |
| 13.2 | JetBrains plugin (IntelliJ, PyCharm, GoLand, RustRover) |
| 13.3 | Neovim plugin (LSP + chat buffer) |
| 13.4 | Language server wrapper: agent provides diagnostics/fixes |
| 13.5 | Inline diff review in editor (accept/reject per hunk) |
| 13.6 | Jump to definition across agent-written code |
| 13.7 | Refactoring agent: rename, extract, move — preview in IDE |
| 13.8 | Test runner integration: agent triggers, shows results in editor |
| 13.9 | GitLens-style blame: "agent X wrote this at step Y of goal Z" |
| 13.10 | Offline mode: local model + cached context |

---

## Phase 14 — Security & Compliance
| # | Subphase |
|---|----------|
| 14.1 | RBAC: roles (owner, lead, developer, viewer) per room/org |
| 14.2 | Audit log immutability (append-only, cryptographic hash chain) |
| 14.3 | Secret scanning on every write (git-secrets, TruffleHog) |
| 14.4 | Data residency: EU/US region selection for memory + logs |
| 14.5 | SOC 2 / ISO 27001 evidence export |
| 14.6 | Agent allow/deny lists for external API calls |
| 14.7 | Ephemeral workspaces: auto-destroy after TTL |
| 14.8 | Supply chain: SBOM generation per goal run |
| 14.9 | Penetration testing agent (scheduled, scoped) |
| 14.10 | Incident response playbook agent |

---

## Phase 15 — Deployment & Operations
| # | Subphase |
|---|----------|
| 15.1 | One-click deploy to Fly.io / Railway / Render / K8s |
| 15.2 | Preview environments per PR (auto-deploy, auto-destroy) |
| 15.3 | Blue/green + canary deployments driven by agent |
| 15.4 | Infrastructure as Code agent (Terraform / Pulumi / Crossplane) |
| 15.5 | Observability stack deploy (Grafana, Loki, Tempo, Prometheus) |
| 15.6 | Database migration agent (safe, reversible, tested) |
| 15.7 | Chaos engineering agent (Litmus / Gremlin) |
| 15.8 | Cost optimization agent (rightsizing, spot instances) |
| 15.9 | Disaster recovery drill agent (quarterly, automated) |
| 15.10 | Runbook agent: executes incident runbooks step-by-step |

---

## Phase 16 — Domain-Specific Agent Packs
| # | Subphase |
|---|----------|
| 16.1 | Web pack: React, Next.js, Remix, Astro, Tailwind, Playwright |
| 16.2 | Backend pack: FastAPI, Django, Node/Express, Go/Chi, Rust/Axum |
| 16.3 | Data pack: dbt, Airflow, Dagster, Polars, DuckDB, Evidence |
| 16.4 | ML pack: PyTorch, JAX, HuggingFace, MLflow, Weights&Biases |
| 16.5 | Mobile pack: React Native, Expo, Flutter, Swift, Kotlin |
| 16.6 | DevOps pack: Terraform, Helm, ArgoCD, Cilium, eBPF |
| 16.6 | Security pack: SAST/DAST, cosign, SLSA, SBOM, Kyverno |
| 16.7 | Docs pack: Docusaurus, Mintlify, OpenAPI, Redoc, Mermaid |
| 16.8 | Testing pack: Vitest, Playwright, Pact, ContractTest, k6 |
| 16.9 | Research pack: ArXiv, Semantic Scholar, Zotero, Obsidian |

---

## Phase 17 — Plugin & Extension System
| # | Subphase |
|---|----------|
| 17.1 | Plugin manifest (WASM or JS) with sandboxed permissions |
| 17.2 | Tool plugins: add custom tools without server restart |
| 17.3 | UI plugins: custom panels, sidebar widgets, chat renderers |
| 17.4 | Model adapter plugins: new providers drop-in |
| 17.5 | Skill plugins: community skill packs installable |
| 17.6 | Theme/branding plugins (org white-label) |
| 17.7 | Marketplace: publish, discover, rate, subscribe |
| 17.8 | Plugin dependencies + version resolution |
| 17.9 | Signed plugins + verification (cosign/sigstore) |
| 17.10 | Hot-reload plugins in dev mode |

---

## Phase 18 — Multi-Tenancy & Organizations
| # | Subphase |
|---|----------|
| 18.1 | Org workspace: multiple projects, shared agent pool |
| 18.2 | SSO (OIDC/SAML) + SCIM provisioning |
| 18.3 | Org-level billing: token budgets, seat licenses |
| 18.4 | Audit log aggregation across org |
| 18.5 | Policy engine: OPA/Rego for org-wide rules |
| 18.5 | Shared memory/skill library across org |
| 18.7 | Cross-project dependency tracking |
| 18.8 | Org templates: standards, linting, CI, security |
| 18.9 | Private registry for agent images/plugins |
| 18.10 | Compliance reports per project/team/org |

---

## Phase 19 — AI-Native Developer Experience
| # | Subphase |
|---|----------|
| 19.1 | "Build this" → agent scaffolds entire project from description |
| 19.2 | "Fix this bug" → agent reproduces, bisects, patches, tests |
| 19.3 | "Refactor this" → agent plans, executes, verifies no regressions |
| 19.4 | "Document this" → agent writes README, ADRs, API docs, diagrams |
| 19.5 | "Review this PR" → agent posts line comments, suggests fixes |
| 19.6 | "Migrate this" → agent upgrades deps, fixes breaking changes |
| 19.7 | "Optimize this" → agent profiles, benchmarks, applies fixes |
| 19.8 | "Secure this" → agent threat-models, adds hardening |
| 19.9 | "Explain this" → agent generates walkthrough + diagrams |
| 19.10 | "Teach me this" → agent creates interactive tutorial |

---

## Phase 20 — Platform Maturity
| # | Subphase |
|---|----------|
| 20.1 | 99.9% uptime SLA + status page |
| 20.2 | Global CDN for frontend + model endpoints |
| 20.3 | Automated canary releases for all components |
| 20.4 | Chaos engineering on platform itself |
| 20.5 | Disaster recovery RTO < 15min, RPO < 1min |
| 20.6 | Penetration test + bug bounty program |
| 20.7 | Community edition + Enterprise edition split |
| 20.8 | Plugin SDK docs + example plugins |
| 20.9 | Agent certification program (skills verified) |
| 20.10 | Self-hosting installer (single binary + SQLite/Postgres) |

---

## How to Use This Roadmap

1. **Pick one phase** that unblocks your current workflow
2. **Complete all 10 subphases** before moving to next phase (they compound)
3. **Ship incrementally** — each subphase should be demoable
4. **Measure**: velocity, agent success rate, human intervention rate
5. **Iterate**: roadmap is living; reorder based on pain points

---

*Generated from the teamz autonomous agent platform — the system that builds itself.*