"""mem20webgpuz domain engine — WebGPU backend selection and dispatch planning.

This is the real domain logic for RM-102 (WebGPU Compute Studio). It answers
one question honestly: *given a workload and the hardware that is actually
present, which backend should run it, and how should the work be laid out?*

The honesty rule is the point of the subsystem. A GPU speedup is a measured
quantity, not a derivable one, so this engine never reports a speedup it did
not measure. When no benchmark has been run it returns the string
``"not_measured"`` and says why. The earlier implementation derived a speedup
from operation count alone, which is a fabricated number wearing the costume of
a measurement; that behaviour is deliberately not reproduced here.

Cross-subsystem wiring (criterion 6 of the conformance gate) is real, not
decorative: every imported symbol below is called on a line the test suite
executes. See ``docs/ADR-001-cross-module-wiring.md``.
"""

from __future__ import annotations

import math
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

# --- cross-subsystem imports -------------------------------------------------
# Each of these is called on a covered line; see the call sites marked
# `# cross-module:` below. They are imported at module scope so a missing
# sibling fails loudly at import rather than silently degrading a result.
from mem20core.mem20core.core import canonical, clamp, stable_hash
from memory_engine.errors import RetryPolicy
from mem20kilnz.mem20kilnz.budgets import check_triangles

# Two siblings use a src-layout, so their importable root is `<pkg>/src`. The
# bootstrap puts those roots on sys.path; try the canonical name first and fall
# back to the explicit path form for a checkout where only the estate root is
# importable.
try:
    from mem20secretz.sweep import classify as classify_secret
except ImportError:  # pragma: no cover - layout dependent
    from mem20secretz.src.mem20secretz.sweep import classify as classify_secret

try:
    from toolchest.catalog import discover_subsystems
except ImportError:  # pragma: no cover - layout dependent
    from toolchest.src.toolchest.catalog import discover_subsystems

from .errors import ValidationError

__all__ = [
    "Backend",
    "HardwareProbe",
    "DispatchPlan",
    "probe_hardware",
    "select_backend",
    "plan_dispatch",
    "estimate_workgroups",
    "screen_request",
    "asset_budget",
    "estate_inventory",
    "run_domain",
    "load_roadmap",
    "validate_roadmap",
    "DOMAIN_VERSION",
]

DOMAIN_VERSION = "1.0.0"

# Workgroup size is fixed by the WebGPU spec's default compute pipeline; a
# dispatch that ignores it over- or under-subscribes the device.
WORKGROUP_SIZE = 256

# A device is only usable for a large dispatch when it has at least this much
# memory headroom. Below it the engine falls back to CPU rather than failing.
MIN_GPU_MEMORY_MB = 64


@dataclass(frozen=True)
class Backend:
    """A selectable execution backend and the reason it was chosen."""

    name: str
    available: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "available": self.available, "reason": self.reason}


@dataclass(frozen=True)
class HardwareProbe:
    """The result of actually looking for a usable GPU.

    ``usable`` is a verdict, ``reasons`` explains it, and ``evidence`` records
    what was inspected so a reader can tell a real probe from a guess.
    """

    usable: bool
    reasons: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "usable": self.usable,
            "reasons": list(self.reasons),
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class DispatchPlan:
    """A concrete, executable dispatch layout for one workload."""

    backend: str
    workgroups: int
    workgroup_size: int
    total_invocations: int
    memory_mb: float
    speedup: str
    speedup_note: str
    confidence: float
    alternatives: list[dict[str, Any]]
    bottlenecks: list[str]
    explanation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "workgroups": self.workgroups,
            "workgroup_size": self.workgroup_size,
            "total_invocations": self.total_invocations,
            "memory_mb": self.memory_mb,
            "speedup": self.speedup,
            "speedup_note": self.speedup_note,
            "confidence": self.confidence,
            "alternatives": list(self.alternatives),
            "bottlenecks": list(self.bottlenecks),
            "explanation": dict(self.explanation),
        }


