#!/usr/bin/env bash
# Run from repo root on branch chore/merge-adapz-autoz after reviewing the merge.
# Removes former adaptive organ trees (absorbed into mem20adapz).
set -euo pipefail
ROOTS=(
  mem20adaptiveachievementenginez
  mem20adaptivedispatchenginez
  mem20adaptiveforgettingenginez
  mem20adaptiveinferencemarketplacez
  mem20adaptiveinterfacecomposerz
  mem20adaptivepersonalityruntimez
  mem20adaptivepricingbrainz
)
for d in "${ROOTS[@]}"; do
  if [ -d "$d" ]; then
    echo "git rm -r $d"
    git rm -r "$d"
  fi
done
echo "Done adaptive. Commit with: git commit -m 'chore: remove absorbed adaptive organ roots'"
