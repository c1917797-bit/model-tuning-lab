"""Qualified explicit plugin entry; importing this package never touches NPU."""
import importlib.util,sys
from pathlib import Path
def register():
 p=Path(__file__).resolve().parent.parent/'worker.py'
 name='_mxr042_entry_receiver'
 if name in sys.modules:
  m=sys.modules[name]
  if Path(m.__file__).resolve()!=p:raise ValueError('foreign preloaded receiver')
 else:
  s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m
  try:s.loader.exec_module(m)
  except BaseException:sys.modules.pop(name,None);raise
 return m.register()
