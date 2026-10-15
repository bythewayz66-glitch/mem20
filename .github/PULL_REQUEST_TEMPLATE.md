<!-- mem20 PR template. Keep every heading; delete only what truly does not apply. -->

## Summary
<!-- What changes, and why. One or two sentences. -->

## Linked issue

Closes #

## Type of change

- [ ] Bug fix
- [ ] New feature / tool
- [ ] Refactor / tech-debt cleanup
- [ ] CI / tooling
- [ ] Documentation only

## How it was verified

<!-- Exact commands you ran and what they printed. "Tests pass" is not enough. -->

```
python3 -m compileall -q <touched paths>
python3 -m pytest <package> -q
```

## Checklist

- [ ] `python3 -m compileall` is clean on every file I touched
- [ ] I did not commit `build/`, `__pycache__/`, `node_modules/`, model caches, or runtime state
- [ ] New or changed tests are included (or this is docs-only)
- [ ] I updated the affected docs (`README.md`, `docs/`, `INDEX.md`) in this PR
- [ ] No secrets, tokens, or personal absolute paths are included
- [ ] If `mem20/mcp_server.py` or another systemd `ExecStart` path moved, the unit file was updated too

## Agent hand-off

<!-- If an agent produced this PR, name it and reference its claim. -->

- Agent:
- Claim: `docs/handoff/claims/`
