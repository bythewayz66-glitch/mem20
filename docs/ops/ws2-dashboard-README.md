# dashboard 270/27 rebuild — verified patch against docs/dashboard.html

The dashboard rebuild ships as this patch because the sandbox has no git write
credential and the 61 KB body cannot be safely re-transcribed through a
single API payload. The patch was verified to reproduce the reviewed build
byte-for-byte before being committed here.

## Verification performed

Base: `docs/dashboard.html` on `feat/ws2-launch-page-270` @ `c9d67fb` (identical to `main`)

    git show HEAD:docs/dashboard.html > base.html
    cp base.html work.html
    patch -s work.html < docs/ops/ws2-dashboard.patch
    cmp work.html <reviewed build>        # => identical

Reviewed build sha256:
`6a89a72524595b77b4dd92aef704e2a609338fe94ddc459c6cfb6c901e7c3c10` (61,488 bytes)

## What it changes

1. Hero chips: adds `Surface 270 tools / 27 domains`.
2. Blocker B2 rewritten — `/sites/` is 403 to anonymous under both a bare client
   and a Chrome UA (measured token-free); the shippable public surface is GitHub
   Pages at `bythewayz66-glitch.github.io/mem20/`, which returns 200. The old
   card cited a launch path that no longer exists.
3. New section `07 — Tool surface`: 270 tools / 27 domains, capability registry
   889, retired surface 257/26, plus a source-of-truth table naming
   `verify_mcp.py`, `README.md`, `docs/index.html`, `docs/finance/inputs.json`
   and `CHANGELOG.md`. States that 27 groups 37 raw tool prefixes.
4. Benchmark section renumbered `07` -> `08`; wiring section `08` -> `09`, so
   numbering stays unique across `00`-`09`.
5. Adversarial 0.000 stays explicit in both the hero chip and the benchmark block.

## Apply

    git apply docs/ops/ws2-dashboard.patch

Expected result: `docs/dashboard.html` matches the sha256 above.

## Published artifact

The rebuilt dashboard is already live at
https://static.teamily.ai/sites/6aacb84a-cf8f-448f-bcd1-8bac8c850dc6/webpages/mem20-launch-dashboard-v4/index.html
(200 with token, 403 to anonymous — see `docs/ops/launch-page-270-urls.md` §4).
