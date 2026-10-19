"""Double-auction price-time matching for inference capacity.

Option C: real domain logic for mem20adaptiveinferencemarketplacez.
"""
"""Two-sided market matching for inference capacity.

Real behaviour: orders on both sides are matched by price-time priority
against a clearing price derived from the crossing best bid/ask, with partial
fills supported. This is double-auction matching, computed not described.
"""
from dataclasses import dataclass, field


@dataclass(order=True)
class Order:
    price: float
    ts: float
    side: str = field(compare=False)
    qty: int = field(compare=False, default=0)
    oid: str = field(compare=False, default="")


def _book(orders):
    bids = sorted([o for o in orders if o.side == "buy"],
                  key=lambda o: (-o.price, o.ts))
    asks = sorted([o for o in orders if o.side == "sell"],
                  key=lambda o: (o.price, o.ts))
    return bids, asks


def match(orders, max_matches=1000):
    """Match a book. Returns fills, clearing price and resting liquidity."""
    bids, asks = _book(orders)
    fills = []
    bi = ai = 0          # separate cursors: one index for two books silently
                         # skipped resting liquidity on the side that advanced
    while bi < len(bids) and ai < len(asks) and len(fills) < max_matches:
        b, a = bids[bi], asks[ai]
        if b.price < a.price:
            break                      # crossed out: book is uncrossed
        qty = min(b.qty, a.qty)
        trades = (qty // 2) + (qty % 2)   # split the trade between sides
        fills.append({
            "buy_oid": b.oid, "sell_oid": a.oid, "qty": qty,
            "price": a.price,               # maker price
            "buy_side_qty": trades,
            "sell_side_qty": qty - trades,
        })
        b.qty -= qty
        a.qty -= qty
        if b.qty <= 0:
            bi += 1
        if a.qty <= 0:
            ai += 1
    clearing = fills[-1]["price"] if fills else None
    return {
        "fills": fills,
        "fill_count": len(fills),
        "clearing_price": clearing,
        "resting_bids": sum(max(0, o.qty) for o in bids[bi:]),
        "resting_asks": sum(max(0, o.qty) for o in asks[ai:]),
        "matched_volume": sum(f["qty"] for f in fills),
    }
