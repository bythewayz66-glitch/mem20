# mem20 documentation index

## Agents
- **[Agent Operating Protocol](handoff/AGENT-OPERATING-PROTOCOL.md)** — required reading before any agent edit (claims, layers, PR rules).
- [Handoff template](handoff/HANDOFF_TEMPLATE.md)
- [Claims](handoff/claims/)

## Finance
- **[Financial model (reconciled)](finance/README.md)** — canonical home of the model. House numbers
  (blended ACV $14,000 · TAM $1.28B · SAM $282M · SOM $1.68M) are treated as inputs and asserted, not re-derived.
  Regenerate with `python3 docs/finance/compute_model.py`; verify only with `--check`. Stated against the live
  **270 tools / 27 domains** surface (257/26 is retired).

## Hygiene
- [Spec authority paths](hygiene/spec-authority-paths.md) (#14 / #15)
- [Generated state](hygiene/generated-state.md) (#16)
- [core.py duplication](hygiene/core-py-duplication.md) (#17)
- [test/ scratch](hygiene/test-scratch.md) (#18)

## Security
GitHub **secret scanning** and push protection are enabled in repository settings
(Settings → Code security). Agents cannot flip org/repo toggles from code; owners
must confirm under the Security tab (issue #11).
