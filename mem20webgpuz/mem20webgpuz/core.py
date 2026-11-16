"""Back-compat shim: the implementation moved to the package modules."""
from . import *  # noqa: F401,F403
from . import __all__ as _all
from .cli import main as cli
__all__ = list(_all) + ["cli"]
