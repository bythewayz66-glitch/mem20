"""Live session wrapper that ties detectors to the AV memory pipeline."""

from __future__ import annotations

from typing import Any, Optional, List, Literal
import time
import uuid

from .pipeline import LieDetector
from .types import DetectionResult, EarpieceCue, SignalType
from .cues import CueGenerator
from .gates import (
    SessionGateState,
    GateError,
    require_consent,
    require_training,
    require_dual_control_for_seal,
    record_dual_acknowledge,
    check_prohibited_uses,
    seal_contamination_check,
    DISCLAIMER,
    DualControlRecord,
)

SessionMode = Literal["interrogation", "therapy", "clinical", "government", "generic"]


class LiveLieSession:
    """One live professional session with continuous detection + cueing."""

    def __init__(
        self,
        detector: Optional[LieDetector] = None,
        mode: SessionMode = "generic",
        enable_earpiece: bool = True,
        consent: bool = False,
        consent_attested_by: Optional[str] = None,
        subject_id: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        operator_id: Optional[str] = None,
        intended_uses: Optional[List[str]] = None,
        training_acknowledged: bool = False,
        training_version: Optional[str] = None,
    ):
        self.session_id = str(uuid.uuid4())
        self.mode = mode
        self.detector = detector or LieDetector()
        self.cue_gen = CueGenerator(mode=mode)
        self.enable_earpiece = enable_earpiece

        self._cues: List[EarpieceCue] = []
        self._all_detections: List[DetectionResult] = []
        self.started_at = time.time()
        self.sealed = False

        # Hard gate state
        self.gates = SessionGateState(
            mode=mode,
            consent=consent,
            consent_recorded_at=time.time() if consent else None,
            consent_attested_by=consent_attested_by,
            subject_id=subject_id,
            jurisdiction=jurisdiction,
            operator_id=operator_id,
            intended_uses=list(intended_uses or []),
            training_acknowledged=training_acknowledged,
            training_version=training_version,
        )

        # Enforce at construction for high-stakes modes
        check_prohibited_uses(self.gates.intended_uses)
        require_consent(self.gates, action="session construction")
        require_training(self.gates)

        # Back-compat meta dict used by older MCP callers
        self._meta: dict = {
            "subject_id": subject_id,
            "jurisdiction": jurisdiction,
            "consent": consent,
            "consent_attested_by": consent_attested_by,
            "operator_id": operator_id,
            "intended_uses": list(intended_uses or []),
            "training_acknowledged": training_acknowledged,
            "training_version": training_version,
        }

    def feed_audio(self, chunk: Any, timestamp: Optional[float] = None) -> List[DetectionResult]:
        require_consent(self.gates, action="feed_audio")
        results = self.detector.process_audio(chunk, timestamp=timestamp)
        self._all_detections.extend(results)
        self._maybe_generate_cues(results)
        return results

    def feed_video(self, frame: Any, timestamp: Optional[float] = None) -> List[DetectionResult]:
        require_consent(self.gates, action="feed_video")
        results = self.detector.process_video(frame, timestamp=timestamp)
        self._all_detections.extend(results)
        self._maybe_generate_cues(results)
        return results

    def feed_transcript(self, text: str, timestamp: Optional[float] = None) -> List[DetectionResult]:
        require_consent(self.gates, action="feed_transcript")
        results = self.detector.process_transcript(text, timestamp=timestamp)
        self._all_detections.extend(results)
        self._maybe_generate_cues(results)
        return results

    def _maybe_generate_cues(self, new_results: List[DetectionResult]) -> None:
        if not self.enable_earpiece:
            return
        new_cues = self.cue_gen.from_detections(new_results, mode=self.mode)
        self._cues.extend(new_cues)

    def get_earpiece_cues(self, since_id: Optional[str] = None) -> List[EarpieceCue]:
        if since_id is None:
            return [c for c in self._cues if not c.acknowledged]
        out = []
        seen = False
        for c in self._cues:
            if c.id == since_id:
                seen = True
                continue
            if seen and not c.acknowledged:
                out.append(c)
        return out

    def acknowledge_cue(self, cue_id: str) -> None:
        for c in self._cues:
            if c.id == cue_id:
                c.acknowledged = True
                break

    def dual_acknowledge(
        self,
        cue_id: str,
        first_officer_id: str,
        second_officer_id: str,
        notes: str = "",
    ) -> DualControlRecord:
        """Government dual-control: two distinct officers must acknowledge a high-priority cue."""
        rec = record_dual_acknowledge(
            self.gates,
            cue_id=cue_id,
            first_officer_id=first_officer_id,
            second_officer_id=second_officer_id,
            notes=notes,
        )
        # Also mark the cue itself acknowledged
        self.acknowledge_cue(cue_id)
        return rec

    def high_priority_cue_ids(self) -> List[str]:
        return [c.id for c in self._cues if c.priority >= 3]

    def seal(self, annotations: Optional[dict] = None) -> dict:
        """Produce the package that will be written to grounded memory.

        Enforces consent, training, dual-control (government), prohibited-use,
        and contamination firewall before returning the package.
        """
        if self.sealed:
            raise RuntimeError("session already sealed")

        require_consent(self.gates, action="seal")
        require_training(self.gates)
        require_dual_control_for_seal(self.gates, self.high_priority_cue_ids())
        check_prohibited_uses(self.gates.intended_uses)

        self.sealed = True
        package = {
            "session_id": self.session_id,
            "mode": self.mode,
            "started_at": self.started_at,
            "sealed_at": time.time(),
            "detections": [d.model_dump() for d in self._all_detections],
            "cues": [c.model_dump() for c in self._cues],
            "annotations": annotations or {},
            "meta": {
                **self._meta,
                "consent": self.gates.consent,
                "consent_recorded_at": self.gates.consent_recorded_at,
                "consent_attested_by": self.gates.consent_attested_by,
                "dual_control_records": [
                    {
                        "cue_id": r.cue_id,
                        "first_officer_id": r.first_officer_id,
                        "second_officer_id": r.second_officer_id,
                        "acknowledged_at": r.acknowledged_at,
                        "notes": r.notes,
                    }
                    for r in self.gates.dual_control_records
                ],
                "training_acknowledged": self.gates.training_acknowledged,
                "training_version": self.gates.training_version,
            },
            "disclaimer": DISCLAIMER,
        }

        # Contamination firewall — mutates package in place, raises on violation
        package = seal_contamination_check(package)
        return package
