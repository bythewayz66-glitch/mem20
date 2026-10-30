"""Hard gates for mem20liez high-stakes modes.

Consent, dual-control, prohibited-use enforcement, and seal-time
contamination firewall. Nothing here is advisory — these raise or
return structured refusals that the MCP tools and session layer must
respect.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Literal
import time

SessionMode = Literal["interrogation", "therapy", "clinical", "government", "generic"]

# Modes that require recorded, affirmative consent before any processing.
CONSENT_REQUIRED_MODES = frozenset({"interrogation", "clinical", "government"})

# Modes that require a second officer/clinician acknowledgement for
# high-priority cues and before seal.
DUAL_CONTROL_MODES = frozenset({"government"})

# Explicitly prohibited uses. Checked at session start and again at seal.
PROHIBITED_USES = (
    "automated_detention",
    "automated_charge",
    "automated_clearance",
    "definitive_deception_claim",
    "clinical_diagnosis",
    "medical_device_claim",
    "polygraph_substitute",
    "covert_surveillance_without_warrant",
    "employment_screening_without_notice",
    "immigration_adjudication",
    "child_custody_determination",
)

PROHIBITED_USE_MESSAGES = {
    "automated_detention": "Automated detention or restraint decisions are prohibited.",
    "automated_charge": "Automated charging decisions are prohibited.",
    "automated_clearance": "Automated security-clearance decisions are prohibited.",
    "definitive_deception_claim": (
        "Presenting any score as definitive proof of deception or intent is prohibited."
    ),
    "clinical_diagnosis": (
        "Issuing or implying a clinical diagnosis from behavioural signals is prohibited."
    ),
    "medical_device_claim": (
        "mem20liez is not a medical device and must not be described as one."
    ),
    "polygraph_substitute": (
        "mem20liez must not be used or marketed as a polygraph substitute."
    ),
    "covert_surveillance_without_warrant": (
        "Covert use without lawful authority / warrant is prohibited."
    ),
    "employment_screening_without_notice": (
        "Employment or pre-employment screening without subject notice is prohibited."
    ),
    "immigration_adjudication": (
        "Use as the sole or primary basis for immigration adjudication is prohibited."
    ),
    "child_custody_determination": (
        "Use as the sole or primary basis for child-custody determinations is prohibited."
    ),
}

DISCLAIMER = (
    "All behavioural signals are probabilistic observations only. "
    "They do not constitute definitive proof of deception, emotion, "
    "or intent. Model versions and confidence scores are recorded "
    "for audit. mem20liez is not a medical device, not a polygraph, "
    "and must not be used for automated legal or clinical decisions."
)


@dataclass
class DualControlRecord:
    cue_id: str
    first_officer_id: str
    second_officer_id: str
    acknowledged_at: float
    notes: str = ""


@dataclass
class SessionGateState:
    """Mutable gate state attached to a LiveLieSession."""

    mode: SessionMode
    consent: bool = False
    consent_recorded_at: Optional[float] = None
    consent_attested_by: Optional[str] = None
    subject_id: Optional[str] = None
    jurisdiction: Optional[str] = None
    operator_id: Optional[str] = None
    dual_control_records: list[DualControlRecord] = field(default_factory=list)
    intended_uses: list[str] = field(default_factory=list)
    training_acknowledged: bool = False
    training_version: Optional[str] = None

    def requires_consent(self) -> bool:
        return self.mode in CONSENT_REQUIRED_MODES

    def requires_dual_control(self) -> bool:
        return self.mode in DUAL_CONTROL_MODES

    def consent_ok(self) -> bool:
        if not self.requires_consent():
            return True
        return bool(self.consent and self.consent_recorded_at)

    def dual_control_count(self) -> int:
        return len(self.dual_control_records)


class GateError(Exception):
    """Raised when a hard gate refuses an operation."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")

    def as_dict(self) -> dict:
        return {"ok": False, "error_code": self.code, "error": self.message}


def check_prohibited_uses(intended_uses: list[str] | None) -> None:
    """Raise GateError if any intended use is on the prohibited list."""
    if not intended_uses:
        return
    for use in intended_uses:
        key = use.strip().lower().replace(" ", "_")
        if key in PROHIBITED_USES:
            raise GateError(
                "prohibited_use",
                PROHIBITED_USE_MESSAGES.get(
                    key, f"Use '{use}' is prohibited by mem20liez policy."
                ),
            )


