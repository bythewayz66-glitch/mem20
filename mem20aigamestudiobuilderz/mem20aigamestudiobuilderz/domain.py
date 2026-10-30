"""AI game studio builder: project scaffolding, asset pipeline, build config."""
import json, os


def scaffold_project(name, genre="action", engine="unity"):
    """Scaffold a game project structure."""
    return {
        "name": name,
        "genre": genre,
        "engine": engine,
        "folders": ["Assets", "Scripts", "Scenes", "Prefabs", "Audio", "UI"],
        "files": ["README.md", "project.json", ".gitignore"],
    }


def asset_pipeline(assets):
    """Plan asset import pipeline with validation."""
    pipeline = []
    for a in assets:
        pipeline.append({
            "id": a.get("id"),
            "type": a.get("type", "unknown"),
            "valid": a.get("format") in ("png", "fbx", "wav", "mp3", "json"),
            "target_dir": a.get("type", "misc") + "s",
        })
    return {"pipeline": pipeline, "valid_count": sum(1 for p in pipeline if p["valid"])}


def build_config(project, platform="pc"):
    """Generate build configuration."""
    return {
        "project": project.get("name"),
        "platform": platform,
        "output_dir": f"build/{platform}",
        "compression": "lz4" if platform == "mobile" else "none",
        "strip_debug": platform != "pc",
    }


def estimate_size(assets):
    """Estimate total build size in MB."""
    total = sum(a.get("size_mb", 0) for a in assets)
    return round(total * 1.15, 2)


def validate_project(project):
    """Validate a project has required fields."""
    required = ["name", "genre", "engine"]
    missing = [r for r in required if r not in project]
    return {"valid": not missing, "missing": missing}
