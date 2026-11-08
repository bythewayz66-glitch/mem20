import os,sys
_h=os.path.dirname(os.path.abspath(__file__)); _p=os.path.abspath(os.path.join(_h,'..','..'))
if _p not in sys.path: sys.path.insert(0,_p)
for _n in list(sys.modules):
 if _n=='mem20multimodaltaskcapturez' or _n.startswith('mem20multimodaltaskcapturez.'):
  if getattr(sys.modules[_n],'__file__',None) is None: del sys.modules[_n]
