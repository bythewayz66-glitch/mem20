# `.opencode/` — OpenCode agent skills

**Owner:** mem20-admin · **Status:** tool-owned config

Skill definitions for the **OpenCode** agent harness. Each skill is a directory with a
`SKILL.md` that teaches the harness a repo-specific workflow.

## What lives here

| Path | What it is |
|---|---|
| [`skills/register-subsystem/SKILL.md`](./skills/register-subsystem/SKILL.md) | The workflow for registering a new `mem20*z` subsystem: where the package goes, what the entry doc must contain, and how it is wired into the surface. |

## Rules

1. **One directory per skill**, each with a `SKILL.md` carrying `name` and a
   triggering-focused `description` in its frontmatter.
2. **Repo-specific only.** A skill that would apply to any repo belongs in the shared
   skill library, not here.
3. **Keep it in sync with the real tree.** A skill that names a path which no longer
   exists is worse than no skill — it teaches the harness a wrong workflow.

## Related

- [`AGENTS.md`](../AGENTS.md) — the agent operating protocol.
- [`docs/handoff/AGENT-OPERATING-PROTOCOL.md`](../docs/handoff/AGENT-OPERATING-PROTOCOL.md) —
  required reading before any agent edit.
