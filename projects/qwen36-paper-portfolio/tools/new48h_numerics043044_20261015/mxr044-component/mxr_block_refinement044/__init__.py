"""Unique opt-in plugin name; never enables legacy diagnostic entrypoints."""
def register():
 import importlib.util,os,sys
 from pathlib import Path
 if os.environ.get('MXR_BLOCK_REFINEMENT044_ENABLE')!='1':return None
 root=Path(__file__).resolve().parent.parent;name='_mxr044_source_bound_installer'
 if name not in sys.modules:
  sys.path.insert(0,str(root));spec=importlib.util.spec_from_file_location(name,root/'observerless_install.py');module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
 return sys.modules[name].install()
