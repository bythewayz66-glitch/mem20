# Claims directory

One file per claimed work item: `<issue-number>-<short-slug>.md`, built from the
claim format in `../AGENT-OPERATING-PROTOCOL.md` §3.

- **In-flight claims** live directly in this folder.
- **Completed claims** move to `archive/` with `status: done` and the merged PR link.
- Stale for 7 days with no update → treat as abandoned, comment on the issue, take it over.

Before editing a file, check it is not already claimed:

```bash
grep -rl "<path/you/want/to/edit>" docs/handoff/claims/
```

No output means it is free to claim.
