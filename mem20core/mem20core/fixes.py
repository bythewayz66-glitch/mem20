"""Runtime overlays on mem20core.core (issues #17, #80).

Two families used to ship their own copy of ``core.py`` and drifted away from
``mem20core``. Rather than fork the module again, both are now served by this
overlay, which is applied by :func:`patch` from the thin ``core.py`` shims:

* free-text credential redaction, and redaction on the events write path and on
  job results (the two write paths that leaked a credential returned by a job);
* ``probe_gpu`` -- a real hardware probe -- and a ``family_otherstack`` that
  reports ``not_measured`` instead of deriving a speedup from operation count.

Keeping the overlay here (not in ``core.py``) is what lets every ``core.py``
stay a <=10-line shim, which is the rule the Syntax gate enforces.
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess

import mem20core.core as _core
from mem20core.core import *  # noqa: F401,F403  re-export the whole surface

# Captured at import, before patch() rebinds the name, so the rid!=102 fallback
# still reaches the real implementation instead of recursing into itself.
_ORIG_FAMILY_OTHERSTACK = _core.family_otherstack

# Export the entire core surface plus the overlays, so a shim is one star-import:
# the names defined in this module shadow their core counterparts.
__all__ = [n for n in dir(_core) if not n.startswith("_")] + [
    "probe_gpu",
    "redact",
    "family_otherstack",
    "patch",
    "PATCH_MARKER",
    "_SECRET_IN_TEXT",
]

PATCH_MARKER = "mem20core.fixes.patch"

# A credential in free text has no sensitive KEY to match on -- "auth failed for
# token=abc" would survive a dict-only redaction -- so match the usual
# "sensitive-name, separator, value" shape and stop at the first delimiter.
_TEXT_SECRET = re.compile(
    r"(?i)\b(" + "|".join(sorted(_core.SENSITIVE_KEYS)) + r")\b(\s*[:=]\s*)"
    r"((?!\[REDACTED\])[^\s,;\"')\]}]+)"  # never re-redact the sentinel
)
# Name kept so anything that referenced the old copy's private regex still works.
_SECRET_IN_TEXT = _TEXT_SECRET


def redact(obj):
    """Dict/list redaction plus the free-text case core.redact() leaves alone."""
    if isinstance(obj, str):
        return _TEXT_SECRET.sub(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", obj)
    if isinstance(obj, dict):
        return {
            k: ("[REDACTED]" if str(k).lower() in _core.SENSITIVE_KEYS else redact(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj


def probe_gpu():
    """Actually check for a usable GPU. Returns (usable, reasons)."""
    reasons = []
    if not os.path.isdir("/dev/dri"):
        reasons.append("no /dev/dri device nodes")
    exe = shutil.which("nvidia-smi")
    if not exe:
        reasons.append("nvidia-smi not installed")
    else:
        try:
            r = subprocess.run([exe, "-L"], capture_output=True, text=True, timeout=10)
            if r.returncode != 0:
                reasons.append("nvidia-smi exited %d (driver unavailable)" % r.returncode)
        except Exception:
            reasons.append("nvidia-smi could not be executed")
    try:
        import torch as _t

        if not _t.cuda.is_available():
            reasons.append("torch reports cuda unavailable")
    except ImportError:
        pass
    return (not reasons), reasons


def family_otherstack(rid, p):
    """core.family_otherstack with rid 102 answered by the real probe."""
    if rid != 102:
        return _ORIG_FAMILY_OTHERSTACK(rid, p)
    ops = float(p.get("operations", 1e6))
    mem = float(p.get("memory_mb", 256))
    gpu, reasons = probe_gpu()
    if p.get("webgpu_available") is True and not gpu:
        reasons.append("request asserted webgpu_available=true but no usable GPU was detected")
    return {
        "backend": "webgpu" if gpu and mem <= 4096 else "cpu",
        "workgroups": max(1, int(math.sqrt(ops / 256))),
        "gpu_detected": gpu,
        "gpu_probe": reasons,
        "caller_asserted_webgpu": p.get("webgpu_available"),
        "speedup": "not_measured",
        "speedup_note": (
            "no benchmark was run; a CPU/webGPU ratio is not derivable from "
            "operation count alone"
        ),
    }


def patch():
    """Bind the overlays onto mem20core.core/StateStore. Idempotent."""
    core = _core  # mem20core.core itself
    core.redact = redact
    store = core.StateStore

    def emit(self, kind, job_id=None, payload=None):
        # The events table is a second, easily-forgotten write path: fixing only
        # the jobs row left the same credential sitting in the event log.
        with self.conn() as c:
            c.execute(
                "INSERT INTO events(ts,kind,job_id,payload) VALUES(?,?,?,?)",
                (core.now(), kind, job_id, core.canonical(redact(payload or {}))),
            )

    def update_job(self, jid, state, result=None, error=None, attempts=None):
        # Redact the result exactly as create_job redacts its request. A
        # credential returned by a job was previously persisted in the clear.
        safe_result = core.canonical(redact(result)) if result is not None else None
        safe_error = redact(error) if isinstance(error, str) else error
        with self.conn() as c:
            old = c.execute("SELECT attempts FROM jobs WHERE id=?", (jid,)).fetchone()
            att = attempts if attempts is not None else (old["attempts"] if old else 0)
            c.execute(
                "UPDATE jobs SET state=?,result=?,error=?,attempts=?,updated=? WHERE id=?",
                (state, safe_result, safe_error, att, core.now(), jid),
            )
        self.emit("job." + state, jid, result if result is not None else {"error": error})

    store.emit = emit
    store.update_job = update_job
    core.family_otherstack = family_otherstack
    core.FAMILY_FUNCS["OtherStack"] = family_otherstack
    return core
