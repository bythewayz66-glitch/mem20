import os, sys
_here=os.path.dirname(os.path.abspath(__file__)); _p=os.path.abspath(os.path.join(_here,'..','..'))
if _p not in sys.path: sys.path.insert(0,_p)
for _n in list(sys.modules):
    if _n=='mem20modalitybridgez' or _n.startswith('mem20modalitybridgez.'):
        if getattr(sys.modules[_n],'__file__',None) is None: del sys.modules[_n]
