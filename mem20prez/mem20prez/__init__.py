"""mem20prez — predictive recall on the real memory substrate."""
from .domain import (
    PredictiveRecallEngine, Prediction, PrefetchResult, EngineHealth,
    get_engine, predict_next, recall_score, prefetch, cache_hit_rate,
    recall_health, recall_report, probe, estate_context,
    record_recall_event, record_outcome,
)
__version__ = "1.1.0"
__all__ = [
    "PredictiveRecallEngine", "Prediction", "PrefetchResult", "EngineHealth",
    "get_engine", "predict_next", "recall_score", "prefetch", "cache_hit_rate",
    "recall_health", "recall_report", "probe", "estate_context",
    "record_recall_event", "record_outcome", "__version__",
]
