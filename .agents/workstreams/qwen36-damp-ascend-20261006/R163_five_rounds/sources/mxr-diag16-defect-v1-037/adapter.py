"""Private instance adaptation of exact original MXRSolve; no global monkeypatch."""
import ctypes,hashlib,importlib.util,json,os,sys,types
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and r['bytes']>0,'strict nonnull Ref3');p=Path(r['path']);need(p.is_absolute()and p.is_file()and not p.is_symlink(),'ordinary exact source/library');b=p.read_bytes();need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'whole immutable bytes');return b
def load_old(m):
 # Namespace package with genuine original file paths; never overwrite mxr_capture.
 name='_mxr025_exact_original';pkg=types.ModuleType(name);pkg.__path__=[str(Path(m['dependencies']['old_solve']['path']).parent)]
 need(name not in sys.modules,'one cold private original namespace');sys.modules[name]=pkg
 for role,leaf in(('old_capture','capture'),('old_solve','solve')):
  r=m['dependencies'][role];checked(r);s=importlib.util.spec_from_file_location(name+'.'+leaf,r['path']);v=importlib.util.module_from_spec(s);sys.modules[s.name]=v;s.loader.exec_module(v);need(Path(v.__file__).resolve()==Path(r['path']),'real source provenance')
 return sys.modules[name+'.solve']
def instances(torch,sr,br,device):
 need(os.environ.get('MXR_Y16_EXPERIMENT_ENABLE')=='1','explicit new variant opt-in')
 m=json.loads(checked(sr));b=json.loads(checked(br));need(m['schema']=='mxr.y16.compensated-source/v1'and m['root']==str(P)and m['default_enabled']is False and m['window']==dict(start=1791916056,cutoff=1792002456)and b['schema']=='mxr.y16.compensated-build/v1'and b['source']==sr and b['status']=='compiled_no_device'and b['NPU']is False and b['Devices']==[]and b['error']is None and not b['secondary'],'actual source-qualified new no-device build, not numerical PASS')
 for r in[*m['files'].values(),*m['dependencies'].values()]:checked(r)
 need(b['header_refs_before']==b['header_refs_after'],'actual build header closure')
 for r in b['header_refs_after'].values():checked(r)
 checked(b['library']);old=load_old(m);original=old.MXRSolve(torch,m['author_root'],m['dependencies']['old_binary']['path'],device)
 lib=ctypes.CDLL(b['library']['path']);variants={}
 for mode,symbol in(('control','call_mxr_y16_control'),('compensated','call_mxr_y16_compensated')):
  fn=getattr(lib,symbol);fn.argtypes=list(original.lib.call_kernel.argtypes);fn.restype=None
  need(len(fn.argtypes)==9,'original exact9argument ABI')
  new=old.MXRSolve.__new__(old.MXRSolve);new.__dict__.update(original.__dict__);new.lib=types.SimpleNamespace(call_kernel=fn);new._experimental_library_handle=lib
  new.experiment_identity=dict(source=sr,build=br,library=b['library'],symbol=symbol,mode=mode,original_identity=original.identity)
  need(new.launch.__func__ is old.MXRSolve.launch and new.eager.__func__ is old.MXRSolve.eager,'unchanged exact original launch/input/dtype/graph refusal')
  variants[mode]=new
 checked(b['library']);return original,variants['control'],variants['compensated']
