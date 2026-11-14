"""mem20eventstreamsuperhighwayz — route typed events across runtimes.

The domain layer (``domain``) is the stream itself: publish, subscribe, consume,
throughput, lag. The ``integration`` layer is the seam onto the rest of the
mem20 estate — durable event memory, multi-hop search, the measured capability
inventory, the fleet gateway, integrity verification and payload compaction.

    from mem20eventstreamsuperhighwayz import domain, integration

    stream = domain.create_stream("orders")
    out = integration.publish_and_persist(stream, "order.created", {"id": 7})
"""

from . import domain, integration
from .domain import (
    consume,
    create_stream,
    lag,
    publish,
    subscribe,
    throughput,
)

__all__ = [
    "consume",
    "create_stream",
    "domain",
    "integration",
    "lag",
    "publish",
    "subscribe",
    "throughput",
]
__version__ = "4.0.0"