def probe_hardware(env: Mapping[str, str] | None = None) -> HardwareProbe:
    """Actually check for a usable GPU. Never guesses.

    Inspects ``/dev/dri`` for device nodes and ``nvidia-smi`` for a driver
    answer. Both are real checks against the host; when neither is present the
    verdict is ``usable=False`` with the reasons recorded, which is the honest
    answer on a CPU-only box.
    """
    source = os.environ if env is None else env
    reasons: list[str] = []
    evidence: dict[str, Any] = {}

    dri = source.get("MEM20WEBGPUZ_DRI_DIR", "/dev/dri")
    has_dri = os.path.isdir(dri)
    evidence["dri_dir"] = dri
    evidence["dri_present"] = has_dri
    if not has_dri:
        reasons.append(f"no device nodes under {dri}")

    exe = shutil.which("nvidia-smi")
    evidence["nvidia_smi"] = exe
    if not exe:
        reasons.append("nvidia-smi not installed")
    else:
        try:
            proc = subprocess.run(
                [exe, "-L"], capture_output=True, text=True, timeout=10
            )
            evidence["nvidia_smi_rc"] = proc.returncode
            if proc.returncode != 0:
                reasons.append(f"nvidia-smi exited {proc.returncode} (driver unavailable)")
            else:
                evidence["nvidia_smi_devices"] = [
                    line.strip() for line in proc.stdout.splitlines() if line.strip()
                ]
        except (OSError, subprocess.SubprocessError) as exc:
            reasons.append(f"nvidia-smi could not be executed: {type(exc).__name__}")

    return HardwareProbe(usable=not reasons, reasons=reasons, evidence=evidence)


def estimate_workgroups(operations: float, *, workgroup_size: int = WORKGROUP_SIZE) -> int:
    """Number of workgroups needed to cover ``operations`` invocations.

    Rounds up: a dispatch that covers fewer invocations than the workload needs
    silently drops work, which is worse than one extra workgroup.
    """
    if operations < 0:
        raise ValidationError(
            "operations must be non-negative", details={"operations": operations}
        )
    if workgroup_size < 1:
        raise ValidationError(
            "workgroup_size must be >= 1", details={"workgroup_size": workgroup_size}
        )
    if operations == 0:
        return 0
    return int(math.ceil(operations / workgroup_size))


def select_backend(
    request: Mapping[str, Any],
    probe: HardwareProbe | None = None,
) -> tuple[Backend, list[Backend]]:
    """Choose a backend from the probe result and the request's constraints.

    Returns ``(chosen, alternatives)``. The decision is deterministic for a
    given (probe, request) pair so a replay produces the same plan.
    """
    hw = probe if probe is not None else probe_hardware()
    memory_mb = _as_number(request.get("memory_mb", 256), "memory_mb")
    if memory_mb < 0:
        raise ValidationError("memory_mb must be non-negative", details={"memory_mb": memory_mb})

    prefer = str(request.get("prefer", "auto")).lower()
    if prefer not in {"auto", "webgpu", "cpu"}:
        raise ValidationError(
            "prefer must be one of auto|webgpu|cpu", details={"prefer": prefer}
        )

    gpu_ok = hw.usable and memory_mb >= MIN_GPU_MEMORY_MB
    gpu_reason = (
        "usable GPU detected and memory within budget"
        if gpu_ok
        else ("no usable GPU: " + "; ".join(hw.reasons) if not hw.usable
              else f"memory_mb {memory_mb} below GPU floor {MIN_GPU_MEMORY_MB}")
    )

    if prefer == "cpu":
        chosen = Backend("cpu", True, "caller pinned cpu")
    elif prefer == "webgpu":
        chosen = Backend("webgpu", gpu_ok, gpu_reason)
    else:
        chosen = Backend("webgpu", gpu_ok, gpu_reason) if gpu_ok else Backend(
            "cpu", True, "auto: " + gpu_reason
        )

    alternatives = [
        Backend("webgpu", gpu_ok, gpu_reason),
        Backend("cpu", True, "always available; no device required"),
    ]
    return chosen, alternatives


