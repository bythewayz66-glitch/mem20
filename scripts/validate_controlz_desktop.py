#!/usr/bin/env python3
"""Validate the checked-in controlz desktop wiring without building Rust.

This is deliberately a structural check: CI runs the real Vite build separately,
while this script catches the common path/config drift that makes Tauri open a
blank window or ship without its release/update contract.
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
    updater_path = tauri / "tauri.updater.conf.json"
    capability_path = tauri / "capabilities" / "default.json"
    release_path = root / ".github" / "workflows" / "controlz-desktop.yml"

    for path in (package_path, config_path, cargo_path, app_path, updater_path, capability_path, release_path):
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

    bundle = config.get("bundle", {})
    require(bundle.get("active") is True, "Tauri bundling must be active")
    require(bundle.get("createUpdaterArtifacts") is True, "signed updater artifacts must be enabled")
    icons = set(bundle.get("icon", []))
    for icon in ("icons/32x32.png", "icons/128x128.png", "icons/128x128@2x.png", "icons/icon.icns", "icons/icon.ico"):
        require(icon in icons and (tauri / icon).is_file(), f"bundle icon is missing: {icon}")

    updater = config.get("plugins", {}).get("updater", {})
    require(updater.get("active") is True, "Tauri updater must be active")
    require(updater.get("pubkey"), "Tauri updater public key is missing")
    require(updater.get("endpoints"), "Tauri updater endpoint is missing")

    capabilities = json.loads(capability_path.read_text(encoding="utf-8"))
    permissions = set(capabilities.get("permissions", []))
    require("updater:default" in permissions, "updater capability permission is missing")

    frontend_dist = (tauri / build.get("frontendDist", "")).resolve()
    expected_frontend_dist = (controlz / "mem20controlz" / "static").resolve()
    require(frontend_dist == expected_frontend_dist, "frontendDist must be FastAPI's static directory")
    cargo = cargo_path.read_text(encoding="utf-8")
    require("name = \"mem20controlz-desktop\"" in cargo, "Tauri Cargo package name drifted")
    require("tauri-plugin-updater" in cargo, "Tauri updater plugin dependency is missing")

    app_source = app_path.read_text(encoding="utf-8")
    require('@app.get("/api/health")' in app_source, "FastAPI health route is required for desktop validation")

    tauri_source = (tauri / "src" / "lib.rs").read_text(encoding="utf-8")
    require("tauri_plugin_updater::Builder" in tauri_source, "Tauri updater plugin is not initialized")
    require("download_and_install" in tauri_source, "Tauri updater install path is missing")

    release_source = release_path.read_text(encoding="utf-8")
    require("tauri-apps/tauri-action" in release_source, "desktop release workflow is missing tauri-action")
    require("TAURI_SIGNING_PRIVATE_KEY" in release_source, "desktop release workflow is missing updater signing")

    print("controlz desktop wiring: valid")
    print(f"frontendDist: {frontend_dist.relative_to(root)}")
    print("signed installers and updater release workflow: configured")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, json.JSONDecodeError) as exc:
        print(f"controlz desktop wiring: INVALID: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
