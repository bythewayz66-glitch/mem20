"""Dynamic narrative engine: story graph, branching, state tracking, with estate report."""
from __future__ import annotations
import random
from . import ecosystem
__all__=["create_story","add_node","choose","current_text","available_choices","narrative_state","narrative_report","probe","estate_context"]

def create_story(start_node):
    return {"current": start_node, "nodes": {start_node: {"text": "", "choices": []}}, "history": [], "state": {}}

def add_node(story, node_id, text, choices=None):
    story["nodes"][node_id] = {"text": text, "choices": choices or []}
    return story

def choose(story, choice_index):
    node = story["nodes"].get(story["current"], {})
    choices = node.get("choices", [])
    if choice_index < 0 or choice_index >= len(choices): return story
    nxt = choices[choice_index].get("target")
    if nxt in story["nodes"]:
        story["history"].append(story["current"]); story["current"] = nxt
        for k, v in choices[choice_index].get("effects", {}).items(): story["state"][k] = v
    return story

def current_text(story): return story["nodes"].get(story["current"], {}).get("text", "")
def available_choices(story): return story["nodes"].get(story["current"], {}).get("choices", [])
def narrative_state(story): return {"current": story["current"], "visited": len(set(story["history"])), "total_nodes": len(story["nodes"]), "state": story["state"]}

def narrative_report(story=None):
    if story is None:
        story=create_story("start"); add_node(story,"start","Begin", [{"label":"Go","target":"end","effects":{"mood":"ok"}}]); add_node(story,"end","End",[])
        choose(story,0)
    st=narrative_state(story); txt=current_text(story)
    peers={
        "narrative_events": ecosystem.narrative_events("narrative.report", {"current":st.get("current"),"visited":st.get("visited")}),
        "challenge_hooks": ecosystem.challenge_hooks(),
        "context_compression": ecosystem.context_compression(txt or "narrative"),
        "focus_guidance": ecosystem.focus_guidance({"goal":"story","state":st.get("state",{})}),
        "capability_routing": ecosystem.capability_routing("story", ["generate","branch","summarize"]),
        "branching_scenarios": ecosystem.branching_scenarios(st.get("state",{})),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"state":st,"text":txt,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=narrative_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
