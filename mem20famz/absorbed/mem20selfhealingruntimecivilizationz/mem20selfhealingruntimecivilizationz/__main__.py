"""Command-line entry point.

Two command families live behind one dispatcher, so nothing from 3.x was dropped
when the 4.0 controller was added:

controller (4.0)
    ``demo`` · ``probe`` · ``catalogue`` · ``run`` · ``report`` · ``serve``
runtime (3.x, still supported)
    ``execute`` · ``simulate`` · ``benchmark`` · ``metrics`` · ``snapshot``

The controller commands are dispatched to
:func:`mem20selfhealingruntimecivilizationz.controller.main`; the runtime commands
keep their original behaviour from :func:`mem20selfhealingruntimecivilizationz
.runtime.main` (the HTTP console/API and the legacy engine).
"""
from __future__ import annotations

import sys

CONTROLLER_COMMANDS = {"demo", "probe", "catalogue", "run", "report"}
RUNTIME_COMMANDS = {"execute", "simulate", "benchmark", "metrics", "snapshot"}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    first = next((a for a in argv if not a.startswith("-")), None)

    # ``serve`` exists in both families: the controller's version adds /health
    # /ready /metrics through mcp/health.py, so it is the one dispatched to.
    if first == "serve":
        from .controller import main as controller_main

        return controller_main(argv)

    if first in RUNTIME_COMMANDS:
        from .runtime import main as runtime_main

        return runtime_main(argv)

    from .controller import main as controller_main

    return controller_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
