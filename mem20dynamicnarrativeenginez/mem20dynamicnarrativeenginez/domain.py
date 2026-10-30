"""Dynamic narrative engine: story graph, branching, state tracking."""
import random


def create_story(start_node):
    return {"current": start_node, "nodes": {start_node: {"text": "", "choices": []}}, "history": [], "state": {}}


def add_node(story, node_id, text, choices=None):
    story["nodes"][node_id] = {"text": text, "choices": choices or []}
    return story


def choose(story, choice_index):
    node = story["nodes"].get(story["current"], {})
    choices = node.get("choices", [])
    if choice_index < 0 or choice_index >= len(choices):
        return story
    nxt = choices[choice_index].get("target")
    if nxt in story["nodes"]:
        story["history"].append(story["current"])
        story["current"] = nxt
        # apply state changes
        for k, v in choices[choice_index].get("effects", {}).items():
            story["state"][k] = v
    return story


def current_text(story):
    return story["nodes"].get(story["current"], {}).get("text", "")


def available_choices(story):
    return story["nodes"].get(story["current"], {}).get("choices", [])


def narrative_state(story):
    return {"current": story["current"], "visited": len(set(story["history"])), "total_nodes": len(story["nodes"]), "state": story["state"]}
