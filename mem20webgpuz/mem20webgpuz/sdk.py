"""mem20webgpuz typed Python client.

A thin, dependency-free client over the HTTP API. It exists so a caller in
another process (or another language binding's reference implementation) does
not have to hand-roll ``http.client`` calls, and so the error taxonomy survives
the wire: a 4xx/5xx response is re-raised as the matching :class:`WebGPUError`
subclass with its ``details`` intact.
"""

from __future__ import annotations

import http.client
import json
import urllib.parse
from typing import Any, Mapping

from mem20core.mem20core.core import canonical

from .errors import (
    BackendUnavailableError,
    JobCancelledError,
    JobNotFoundError,
    QuotaExceededError,
    ValidationError,
    WebGPUError,
)

__all__ = ["Client", "ClientError"]

# Wire error name -> local exception class.
_ERRORS: dict[str, type[WebGPUError]] = {
    "ValidationError": ValidationError,
    "BackendUnavailableError": BackendUnavailableError,
    "QuotaExceededError": QuotaExceededError,
    "JobCancelledError": JobCancelledError,
    "JobNotFoundError": JobNotFoundError,
}


class ClientError(WebGPUError):
    """A transport-level failure (connection refused, bad response)."""


class Client:
    """Typed client for one mem20webgpuz API endpoint."""

    def __init__(self, base_url: str = "http://127.0.0.1:8767", *, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # -- transport ---------------------------------------------------------
    def _request(self, method: str, path: str, payload: Any = None) -> Any:
        parsed = urllib.parse.urlparse(self.base_url)
        if not parsed.hostname:
            raise ClientError("base_url has no host", details={"base_url": self.base_url})
        conn = http.client.HTTPConnection(
            parsed.hostname, parsed.port or 80, timeout=self.timeout
        )
        prefix = parsed.path.rstrip("/")
        body = canonical(payload).encode() if payload is not None else None
        headers = {"Content-Type": "application/json"} if body else {}
        try:
            conn.request(method, prefix + path, body, headers)
            response = conn.getresponse()
            raw = response.read()
            status = response.status
        except OSError as exc:
            raise ClientError(
                f"transport failure: {type(exc).__name__}", details={"path": path}
            ) from exc
        finally:
            conn.close()

        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise ClientError(
                "response was not JSON", details={"status": status, "path": path}
            ) from exc

        if status >= 400:
            name = str(data.get("error", ""))
            cls = _ERRORS.get(name, WebGPUError)
            raise cls(
                str(data.get("message", f"HTTP {status}")),
                details=dict(data.get("details") or {}),
            )
        return data

    # -- surface -----------------------------------------------------------
    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def ready(self) -> dict[str, Any]:
        return self._request("GET", "/ready")

    def inspect(self) -> dict[str, Any]:
        return self._request("GET", "/v1/inspect")

    def capabilities(self) -> dict[str, Any]:
        return self._request("GET", "/v1/capabilities")

    def run(self, request: Mapping[str, Any], idempotency_key: str | None = None) -> dict[str, Any]:
        return self._request(
            "POST", "/v1/run", {"request": dict(request), "idempotency_key": idempotency_key}
        )

    def jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._request("GET", f"/v1/jobs?limit={int(limit)}")

    def job(self, job_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/jobs/{job_id}")

    def cancel(self, job_id: str) -> dict[str, Any]:
        return self._request("POST", f"/v1/jobs/{job_id}/cancel", {})

    def events(self, after: int = 0) -> list[dict[str, Any]]:
        return self._request("GET", f"/v1/events?after={int(after)}")

    def create_resource(self, body: Any, resource_id: str | None = None) -> dict[str, Any]:
        return self._request("POST", "/v1/resources", {"body": body, "id": resource_id})

    def resources(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._request("GET", f"/v1/resources?limit={int(limit)}")

    def resource(self, resource_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/resources/{resource_id}")

    def update_resource(
        self, resource_id: str, body: Any, expected_version: int | None = None
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/resources/{resource_id}",
            {"body": body, "expected_version": expected_version},
        )

    def delete_resource(self, resource_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/v1/resources/{resource_id}")

    def feedback(self, signal: str, value: float, note: str = "") -> dict[str, Any]:
        return self._request(
            "POST", "/v1/feedback", {"signal": signal, "value": value, "note": note}
        )
