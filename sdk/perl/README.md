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

The SDK launches the server for you. Point `cwd` at a mem20 **checkout root**
(the directory containing `mcp/`), because the server is run as
`python mcp/mcp_server.py` and imports its siblings by script-directory name:

```perl
use strict;
use warnings;
use Mem20;

Mem20::configure(sub {
    my $c = shift;
    $c->cwd('/opt/mem20');          # the directory containing mcp/
    $c->timeout(60);
});

my $client = Mem20::client;

$client->memory_store(
    content          => 'prod runs build 4127',
    category         => 'project',        # user_pref | project | tool | general
    tags             => [ 'prod', 'build' ],
    epistemic_status => 'observed',       # REQUIRED
);

my $hits = $client->memory_recall( query => 'what build is prod on', limit => 5 );
print $client->text($hits), "\n";

my $surface = $client->verify_surface;
printf "%d tools, ok=%d\n", $surface->{tools}, $surface->{ok};

$client->close;
```

Run it end to end:

```bash
# MEM20_PYTHON is only needed when `python3` on PATH is not the interpreter
# that has mem20's dependencies installed.
MEM20_PYTHON=/opt/mem20/.venv/bin/python \
  perl -Ilib examples/quickstart.pl /opt/mem20
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

Three routes to the same **270-tool surface across 27 domains** (verified live
against mem20 3.0.0 — see `AUDIT.md`):

```perl
# 1. the named memory primitives
$client->memory_store(content => 'x', category => 'general', epistemic_status => 'observed');
$client->memory_recall(query => 'x', limit => 10);

# 2. any tool, by name — flat pairs or a single hashref
my $out = $client->tool('memory_status');
my $hit = $client->tool('memory_recall', { query => 'x', limit => 5 });

# 3. dynamic dispatch — any advertised tool as a method
$client->memory_status;
$client->cog_plan(goal => 'ship the 3.0 baseline');
```

`verify_surface` compares the live `tools/list` count with the 270/27 this
release was built and tested against:

```perl
my $s = $client->verify_surface;
# { ok => 1, tools => 270, expected_tools => 270, domains => 27, server_version => '3.0.0' }
```

Note that 270 tool *names* bucket into 37 prefixes: `memory_*` and `vault_*` sit
inside one domain, and a bare `reflexion` has no underscore. The domain figure
comes from the server's `register_*_tools()` modules, never from splitting
names.

### Long-running tools

**24** LLM-backed tools (`imagination_*`, `cog_*`, `tot_*`, `beam_search`,
`least_to_most`, `react_reason`, `theory_of_mind_*`, `self_model_reflect`,
`memory_auto_consolidate`, `cognitive_substrate`) return a job envelope instead
of an answer:

```json
{"job_id":"1d68a688ff44","status":"running","tool":"cog_plan"}
```

```perl
my $final = $client->call_tool_await('cog_plan', goal => 'ship it');
# or, explicitly:
my $job = $client->job_from($client->tool('cog_plan', goal => 'ship it'));
my $done = $client->wait_for_job($job->{job_id}, timeout => 60);
```

The set is a hand-maintained literal in `mcp/server.py`, not a name pattern, so
the SDK ships a copy of it and lets you ask:

```perl
my $tools = $client->long_running_tools;   # 24 names
$client->is_long_running('cog_plan');      # 1
$client->is_long_running('cog_working_memory');  # 0 -- a cog_* tool that answers inline
```

`wait_for_job` never returns a still-running status: it raises
`Mem20::JobTimeoutError` on deadline and `Mem20::JobFailedError` for a terminal
`error`/`not_found` (or an `ok` with a null result). `call_tool_await` raises
`Mem20::JobFailedError` if a long-running tool answers without a `job_id`,
because that is a status word where a result belongs.

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

All derive from `Mem20::Error`:

| Class | Raised when |
|---|---|
| `Mem20::ConfigurationError` | bad option, unknown key, out-of-range value, mutation of a frozen config |
| `Mem20::ValidationError` | a tool argument rejected **locally** against the tool's own `inputSchema` (isa `ConfigurationError`) |
| `Mem20::TransportError` | child failed to start, died mid-call, timed out, or emitted non-JSON |
| `Mem20::ToolError` | the call reached the server and failed there (carries `code`/`data`, `tool`, `is_error`, `soft_error`) |
| `Mem20::JobTimeoutError` | a background job did not reach a terminal state before the deadline |
| `Mem20::JobFailedError` | a job ended `error`/`not_found`, or `ok` with a null result |

### mem20 reports tool failure three different ways

This is the trap the SDK exists to paper over:

| Server behaviour | Observed with | SDK |
|---|---|---|
| JSON-RPC error object | unknown *method* | `ToolError`, no `code` from result |
| **protocol success**, `result.isError = true` | unknown *tool*, handler exception | `ToolError`, `is_error = 1` |
| **protocol success**, `result.isError = false`, text starts `Error` | rejected `epistemic_status`, bad args | `ToolError`, `soft_error = 1` |

The third row is the dangerous one: the envelope is a protocol success, so a
client that trusts `isError` reports a **dropped write as a stored fact**. Raw
transcripts are in `AUDIT.md`.

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
because "server closed stdout" on its own tells you nothing. stderr is held in
`O_NONBLOCK` so that reading it while composing an error can never turn a
timeout into a hang.

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

Against a live server, with the checkout and an interpreter that has mem20's
dependencies:

```bash
MEM20_MCP_DIR=/opt/mem20/mcp MEM20_PYTHON=/opt/mem20/.venv/bin/python \
  prove -Ilib t/90-live-server.t
```

That suite asserts the 270-tool surface, a `memory_store` → `memory_recall`
round trip through the grounded partition, local refusal of a missing
`epistemic_status`, `ToolError` for an unknown tool, `soft_error` for a rejected
status, and a `cog_plan` job polled to a terminal state.

`t/95-jobs.t` drives **all 24** long-running tools from the `{job_id,
status:"running"}` envelope to a terminal state against a hermetic child
process, asserting each job's own result and `job_id` — not the envelope shape.
It is mutation-checked: restoring the old "return the last status on deadline"
bug fails 3 of 10 subtests, and a single-shot (never polls) implementation
fails 4 of 10.

## Status

Version 0.2.0, validated against mem20 server **3.0.0** on the **270-tool /
27-domain** surface. The SDK versions independently of the server
(`$Mem20::Version::VERSION` vs `$Mem20::Version::SERVER_VERSION`).

`AUDIT.md` records how the surface figure was established (registration count
plus a live `tools/list`, not a grep) and every server behaviour the SDK works
around: the three distinct failure shapes, the unenforced `epistemic_status`,
the job-envelope tools, and the `aiohttp` gap in `requirements.txt`.

## See also

- `mem20-sdk-ruby/` — the Ruby gem, same surface
- `mem20api/` — the Python API
- `../docs/API.md` — the tool surface both SDKs expose
