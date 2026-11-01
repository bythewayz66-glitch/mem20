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
