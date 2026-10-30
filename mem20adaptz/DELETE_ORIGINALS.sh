#!/usr/bin/env bash
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
echo "Done. Commit: git commit -m 'chore(adaptz): remove absorbed mem20adaptive* organ roots'"
