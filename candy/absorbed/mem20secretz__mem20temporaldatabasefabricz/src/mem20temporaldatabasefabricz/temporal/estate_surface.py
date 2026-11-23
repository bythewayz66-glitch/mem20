"""Estate surfaces this subsystem *reports* through, rather than decides by.

Two projects answer questions about the estate's own state rather than about a
belief: ``mem20ircz`` classifies wire lines, ``toolchest`` knows what the estate
exposes. Both are consulted rather than re-derived, because a local copy of
either would drift away from the real thing and the drift would be silent.

================  ==========================================================
mem20 project      symbol used
================  ==========================================================
``mem20ircz``      ``filter.classify``, ``filter.NoiseMeter``
``toolchest``      ``catalog.load_inventory``
================  ==========================================================
"""

from __future__ import annotations

from .estate import REPO_ROOT, UNAVAILABLE, estate_path, need

__all__ = ["wire_noise", "is_noise_line", "tool_inventory"]

estate_path()

try:
    from mem20ircz.filter import NoiseMeter as _NoiseMeter
    from mem20ircz.filter import classify as _classify_wire_line
except ImportError as _exc:  # pragma: no cover
    _NoiseMeter = None
    _classify_wire_line = None
    UNAVAILABLE["mem20ircz.filter"] = f"{type(_exc).__name__}: {_exc}"

try:
    from toolchest.catalog import load_inventory as _load_inventory
except ImportError as _exc:  # pragma: no cover
    _load_inventory = None
    UNAVAILABLE["toolchest.catalog"] = f"{type(_exc).__name__}: {_exc}"


class _WireMessage:
    """The subset of a parsed wire line that ``mem20ircz.filter.classify`` reads.

    Built here rather than importing the transport's own message class: that type
    drags in ``mem20botz``, whose package import pulls the whole bot crew. The
    classifier's *contract* - ``command``/``text``/``is_channel``/``target`` - is
    what this seam depends on, and that is stable.
    """

    __slots__ = ("command", "text", "target", "prefix", "_params", "_is_channel")

    def __init__(self, command: str, text: str, target: str = "#mem20",
                 params: list[str] | None = None, prefix: str = ""):
        self.command = command
        self.text = text
        self.prefix = prefix
        self._params = list(params) if params is not None else [target]
        self.target = self._params[0] if self._params else ""
        self._is_channel = bool(self.target) and self.target[0] in "#&+!"

    @property
    def is_channel(self) -> bool:
        return self._is_channel

    @property
    def params(self) -> list[str]:
        return list(self._params)


def wire_noise() -> dict:
    """Prove the estate's wire classifier is live, and report what it decided.

    Temporal ingestion is often driven by messages that arrive over a chat/wire
    transport. ``mem20ircz.filter`` already decides what is a protocol message, a
    CTCP burst or a numeric reply - a classification tuned against real estate
    traffic. Reimplementing "is this noise?" locally would drift from it and
    silently ingest join/part storms as beliefs.

    The classifier is exercised on both branches, so a caller can see it is the
    live estate classifier and not a local heuristic that always says yes.
    """
    classify = need(_classify_wire_line, "filter.classify", "mem20ircz")
    meter = need(_NoiseMeter, "filter.NoiseMeter", "mem20ircz")
    person = classify(_WireMessage("PRIVMSG", "deploy target is staging"))
    protocol = classify(_WireMessage("001", ""))
    return {
        "classifier": "mem20ircz.filter.classify",
        "person_kept": bool(person.keep),
        "person_reason": person.reason,
        "protocol_kept": bool(protocol.keep),
        "protocol_reason": protocol.reason,
        "meter": type(meter()).__name__,
    }


def is_noise_line(text: str) -> bool:
    """Is this *wire line* one the estate classifier says to drop?

    ``filter.classify`` classifies a **parsed protocol line**, not free text - it
    reads ``command``/``target``/``is_channel``. Handing it a bare sentence and
    calling the answer "noise" would be exactly the decorative wiring criterion 6
    exists to catch: the call would execute, the result would be meaningless, and
    ledger rows would be kept or dropped for the wrong reason.

    So a line is only classified when it is shaped like a wire line: it starts
    with ``:`` (a prefix) or its first token is a known command or a numeric
    reply. Anything else is content, and content is not the classifier's business
    - ``False`` here means "not a wire line", not "worth believing".
    """
    classify = need(_classify_wire_line, "filter.classify", "mem20ircz")
    message = _parse_wire_line(text)
    if message is None:
        return False
    return not bool(classify(message).keep)


def _parse_wire_line(text: str):
    """Parse ``text`` as an IRC line, or return None when it is not one.

    The shape test is deliberately strict. Ordinary English contains words like
    ``notice`` and ``part``, and a permissive parser would classify a sentence as
    a protocol message and silently drop a real memory.
    """
    stripped = text.strip()
    if not stripped:
        return None
    from mem20ircz.filter import (  # noqa: PLC0415 - kept with its guard
        ADMIN_COMMANDS, PROTOCOL_COMMANDS, ROSTER_COMMANDS,
    )

    has_prefix = stripped.startswith(":")
    head = stripped.split(" ", 1)[0]
    if has_prefix:
        # :prefix COMMAND params... - the command is the second token.
        parts = stripped.split(" ", 2)
        if len(parts) < 2:
            return None
        head = parts[1]
    known = head.isdigit() or head.upper() in (
        set(PROTOCOL_COMMANDS) | set(ADMIN_COMMANDS) | set(ROSTER_COMMANDS)
        | {"PRIVMSG", "NOTICE", "JOIN", "PART", "QUIT", "MODE", "NICK", "PING"}
    )
    if not known:
        return None

    # Now that it genuinely is a protocol line, split it the way the transport
    # does: optional prefix, command, then params with the trailing text last.
    body = stripped
    prefix = ""
    if has_prefix:
        prefix, _, body = body[1:].partition(" ")
    if " :" in body:
        head_part, _, trailing = body.partition(" :")
    else:
        head_part, trailing = body, ""
    tokens = head_part.split()
    if not tokens:
        return None
    command = tokens[0]
    params = tokens[1:]
    if trailing:
        params = params + [trailing]
    return _WireMessage(command, trailing, params=params, prefix=prefix)


# -- toolchest: what does the estate actually expose? ----------------------

def tool_inventory(limit: int = 5) -> dict:
    """The estate's tool inventory, read from the catalog's own file.

    ``export`` writes a durable state snapshot, and a snapshot claiming a
    capability the estate does not expose is a false record on the known axis.
    ``toolchest.catalog.load_inventory`` is the estate's reader for that file, so
    it is consulted at export time rather than assumed.
    """
    load = need(_load_inventory, "catalog.load_inventory", "toolchest")
    path = REPO_ROOT / "toolchest" / "inventory.json"
    if not path.is_file():
        return {"source": "toolchest.catalog.load_inventory", "total": 0,
                "sample": [], "error": f"no inventory at {path}"}
    inventory = load(path)
    entries = inventory.get("entries") if isinstance(inventory, dict) else None
    if isinstance(entries, list):
        names = [str(e.get("name", e)) if isinstance(e, dict) else str(e)
                 for e in entries]
    elif isinstance(inventory, dict):
        names = sorted(inventory.keys())
    else:  # pragma: no cover - catalog contract changed
        names = []
    return {
        "source": "toolchest.catalog.load_inventory",
        "total": len(names),
        "sample": names[:limit],
        "counts": inventory.get("counts", {}) if isinstance(inventory, dict) else {},
    }
