"""Import finder for absorbed mem20*z packages.
Resolves `mem20<name>z` (and submodules) to their canonical absorbed locations.
Installed via .pth or imported explicitly; no symlinks.
"""
from __future__ import annotations

import importlib.abc
import importlib.machinery
import importlib.util
import json
import os
import sys

_MAP = None
_ROOT = "/opt/mem20"


def _load():
    global _MAP, _ROOT
    if _MAP is not None:
        return _MAP
    path = os.path.join(_ROOT, ".mem20-absorbed-map.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _ROOT = data.get("root", _ROOT)
        _MAP = data.get("mapping", {})
    except Exception:
        _MAP = {}
    return _MAP


class AbsorbedFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        mapping = _load()
        parts = fullname.split(".")
        top = parts[0]
        if top not in mapping:
            return None
        base = mapping[top]
        if len(parts) == 1:
            # top-level package
            init = os.path.join(base, "__init__.py")
            if os.path.isfile(init):
                return importlib.util.spec_from_file_location(
                    fullname, init,
                    submodule_search_locations=[base],
                )
            # namespace-like or single file? try as dir
            if os.path.isdir(base):
                return importlib.machinery.ModuleSpec(fullname, None, is_package=True)
            return None
        # submodule/subpackage
        subpath = os.path.join(base, *parts[1:])
        # package?
        init = os.path.join(subpath, "__init__.py")
        if os.path.isfile(init):
            return importlib.util.spec_from_file_location(
                fullname, init,
                submodule_search_locations=[subpath],
            )
        mod = subpath + ".py"
        if os.path.isfile(mod):
            return importlib.util.spec_from_file_location(fullname, mod)
        # maybe directory without __init__? treat as namespace package
        if os.path.isdir(subpath):
            spec = importlib.machinery.ModuleSpec(fullname, None, is_package=True)
            spec.submodule_search_locations = [subpath]
            return spec
        return None


def install():
    # avoid duplicates
    for f in sys.meta_path:
        if isinstance(f, AbsorbedFinder):
            return
    sys.meta_path.insert(0, AbsorbedFinder())


install()
