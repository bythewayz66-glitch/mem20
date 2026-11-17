# GH-EXP-001 hero arms and switchback assets

This directory contains the concrete assets to start GH-EXP-001 ("Prove It" hero) as a day-level switchback on a static site.

## Files
- `control.html` — control hero arm (current message framing baseline copy).
- `treatment.html` — treatment hero arm ("prove it": grounded/simulated partition + auditability claim first, install command above the fold, benchmark caveat visible).
- `switchback.js` — client-side day-level switchback selector based on `schedule.json` (UTC day key). Intended to be included by the live landing page when the experiment is activated.
- `schedule.json` — pre-committed arm assignment by UTC date (`YYYY-MM-DD`). Edit before launch to set the committed coin-flip schedule.
- `per-visitor-randomization.js` — privacy-respecting per-visitor variant assignment helper (localStorage only, no cookies, no external beacon required) for measurement/analysis when analytics collection is enabled.

## Activation (static Pages)
1. Review and finalize `schedule.json` for the experiment window (and any pre-committed extension window).
2. Decide the serving mode:
   - **Full-page arm swap:** route `/` to the assigned arm page for the day (requires a small loader/redirect in `docs/index.html`).
   - **Hero-only swap:** include `switchback.js` on `docs/index.html` and let it render/inject the treatment hero on treatment days.
3. Ensure analytics collection is configured (see `docs/series/analytics.js`) and verify events include arm assignment metadata.

## Notes
- Day-level assignment is the honest design for a static page without server-side bucketing.
- Per-visitor randomization here is for measurement support; do not claim day-level and visitor-level designs are equivalent.
- `control.html` and `treatment.html` are self-contained snapshots for review/testing and can be diffed to audit message changes.
