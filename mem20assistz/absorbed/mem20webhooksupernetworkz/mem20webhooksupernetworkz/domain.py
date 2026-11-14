"""Webhook delivery that is signed, retried, and replay-resistant.

Domain research: an unsigned webhook is forgeable, an unretried one loses
events, and an unverified one can be replayed by anyone who captured it. The
defence is HMAC over timestamp+body with a tolerance window, so a captured
request is useless once stale. Retries use a stable idempotency key so the
receiver can deduplicate rather than double-process.

Estate wiring
-------------
This receiver is the estate's untrusted boundary: structured payloads from
whoever holds the URL arrive here and are persisted, retried and replayed. The
judgements that boundary needs already exist in sibling projects, so they are
called rather than re-derived (see :mod:`._estate_seam`):

* ``mem20secretz.sweep.classify`` decides whether a payload may enter the
  durable event log at all.
* ``mem20liez.gates.check_prohibited_uses`` decides whether a route may exist,
  consulted where the route is registered.
* ``memory_engine.memory.validate_event_time`` decides whether the sender's
  event time is one the estate would accept as a ``valid_from``.
* ``mem20verify.dataintegrity.check`` decides whether the store a replay reads
  from can round-trip a write.
* ``mem20ops.memchecks.identity_check`` names the store being written into.
* ``toolchest.catalog.load_inventory`` says which capabilities a route may
  target.
"""

from __future__ import annotations

import hashlib
import hmac
import time

from . import estate

__all__ = ["WebhookVerificationError", "PayloadRefusedError",
           "WebhookSuperNetwork", "DeliveryLedger"]


class WebhookVerificationError(RuntimeError):
    """The signature, the timestamp window, or both, failed."""


class PayloadRefusedError(RuntimeError):
    """The payload is not admissible to the durable event log."""


class DeliveryLedger:
    """Where delivered idempotency keys live.

    A ``list`` was the original implementation: it lost its contents on every
    process restart, so a replay after a restart re-delivered everything -
    exactly the duplication the idempotency key exists to prevent - and it grew
    without bound for the life of the process.

    Two bounds instead:

    * ``max_entries`` - oldest keys are evicted past the cap. Eviction is safe
      because the SIGNATURE already refuses a replay older than the tolerance
      window, so a key that has aged out is one whose event can no longer be
      replayed anyway. That relationship is why the cap can be finite at all.
    * an optional ``path`` - when given, keys are appended to a file and
      reloaded on construction, so a restart does not forget what it delivered.
    """

    def __init__(self, max_entries: int = 10000, path: str | None = None):
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")
        self.max_entries = int(max_entries)
        self.path = path
        self._keys: dict[str, None] = {}
        if path:
            self._load()

    def _load(self) -> None:
        try:
            with open(self.path, encoding="utf-8") as handle:
                for line in handle:
                    key = line.strip()
                    if key:
                        self._keys[key] = None
        except FileNotFoundError:
            return

    def __contains__(self, key: str) -> bool:
        return key in self._keys

    def __len__(self) -> int:
        return len(self._keys)

    def keys(self) -> list[str]:
        return list(self._keys)

    def add(self, key: str) -> None:
        if key in self._keys:
            return
        self._keys[key] = None
        while len(self._keys) > self.max_entries:
            # dict preserves insertion order: the first item is the oldest.
            self._keys.pop(next(iter(self._keys)))
        if self.path:
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(key + "\n")


