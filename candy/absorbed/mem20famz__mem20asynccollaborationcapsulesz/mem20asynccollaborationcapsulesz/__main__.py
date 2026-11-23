import sys, json
from . import domain as d
if __name__ == "__main__":
    print(json.dumps({"ok": True, "module": d.__name__}, indent=2))
    sys.exit(0)
