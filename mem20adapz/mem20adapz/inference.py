"""Double-auction price-time matching for inference capacity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class Order:
    price: float
    ts: float
    side: str = field(compare=False)
    qty: int = field(compare=False, default=0)
    oid: str = field(compare=False, default="")
    agent: str = field(compare=False, default="")
    model: str = field(compare=False, default="")


def _book(orders: list[Order]):
    bids = sorted([o for o in orders if o.side == "buy"], key=lambda o: (-o.price, o.ts))
    asks = sorted([o for o in orders if o.side == "sell"], key=lambda o: (o.price, o.ts))
    return bids, asks


def match(orders: list[Order], max_matches: int = 1000) -> dict[str, Any]:
    working = [Order(price=o.price, ts=o.ts, side=o.side, qty=o.qty, oid=o.oid, agent=o.agent, model=o.model) for o in orders]
    bids, asks = _book(working)
    fills = []
    bi = ai = 0
    while bi < len(bids) and ai < len(asks) and len(fills) < max_matches:
        b, a = bids[bi], asks[ai]
        if b.price < a.price:
            break
        qty = min(b.qty, a.qty)
        fills.append({"buy_oid": b.oid, "sell_oid": a.oid, "qty": qty, "price": a.price, "buy_agent": b.agent, "sell_agent": a.agent, "model": a.model or b.model})
        b.qty -= qty
        a.qty -= qty
        if b.qty <= 0:
            bi += 1
        if a.qty <= 0:
            ai += 1
    return {"fills": fills, "fill_count": len(fills), "clearing_price": fills[-1]["price"] if fills else None, "resting_bids": sum(max(0, o.qty) for o in bids[bi:]), "resting_asks": sum(max(0, o.qty) for o in asks[ai:]), "matched_volume": sum(f["qty"] for f in fills)}


@dataclass
class InferenceMarketplace:
    orders: list[Order] = field(default_factory=list)
    _seq: int = 0

    def _next_oid(self) -> str:
        self._seq += 1
        return f"ord-{self._seq:06d}"

    def bid(self, price: float, qty: int, *, agent: str = "", model: str = "", ts: float | None = None) -> Order:
        import time
        o = Order(price=price, ts=time.time() if ts is None else ts, side="buy", qty=qty, oid=self._next_oid(), agent=agent, model=model)
        self.orders.append(o)
        return o

    def ask(self, price: float, qty: int, *, agent: str = "", model: str = "", ts: float | None = None) -> Order:
        import time
        o = Order(price=price, ts=time.time() if ts is None else ts, side="sell", qty=qty, oid=self._next_oid(), agent=agent, model=model)
        self.orders.append(o)
        return o

    def clear(self) -> dict[str, Any]:
        result = match(self.orders)
        qty_left = {}
        for f in result["fills"]:
            qty_left[f["buy_oid"]] = qty_left.get(f["buy_oid"], 0) + f["qty"]
            qty_left[f["sell_oid"]] = qty_left.get(f["sell_oid"], 0) + f["qty"]
        remaining = []
        for o in self.orders:
            residual = o.qty - qty_left.get(o.oid, 0)
            if residual > 0:
                remaining.append(Order(price=o.price, ts=o.ts, side=o.side, qty=residual, oid=o.oid, agent=o.agent, model=o.model))
        self.orders = remaining
        return result
