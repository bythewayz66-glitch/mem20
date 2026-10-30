"""Reality-to-software compiler: ingest real-world specs into code."""
import re


def ingest(spec_text):
    # parse simple key: value lines
    out = {}
    for line in spec_text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def compile_to_code(spec, lang="python"):
    name = spec.get("name", "app")
    if lang == "python":
        return f"class {name.title()}:\n    pass\n"
    return f"// {name}"


def validate_spec(spec):
    required = ["name"]
    missing = [r for r in required if r not in spec]
    return {"valid": not missing, "missing": missing}


def diff_spec(old, new):
    changes = {}
    for k in set(old) | set(new):
        if old.get(k) != new.get(k):
            changes[k] = {"from": old.get(k), "to": new.get(k)}
    return changes


def compile_health(spec):
    return {"fields": len(spec), "valid": "name" in spec}
