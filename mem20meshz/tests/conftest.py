import os, sys
_here = os.path.dirname(os.path.abspath(__file__))
_project = os.path.abspath(os.path.join(_here, '..'))
if _project not in sys.path:
    sys.path.insert(0, _project)
for _n in list(sys.modules):
    if _n == 'mem20meshz' or _n.startswith('mem20meshz.'):
        _m = sys.modules[_n]
        if getattr(_m, '__file__', None) is None:
            del sys.modules[_n]
