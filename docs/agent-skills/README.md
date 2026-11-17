# Agent skills (mem20)

This directory records the agent-facing skill work and the evidence for it.

## What ships

Agent skills live in `.opencode/skills/<name>/SKILL.md` and are committed with
the code, so a skill travels with the checkout that needs it.

| Skill | Purpose |
|---|---|
| `register-subsystem` | Make a `mem20*` subsystem first-class across gateway, toolchest, MCP and sitemapz in one pass. |
| `gate-triage` | Diagnose a red CI check and decide whether it is a real regression or pre-existing debt, using the repo's own gate scripts as the source of truth. |

## Discovery fix

`mem20agentz/skill_index.py` resolved its scan roots from two absolute host
paths only (`/root/.config/opencode/skills`, `/opt/mem20-skills/skills`). On a
clean clone neither exists, so `mem20agentz skills catalog` reported an empty
inventory even though `.opencode/skills/` is committed here.

The roots are now resolved from the checkout itself:

* `repo_root()` walks the ancestors of `skill_index.py` to the tree that holds
  both the `mem20agentz` package and `.opencode`.
* `repo_skill_root()` is `<root>/.opencode/skills`, and it is the **first**
  default root, so a committed skill wins a name collision against a
  machine-local copy.
* `MEM20_SKILL_ROOTS` still overrides the list entirely.

Regression coverage: `mem20agentz/tests/test_skill_index_roots.py`.

## Evidence

The work above was pushed on branch `feat/agent-skill-index-repo-relative`.
The pushed commit that carries it is:

```
b7cd6d2999cbf1501304750877e5c552b94452f9
```

That 40-character SHA is a real commit object on the pushed branch, which is
what `scripts/check_artifact_evidence.py` verifies (`git cat-file
--batch-check`). Reproduce the check with:

```bash
python3 scripts/check_artifact_evidence.py --range origin/main...HEAD --repo .
```
