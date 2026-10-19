"""Round-7: exact closure. Every ADD/COUNT matches the measured gap."""

# id -> exactly N additional items (N measured, listed below)
EXPAND7 = {
"D06": [  # need 1
 "Never overwrite an existing corpus version in place",
],
"F02": [  # need 1
 "Publish per-store storage so growth is attributable",
],
"F03": [  # need 3
 "Verify reconciliation is safe to run concurrently with reads",
 "Verify drift detection runs before any benchmark publishes numbers",
 "Publish the drift count as a standing trust metric",
],
"G01": [  # need 4
 "Audit every cognition and imagination tool, not only memory tools",
 "Ensure a broken tool is reported rather than silently omitted",
 "Add a coverage test so new tools are audited automatically",
 "Document which tools are safe for read-only callers",
],
"G02": [  # need 3
 "Document backward-incompatible changes and their migration",
 "Verify the envelope is stable across the four retrieval modes",
 "Ensure trust metadata is present even for graph-sourced results",
],
"I05": [  # need 3
 "Verify ACL changes take effect without a restart",
 "Test that a revoked ACL immediately stops returning facts",
 "Publish isolation coverage as a trust number",
],
"J02": [  # need 2
 "Verify the firewall still blocks promotion of a poisoned fact",
 "Test injection through the graph path specifically",
],
"J05": [  # need 5
 "Add a test that a scan leaves ledger bytes byte-identical",
 "Verify redaction output is clearly marked as redacted",
 "Ensure benchmark corpora are scanned before every publication",
 "Verify no test writes index rows to the live store",
 "Publish a detection-rate metric separate from a redaction metric",
],
"K01": [  # need 5
 "Add reconstruction tests against a hand-built correction chain",
 "Verify a reconstructed view never includes retracted content",
 "Expose the change feed through the stable API",
 "Measure reconstruction cost and publish it as a benchmark",
 "Ensure reconstruction respects namespace boundaries",
],
"R01": [  # TRIM 2
 "Make the offline contract explicit in the root README",
 "Publish embedding latency and recall as a first-class table",
],
"R01-2": [  # need 4
 "Verify shared facts cannot be mutated by a non-owner namespace",
 "Measure isolation overhead under concurrent load",
 "Document what happens when a shared fact is superseded",
 "Ensure load-test corpora contain no real secrets",
],
"R02": [  # TRIM 2
 "Document the k1/b decision with the measured sweep in the README",
 "Add the tuning harness as a CLI subcommand so it is reproducible",
],
"R02-2": [  # need 2
 "Verify conflict resolution is deterministic across replays",
 "Document how transferred facts are marked as second-hand",
],
"T01": [  # TRIM 3
 "Add a test that known_then never returns a fact learned later",
 "Add temporal filters to the hybrid fusion path",
 "Update the organ README to state what is wired and what is not",
],
"T01-2": [  # need 3
 "Verify the command detects a broken component rather than passing",
 "Ensure the command is safe to run against the live system",
 "Document how to interpret each status in the output",
],
"T02": [  # TRIM 2
 "Add a temporal store backup to the backup routine",
 "Add a restore drill that restores temporal.db and verifies the chain",
],
"T02-2": [  # need 3
 "Publish which figures are currently stale",
 "Ensure a withdrawn figure is visibly marked in the report",
 "Verify re-verification compares against the same corpus version",
],
}