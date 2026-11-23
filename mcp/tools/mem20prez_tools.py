"""mem20prez MCP tools — predictive recall on grounded memory."""
from __future__ import annotations
import json, os, sys
from typing import Any, Dict
try:
    import mcp_types as mt
    MCP_SDK_AVAILABLE = True
except ImportError:
    MCP_SDK_AVAILABLE = False
    mt = None  # type: ignore

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _load():
    p = os.path.join(_REPO_ROOT, "mem20prez")
    if p not in sys.path:
        sys.path.insert(0, p)
    import mem20prez.domain as domain
    return domain

def _d(v):
    return json.dumps(v, indent=2, default=str)

class PrezToolsMixin:
    def register_prez_tools(self):
        if not MCP_SDK_AVAILABLE:
            return
        self.tools["prez_status"] = mt.Tool(
            name="prez_status", title="Predictive Recall Status",
            description="Model health and ranked next-topic predictions.",
            inputSchema={"type": "object", "properties": {
                "context_topic": {"type": "string"},
                "history": {"type": "array", "items": {"type": "string"}},
            }})
        self.tools["prez_predict"] = mt.Tool(
            name="prez_predict", title="Predict Next Topics",
            description="Rank topics likely needed next from learned transitions.",
            inputSchema={"type": "object", "properties": {
                "context_topic": {"type": "string"},
                "history": {"type": "array", "items": {"type": "string"}},
                "candidates": {"type": "array", "items": {"type": "string"}},
                "k": {"type": "integer", "default": 8},
            }})
        self.tools["prez_prefetch"] = mt.Tool(
            name="prez_prefetch", title="Prefetch Grounded Memories",
            description="Predict then pull grounded facts only (no simulated).",
            inputSchema={"type": "object", "properties": {
                "context_topic": {"type": "string"},
                "context_tags": {"type": "array", "items": {"type": "string"}},
                "k": {"type": "integer", "default": 5},
            }})
        self.tools["prez_record_outcome"] = mt.Tool(
            name="prez_record_outcome", title="Record Prediction Outcome",
            description="Mark whether a prediction/recall was useful.",
            inputSchema={"type": "object", "properties": {
                "prediction_id": {"type": "string"},
                "used_fact_ids": {"type": "array", "items": {"type": "string"}},
                "useful": {"type": "boolean"},
            }, "required": ["prediction_id", "useful"]})
        self.tools["prez_doctor"] = mt.Tool(
            name="prez_doctor", title="Predictive Recall Doctor",
            description="Health + memory_engine peer check.",
            inputSchema={"type": "object", "properties": {}})

    async def _prez_status(self, args: Dict[str, Any]) -> str:
        try:
            return _d(_load().recall_report(history=args.get("history"), context_topic=args.get("context_topic")))
        except Exception as e:
            return _d({"ok": False, "error": f"{type(e).__name__}: {e}"})

    async def _prez_predict(self, args: Dict[str, Any]) -> str:
        try:
            eng = _load().get_engine()
            preds = eng.predict_next(
                context_topic=args.get("context_topic"), history=args.get("history"),
                candidates=args.get("candidates"), k=int(args.get("k") or 8))
            return _d({"ok": True, "predictions": [
                {"topic": p.topic, "score": p.score, "reason": p.reason, "source": p.source} for p in preds]})
        except Exception as e:
            return _d({"ok": False, "error": f"{type(e).__name__}: {e}"})

    async def _prez_prefetch(self, args: Dict[str, Any]) -> str:
        try:
            r = _load().get_engine().prefetch(
                context_topic=args.get("context_topic"), context_tags=args.get("context_tags"),
                k=int(args.get("k") or 5), grounded_only=True)
            return _d({"ok": True, "event_id": r.event_id, "grounded_only": r.grounded_only,
                       "query_topics": list(r.query_topics), "latency_ms": r.latency_ms,
                       "predictions": [{"topic": p.topic, "score": p.score} for p in r.predictions],
                       "facts": list(r.facts)})
        except Exception as e:
            return _d({"ok": False, "error": f"{type(e).__name__}: {e}"})

    async def _prez_record_outcome(self, args: Dict[str, Any]) -> str:
        try:
            oid = _load().record_outcome(args["prediction_id"], args.get("used_fact_ids") or [], bool(args["useful"]))
            return _d({"ok": True, "outcome_id": oid})
        except Exception as e:
            return _d({"ok": False, "error": f"{type(e).__name__}: {e}"})

    async def _prez_doctor(self, args: Dict[str, Any]) -> str:
        try:
            return _d(_load().probe())
        except Exception as e:
            return _d({"ok": False, "error": f"{type(e).__name__}: {e}"})
