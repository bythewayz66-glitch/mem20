"""Round-4 final completion: close the last shortfalls."""

EXPAND4 = {
"L03": [
 "Ensure each new test names the organ it covers",
 "Verify coverage counts are measured, not estimated",
 "Report the exact untested-organ list in the gap document",
],
"M01": [
 "Verify quality measurement is valid at each corpus size",
 "Ensure scaling results are reproducible from a documented command",
],
"Q02": [
 "Ensure pinned lessons load at session start",
 "Verify a lesson is removed once it no longer applies",
],
"R01-2": [
 "Publish the load-test limits alongside the benchmark numbers",
],
"S01": [
 "Verify the fix covers every status surface, not just memory_status",
 "Ensure the absent-versus-empty distinction is testable in CI",
],
"T03": [
 "Ensure the gate names the failing check, not only the organ",
 "Publish the gate result as part of the canonical status",
],
"U01": [
 "Verify both temporal suites remain green after consolidation",
],
"U03": [
 "Ensure each milestone has a named owner and gate",
],
"X01": [
 "Verify a cold start with no network fails fast, never hangs",
 "Document the operator-visible difference between cold and warm",
 "Publish warm-start as a measured benchmark figure",
],
"X02": [
 "Document every empty-result reason in the API reference",
 "Verify the reason code is stable across versions",
],
"X03": [
 "Verify determinism is unaffected by index growth",
 "Ensure ties are broken by a documented total order",
],
"X04": [
 "Verify budget exhaustion returns partial results, never an error",
 "Ensure budgets cannot be disabled silently by an agent",
],
"X05": [
 "Ensure field weights are published in the benchmark output",
 "Verify field weighting holds under multi-hop queries",
],
"X06": [
 "Ensure an unvalidated metric can never gate a release",
 "Document the induced-failure proof for the headline metrics",
],
"X07": [
 "Ensure every target maps to exactly one measured metric",
 "Publish target achievement only with its evidence attached",
],
}