# Absorbed adaptive packages

This file is the audit trail for the organ merge into `mem20adapz`.

| Former root directory | Short id | Notes |
|----------------------|----------|-------|
| mem20adaptiveachievementenginez | achievement | |
| mem20adaptivedispatchenginez | dispatch | |
| mem20adaptiveforgettingenginez | forgetting | |
| mem20adaptiveinferencemarketplacez | inference | |
| mem20adaptiveinterfacecomposerz | interface | |
| mem20adaptivepersonalityruntimez | personality | |
| mem20adaptivepricingbrainz | pricing | |

**Rule:** functionality is consolidated, not deleted. Implementations that still
need a long import path should be vendored under `members/` before root dirs
are removed.
