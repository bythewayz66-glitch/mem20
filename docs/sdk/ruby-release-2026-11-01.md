# mem20 Ruby SDK — gemspec, packaging, and a green `rspec` run

**Date:** 2026-11-01
**Owner directive:** [`docs/ops/owner-directive-2026-11-01.md`](../ops/owner-directive-2026-11-01.md) @ `06fa1220e964f84aabac78127fc18463dfa6798d` (roster item **11. Mem20-Ruby-Expert — G5**)
**Branch:** `ruby-sdk-release-2026-11-01`, cut from `main` @ `2ea4492209dfaae6afb22ca884132a0d1849bfcf`
**SDK location:** `mem20-sdk-ruby/**`
**Raw transcript:** [`docs/rspec-summary-2026-11-01.txt`](../rspec-summary-2026-11-01.txt)

---

## 1. What the gap actually is

The gap register records that **PyPI 404s** for `mem20`, `mem20-mcp` and `mem20-sdk`.
The Ruby counterpart is the same shape of gap: the gem builds and tests clean, but it
**is not on RubyGems**. Probed in this run:

```
$ curl -s -o /dev/null -w '%{http_code}' https://rubygems.org/api/v1/gems/mem20-sdk.json
404
$ ... mem20.json        -> 404
$ ... mem20-mcp.json    -> 404
```

So the Ruby SDK had a working gem in the tree with no packaging guarantees and no
publishable artifact. This branch fixes the **packaging** half and proves it with a
green suite; the **publish** half is blocked on a credential that does not exist in
this environment (§6).

---

## 2. Gemspec changes (`mem20-sdk-ruby/mem20-sdk.gemspec`)

The gemspec already built, but it had five things a publishable gem should not ship
with. Each is now fixed:

| Change | Why |
|---|---|
| `spec.files = Dir[...].sort` (was unsorted `Dir[...]`) | An unsorted glob makes the packaged file **list** depend on filesystem order. Two builds of the same tree could differ in entry order. Sorted now, and pinned by a spec. |
| `spec.metadata["allowed_push_host"] = "https://rubygems.org"` | Without it a stray `gem push --host` can land on a mirror. Now the gem can only go to RubyGems. |
| `spec.metadata["bug_tracker_uri"]` | RubyGems renders a link for it; it was the one metadata field missing from the set. |
| `spec.required_rubygems_version = ">= 3.3.0"` | `allowed_push_host` in metadata and MFA enforcement need a modern RubyGems. Declared rather than assumed. |
| metadata URIs re-pointed and verified | `homepage`, `source_code_uri`, `changelog_uri`, `documentation_uri` all resolve under `bythewayz66-glitch/mem20`. No `JaysonAIOnline` reference remains anywhere in the tree (`grep -rn JaysonAIOnline .` → no hits). |

`spec.files` still resolves to exactly these 18 entries — the whole library, the docs,
the examples, and the three top-level files a reader needs:

```
CHANGELOG.md  LICENSE  README.md
docs/API.md  docs/EVIDENCE.md  docs/INSTALL.md  docs/USAGE.md
examples/health_probe.rb  examples/quickstart.rb  examples/rails_initializer.rb
lib/mem20.rb  lib/mem20/client.rb  lib/mem20/config.rb  lib/mem20/errors.rb
lib/mem20/job.rb  lib/mem20/surface.rb  lib/mem20/transport/stdio.rb  lib/mem20/version.rb
```

Deliberately **not** packaged: `*.gem`, `Gemfile.lock`, `spec/**`. The gemspec declares
**zero runtime dependencies** (stdlib only: `json`, `open3`, `net/http`, `timeout`), so
`gem install mem20-sdk` pulls nothing else in.

---

## 3. New packaging spec (`mem20-sdk-ruby/spec/mem20/packaging_spec.rb`)

The library specs never touched the gemspec — the code could be perfect and still ship
a `.gem` missing a file. Eleven examples now cover the packaging contract, and the last
one **builds the real `.gem`** and reads its payload back:

```
mem20-sdk packaging
  loads as a valid Gem::Specification
  takes its version from Mem20::VERSION rather than repeating it
  declares the Ruby floor the code actually needs
  ships no runtime dependencies
  points every metadata URI at the canonical repo
  requires MFA for pushes and pins the push host
  packages every library file, and nothing outside the declared globs
  packages the docs, examples and top-level files a reader needs
  keeps spec.files sorted so two builds of one tree are byte-identical
  never packages a built .gem, a lockfile or the specs
  builds a .gem whose payload matches spec.files
```

Two things this catches that nothing else did:

- **A file added to `lib/` but not packaged.** The first example compares
  `spec.files.grep(%r{\Alib/})` against `Dir["lib/**/*.rb"]` on disk. Add a new
  `lib/mem20/*.rb` and forget the glob and the suite goes red.
- **A version drift between the gemspec and the code.** `gemspec.version` is asserted
  equal to `Mem20::VERSION`, so the two cannot diverge silently.

