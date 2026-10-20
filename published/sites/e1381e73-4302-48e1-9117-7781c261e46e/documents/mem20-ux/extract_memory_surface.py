"""Extract the memory_* tool surface from the canonical mem20 checkout.

Reads the server modules with the ast module and pulls each mt.Tool(...) call's
name, title and description, so the memory-surface grouping is derived from the
repository rather than typed by hand.

Usage:  python3 extract_memory_surface.py /tmp/mem20chk > memory_surface_raw.json
"""
import ast
import json
import pathlib
import sys

ROOTS = ("mcp", "mcp_server_dir")


def walk(root: pathlib.Path):
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        yield path, tree


def literal(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def extract(root: pathlib.Path):
    found = {}
    for path, tree in walk(root):
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = getattr(func, "attr", None) or getattr(func, "id", None)
            if name != "Tool":
                continue
            kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}
            tool_name = literal(kwargs.get("name")) if "name" in kwargs else None
            if not isinstance(tool_name, str) or not tool_name.startswith("memory_"):
                continue
            record = {
                "name": tool_name,
                "title": literal(kwargs.get("title")) or "",
                "description": literal(kwargs.get("description")) or "",
                "module": str(path),
            }
            prior = found.get(tool_name)
            if prior is None or len(record["description"]) > len(prior["description"]):
                found[tool_name] = record
    return found


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    found = extract(root)
    payload = {
        "tool_count_memory": len(found),
        "tools": [found[k] for k in sorted(found)],
    }
    json.dump(payload, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
