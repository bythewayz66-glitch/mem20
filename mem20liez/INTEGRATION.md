# mem20liez — Integration

## MCP server (zero-config, works on `git clone --depth 1`)

`mcp/server.py` **auto-loads** the full implementation. History is an
optimisation, never a requirement — the resolution ladder is:

1. **Vendored copy** — `mem20liez/_server_impl.py`, committed to the repo. This
   is what makes a `git clone --depth 1` checkout work with no history at all.
2. **Local git object database** — `git show <pinned-sha>:mcp/server.py`.
3. **Targeted fetch** — if the clone is shallow and the object is absent,
   `git fetch --depth=1 origin <pinned-sha>` and retry step 2. Disable with
   `MEM20_MCP_AUTO_FETCH=0` (useful in air-gapped CI).
4. **History scan** — newest committed `mcp/server.py` blob that looks like the
   full implementation.
5. **Actionable failure** — a diagnostic naming the detected condition
   (shallow clone / no `.git` / rewritten commit) and the exact fix.

The `LieToolsMixin` patch is applied in memory when the recovered source is
unpatched. A vendored copy is already patched and is used verbatim.

```bash
git clone --depth 1 https://github.com/bythewayz66-glitch/mem20.git
cd mem20 && python3 ./launcher.py     # works — no unshallow, no extra fetch
```

### Environment knobs

| Variable | Default | Meaning |
|---|---|---|
| `MEM20_MCP_AUTO_FETCH` | `1` | Set `0` to forbid network fetches during startup |
| `MEM20_GOOD_COMMIT` | pinned SHA | Override the source commit for history recovery |

### Regenerating the vendored impl

`mem20liez/_server_impl.py` is a build artefact of one upstream commit plus the
in-memory patch. Rebuild or verify it with:

```bash
python mem20liez/regen_server_impl.py           # rewrite the file
python mem20liez/regen_server_impl.py --check   # non-zero if stale
```

Run `--check` after bumping `_GOOD_COMMIT` or editing the patch helpers in
`mcp/server.py`. CI runs it too, so a stale artefact fails fast instead of
silently serving an old server.

### Tarball / non-git installs

A tarball or vendored install has no `.git`, so steps 2–4 are unavailable and
the committed vendored copy is used directly — which is the normal case, since
it ships in the repo. If it is missing:

```bash
python mem20liez/regen_server_impl.py --sha <sha>
```

## Tools

`mcp/tools/lie_tools.py` — `LieToolsMixin` registered automatically by the restored server.

## Grounded + braid on seal

`lie_seal_session` calls `remember()` and `braid_commit(op="liez.session.sealed")` when those engines are available.
