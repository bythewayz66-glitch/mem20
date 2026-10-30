"""AI level architect: layout generation, difficulty curve, pacing."""
import math, random


def generate_layout(width, height, rooms=5, seed=0):
    """Generate a simple room-based level layout."""
    rng = random.Random(seed)
    rooms_out = []
    for i in range(rooms):
        w = rng.randint(3, 8)
        h = rng.randint(3, 8)
        x = rng.randint(0, max(1, width - w))
        y = rng.randint(0, max(1, height - h))
        rooms_out.append({"id": f"room_{i}", "x": x, "y": y, "w": w, "h": h})
    return {"width": width, "height": height, "rooms": rooms_out}


def difficulty_curve(levels, base=1.0, growth=1.15):
    """Compute difficulty values across levels."""
    return [round(base * (growth ** i), 3) for i in range(levels)]


def place_enemies(layout, density=0.3, seed=0):
    """Place enemies in rooms based on density."""
    rng = random.Random(seed)
    placements = []
    for room in layout.get("rooms", []):
        area = room["w"] * room["h"]
        count = max(0, int(area * density))
        for j in range(count):
            placements.append({"room": room["id"], "x": rng.randint(room["x"], room["x"]+room["w"]-1),
                               "y": rng.randint(room["y"], room["y"]+room["h"]-1)})
    return placements


def pacing_profile(total_time, segments=4):
    """Split total time into pacing segments (intro, rise, climax, outro)."""
    weights = [0.15, 0.35, 0.35, 0.15]
    # normalize
    s = sum(weights)
    weights = [w / s for w in weights]
    times = [round(total_time * w, 2) for w in weights]
    labels = ["intro", "rise", "climax", "outro"]
    return [{"label": l, "duration": t} for l, t in zip(labels, times)]


def validate_level(layout):
    """Validate a level layout."""
    if not layout.get("rooms"):
        return {"valid": False, "reason": "no rooms"}
    if layout["width"] <= 0 or layout["height"] <= 0:
        return {"valid": False, "reason": "invalid dimensions"}
    return {"valid": True, "room_count": len(layout["rooms"])}