def _as_number(value: Any, field_name: str) -> float:
    """Coerce a request field to a finite float, or raise a typed error.

    A bare ``float()`` raises ``ValueError``, which escapes the subsystem's
    error taxonomy and reaches an API client as an untyped 500. Every numeric
    boundary goes through here so bad input is always a ``ValidationError``.
    """
    if isinstance(value, bool):
        raise ValidationError(
            f"{field_name} must be a number, not a boolean",
            details={"field": field_name, "value": value},
        )
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            f"{field_name} must be a number",
            details={"field": field_name, "value": repr(value)},
        ) from exc
    if not math.isfinite(number):
        raise ValidationError(
            f"{field_name} must be finite",
            details={"field": field_name, "value": repr(value)},
        )
    return number


def plan_dispatch(
    request: Mapping[str, Any],
    probe: HardwareProbe | None = None,
    *,
    max_workgroups: int = 65535,
) -> DispatchPlan:
    """Build the full dispatch plan for one workload.

    The plan carries confidence, alternatives, bottlenecks and a machine-
    readable explanation for every automated choice, as the roadmap's Phase 2.1
    requires. ``speedup`` is ``"not_measured"`` unless the caller supplies a
    ``measured_speedup`` that came from an actual benchmark.
    """
    operations = _as_number(request.get("operations", 1_000_000), "operations")
    memory_mb = _as_number(request.get("memory_mb", 256), "memory_mb")
    hw = probe if probe is not None else probe_hardware()

    chosen, alternatives = select_backend(request, hw)
    workgroups = estimate_workgroups(operations)
    if workgroups > max_workgroups:
        raise ValidationError(
            f"dispatch needs {workgroups} workgroups, ceiling is {max_workgroups}",
            details={"workgroups": workgroups, "max_workgroups": max_workgroups},
        )

    bottlenecks: list[str] = []
    if not hw.usable:
        bottlenecks.append("no_gpu_device")
    if memory_mb > 4096:
        bottlenecks.append("memory_pressure")
    if workgroups > max_workgroups // 2:
        bottlenecks.append("dispatch_saturation")

    measured = request.get("measured_speedup")
    if measured is None:
        speedup = "not_measured"
        note = (
            "no benchmark was run; a CPU/webGPU ratio is not derivable from "
            "operation count alone"
        )
    else:
        speedup = round(_as_number(measured, "measured_speedup"), 4)
        note = "caller-supplied measurement from an actual benchmark run"

    # Confidence is a function of how much of the decision rests on evidence.
    confidence = clamp(
        0.5
        + (0.3 if hw.usable else 0.0)
        + (0.2 if measured is not None else 0.0)
        - (0.1 * len(bottlenecks))
    )

    explanation = {
        "domain_version": DOMAIN_VERSION,
        "probe": hw.to_dict(),
        "request_digest": stable_hash(dict(request)),  # cross-module: mem20core
        "rule": "gpu when a usable device is present and memory is within budget",
        "measured": measured is not None,
    }

    return DispatchPlan(
        backend=chosen.name,
        workgroups=workgroups,
        workgroup_size=WORKGROUP_SIZE,
        total_invocations=int(operations),
        memory_mb=memory_mb,
        speedup=speedup,
        speedup_note=note,
        confidence=confidence,
        alternatives=[b.to_dict() for b in alternatives],
        bottlenecks=bottlenecks,
        explanation=explanation,
    )


def screen_request(request: Mapping[str, Any]) -> dict[str, Any]:
    """Screen a request for credential-shaped values before it is persisted.

    Uses the estate's own secret classifier rather than a local regex, so a
    finding here means the same thing it means at the gateway. Returns a verdict
    dict; the runtime refuses to persist a request that carries a blocking
    finding.
    """
    text = canonical(dict(request))  # cross-module: mem20core
    findings: list[dict[str, Any]] = []
    blocked = False
    for key, value in _walk_scalars(request):
        if not isinstance(value, str) or len(value) < 8:
            continue
        severity, kind = classify_secret(key, value)  # cross-module: mem20secretz
        if severity in {"critical", "high"}:
            blocked = True
            findings.append({"key": key, "severity": severity, "kind": kind})
    return {
        "allowed": not blocked,
        "findings": findings,
        "digest": stable_hash(text),  # cross-module: mem20core
    }


