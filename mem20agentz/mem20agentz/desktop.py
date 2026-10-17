"""Unified office frontend + web app (sub-phase 2.9).

`Frontend` is the ONE office-style surface over the mem20 backend. It is a
thin client: every panel (chat, status, ledger, cron, projects) is fed by the
same endpoints the wire/desktop clients consume (`/chat`, `/status`,
`/ledger`) plus one composed bundle (`/office`). Chat transports and
transcripts are shared with `gateway_web.WebGateway` under the same `web:`
session prefix, so desktop/webgateway/office/CLI hold no divergent state.

The HTML app renders a dependency-free CSS-3D office room: bridges are desks,
projects are shelves, cron jobs are wall slots, the ledger is the floor. All
state is fetched live from `/office`.
"""

from __future__ import annotations

import html
import http.server
import json
import os
import pathlib
import subprocess
import sys
import threading
import time
import uuid
from typing import Optional

from . import __version__
from .config import load_config

FRONTEND_DIR = pathlib.Path(__file__).parent / "frontend"

# Resolve sibling package roots from env, then fall back to the monorepo
# layout (…/mem20/mem20agentz/mem20agentz/desktop.py → parents[2] is mem20/).
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CREWZ_ROOT = os.environ.get("MEM20_CREWZ_ROOT") or str(_REPO_ROOT / "mem20crewz")
GAMEZ_ROOT = os.environ.get("MEM20_GAMEZ_ROOT") or str(_REPO_ROOT / "mem20gamez")
RUNTIME_ROOT = pathlib.Path(os.path.expanduser(
    os.environ.get("MEM20_RUNTIME", "~/.mem20agentz")))


def _sys_python() -> str:
    return sys.executable


_FALLBACK_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>mem20</title></head>
<body><h1>mem20</h1>
<p>frontend template missing at
<code>mem20agentz/frontend/index.html</code> — reinstall the package.</p>
<div id="office"></div>
<div id="t-office"></div><div id="t-kanban"></div>
<div id="t-production"></div><div id="t-settings"></div><div id="t-chat"></div>
<script>window.MEM20_READY = "mem20 client ready.";/* /office */</script>
</body></html>
"""
