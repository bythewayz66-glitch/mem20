"""Instant app synthesis: spec to app, scaffolding, deployment."""
import hashlib


def synthesize(spec):
    return {
        "name": spec.get("name"),
        "pages": spec.get("pages", ["home"]),
        "components": spec.get("components", []),
        "framework": spec.get("framework", "react"),
        "files": ["App.jsx", "index.html", "package.json"],
    }


def scaffold(app):
    return {"dirs": ["src", "public", "tests"], "files": list(app.get("files", [])), "entry": "src/App.jsx"}


def estimate_size(app):
    base = len(app.get("pages", [])) * 50 + len(app.get("components", [])) * 20
    return base


def validate_spec(spec):
    required = ["name"]
    missing = [r for r in required if r not in spec]
    return {"valid": not missing, "missing": missing}


def deploy_config(app, target="vercel"):
    return {"target": target, "build_cmd": "npm run build", "output_dir": "dist", "env": {}}
