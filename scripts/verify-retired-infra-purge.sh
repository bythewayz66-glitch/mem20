#!/usr/bin/env bash
# Gate for G8: no retired infra identity may survive on the branch outside the
# documented allowlist. See docs/ops/retired-infra-allowlist-2026-11-01.md.
#
# Usage:  bash scripts/verify-retired-infra-purge.sh [ref]
#         ref defaults to HEAD.
#
# Exit 0 = gate passed. Exit 1 = a non-allowlisted reference survived.
set -uo pipefail

REF="${1:-HEAD}"
PATTERN='sidney|gabe'

# The allowlist. Path prefixes end in "/"; everything else is an exact path.
# Each entry is justified in the allowlist document; keep the two in sync.
ALLOW=(
  "published/"                                                   # A1  immutable archive
  ".sitemap/sitemap.json"                                        # A2  generated snapshot
  "docs/ops/branch-inventory-2026-10-31.md"                      # A3  dated audit record
  "docs/ops/branch-disposition-2026-10-31.md"                    # A4  dated audit record
  "docs/ops/owner-directive-2026-11-01.md"                       # A5  the directive itself
  "docs/ops/tag-audit-2026-10-31.md"                             # A6  dated audit record
  "docs/ops/roster-verification-2026-10-27.md"                   # A7  dated audit record
  "docs/gtm/claim-ledger.md"                                     # A8  verbatim commit subject
  "docs/market/market-claims-consistency-2026-10-31.md"          # A9  real on-disk path
  "docs/pricing/RECONCILIATION_NOTE.md"                          # A10 real on-disk path
  "scripts/sweep-tool-counts.py"                                 # A11 real on-disk path
  "docs/ops/retired-infra-allowlist-2026-11-01.md"               # A12 this document
  "scripts/verify-retired-infra-purge.sh"                        # A13 this script
)

is_allowed() {
  local path="$1" entry
  for entry in "${ALLOW[@]}"; do
    case "$entry" in
      */) [[ "$path" == "$entry"* ]] && return 0 ;;
      *)  [[ "$path" == "$entry" ]] && return 0 ;;
    esac
  done
  return 1
}

echo "== ref: $REF"
echo "== pattern: $PATTERN (case-insensitive)"
echo

total_files=0
total_hits=0
violations=0
violation_files=0

# git grep -c prints "path:count" for every file with at least one hit.
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  path="${line%:*}"
  count="${line##*:}"
  # `git grep <ref>` prefixes each path with "<ref>:"; strip it so the allowlist
  # matches on the repo-relative path.
  path="${path#"$REF":}"
  total_files=$((total_files + 1))
  total_hits=$((total_hits + count))
  if is_allowed "$path"; then
    printf '  ALLOW  %-4s %s\n' "$count" "$path"
  else
    printf '  FAIL   %-4s %s\n' "$count" "$path"
    violations=$((violations + count))
    violation_files=$((violation_files + 1))
  fi
done < <(git grep -ciE "$PATTERN" "$REF" -- . 2>/dev/null)

echo
echo "== files with a hit: $total_files   hits: $total_hits"
echo "== non-allowlisted files: $violation_files   non-allowlisted hits: $violations"

if [[ "$violations" -ne 0 ]]; then
  echo
  echo "GATE FAILED: $violations reference(s) outside the allowlist."
  echo "Either purge them, or add a justified entry to"
  echo "docs/ops/retired-infra-allowlist-2026-11-01.md and to ALLOW above."
  exit 1
fi

echo
echo "GATE PASSED: every remaining reference is allowlisted."

# The FLEET_SITES change touches tested code, so the gate re-runs that suite.
if [[ -d mem20controlz ]]; then
  echo
  echo "== mem20controlz suite"
  ( cd mem20controlz && python3 -m pytest tests/test_websites.py -q ) || {
    echo "GATE FAILED: mem20controlz tests did not pass."
    exit 1
  }
fi

exit 0