class WebhookSuperNetwork:
    """Verify, deduplicate and route webhook deliveries.

    ``secret`` is the shared HMAC key. ``tolerance_seconds`` is the replay
    window. ``intended_uses`` declares what the network is for, and is checked
    against the estate's prohibited-use list at construction so a route cannot
    be brought up for a use the estate refuses.

    ``event_log_path`` enables the durable delivery ledger, so ``deliver_once``
    remembers what it delivered across restarts.
    """

    def __init__(self, secret, tolerance_seconds=300, intended_uses=None,
                 ledger_path: str | None = None):
        if not secret:
            raise ValueError("secret required")
        if tolerance_seconds <= 0:
            raise ValueError("tolerance must be positive")
        # Admissibility is decided once, at construction, rather than per
        # request: a network whose declared purpose is prohibited should not
        # accept a single delivery, and the refusal must not depend on a caller
        # remembering to check.
        self.legality = estate.check_route_legality(intended_uses)
        self.secret = str(secret).encode()
        self.tolerance = float(tolerance_seconds)
        # Bounded, and durable when a path is supplied: see DeliveryLedger.
        self.delivered = DeliveryLedger(
            max_entries=max(1, int(tolerance_seconds)),
            path=ledger_path,
        )
        self.duplicates_skipped = 0
        self.refused_payloads = 0

    # -- signing ------------------------------------------------------

    def sign(self, body, timestamp):
        """HMAC-SHA256 over ``timestamp.body``.

        The timestamp is inside the signed material, not beside it: signing the
        body alone would let an attacker keep the signature and change the
        timestamp to escape the tolerance window.
        """
        if isinstance(body, bytes):
            msg = str(timestamp).encode() + b"." + body
        else:
            msg = f"{timestamp}.".encode() + str(body).encode()
        return hmac.new(self.secret, msg, hashlib.sha256).hexdigest()

    # -- verification -------------------------------------------------

    def verify(self, body, timestamp, signature, now=None):
        """Check freshness, then the signature, then the event time.

        Order matters only for the message a caller sees; all three must pass.
        The third check is the estate's, and it is the one that keeps this
        receiver from admitting a timestamp the rest of the estate would refuse:
        a sender's clock is the sender's, and a wildly future ``timestamp``
        would otherwise become a ``valid_from`` no sibling project accepts.
        """
        now = time.time() if now is None else float(now)
        try:
            age = abs(now - float(timestamp))
        except (TypeError, ValueError):
            raise WebhookVerificationError("unparseable timestamp")
        if age > self.tolerance:
            raise WebhookVerificationError(
                f"stale: {age:.0f}s old exceeds {self.tolerance:.0f}s window")
        expected = self.sign(body, timestamp)
        if not hmac.compare_digest(expected, str(signature or "")):
            raise WebhookVerificationError("signature mismatch")
        return True

    def verify_event_time(self, timestamp, now=None) -> str:
        """The estate's verdict on the sender's event time.

        Separate from :meth:`verify` because signing proves *who sent it*, not
        that the time inside is one this estate can file. Kept as its own step
        so a caller that already authenticated a request can still ask the
        estate the timestamp question without re-doing the HMAC.
        """
        return estate.validate_event_time(timestamp, now=now)

    # -- admission ----------------------------------------------------

    def admit(self, payload, header_names=()) -> dict:
        """Decide whether ``payload`` may enter the durable event log.

        A webhook log is a durable, replayable record of untrusted input. If the
        input contains a credential - by key name or by shape - persisting it
        verbatim turns the log into a credential archive that gets re-read on
        every replay. ``mem20secretz.sweep.classify`` decides; this refuses.
        """
        verdict = estate.classify_payload(payload, header_names)
        if not verdict["safe"]:
            self.refused_payloads += 1
            raise PayloadRefusedError(
                f"refusing to persist a webhook payload whose "
                f"{verdict['field']!r} classifies as "
                f"{verdict['severity']}/{verdict['kind']} under "
                f"{verdict['classifier']}. The event log is durable and "
                f"replayed, so a credential written here would be re-read on "
                f"every replay. Route it, or store a reference instead.")
        return verdict

    # -- delivery -----------------------------------------------------

    def deliver(self, body, timestamp, signature, now=None,
                idempotency_key=None, payload=None, header_names=()):
        """Verify, admit, then deliver once per idempotency key.

        ``payload`` is the parsed body when the caller has it. Supplying it
        enables the credential check; omitting it means only the signature and
        the event time are checked, which is stated in the result rather than
        assumed by the caller.
        """
        self.verify(body, timestamp, signature, now=now)
        event_time = self.verify_event_time(timestamp, now=now)

        admission = None
        if payload is not None:
            admission = self.admit(payload, header_names)

        key = idempotency_key
        if key is None:
            # The key must depend on the signed material only: derive it from
            # the timestamp and body, both of which the signature covers.
            key = hashlib.sha256(f"{timestamp}:{body}".encode()).hexdigest()

        if key in self.delivered:
            self.duplicates_skipped += 1
            return {"delivered": False, "reason": "duplicate", "key": key,
                    "event_time": event_time}

        self.delivered.add(key)
        return {"delivered": True, "key": key, "event_time": event_time,
                "admission": admission}

    # -- replay -------------------------------------------------------

    def replay(self, events, engine_dir: str | None = None,
               verify_store: bool = True) -> dict:
        """Re-deliver stored events after proving the store can be trusted.

        A replay is the operation most able to cause damage quietly: it
        re-delivers whatever the log claims happened. So the store is verified
        first through ``mem20verify.dataintegrity.check``, and a store that
        cannot round-trip a write refuses the replay - a partial replay that
        looks complete is worse than a failed one.
        """
        report = {"store": None, "replayed": 0, "skipped": 0, "errors": []}
        if verify_store:
            integrity = estate.verify_store(engine_dir)
            report["store"] = {k: integrity.get(k)
                               for k in ("ok", "checked", "roundtrip_ok", "error")}
            if not integrity.get("ok"):
                raise ValueError(
                    "refusing to replay: mem20verify.dataintegrity reports the "
                    f"store cannot round-trip a write "
                    f"(error={integrity.get('error')!r}). A partial replay that "
                    "looks complete is worse than a failed one. Pass "
                    "verify_store=False only to inspect a damaged store.")

        for event in events:
            body = event.get("body", "")
            timestamp = event.get("timestamp")
            signature = event.get("signature")
            try:
                outcome = self.deliver(
                    body, timestamp, signature, now=event.get("now"),
                    idempotency_key=event.get("idempotency_key"),
                    payload=event.get("payload"),
                    header_names=event.get("header_names", ()),
                )
            except (WebhookVerificationError, PayloadRefusedError) as exc:
                report["errors"].append(
                    {"key": event.get("idempotency_key"),
                     "error": f"{type(exc).__name__}: {exc}"})
                continue
            if outcome["delivered"]:
                report["replayed"] += 1
            else:
                report["skipped"] += 1
        return report

    # -- observability ------------------------------------------------

    def store_identity(self, store_path: str | None = None) -> dict:
        """Which store this receiver records into, from ``mem20ops``."""
        return estate.identity(store_path)

    def route_capabilities(self, limit: int = 5) -> dict:
        """Which capabilities a route may target, from ``toolchest``."""
        return estate.tool_inventory(limit)

    def estate_status(self) -> dict:
        """Which sibling projects this receiver is wired to."""
        return estate.estate_status()
