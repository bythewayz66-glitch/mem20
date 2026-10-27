#!/usr/bin/env python3
"""Validate the checked-in controlz desktop wiring without building Rust.

This is deliberately a structural check: CI runs the real Vite build separately,
while this script catches the common path/config drift that makes Tauri open a
blank window. It does not claim that a backend sidecar exists; that is issue #36.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


class ValidationError(Exception):
    """A repository contract is missing or inconsistent."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    controlz = root / "mem20controlz"
    web = controlz / "mem20controlz" / "web"
    tauri = controlz / "src-tauri"

    package_path = web / "package.json"
    config_path = tauri / "tauri.conf.json"
    cargo_path = tauri / "Cargo.toml"
    app_path = controlz / "mem20controlz" / "app.py"

    for path in (package_path, config_path, cargo_path, app_path):
        require(path.is_file(), f"required desktop file is missing: {path.relative_to(root)}")

    package = json.loads(package_path.read_text(encoding="utf-8"))
    scripts = package.get("scripts", {})
    require(scripts.get("desktop:dev"), "web/package.json lacks desktop:dev")
    require(scripts.get("desktop:build"), "web/package.json lacks desktop:build")
    require(scripts.get("build") == "vite build", "web build must remain the Vite build")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    build = config.get("build", {})
    require(build.get("devUrl") == "http://127.0.0.1:5173", "Tauri devUrl must match Vite")
    require(build.get("beforeDevCommand"), "Tauri must start Vite before dev")
    require(build.get("beforeBuildCommand"), "Tauri must build the frontend before packaging")

    frontend_dist = (tauri / build.get("frontendDist", "")).resolve()
    expected_frontend_dist = (controlz / "mem20controlz" / "static").resolve()
    require(frontend_dist == expected_frontend_dist, "frontendDist must be FastAPI's static directory")
    require("name = \"mem20controlz-desktop\"" in cargo_path.read_text(encoding="utf-8"), "Tauri Cargo package name drifted")

    app_source = app_path.read_text(encoding="utf-8")
    require('@app.get("/api/health")' in app_source, "FastAPI health route is required for desktop validation")

    print("controlz desktop wiring: valid")
    print(f"frontendDist: {frontend_dist.relative_to(root)}")
    print("backend sidecar: not claimed (issue #36)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, json.JSONDecodeError) as exc:
        print(f"controlz desktop wiring: INVALID: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
