# Launch page rebuilt on the live surface — 2026-11-16

## What changed

docs/index.html — rebuilt from the current main source so the launch page states the
**live** surface (487 MCP tools / 129 domains) instead of leaving the reader to guess.

## Before

- curl -sS -o /tmp/live_before.html -w '%{http_code} %{size_download}' https://mem20.com/ -> 200 / 10998
- sha256sum of the live body -> 3cf3f60366c35f948aa90ec91890494b78b478d3cbf4624816dffcd7c108c89e
- sha256sum of docs/index.html on main at 0224a64946a2c00313a9872515893157adcbc47e -> 3cf3f60366c35f948aa90ec91890494b78b478d3cbf4624816dffcd7c108c89e
- diff of the live body against docs/index.html -> empty; the served bytes were byte-identical to the file on main
- a scan of the served HTML for a tool/domain count returned no match — the page stated no tool or domain figure at all

The retired band was not printed on the page itself; it lived in the docs around it
(docs/gtm/mem20-launch-copy.md, docs/market/competitive-matrix-2026-11-01.md,
docs/gtm/launch-instrumentation.md). The page's own "On the numbers" note deferred the figure to
README.md rather than stating it. That is the gap this change closes: the page now carries the
measurement, and carries it from the pinned source.

## After

- sha256sum of docs/index.html -> f5939a160030d246dcdb8ec04d3744d7a26e1fe328f60387231a5ffe0cf9d721
- wc -c docs/index.html -> 15327
- the committed blob size reported by the GitHub API -> 15327, matching the local file byte for byte
- git diff --stat against main -> 1 file changed, 93 insertions, 11 deletions

New content:

- hero fact strip now reads v4.0.0, 487 MCP tools, 129 domains, Apache-2.0
- new section "The surface, measured" — 487 tools, 129 domains, 19 unwired tools, plus the twelve
  largest domains: memory 55, cognitive 19, world 14, versioncontrol 11, cloudservice 10,
  database 10, filesystem 10, lie 10, productivity 10, braid 9, communication 9, dev 9
- the "On the numbers" note now names docs/surface.json and the CI doc-count drift gate as the
  reason the page and the server cannot disagree
- the meta description and og:description carry the same figure

## Verification

Doc-count drift gate, run against the working tree after the rebuild:

- live pin: 487 tools / 129 domains
- scanned: 85 live docs
- result: OK, no retired tool/domain band in any live doc
- exit code 0

Retired-band scan over the rebuilt page returned no match.

Headless Chromium render of the local file at 1440x1000:

- TITLE: mem20 — auditable agent memory
- H1: A memory that can prove what it knows.
- facts: v4.0.0, VERSION, 487, MCP TOOLS, 129, DOMAINS, Apache-2.0, LICENSE
- has 487: True, has 129: True
- retired 257: False, retired 268: False
- surface numbers: 487 MCP TOOLS, 129 DOMAINS, 19 UNWIRED TOOLS
- domain rows: 12
- console errors: none
- scrollWidth / clientWidth: 1440 / 1440 — no horizontal overflow

## Source of the numbers

docs/surface.json on main:

- tools: 487
- domains: 129
- unwired_tools: 19
- cross_check: ast_tools 487, ast_domains 129, only_ast empty, only_live empty

Generated from the live JSON-RPC tools/list response; the AST catalog agrees exactly, with no tool
present in one catalog and missing from the other.

## Rollback

Revert this commit. docs/index.html returns to
3cf3f60366c35f948aa90ec91890494b78b478d3cbf4624816dffcd7c108c89e (10,998 bytes), which is what
https://mem20.com/ serves today. No DNS, Pages configuration, or workflow file is touched by this
change, so a revert needs no redeploy beyond the normal Pages build.

## Not verified in this change

The post-merge state of https://mem20.com/. The deployed bytes can only be re-checked against main
after this branch is merged and the Pages workflow redeploys. The pre-change check above
(live equal to main, HTTP 200, byte-identical) is the state as of this commit.
