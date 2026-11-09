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


# --- 1st-class pipeline extensions (RM-246, #332) ---

DEFAULT_STAGES = (
    "blockout",
    "encounters",
    "navigation",
    "streaming",
    "lighting",
    "playability_tests",
)


def build_pipeline(level_spec=None, stages=None):
    level_spec = dict(level_spec or {})
    stage_names = list(stages or level_spec.get("stages") or DEFAULT_STAGES)
    grid = level_spec.get("grid") or [[0] * max(4, int(level_spec.get("width", 8)))] * max(4, int(level_spec.get("height", 8)))
    layout = level_spec.get("layout") or {"width": len(grid[0]) if grid else 8, "height": len(grid), "rooms": level_spec.get("rooms") or [{"id": "r1", "w": 4, "h": 4}]}
    built = []
    prev = None
    for i, name in enumerate(stage_names):
        sid = str(name if not isinstance(name, dict) else name.get("id") or name.get("name") or f"stage-{i}")
        deps = [prev] if prev else []
        artifact = {"id": f"artifact-{sid}", "stage": sid, "type": sid, "status": "pending"}
        checkpoint = {"id": f"checkpoint-{sid}", "stage": sid, "criteria": [f"{sid}:validated"], "passed": False}
        transformation = {"from": prev, "to": sid, "op": f"produce_{sid}"}
        built.append({
            "id": sid, "order": i, "status": "pending", "depends_on": deps,
            "artifact": artifact, "checkpoint": checkpoint, "transformation": transformation,
        })
        prev = sid
    return {
        "pipeline_id": level_spec.get("id") or f"levelpipe-{abs(hash(str(level_spec)))%10**8}",
        "level_spec": level_spec, "layout": layout, "grid": grid, "stages": built,
        "dependencies": [{"from": d, "to": s["id"]} for s in built for d in s["depends_on"]],
        "artifacts": [s["artifact"] for s in built],
        "checkpoints": [s["checkpoint"] for s in built],
        "transformations": [s["transformation"] for s in built],
        "status": "planned",
    }


def _stage_work(pipeline, stage):
    sid = stage["id"]
    grid = pipeline.get("grid") or [[0, 0], [0, 0]]
    layout = pipeline.get("layout") or {"width": 8, "height": 8, "rooms": [{"id": "r1"}]}
    if sid == "navigation":
        nav = generate_navmesh(grid)
        path = pathfind(grid, (0, 0), (max(0, len(grid[0]) - 1), max(0, len(grid) - 1)))
        return {"navmesh_cells": len(nav), "sample_path_len": len(path), "reachable": bool(path) or len(nav) > 0}
    if sid == "blockout":
        v = validate_level(layout)
        return {"layout_valid": v.get("valid"), "rooms": v.get("rooms", 0)}
    if sid == "encounters":
        props = place_props(layout, (pipeline.get("level_spec") or {}).get("props") or ["spawn", "cover", "objective"], seed=1)
        return {"encounter_props": props, "count": len(props)}
    if sid == "playability_tests":
        return playability_test(pipeline)
    if sid in ("streaming", "lighting"):
        return {"prepared": True, "stage": sid, "budget_ms": 16 if sid == "lighting" else 8}
    return {"prepared": True, "stage": sid}


def playability_test(pipeline):
    grid = pipeline.get("grid") or [[0, 0], [0, 0]]
    layout = pipeline.get("layout") or {"rooms": [{"id": "r1"}]}
    nav = generate_navmesh(grid)
    start = (0, 0)
    end = (max(0, len(grid[0]) - 1), max(0, len(grid) - 1))
    path = pathfind(grid, start, end)
    layout_ok = validate_level(layout).get("valid", False)
    reachable = bool(path) or (start == end)
    return {
        "ok": bool(layout_ok and (reachable or nav)),
        "layout_valid": layout_ok, "navmesh_cells": len(nav), "path_found": bool(path), "path_length": len(path),
        "issues": ([] if layout_ok else ["invalid_layout"]) + ([] if (reachable or nav) else ["no_path"]),
    }


def pipeline_status_update(pipeline):
    stages = pipeline.get("stages") or []
    if stages and all(s.get("status") == "done" for s in stages):
        pipeline["status"] = "completed"
    elif any(s.get("status") == "failed" for s in stages):
        pipeline["status"] = "failed"
    elif any(s.get("status") in ("done", "blocked", "failed") for s in stages):
        pipeline["status"] = "in_progress"
    else:
        pipeline["status"] = "planned"
    return pipeline


def pipeline_progress(pipeline):
    stages = pipeline.get("stages") or []
    done = sum(1 for s in stages if s.get("status") == "done")
    total = len(stages)
    done_ids = {s["id"] for s in stages if s.get("status") == "done"}
    ready = sum(1 for s in stages if s.get("status") == "pending" and all(d in done_ids for d in (s.get("depends_on") or [])))
    return {"done": done, "total": total, "ready": ready, "failed": sum(1 for s in stages if s.get("status") == "failed"), "progress": round(done / max(1, total), 4)}


def run_pipeline_stage(pipeline, stage_id):
    stages = pipeline.get("stages") or []
    done_ids = {s["id"] for s in stages if s.get("status") == "done"}
    for s in stages:
        if s["id"] != stage_id:
            continue
        deps = s.get("depends_on") or []
        if not all(d in done_ids for d in deps):
            s["status"] = "blocked"
            pipeline_status_update(pipeline)
            return pipeline
        result = _stage_work(pipeline, s)
        s["status"] = "done"
        s["result"] = result
        s["artifact"]["status"] = "ready"
        s["artifact"]["summary"] = {k: v for k, v in result.items() if not isinstance(v, (list, dict)) or k in ("issues",)}
        s["checkpoint"]["passed"] = bool(result.get("ok", True)) if stage_id == "playability_tests" else True
        if stage_id == "playability_tests" and not result.get("ok"):
            s["status"] = "failed"
            s["artifact"]["status"] = "failed"
        break
    pipeline_status_update(pipeline)
    return pipeline


def compile_level_plan(level_spec=None, stages=None, run_all=True):
    pipeline = build_pipeline(level_spec=level_spec, stages=stages)
    if run_all:
        for _ in range(len(pipeline["stages"]) + 1):
            progressed = False
            done_ids = {s["id"] for s in pipeline["stages"] if s.get("status") == "done"}
            for s in pipeline["stages"]:
                if s.get("status") == "pending" and all(d in done_ids for d in (s.get("depends_on") or [])):
                    run_pipeline_stage(pipeline, s["id"])
                    progressed = True
            if not progressed:
                break
    return {
        "ok": pipeline.get("status") in ("completed", "in_progress", "planned"),
        "pipeline": pipeline,
        "progress": pipeline_progress(pipeline),
        "summary": {
            "pipeline_id": pipeline["pipeline_id"],
            "stages": len(pipeline["stages"]),
            "dependencies": len(pipeline["dependencies"]),
            "artifacts": len(pipeline["artifacts"]),
            "checkpoints": len(pipeline["checkpoints"]),
            "status": pipeline["status"],
        },
    }
