# `entries/` — session memory entries (generated, gitignored)

**Owner:** mem20 memory engine · **Status:** generated data, not source

This directory holds the **memory entries** the mem20 engine writes during a session —
timestamped, priority-tagged notes grouped by topic (`general`, `project`,
`self_model`, `corrigibility_tier`, …). They are the on-disk form of the agent's
episodic memory, not documentation and not code.

## Important: this directory is gitignored

`.gitignore` ignores `entries/*.md`. Force-added entries fall out of `git status` and
are easy to lose, so this README is tracked via a `!entries/README.md` negation.

If you intend to version a specific entry, add a targeted negation rather than
force-adding.

## File shape

Each file is a topic bucket. Entries inside are appended in reverse-chronological
order with a heading that carries the ISO timestamp, priority and tags:

```
## 2026-09-06T19:42:48.017670+00:00  (pri=normal, tags=[])
<entry body>
```

## Rules

1. **Do not hand-edit entries.** They are engine-written; a hand edit desynchronises
   the file from the memory store.
2. **Do not treat entries as documentation.** They are a session log. Anything that
   should be read by a human as docs belongs under `docs/`.
3. **Do not commit new entries by default.** They are per-session state. Commit one
   only when it is deliberately being preserved as evidence, and say why in the commit
   message.

## Related

- [`memory_engine/README.md`](../memory_engine/README.md) — the engine that writes these.
- [`docs/01-architecture.md`](../docs/01-architecture.md) — where entries sit in the
  memory model.
