"""Runtime compatibility engine: check version/env compatibility."""
import sys, platform


def check_python(min_version=(3,11)):
    v = sys.version_info[:2]
    return v >= min_version


def check_deps(deps, installed):
    missing = [d for d in deps if d not in installed]
    return {"ok": not missing, "missing": missing}


def compatibility_report(env, requirements):
    report = {}
    report["python_ok"] = check_python(requirements.get("python", (3, 11)))
    report["deps"] = check_deps(requirements.get("deps", []), env.get("installed", []))
    report["platform"] = platform.system()
    report["compatible"] = report["python_ok"] and report["deps"]["ok"]
    return report


def suggest_fixes(report):
    fixes = []
    if not report.get("python_ok"):
        fixes.append("upgrade python")
    for m in report.get("deps", {}).get("missing", []):
        fixes.append(f"install {m}")
    return fixes
