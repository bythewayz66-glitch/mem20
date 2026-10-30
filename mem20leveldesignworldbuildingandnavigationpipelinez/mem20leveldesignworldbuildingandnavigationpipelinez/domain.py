"""Level design, world building, and navigation pipeline."""
import random, math


def generate_navmesh(grid):
    # simple: mark walkable cells
    walkable = []
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == 0:
                walkable.append((x, y))
    return walkable


def pathfind(grid, start, end):
    # BFS
    from collections import deque
    if start == end:
        return [start]
    q = deque([start])
    visited = {start}
    parent = {start: None}
    while q:
        cur = q.popleft()
        if cur == end:
            break
        x, y = cur
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] == 0 and (nx,ny) not in visited:
                visited.add((nx,ny))
                parent[(nx,ny)] = cur
                q.append((nx,ny))
    if end not in parent:
        return []
    path = []
    cur = end
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path


def place_props(layout, props, seed=0):
    rng = random.Random(seed)
    placements = []
    for p in props:
        placements.append({"prop": p, "x": rng.randint(0, layout.get("width", 10)-1), "y": rng.randint(0, layout.get("height", 10)-1)})
    return placements


def validate_level(layout):
    if not layout.get("rooms"):
        return {"valid": False, "reason": "no rooms"}
    return {"valid": True, "rooms": len(layout["rooms"])}
