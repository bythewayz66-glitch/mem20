"""Package conftest: prefer project-local package resolution for tests."""
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_ESTATE_ROOT = os.path.dirname(_PROJECT_ROOT)

# Keep project root first for `mem20enginez.mem20enginez` inner package resolution.
# Do not delete modules aggressively; allow normal imports.
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
