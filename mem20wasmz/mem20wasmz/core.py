import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)
from mem20core.fixes import *  # noqa: F401,F403
from mem20core.fixes import patch as _patch; _patch()

# Override load_roadmap to use mem20wasmz's roadmap.json
from pathlib import Path
import json

def load_roadmap(path=None):
    """Load mem20wasmz's roadmap.json instead of mem20core's."""
    p = Path(path or Path(__file__).with_name('roadmap.json'))
    return json.loads(p.read_text())