def require_consent(state: SessionGateState, *, action: str = "start") -> None:
    if not state.requires_consent():
        return
    if not state.consent_ok():
        raise GateError(
            "consent_required",
            f"Affirmative consent is required for mode={state.mode!r} before {action}. "
            "Pass consent=true and record who attested.",
        )


def require_training(state: SessionGateState) -> None:
    """High-stakes modes require the operator to have acknowledged training."""
    if state.mode not in CONSENT_REQUIRED_MODES:
        return
    if not state.training_acknowledged:
        raise GateError(
            "training_required",
            f"Operator training acknowledgement is required for mode={state.mode!r}. "
            "See docs/use-cases/TRAINING-MEM20LIEZ.md and call lie_acknowledge_training.",
        )


def require_dual_control_for_seal(state: SessionGateState, high_priority_cue_ids: list[str]) -> None:
    """Government mode: every high-priority cue must have dual acknowledgement before seal."""
    if not state.requires_dual_control():
        return
    if not high_priority_cue_ids:
        return
    acknowledged = {r.cue_id for r in state.dual_control_records}
    missing = [cid for cid in high_priority_cue_ids if cid not in acknowledged]
    if missing:
        raise GateError(
            "dual_control_incomplete",
            f"Government mode requires dual-control acknowledgement for high-priority "
            f"cues before seal. Missing: {missing}. Use lie_dual_acknowledge.",
        )


def record_dual_acknowledge(
    state: SessionGateState,
    cue_id: str,
    first_officer_id: str,
    second_officer_id: str,
    notes: str = "",
) -> DualControlRecord:
    if not state.requires_dual_control():
        raise GateError(
            "dual_control_not_applicable",
            f"Dual control is only required/available for modes {sorted(DUAL_CONTROL_MODES)}.",
        )
    if not first_officer_id or not second_officer_id:
        raise GateError(
            "dual_control_ids_required",
            "Both first_officer_id and second_officer_id are required.",
        )
    if first_officer_id.strip() == second_officer_id.strip():
        raise GateError(
            "dual_control_same_officer",
            "Dual control requires two distinct officer/clinician identifiers.",
        )
    rec = DualControlRecord(
        cue_id=cue_id,
        first_officer_id=first_officer_id.strip(),
        second_officer_id=second_officer_id.strip(),
        acknowledged_at=time.time(),
        notes=notes or "",
    )
    state.dual_control_records.append(rec)
    return rec


def seal_contamination_check(package: dict) -> dict:
    """Strengthen the contamination firewall for liez packages.

    Ensures the sealed package is tagged as grounded observational data,
    never as a definitive finding, and always carries the disclaimer.
    Returns the (possibly augmented) package; raises GateError on violation.
    """
    if not isinstance(package, dict):
        raise GateError("seal_invalid", "Seal package must be a dict.")

    # Force epistemic status
    package.setdefault("epistemic_status", "observed_indicator")
    package["origin"] = "grounded"
    package["is_definitive_finding"] = False
    package["disclaimer"] = DISCLAIMER

    # Refuse any attempt to mark the package as a diagnosis or legal finding
    annotations = package.get("annotations") or {}
    banned_keys = {
        "diagnosis",
        "legal_finding",
        "deception_confirmed",
        "guilty",
        "clearance_denied",
        "detain",
    }
    for k in annotations:
        if k.lower() in banned_keys:
            raise GateError(
                "contamination_attempt",
                f"Annotation key '{k}' would contaminate the grounded store with a "
                f"definitive claim. Remove it; indicators only.",
            )

    # Ensure every detection in the package still carries confidence + model id
    for d in package.get("detections") or []:
        conf = d.get("confidence") or {}
        if "score" not in conf or "model_id" not in conf:
            raise GateError(
                "missing_confidence",
                "Every detection must carry confidence.score and confidence.model_id.",
            )

    package["firewall"] = {
        "contamination_check": "passed",
        "origin": "grounded",
        "epistemic_status": "observed_indicator",
        "is_definitive_finding": False,
    }
    return package