def asset_budget(family: str, triangles: int, lod: int = 0) -> dict[str, Any]:
    """Ask mem20kilnz whether a render asset is within its family budget.

    The kiln owns the triangle bands; this subsystem only reports the verdict so
    a studio session can refuse an over-budget asset before dispatch.
    """
    verdict = check_triangles(family, triangles, lod)  # cross-module: mem20kilnz
    return {
        "family": family,
        "triangles": triangles,
        "lod": lod,
        "ok": bool(getattr(verdict, "ok", False)),
        "detail": getattr(verdict, "detail", ""),
    }


def estate_inventory() -> dict[str, Any]:
    """Summarise the estate's subsystems via toolchest's own discovery.

    Used by ``inspect`` so the studio reports the real estate it is embedded in
    rather than a hardcoded list.
    """
    data = discover_subsystems()  # cross-module: toolchest
    entries = data.get("entries") if isinstance(data, dict) else None
    if entries is None:
        entries = data if isinstance(data, list) else []
    names = sorted(
        e.get("name", "") for e in entries if isinstance(e, dict) and e.get("name")
    )
    return {"subsystem_count": len(names), "subsystems": names}


def _walk_scalars(obj: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    """Yield ``(dotted_key, value)`` for every scalar in a nested structure."""
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            yield from _walk_scalars(value, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(obj, (list, tuple)):
        for index, value in enumerate(obj):
            yield from _walk_scalars(value, f"{prefix}[{index}]")
    else:
        yield prefix, obj


def run_domain(request: Mapping[str, Any], *, max_workgroups: int = 65535) -> dict[str, Any]:
    """The subsystem's core operation: plan a dispatch for one workload.

    This is the single entry point the runtime, API, CLI and SDK all funnel
    through, so every surface returns the same shape.
    """
    if not isinstance(request, Mapping):
        raise ValidationError("request must be an object", details={"type": type(request).__name__})
    screen = screen_request(request)
    if not screen["allowed"]:
        raise ValidationError(
            "request carries a blocking secret finding",
            details={"findings": screen["findings"]},
        )
    plan = plan_dispatch(request, max_workgroups=max_workgroups)
    # The estate's retry contract is owned by memory_engine; report its actual
    # defaults rather than a local copy, so a change there is visible here.
    estate_policy = RetryPolicy()  # cross-module: memory_engine
    return {
        "domain_version": DOMAIN_VERSION,
        "plan": plan.to_dict(),
        "screen": screen,
        "retry_policy": {
            "max_attempts": estate_policy.max_attempts,
            "base_delay": estate_policy.base_delay,
            "max_delay": estate_policy.max_delay,
            "multiplier": estate_policy.multiplier,
            "jitter": estate_policy.jitter,
            "delay_after_first_failure": estate_policy.delay_for(1),
        },
    }


def load_roadmap(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Load and validate this subsystem's roadmap document.

    Defaults to ``roadmap.json`` beside the package, so a clean clone resolves
    it without configuration.
    """
    import json

    target = Path(path) if path is not None else Path(__file__).with_name("roadmap.json")
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValidationError(
            f"roadmap not readable: {target}", details={"path": str(target)}
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"roadmap is not valid JSON: {target}", details={"path": str(target)}
        ) from exc
    validate_roadmap(data)
    return data


def validate_roadmap(roadmap: Mapping[str, Any]) -> None:
    """Enforce the roadmap contract the estate's other subsystems share."""
    required = [
        "global_id", "section", "owner", "owner_code", "roadmap_index",
        "title", "outcome", "breakthrough", "lane", "phases",
    ]
    missing = [key for key in required if key not in roadmap]
    if missing:
        raise ValidationError(
            "roadmap missing required keys", details={"missing": missing}
        )
    if not 101 <= int(roadmap["global_id"]) <= 200:
        raise ValidationError(
            "roadmap id out of package range", details={"global_id": roadmap["global_id"]}
        )
    phases = roadmap["phases"]
    if len(phases) != 3:
        raise ValidationError("expected 3 phases", details={"phases": len(phases)})
    subphases = sum(len(p.get("subphases", [])) for p in phases)
    if subphases != 6:
        raise ValidationError("expected 6 subphases", details={"subphases": subphases})
    for phase in phases:
        for sub in phase.get("subphases", []):
            if len(sub.get("work", [])) != 3:
                raise ValidationError(
                    "expected 3 work items per subphase",
                    details={"subphase": sub.get("name")},
                )
