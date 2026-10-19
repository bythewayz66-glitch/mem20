# mem20 Perl SDK

Perl client for the mem20 memory + cognition server. It speaks **JSON-RPC 2.0
over stdio** to a mem20 MCP server process (MCP protocol revision
`2025-06-18`), and it installs with **nothing but core Perl** — no CPAN
access, no compiler, no network at install time.

This is the third language in the family, alongside the Python API
(`mem20api/`) and the Ruby gem (`mem20-sdk-ruby/`). All three expose the same
surface with the same method names.

## Why no CPAN dependencies

The SDK is meant to be droppable into environments where installing CPAN
modules is a fight: air-gapped hosts, distro-packaged interpreters, legacy
applications. Everything it needs — `JSON::PP`, `IPC::Open3`, `IO::Select`,
`HTTP::Tiny`, `Time::HiRes`, `POSIX` — ships with perl itself, so
`perl Makefile.PL && make test` works offline on any 5.20+ interpreter.

That constraint is enforced by a test (`t/00-load.t` asserts every `use`
resolves to a core module), not just by intention.

## Install

```bash
# from a checkout
cd sdk/perl
perl Makefile.PL
make
make test
make install        # or:  perl -Ilib your_script.pl  to run uninstalled
```

```bash
# without installing, straight from the tree
perl -Ilib -e 'use Mem20; print $Mem20::Version::VERSION, "\n"'
```

Requires Perl 5.20 or newer.

## Quick start

The SDK launches the server for you. Point `cwd` at a mem20 checkout:

```perl
use strict;
use warnings;
use Mem20;

Mem20::configure(sub {
    my $c = shift;
    $c->cwd('/opt/mem20');          # where mcp/mcp_server.py lives
    $c->timeout(60);
});

my $client = Mem20::client;

$client->memory_store(
    content  => 'prod runs build 4127',
    category => 'deploys',
    tags     => [ 'prod', 'build' ],
);

my $hits = $client->memory_recall( query => 'what build is prod on', limit => 5 );
print Mem20::Client::text($hits), "\n";

$client->close;
```

## Configuration

Every value has a default, and every `MEM20_*` variable the server documents
is honoured, so one `.env` configures both halves:

| Option | Environment | Default |
|---|---|---|
| `server_command` | — | `['python3', 'mcp/mcp_server.py']` |
| `cwd` | — | *unset* |
| `store_path` | `MEM20_STORE_PATH` | *server default* |
| `cog_path` | `MEM20_COG_PATH` | *server default* |
| `llm_base_url` | `MEM20_LLM_BASE_URL` | `https://integrate.api.nvidia.com/v1` |
| `llm_model` | `MEM20_LLM_MODEL` | *unset* |
| `llm_api_key` | `MEM20_LLM_API_KEY`, `NVAPI_KEY`, `NVIDIA_API_KEY` | *unset* |
| `health_port` | `MEM20_HEALTH_PORT` | `8080` |
| `health_host` | — | `127.0.0.1` |
| `protocol_version` | — | `2025-06-18` |
| `timeout` | — | `30.0` seconds |

```perl
# plain options
Mem20::configure(health_port => 9090);

# or the block DSL
Mem20::configure(sub { $_[0]->health_port(9090) });
```

The resulting config is **frozen**: a client's configuration cannot change
underneath it. Setting an attribute on a frozen config throws
`Mem20::ConfigurationError` rather than silently doing nothing.

Values are validated when you set them, not when you call — `health_port(0)`
fails immediately and leaves the previous good value in place.

## Calling tools

Three routes to the same 257-tool surface:

```perl
# 1. the named memory primitives
$client->memory_store(content => 'x', category => 'general');
$client->memory_recall(query => 'x', limit => 10);

# 2. any tool, by name
my $out = $client->tool('memory_status', {});

# 3. dynamic dispatch — any advertised tool as a method
$client->memory_status;
$client->cog_plan(goal => 'ship the 3.0 baseline');
```

Dynamic dispatch only works for tools the server actually advertises, so a
typo fails loudly (`can` returns false) instead of quietly returning nothing.

## Health surface

```perl
$client->healthy;   # 1/0 — is GET :port/health answering 2xx?
$client->health;    # decoded /health JSON, or undef if not answering
$client->ready;     # decoded /ready JSON, or undef
$client->metrics;   # decoded /metrics JSON; throws if unreachable
```

`health` and `ready` return `undef` on failure because callers overwhelmingly
want to test-and-continue; `metrics` throws because there is no sensible
"no data" value for a counter dump.

## Errors

Four classes, all deriving from `Mem20::Error`:

| Class | Raised when |
|---|---|
| `Mem20::ConfigurationError` | bad option, unknown key, out-of-range value, mutation of a frozen config |
| `Mem20::TransportError` | child failed to start, died mid-call, timed out, or emitted non-JSON |
| `Mem20::ToolError` | the server answered with a JSON-RPC error object (carries `code` and `data`) |
| `Mem20::Error` | base class — catch this to catch everything |

```perl
eval { $client->memory_recall(query => 'x') };
if (my $err = $@) {
    if (ref $err && $err->isa('Mem20::ToolError')) {
        warn "server: " . $err->message . " (code " . ($err->code // '?') . ")\n";
        warn "data: "   . encode_json($err->data) . "\n" if $err->data;
    }
}
```

## A note on stderr

The transport watches the child's **stdout and stderr together**. Reading only
stdout deadlocks the moment the server fills its 64 KiB stderr pipe buffer: the
server blocks writing stderr, stops writing stdout, and the client waits for a
reply that can never come. `t/20-client.t` has a regression test that runs a
deliberately chatty server to prove this does not happen.

The last 4 KB of stderr is retained and appended to every transport error,
because "server closed stdout" on its own tells you nothing.

## Tests

```bash
prove -Ilib t/*.t
```

The suite drives a **real child process** over **real pipes**
(`t/support/fake_mcp_server.pl`), not a mock, so framing, buffering and
deadlock bugs surface here rather than in production.

Coverage: module loading and the core-only dependency invariant, config
defaults/validation/env mapping/freezing, the MCP handshake, tool listing,
argument marshalling, error-object mapping, crash handling, invalid JSON,
stderr backpressure, timeout enforcement, dynamic dispatch, and idempotent
close.

## Status

Version 0.1.0, validated against mem20 server **3.0.0**. The SDK versions
independently of the server (`$Mem20::Version::VERSION` vs
`$Mem20::Version::SERVER_VERSION`).

## See also

- `mem20-sdk-ruby/` — the Ruby gem, same surface
- `mem20api/` — the Python API
- `../docs/API.md` — the tool surface both SDKs expose
