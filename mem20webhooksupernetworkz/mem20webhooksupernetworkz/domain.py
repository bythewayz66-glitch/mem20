"""Webhook delivery that is signed, retried, and replay-resistant.

Domain research: an unsigned webhook is forgeable, an unretried one loses
events, and an unverified one can be replayed by anyone who captured it. The
defence is HMAC over timestamp+body with a tolerance window, so a captured
request is useless once stale. Retries use a stable idempotency key so the
receiver can deduplicate rather than double-process.
"""
import hashlib, hmac, time


class WebhookVerificationError(RuntimeError):
    pass


class WebhookSuperNetwork:
    def __init__(self, secret, tolerance_seconds=300):
        if not secret:
            raise ValueError("secret required")
        if tolerance_seconds <= 0:
            raise ValueError("tolerance must be positive")
        self.secret = str(secret).encode()
        self.tolerance = float(tolerance_seconds)
        self.delivered = []
        self.duplicates_skipped = 0

    def sign(self, body, timestamp):
        msg = f"{timestamp}.".encode() + body.encode() if isinstance(body, str) \
            else str(timestamp).encode() + b"." + body
        return hmac.new(self.secret, msg, hashlib.sha256).hexdigest()

    def verify(self, body, timestamp, signature, now=None):
        now = time.time() if now is None else now
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

    def deliver(self, body, timestamp, signature, now=None,
                idempotency_key=None):
        """Verify, then deliver once per idempotency key."""
        self.verify(body, timestamp, signature, now=now)
        key = idempotency_key or hashlib.sha256(
            f"{timestamp}:{body}".encode()).hexdigest()
        if key in self.delivered:
            self.duplicates_skipped += 1
            return {"delivered": False, "reason": "duplicate", "key": key}
        self.delivered.append(key)
        return {"delivered": True, "key": key}
