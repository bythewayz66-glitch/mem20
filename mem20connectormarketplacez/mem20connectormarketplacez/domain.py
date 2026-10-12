"""Least-connections load balancing with health withdrawal.

Domain research: least-connections rather than round-robin, because it
self-corrects when a backend is slow. A slow backend accumulates in-flight
requests and stops receiving new ones. Health is explicit: a backend that
reports unhealthy must receive zero traffic, and saying so is a testable
property rather than a comment.
"""
import threading, time


class ConnectorMarketplace:
    def __init__(self, backends=None):
        self._lock = threading.Lock()
        self._conns = {b: 0 for b in (backends or [])}
        self._healthy = {b: True for b in self._conns}
        self._sticky = {}

    def add(self, backend):
        with self._lock:
            self._conns.setdefault(backend, 0)
            self._healthy.setdefault(backend, True)

    def set_healthy(self, backend, healthy):
        with self._lock:
            self._healthy[backend] = bool(healthy)
            if not healthy:
                self._sticky.pop(backend, None)

    def pick(self, key=None):
        """Choose a backend. Returns None when nothing is healthy."""
        with self._lock:
            healthy = [b for b in self._conns if self._healthy.get(b, True)]
            if not healthy:
                return None
            if key is not None:
                prev = self._sticky.get(key)
                if prev is not None and self._healthy.get(prev, True):
                    b = prev
                else:
                    b = min(healthy, key=lambda x: (self._conns[x], x))
                    self._sticky[key] = b
            else:
                b = min(healthy, key=lambda x: (self._conns[x], x))
            self._conns[b] += 1
            return b

    def release(self, backend):
        with self._lock:
            if backend in self._conns and self._conns[backend] > 0:
                self._conns[backend] -= 1

    @property
    def in_flight(self):
        return dict(self._conns)
