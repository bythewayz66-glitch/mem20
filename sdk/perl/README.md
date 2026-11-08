# mem20 Perl SDK

**First-class Perl client** for the mem20 MCP server. Plain JSON-RPC 2.0 over
stdio, no non-core dependencies.

| | |
|--|--|
| SDK version | 0.2.0 |
| Protocol | JSON-RPC 2.0 / stdio, MCP `2025-06-18` |
| Server baseline | 3.1.2 |
| Tool surface | **311 tools across 39 domains** |
| Perl | 5.16+ (core modules only) |

## Quick start

Three routes to the same **311-tool surface across 39 domains** (verified live
against mem20 3.1.2 — see `AUDIT.md`):

```perl
use Mem20::Client;

my $client = Mem20::Client->new(
    server => '/path/to/mem20/mcp/mcp_server.py',
);

# 1. call a tool by name, raw
my $r = $client->call_tool('memory_store', {
    content          => 'the deploy gate needs a human approval',
    category         => 'project',
    epistemic_status => 'observed',
});

# 2. dynamic method
my $recalled = $client->memory_recall({ query => 'deploy gate', limit => 5 });

# 3. explicit finder
my $tool = $client->find_tool('memory_store');
```

## Tool surface

`verify_surface` compares the live `tools/list` count with the 311/39 this
release was built and tested against:

```perl
my $surface = $client->verify_surface;
# { ok => 1, tools => 311, expected_tools => 311, domains => 39, server_version => '3.1.2' }
```

Note that tool *names* bucket into more prefixes than there are domains:
`memory_*` and `vault_*` sit inside one domain, and a bare `reflexion` has no
underscore. The domain figure comes from the server's `register_*_tools()`
modules, never from splitting names.

## Tests

```bash
prove -Ilib t/*.t                 # 117 tests, no server needed
MEM20_LIVE=1 prove -Ilib t/90-live-server.t   # against a real server
```

That suite asserts the 311-tool surface, a `memory_store` → `memory_recall`
round trip through the grounded partition, and that promotion without evidence
is refused.

## Contamination

The engine guarantees `contamination_rate == 0.0`. `memory_audit_contamination`
surfaces that invariant.

## Versioning

Version 0.2.0, validated against mem20 server **3.1.2** on the **311-tool /
39-domain** surface.

## License

MIT.
