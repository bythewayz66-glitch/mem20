"""Dual-read / dual-write cutover that can be abandoned safely.

Domain research: migrating a live store means old and new must both be correct
during the overlap. The failure that bites is abandoning a migration halfway and
finding the two stores disagree. The fix is verification: before cutover the two
must be checked for agreement, and after cutover the old store must stop being
written. An unverified cutover is refused rather than assumed.
"""
class MigrationNotVerified(RuntimeError):
    pass


class ZeroDowntimeMigrationBrain:
    def __init__(self, verify=None):
        self.verify = verify
        self.phase = "idle"
        self.writes = {"old": 0, "new": 0}
        self.cutover_at = None
        self.rolled_back = False

    def write(self, record):
        if self.phase == "cutover":
            self.writes["new"] += 1
        elif self.phase in ("migrating", "rollback"):
            self.writes["old"] += 1
            self.writes["new"] += 1     # dual write
        else:
            self.writes["old"] += 1
        return record

    def read(self, key):
        if self.phase == "cutover":
            return ("new", key)
        if self.phase in ("migrating", "rollback"):
            return ("verify", key)     # must be reconciled, not guessed
        return ("old", key)

    def begin(self):
        self.phase = "migrating"
        return self.phase

    def verify_and_cutover(self):
        """Refuse to cut over unless the two stores actually agree."""
        if self.phase != "migrating":
            raise MigrationNotVerified(f"cannot cut over from phase {self.phase!r}")
        if self.verify is None:
            raise MigrationNotVerified("no verifier supplied; refusing unverified cutover")
        report = self.verify()
        if not report.get("match"):
            raise MigrationNotVerified(
                f"stores disagree: {report.get('old_only')} old-only, "
                f"{report.get('new_only')} new-only")
        self.phase = "cutover"
        return {"phase": self.phase, "verified": True, "detail": report}

    def rollback(self):
        if self.phase == "idle":
            raise MigrationNotVerified("nothing to roll back from idle")
        self.phase = "rollback"
        self.rolled_back = True
        return self.phase
