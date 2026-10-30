"""Assemble vendored runtime from parts."""
from pathlib import Path
_p = Path(__file__).resolve().parent
_src = (_p/"_rt_part1.py").read_text() + (_p/"_rt_part2.py").read_text()
exec(compile(_src, str(_p/"runtime_assembled.py"), "exec"), globals())
