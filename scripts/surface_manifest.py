#!/usr/bin/env python3
"""Generate and check mem20's one authoritative surface manifest.

The live server's ``tools/list`` response is the authority for the tool count.
The AST catalog in ``web/scripts/extract-tools.py`` supplies the per-tool domain
and declaring module, and the generator refuses to emit anything unless the two
sets are identical. Outputs:

    docs/surface.json          machine-readable counts, domains, modules
    docs/TOOL-DOMAINS.md       human-readable domain mapping
    web/src/data/tools.json    the website's generated tool catalog

Usage:
    python3 scripts/surface_manifest.py --write     # regenerate all three
    python3 scripts/surface_manifest.py --check     # live + files + docs (CI)
    python3 scripts/surface_manifest.py --check-docs # offline docs-only check
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SURFACE_JSON = REPO / "docs" / "surface.json"
TOOL_DOMAINS = REPO / "docs" / "TOOL-DOMAINS.md"
WEB_CATALOG = REPO / "web" / "src" / "data" / "tools.json"
EXTRACTOR = REPO / "web" / "scripts" / "extract-tools.py"
LAUNCH_GATE = REPO / "scripts" / "check_launch_gate.py"

#: Docs that describe the surface as it is *today*, so they must track the live
#: count. Dated reports, audits and narratives are deliberately excluded: they
#: are history, and rewriting their numbers would falsify it.
CURRENT_DOCS = (
    "README.md",
    "docs/README.md",
    "docs/INDEX.md",
    "docs/01-architecture.md",
    "docs/02-tools-reference.md",
    "docs/05-complete-tools-reference.md",
    "docs/TOOL-DOMAINS.md",
    "docs/troubleshooting-mcp-server-startup.md",
    "toolchest/README.md",
    "SDKS.md",
    "docs/index.html",
    "docs/dashboard.html",
)

RETIRED = (
    ("257 / 26", "retired — predates the `lie_*` domain and undercounted `memory_*`"),
    ("268 / 26", "retired — counted `mcp/tools/` only, omitting the root-level tool modules"),
    ("270 / 27", "retired — earlier 27-domain taxonomy; the surface has since grown to 39 domains"),
    ("306 / 38", "retired — the pre-temporal surface: 306 tools before the five `temporal_*` tools landed"),
    ("306 / 39", "retired — a mismatched pair: 306 was the pre-temporal tool count, 39 the post-temporal domain count"),
)

RETIRED_MARKERS = (
    "retired",
    "predates",
    "superseded",
    "previous",
    "prior",
    "earlier",
    "historic",
    "before the",
    "no longer",
    "old value",
)

TOOL_CLAIM = re.compile(
    r"(?<![-\w])(\d{2,3})\s+(?:(?:MCP|unique|real|distinct|registered|live)\s+){0,2}tools?\b",
    re.IGNORECASE,
)
DOMAIN_CLAIM = re.compile(
    r"(?<![-\w])(\d{1,2})\s+(?:(?:MCP|distinct|live)\s+)?domains?\b",
    re.IGNORECASE,
)
TABLE_TOOL_CLAIM = re.compile(r"MCP tools\s*\|\s*\*{0,2}(\d{2,3})", re.IGNORECASE)


class SurfaceError(RuntimeError):
    pass


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_if_changed(path: Path, text: str) -> bool:
    if path.exists() and _read(path) == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def _server_python() -> str:
    """Interpreter that can import the mem20 server's dependencies.

    CI installs the project into the active interpreter, so sys.executable is
    right there. A local checkout usually keeps those dependencies in `.venv`,
    so prefer that when it exists.
    """
    if os.name == "nt":
        venv = REPO / ".venv" / "Scripts" / "python.exe"
    else:
        venv = REPO / ".venv" / "bin" / "python"
    return str(venv) if venv.is_file() else sys.executable


def live_tool_names() -> list[str]:
    """Read the names from a real JSON-RPC ``tools/list`` response."""
    messages = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "surface-manifest", "version": "1"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]
    payload = "".join(json.dumps(message) + "\n" for message in messages)
    completed = subprocess.run(
        [_server_python(), str(REPO / "launcher.py")],
        cwd=REPO,
        input=payload,
        capture_output=True,
        text=True,
        timeout=240,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    response = None
    for line in completed.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            message = json.loads(line)
        except ValueError:
            continue
        if message.get("id") == 2:
            response = message
    if response is None:
        raise SurfaceError(
            "tools/list returned no response (exit %d); stderr:\n%s"
            % (completed.returncode, completed.stderr[-2000:])
        )
    if "error" in response:
        raise SurfaceError("tools/list failed: %s" % response["error"])
    return sorted(tool["name"] for tool in response["result"]["tools"])


def ast_catalog(destination: Path | None = None) -> dict:
    """Run the AST extractor and return its payload."""
    temporary = None
    if destination is None:
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        handle.close()
        temporary = Path(handle.name)
        destination = temporary
    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(EXTRACTOR),
                "--root",
                str(REPO),
                "--out",
                str(destination),
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if completed.returncode != 0:
            raise SurfaceError(
                "AST extractor failed (exit %d):\n%s"
                % (completed.returncode, completed.stderr[-2000:])
            )
        return json.loads(_read(destination))
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def prefix_for(name: str) -> str:
    if "_" in name:
        return name.split("_", 1)[0] + "_*"
    return name


def build_manifest(catalog: dict, live_names: list[str]) -> dict:
    ast_names = {tool["n"] for tool in catalog["tools"]}
    only_live = sorted(set(live_names) - ast_names)
    only_ast = sorted(ast_names - set(live_names))
    if only_live or only_ast:
        raise SurfaceError(
            "live tools/list and the AST catalog disagree; "
            "only live: %s; only AST: %s" % (only_live, only_ast)
        )
    if len(live_names) != len(set(live_names)):
        raise SurfaceError("tools/list contains duplicate tool names")

    detail = []
    for domain in catalog["domains"]:
        tools = [tool for tool in catalog["tools"] if tool["x"] == domain]
        detail.append(
            {
                "domain": domain,
                "tools": len(tools),
                "prefixes": sorted({prefix_for(tool["n"]) for tool in tools}),
                "modules": sorted({tool["m"] for tool in tools}),
            }
        )
    detail.sort(key=lambda entry: (-entry["tools"], entry["domain"]))

    return {
        "schema": 1,
        "tools": len(live_names),
        "domains": len(detail),
        "domain_names": sorted(entry["domain"] for entry in detail),
        "domain_counts": {
            entry["domain"]: entry["tools"] for entry in sorted(detail, key=lambda e: e["domain"])
        },
        "domains_detail": detail,
        "unwired_tools": sorted(tool["n"] for tool in catalog.get("unwired", [])),
        "source": (
            "tools/list via launcher.py; domains and modules from the AST catalog "
            "generated by web/scripts/extract-tools.py"
        ),
        "cross_check": {
            "ast_tools": catalog["count"],
            "ast_domains": catalog["domain_count"],
            "only_live": only_live,
            "only_ast": only_ast,
        },
    }


def render_tool_domains(manifest: dict) -> str:
    tools = manifest["tools"]
    domains = manifest["domains"]
    cross = manifest["cross_check"]
    unwired = manifest["unwired_tools"]

    lines = [
        "# The %d MCP domains — authoritative mapping" % domains,
        "",
        "**%d tools across %d domains.** Generated from the server's live `tools/list`" % (tools, domains),
        "response by `scripts/surface_manifest.py`, with every tool name and domain",
        "cross-checked against the AST catalog in `web/src/data/tools.json`.",
        "Do not edit this file by hand.",
        "",
        "Regenerate and verify:",
        "",
        "```bash",
        "python3 scripts/surface_manifest.py --write",
        "python3 scripts/surface_manifest.py --check   # CI: fail on drift",
        "```",
        "",
        "## How the numbers are derived",
        "",
        "| step | value | why |",
        "|---|---:|---|",
        "| live `tools/list` | **%d** | the wire surface a client actually receives |" % tools,
        "| AST catalog, wired | **%d** | `mt.Tool(...)` declarations in modules the server inherits |" % cross["ast_tools"],
        "| AST declarations, unwired | %d | declared in source but not registered by any inherited mixin |" % len(unwired),
        "| domains | **%d** | distinct owning modules after the documented folds |" % cross["ast_domains"],
        "| names only in `tools/list` | %d | must be 0 |" % len(cross["only_live"]),
        "| names only in the AST catalog | %d | must be 0 |" % len(cross["only_ast"]),
        "",
        "The two collections are compared as sets, so a count can only agree if the",
        "same tools are present. A non-empty symmetric difference aborts generation.",
        "",
        "## The %d domains" % domains,
        "",
        "| # | Domain | Tools | Prefixes | Modules |",
        "|---:|---|---:|---|---|",
    ]
    for index, entry in enumerate(manifest["domains_detail"], start=1):
        prefixes = ", ".join("`%s`" % prefix for prefix in entry["prefixes"])
        modules = ", ".join("`%s`" % module for module in entry["modules"])
        lines.append(
            "| %d | `%s` | %d | %s | %s |"
            % (index, entry["domain"], entry["tools"], prefixes, modules)
        )
    lines.extend(
        [
            "| — | **total** | **%d** | | |" % tools,
            "",
            "## Unwired declarations",
            "",
            "The AST catalog sees %d declaration(s) that no inherited mixin registers." % len(unwired),
            "They are excluded from the live count and listed here so the gap stays visible:",
            "",
        ]
    )
    if unwired:
        lines.extend("- `%s`" % name for name in unwired)
    else:
        lines.append("_None._")
    lines.extend(
        [
            "",
            "## Retired numbers",
            "",
            "| number | status |",
            "|---|---|",
        ]
    )
    lines.extend("| **%s** | %s |" % (number, status) for number, status in RETIRED)
    lines.append("")
    return "\n".join(lines)


def expected_outputs(manifest: dict, catalog: dict) -> dict[Path, str]:
    return {
        SURFACE_JSON: json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        TOOL_DOMAINS: render_tool_domains(manifest),
        WEB_CATALOG: json.dumps(catalog, separators=(",", ":")) + "\n",
    }


def check_docs(manifest: dict) -> list[str]:
    problems: list[str] = []
    tools = manifest["tools"]
    domains = manifest["domains"]

    for relative in CURRENT_DOCS:
        path = REPO / relative
        if not path.is_file():
            problems.append("%s: listed as current-facing but missing" % relative)
            continue
        for line_number, line in enumerate(_read(path).splitlines(), start=1):
            lowered = line.lower()
            if any(marker in lowered for marker in RETIRED_MARKERS):
                continue
            # A markdown heading such as "## Memory Tools (36 tools)" counts the
            # subset documented beneath it, not the whole surface. Only a heading
            # that says "across N domains" is making a total-surface claim.
            heading = line.lstrip().startswith("#")
            check_tool_claims = not heading or "across" in lowered
            if check_tool_claims:
                for pattern in (TOOL_CLAIM, TABLE_TOOL_CLAIM):
                    for match in pattern.finditer(line):
                        value = int(match.group(1))
                        if value != tools:
                            problems.append(
                                "%s:%d claims %d tools, live is %d: %s"
                                % (relative, line_number, value, tools, line.strip())
                            )
            for match in DOMAIN_CLAIM.finditer(line):
                value = int(match.group(1))
                if value != domains:
                    problems.append(
                        "%s:%d claims %d domains, live is %d: %s"
                        % (relative, line_number, value, domains, line.strip())
                    )

    inputs = json.loads(_read(REPO / "docs" / "finance" / "inputs.json"))
    surface = inputs.get("tool_surface", {})
    if (surface.get("tools"), surface.get("domains")) != (tools, domains):
        problems.append(
            "docs/finance/inputs.json tool_surface is %s/%s, live is %d/%d"
            % (surface.get("tools"), surface.get("domains"), tools, domains)
        )

    verify_mcp = _read(REPO / "verify_mcp.py")
    match = re.search(r'MEM20_EXPECTED_TOOLS",\s*"(\d+)"', verify_mcp)
    if not match or int(match.group(1)) != tools:
        problems.append(
            "verify_mcp.py default expected count is %s, live is %d"
            % (match.group(1) if match else "missing", tools)
        )

    mcp_verify = _read(REPO / ".github" / "workflows" / "mcp-verify.yml")
    match = re.search(r'MEM20_EXPECTED_TOOLS:\s*"(\d+)"', mcp_verify)
    if not match or int(match.group(1)) != tools:
        problems.append(
            ".github/workflows/mcp-verify.yml pins %s tools, live is %d"
            % (match.group(1) if match else "missing", tools)
        )

    finance_workflow = _read(REPO / ".github" / "workflows" / "finance-model-drift.yml")
    match = re.search(
        r"\(s\['tools'\],\s*s\['domains'\]\)==\((\d+),\s*(\d+)\)",
        finance_workflow,
    )
    if not match or (int(match.group(1)), int(match.group(2))) != (tools, domains):
        problems.append(
            ".github/workflows/finance-model-drift.yml asserts %s, live is %d/%d"
            % (
                "%s/%s" % (match.group(1), match.group(2)) if match else "missing",
                tools,
                domains,
            )
        )

    return problems


def check_versions() -> list[str]:
    problems: list[str] = []
    version = _read(REPO / "VERSION").strip()
    pyproject = _read(REPO / "pyproject.toml")
    match = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)
    if not match or match.group(1) != version:
        problems.append(
            "pyproject.toml version is %s, VERSION is %s"
            % (match.group(1) if match else "missing", version)
        )

    for relative, pattern in (
        ("docs/README.md", r">\s*\*\*Version:\*\*\s*([^\s]+)"),
        ("docs/01-architecture.md", r"\*\*Version:\*\*\s*([^\s]+)"),
        ("mem20-sdk-godot/README.md", r"Server baseline:\s*mem20\s*\*\*([^*]+)\*\*"),
    ):
        text = _read(REPO / relative)
        found = re.search(pattern, text)
        if not found or found.group(1).strip() != version:
            problems.append(
                "%s states version %s, VERSION is %s"
                % (relative, found.group(1).strip() if found else "missing", version)
            )

    index_html = _read(REPO / "docs" / "index.html")
    badges = re.findall(
        r'<span class="badge">v?([0-9]+\.[0-9]+\.[0-9]+)</span>', index_html
    )
    if not badges:
        problems.append("docs/index.html carries no version badge")
    stale_badges = sorted({badge for badge in badges if badge != version})
    if stale_badges:
        problems.append(
            "docs/index.html badge says %s, VERSION is %s"
            % (", ".join("v" + badge for badge in stale_badges), version)
        )

    spec = importlib.util.spec_from_file_location("mem20_launch_gate", LAUNCH_GATE)
    if spec is None or spec.loader is None:
        problems.append("cannot load scripts/check_launch_gate.py")
        return problems
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    retired = module.retired_versions_for(version)
    if any(candidate.lstrip("v") == version.lstrip("v") for candidate in retired):
        problems.append(
            "scripts/check_launch_gate.py treats the current VERSION %s as retired: %s"
            % (version, retired)
        )
    return problems


def write_outputs(outputs: dict[Path, str]) -> list[str]:
    changed = []
    for path, text in outputs.items():
        if _write_if_changed(path, text):
            changed.append(str(path.relative_to(REPO)))
    return changed


def check_outputs(outputs: dict[Path, str]) -> list[str]:
    problems = []
    for path, text in outputs.items():
        relative = str(path.relative_to(REPO))
        if not path.is_file():
            problems.append("%s is missing; run scripts/surface_manifest.py --write" % relative)
        elif _read(path) != text:
            problems.append("%s is stale; run scripts/surface_manifest.py --write" % relative)
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="regenerate the manifest and docs")
    group.add_argument("--check", action="store_true", help="check live surface, generated files and docs")
    group.add_argument("--check-docs", action="store_true", help="offline check of docs against docs/surface.json")
    args = parser.parse_args(argv)

    if args.check_docs:
        manifest = json.loads(_read(SURFACE_JSON))
        problems = check_docs(manifest) + check_versions()
        return _report(problems, "docs and version references match the committed surface")

    live_names = live_tool_names()
    catalog = ast_catalog()
    manifest = build_manifest(catalog, live_names)
    outputs = expected_outputs(manifest, catalog)

    if args.write:
        changed = write_outputs(outputs)
        problems = check_docs(manifest) + check_versions()
        if changed:
            print("updated: %s" % ", ".join(changed))
        return _report(problems, "surface is %d tools / %d domains" % (manifest["tools"], manifest["domains"]))

    problems = check_outputs(outputs) + check_docs(manifest) + check_versions()
    return _report(problems, "surface is %d tools / %d domains" % (manifest["tools"], manifest["domains"]))


def _report(problems: list[str], success: str) -> int:
    if problems:
        print("SURFACE DRIFT (%d):" % len(problems), file=sys.stderr)
        for problem in problems:
            print("  - %s" % problem, file=sys.stderr)
        return 1
    print("OK: %s" % success)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
