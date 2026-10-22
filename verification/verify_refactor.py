from pathlib import Path
import os

MCP_DIR = os.environ.get("MEM20_MCP_DIR", str(Path(__file__).resolve().parents[1] / "mcp"))
