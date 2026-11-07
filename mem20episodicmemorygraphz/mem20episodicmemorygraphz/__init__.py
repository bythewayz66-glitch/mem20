"""mem20episodicmemorygraphz (RM-021): Episodic Memory Graph."""
from __future__ import annotations
import importlib
from .domain import (
    add_event, context_diff, create_episode, entity_index, episode_graph, forget,
    graph_query, link_episodes, neighbors, recall, timeline,
)
__version__ = "1.0.0"
__all__ = [
    "add_event","context_diff","create_episode","entity_index","episode_graph","forget",
    "graph_query","link_episodes","neighbors","recall","timeline",
    "EpisodicService","ValidationError","ecosystem","__version__",
]
def __getattr__(name):
    if name in ("EpisodicService","ValidationError"): return getattr(importlib.import_module(".service",__name__), name)
    if name=="ecosystem": return importlib.import_module(".ecosystem",__name__)
    raise AttributeError(name)