Honest note on determinism: `spec.files` is now sorted, so the **payload** is
deterministic. The `.gem` file's own sha256 is **not** reproducible across builds,
because RubyGems stamps `metadata.gz` with the build time — the two builds in this run
produced `33786e3d…` and `2867cd37…` for identical payloads. That is RubyGems'
behaviour, not something the gemspec can pin.

---

## 4. The green run (verbatim from `docs/rspec-summary-2026-11-01.txt`)

Environment: Debian Linux x86_64, `ruby 3.1.2p20 (2022-04-12 revision 4491bb740a)`,
rspec 3.13.2, rubocop 1.92.2, rake 13.4.2 — resolved fresh by `bundle install` in this
run.

```
$ bundle exec rspec
...
Finished in 0.99071 seconds (files took 0.18987 seconds to load)
84 examples, 0 failures

Randomized with seed 63244
```

```
$ bundle exec rubocop --format simple

25 files inspected, no offenses detected
```

```
$ for f in $(find lib -name '*.rb' | sort); do ruby -c "$f"; done
Syntax OK   (× 8 — every file under lib/)
```

The suite is **hermetic**: the transport specs spawn
`spec/support/mini_mcp_server.rb`, a real child process speaking JSON-RPC over stdio,
so CI needs neither Python nor a running mem20 server. That is what makes "84 examples,
0 failures" meaningful on a machine with no mem20 install.

---

## 5. `gem build` and install verification

```
$ gem build mem20-sdk.gemspec
  Successfully built RubyGem
  Name: mem20-sdk
  Version: 0.2.0
  File: mem20-sdk-0.2.0.gem

$ gem install --local ./mem20-sdk-0.2.0.gem --no-document
Successfully installed mem20-sdk-0.2.0
1 gem installed

$ cd /tmp && ruby -e 'require "mem20"; ...'    # outside the source tree
loaded_from=/var/lib/gems/3.1.0/gems/mem20-sdk-0.2.0/lib/mem20.rb
VERSION=0.2.0
SERVER_VERSION=2.1.0rc2
PROTOCOL_VERSION=2025-06-18
surface=270 tools across 27 domains (268 domain tools + 2 infra tools: job_status, job_wait)
surface_consistent=true
```

The `loaded_from` line is the point: it resolves to the **installed gem**, not
`mem20-sdk-ruby/lib`, so the packaged artifact actually loads.

`rake surface:check` also passes, re-deriving the surface from the Python sources
rather than trusting the constant:

```
source:  27 modules, 268 domain tools, 2 infra tools (job_status, job_wait), 270 total
surface: 270 tools across 27 domains (268 domain tools + 2 infra tools: job_status, job_wait)
OK - Mem20::Surface matches mcp/
```

---

## 6. What is NOT done — publishing

**`gem push` was not attempted.** There is no RubyGems API key in this environment:
`$GEM_HOST_API_KEY` is unset and `~/.gem/credentials` does not exist. Rather than
report a publish that did not happen, this section states the blocker plainly.

The packaging is release-ready and the release path is already wired:
`.github/workflows/release.yml` triggers on a `mem20-sdk-ruby-v*` tag, **checks the tag
against `Mem20::VERSION` before pushing** so a mistyped tag cannot ship a mismatched
gem, re-runs the suite, installs the built gem and loads it, and only then calls
`gem push`. It fails loudly when `RUBYGEMS_API_KEY` is absent instead of skipping.

To close the RubyGems 404, one of these must happen:

```bash
# Option A — CI (preferred): one-time secret, then a tag
#   Settings > Secrets and variables > Actions > RUBYGEMS_API_KEY
git tag -a mem20-sdk-ruby-v0.2.0 -m "mem20-sdk 0.2.0"
git push origin mem20-sdk-ruby-v0.2.0

# Option B — from a workstation holding a key scoped to mem20-sdk
cd mem20-sdk-ruby
gem build mem20-sdk.gemspec
gem push mem20-sdk-0.2.0.gem
```

Until one of those runs, **the gem is not installable from RubyGems** and the 404
stands. This branch does not claim otherwise. Note also that `mem20` and `mem20-mcp`
(PyPI) are a separate, Python-side gap that this Ruby branch does not touch.

---

## 7. Not claimed

No memory-quality, retrieval-accuracy, LongMemEval or LoCoMo figures appear here —
none were measured in this run. The numbers in this document describe the Ruby SDK's own
build, packaging and test behaviour, not the quality of the memory engine it talks to.
The only live-server figure anywhere in the SDK (`docs/EVIDENCE.md`, 5.805 ms
round-trip) is from the retired Sidney host and is labelled as such there.

---

## 8. Reproduction

```bash
git clone --branch ruby-sdk-release-2026-11-01 https://github.com/bythewayz66-glitch/mem20.git
cd mem20/mem20-sdk-ruby
bundle install
bundle exec rspec                      # 84 examples, 0 failures
bundle exec rubocop --format simple    # 25 files inspected, no offenses detected
bundle exec rake surface:check         # OK - Mem20::Surface matches mcp/
gem build mem20-sdk.gemspec            # mem20-sdk 0.2.0
gem install --local ./mem20-sdk-0.2.0.gem --no-document
cd /tmp && ruby -e 'require "mem20"; puts Mem20::VERSION'   # 0.2.0
```
