"""Round-2 completion: trim over-length plans and expand thin plans to 20-30 items.

Every item is specific and grounded, not filler.
"""

TRIM = {
 "R01": [  # 32 -> drop the 2 least essential
  "Document the tested limits honestly",
  "Classify knowledge as shared or isolated",
 ],
 "R02": [
  "Measure whether transferred knowledge helps the receiving agent",
 ],
 "T01": [
  "Require evidence of execution for every done claim",
 ],
 "T02": [
  "Verify the bi-temporal and grounded-firewall claims against real enforcement",
 ],
}

EXPAND2 = {
"E07": [
 "Verify the install matrix runs on a clean virtualenv, not the live one",
 "Add an entry-point invocation check per packaged organ",
 "Fail the CI job on any organ that fails to import",
 "Record failures per organ so they are individually actionable",
 "Ensure the smoke suite is hermetic and needs no network",
],
"H01": [
 "Verify no service holds a port claimed by another unit",
 "Check every ExecStart before touching any port",
 "Alert on any unit that fails to reach active state",
 "Document restart policy for each unit explicitly",
],
"H02": [
 "Add a privacy statement before any analytics is enabled",
 "Ensure every claim links to the reproducible benchmark run",
 "Document the deployment process so it can be repeated",
],
"H03": [
 "Report every duplicate found across the whole estate",
 "Document the single-source convention for roadmaps",
 "Ensure the canonical copy is the one referenced elsewhere",
],
"H04": [
 "Verify no registry entry points at a missing package",
 "Document how an agent discovers a newly registered tool",
 "Ensure registry refresh is cheap enough to run routinely",
],
"H05": [
 "Publish when each gate failure was first seen",
 "Ensure the gate cannot be bypassed by a partial run",
],
"L03": [
 "Prioritise by claim strength, not alphabetically",
 "Verify added tests fail when behaviour regresses",
],
"M01": [
 "Verify the harness terminates at the largest corpus size",
],
"M03": [
 "Verify memory reduction does not regress latency",
],
"N01": [
 "Ensure trust tools are uniformly exposed across platforms",
 "Document which surface each platform is expected to use",
],
"O01": [
 "Verify the baseline itself is reproducible from a clean checkout",
],
"O03": [
 "Ensure every phase criterion is machine-checkable",
],
"Q02": [
 "Ensure pinned lessons are revisited when related work resumes",
],
"R01-2": [
 "Verify shared reads cannot mutate another namespace's facts",
 "Document which knowledge classes are shared by default",
],
"R02-2": [
 "Verify conflict resolution never silently loses provenance",
],
"S01": [
 "Add a regression test for the false-green status class",
],
"T01-2": [
 "Verify the single command fails when any component is broken",
 "Document the exit codes of the verification command",
],
"T02-2": [
 "Schedule re-verification so drift is caught without manual action",
 "Verify withdrawal actually removes the stale figure",
],
"T03": [
 "Ensure gate failures name the organ and the failing check",
],
"U01": [
 "Verify consolidation does not change temporal query results",
],
"U02": [
 "Verify every registry entry resolves to real on-disk code",
],
"U03": [
 "Verify each milestone gate is machine-checkable",
],
"X01": [
 "Measure whether pre-resolving the model path actually removes the hang",
 "Verify a warm index never serves results from a superseded generation",
 "Test warm-start behaviour with no network and no model cache",
],
"X02": [
 "Distinguish an empty namespace from an empty corpus",
 "Distinguish a filtered-by-trust-threshold empty from a genuinely empty one",
 "Report how often unindexed-present facts are found and repaired",
 "Make the reason code machine-readable in the JSON envelope",
 "Add a dashboard panel showing empty-result reason distribution",
 "Verify reason codes never leak internal state to callers",
],
"X03": [
 "Verify determinism across a fresh process, not just within one",
 "Pin any implicit ordering dependency found in the codebase",
 "Verify determinism holds on a different machine or CPU",
 "Report the determinism guarantee in the API docs",
],
"X04": [
 "Measure budget-exhaustion frequency per query kind",
 "Ensure budget exhaustion is reported, never silent",
 "Verify partial results still carry full provenance",
 "Document recommended budget defaults per agent type",
],
"X05": [
 "Verify actor matches never outrank content matches improperly",
 "Measure field-weight sensitivity on the labelled set",
 "Document which fields are authoritative when they conflict",
],
"X06": [
 "Re-validate every metric after the corpus grows to 1500",
 "Publish which metrics are gate-worthy versus informational",
 "Remove any metric that failed validation from the gate",
 "Keep induced-failure validation as a required CI step",
],
"X07": [
 "Publish the gap between current value and every target",
 "Make target tracking a release checklist item",
 "Verify each target has a reproducible measurement command",
 "Report missed targets honestly at each review",
],
}

# done_when for the 7 new plans
DONE_WHEN = {
 "X01": "Cold and warm start are measured separately, first-query latency is bounded, and an offline cold start fails fast rather than hanging.",
 "X02": "Every empty result carries a machine-readable reason code distinguishing absent, unindexed, filtered and abstained.",
 "X03": "Equivalent queries provably return byte-identical ordered results across processes, machines and index rebuilds.",
 "X04": "Every query has a hard, tested budget for hops, edges, sub-queries and wall time, and exhaustion is signalled rather than silent.",
 "X05": "Field-weighted retrieval is implemented and measured against flat concatenation, with tuned weights and no regression on any query kind.",
 "X06": "Every published metric provably detects the failure it claims to detect, and metrics that cannot are discontinued rather than trusted.",
 "X07": "Every retrieval and trust goal has a numeric target, a reproducible measurement command, and a published current value beside it.",
}