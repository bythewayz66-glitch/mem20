#!/usr/bin/env bash
# Run from the mem20 repo root AFTER mem20adapz 1.0.0 has been merged.
# Removes the former adaptive organ trees that are now absorbed.
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

echo "Removing absorbed adaptive organ roots..."
for d in "${ROOTS[@]}"; do
  if [ -d "$d" ]; then
    echo "  git rm -r $d"
    git rm -r "$d"
  else
    echo "  (already gone) $d"
  fi
done

echo ""
echo "Done. Commit with:"
echo "  git commit -m 'chore(adapz): remove absorbed mem20adaptive* organ roots — live in mem20adapz 1.0.0'"
