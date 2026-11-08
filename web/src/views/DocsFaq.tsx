  {
    q: 'How many tools does mem20 actually expose?',
    a: (
      <>
        {CATALOG.count} tools across {CATALOG.domain_count} domains, counted from source. The count is
        produced by parsing every <span className="mono">mt.Tool(…)</span> registration in{' '}
        <span className="mono">mcp/**/*.py</span> and then keeping only the ones whose mixin is
        actually inherited by <span className="mono">Mem20MCPServer</span> (or whose{' '}
        <span className="mono">install()</span> is called from{' '}
        <span className="mono">mcp/tools/__init__.py</span>). A declaration that is never wired is
        not a tool the server can answer, so it is excluded from the count and listed separately as
        unwired. Older counts quoted in past decks and release notes are retired and are not
        restated here — the number above is the only one this build asserts.
      </>
    ),
    src: 'src/data/tools.json (wiring-checked AST extraction)',
    tags: ['tools', 'catalog', 'count'],
  },