"""Private source/clock data bindings over exact030/031 stage functions."""
import hashlib,importlib.util
from pathlib import Path
START,CUT=1791916056,1792002456
def need(v,m):
 if not v:raise ValueError(m)
def load(ref,name):
 p=Path(ref['path']);raw=p.read_bytes();need(p.is_absolute()and not p.is_symlink()and len(raw)==ref['bytes']and hashlib.sha256(raw).hexdigest()==ref['sha256'],'whole exact stage donor');s=importlib.util.spec_from_file_location(name,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def view(stage,root,ref):
 need(stage in('build','numeric'),'one existing bounded stage');A=load(ref,'_mxr035_immutable_'+stage);A.P=Path(root);A.START=START;A.CUT=CUT
 old_load=A.load
 if stage=='build':
  def source_load(ref,name):
   module=old_load(ref,name)
   if name=='_mxr026_exact023_preparer':
    original=module.prepare
    def renewed(*args):
     result=original(*args);C=result[2];need(C.CUTOFF==1791922930,'immutable023 returned expected historical private clock');C.CUTOFF=CUT;return result
    module.prepare=renewed
   return module
  A.load=source_load
 old_prepare=A.prepare
 def prepare(*args):
  result=old_prepare(*args);C=result[3];E=result[4]
  need(C.CUTOFF==CUT and C.PHASE==(450 if stage=='build'else 300)and C.CLEANUP==90,'actual existing stage clock/budget, not oldrun extension')
  C.OWNER='mxr-r156-diag16-'+stage+('-038'if stage=='build'else'-039');C.ROOT=Path(root)
  for f in(C.labels,C.create_argv,C.inspect_owned):f.__globals__.update(OWNER=C.OWNER,ROOT=C.ROOT)
  need(E['Joint'].__init__.__globals__['C']is C and E['controller'].__globals__['C']is C,'unchanged functions share actual private C')
  return result
 A.prepare=prepare
 return A
