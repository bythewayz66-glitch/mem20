# mem20 Agent Operating Protocol

**Status:** active · **Owner:** @bythewayz66-glitch · **Applies to:** every AI agent working this repo

Three agents work mem20. Without a protocol they edit the same files, produce
conflicting commits, and duplicate work. This document is that protocol. Read it
in full before your first edit; keep it short, keep it true.

---

## 1. Participants and ownership boundaries

Each agent owns a **layer**. Own your layer; propose changes to the others'
layers through an issue instead of editing them directly.

| Agent | Owns (write access) | Does not touch |
|---|---|---|
| **Teamily** | Repo hygiene: `.github/`, `docs/`, top-level `*.md`, issue triage, CI config, audits and cross-repo reporting, `docs/handoff/` | Package source code, runtime wiring, systemd units |
| **Hermes** | Runtime & deployment: service units, `launch/`, `bin/`, config surfaces (`~/.mem20`), bridge/gateway wiring, install & upgrade path, `CONFWORK.md` | Application logic inside packages, docs prose |
| **OpenCode** | Implementation: package source (`mem20*z/**`), bug fixes, features, refactors, `tests/**` | `.github/`, release/versioning, service units |

Shared, read-only-by-convention: `README.md`, `INDEX.md`, `CANONICAL.md`,
`CHANGELOG.md`. Change them only in a PR that also changes the thing they
describe, and note it in the PR body.

> If a task crosses layers, it is **two tasks**. Split it into two issues and
> hand off at the boundary. Do not "just quickly" edit another layer.

---

## 2. The work queue is GitHub Issues

GitHub Issues is the single source of truth for work. Nothing is "being done"
until it has an issue.

- Every issue carries a **`severity:*`** label (`critical` > `high` > `medium` > `low`)
  and at least one component label (`bug`, `enhancement`, `tooling`, `ci`,
  `tech-debt`, `security`).
- Priority is the label order above, then issue age.
- If you find work with no issue, **open the issue first**, then claim it. A
  finding with no issue is a finding that will be lost.

---

## 3. Claims — one writer per file

The failure mode this prevents: two agents editing one file, one commit
silently reverting the other. The rule is absolute: **before you edit a file,
claim it.**

### To claim

1. Confirm no open claim lists your files. Check `docs/handoff/claims/`:

   ```bash
   grep -rl "<path/you/want/to/edit>" docs/handoff/claims/
   ```

2. Create `docs/handoff/claims/<issue-number>-<short-slug>.md` from the template
   below, with `status: in-progress`, `.github/`-owned agents committing it
   themselves and code agents including it in their first commit.
3. Use a branch named `<agent>/<issue-number>-<short-slug>`
   (e.g. `opencode/42-fix-gateway-fstring`).

### Claim file format

```markdown
---
issue: 42
agent: opencode
status: in-progress        # in-progress | blocked | review | done
branch: opencode/42-fix-gateway-fstring
opened: 2026-10-15
updated: 2026-10-15
files:                      # exact paths; nobody else edits these while in-progress
  - mem20agentz/mem20agentz/gateway_web.py
depends_on: []              # other issue numbers that must land first
---

## Intent
One sentence: what this change does.

## State
What is done, what is left.

## Next step
The literal next action, precise enough for another agent to take over.

## Verification
Exact commands that prove it works, and their last observed output.

## Blockers
Anything stopping progress, and who can unblock it.
```

### Claim lifecycle

`in-progress` → (`blocked` ↔ `in-progress`) → `review` → `done`

- On **done**: set `status: done`, add the merged PR/commit link, and move the
  file to `docs/handoff/claims/archive/`.
- On **blocked**: say what is needed and who can provide it, and @-mention them
  on the issue.
- A claim with no update for **7 days** is considered abandoned; any agent may
  take it over after commenting on the issue.

### Conflicts

- Two claims naming the same file: the **earlier-opened claim wins**. The second
  agent stops, comments on the issue, and either waits or takes different work.
- Never `git push --force`, never rebase another agent's branch, never revert a
  commit you did not author without an issue and a comment.

---

## 4. Handoff documents — what passes between agents

A handoff is a claim file (above) **plus** a handoff note when the whole task
moves from one layer to another. Use `docs/handoff/HANDOFF_TEMPLATE.md`.

A handoff **must** contain, or it is not a handoff:

1. **Context** — the goal and why, linked to the issue.
2. **Current state** — exactly what exists now: branch, commit SHA, files changed,
   what was verified and how.
3. **Next steps** — the literal next actions, in order, with the commands.
4. **Boundaries** — what the receiving agent must **not** change.
5. **Blockers / open questions** — with the human decision needed, if any.

A handoff that says "continue from here" without those five is incomplete.

---

## 5. Branches, commits, PRs

- Branch: `<agent>/<issue-number>-<slug>`. Never commit to `main` directly.
- Commit: Conventional Commits (`fix(scope):`, `feat(scope):`, `docs:`, `ci:`).
- One issue per PR. Reference it: `Closes #<n>`.
- PR body uses `.github/PULL_REQUEST_TEMPLATE.md` and names the agent + claim.
- The human owner (@bythewayz66-glitch) merges. Agents open PRs; they do not merge.
- No PR merges with a failing `Syntax gate` check.

---

## 6. Staying in sync

`docs/handoff/STATE.md` is the living board — **update it when your claim
changes state.** It is how an agent with no prior context picks up work in one
read. Keep it to the current week; move older rows to `archive/`.

At the start of every session:

1. Read `docs/handoff/STATE.md`.
2. Read the open `docs/handoff/claims/`.
3. Pick an issue that is unclaimed and in your layer.

---

## 7. Escalation to the human

Escalate — do not decide — when a change:

- moves an entry point or a systemd `ExecStart` target,
- changes packaging, versioning, or release flow,
- deletes or restructures a tree,
- touches secrets, credentials, or network exposure,
- contradicts the three-agents-one-repo model itself.

Escalate by opening an issue labelled `blocked` and @-mentioning the owner.
