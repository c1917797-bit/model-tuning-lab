"""Only source-owned shared phase custody; no new executor/authority."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def need(v,s):
 if not v:raise ValueError(s)
def once(raw,a,b):
 s=raw.decode();need(s.count(a)==1,'one exact phase seam '+a[:70]);return s.replace(a,b,1).encode()
def adapt(files):
 out=dict(files)
 out['shared_phase_clock.py']=(ROOT/'shared_phase_clock.py').read_bytes()
 out['contract090.py']=once(out['contract090.py'],
  "  FSV.execution_window(m,clock=True,require_phase=True)",
  "  import shared_phase_clock as PHASE_CLOCK\n  PHASE_CLOCK.admission(sys.modules[__name__],sr,m)")
 out['host_service.py']=once(out['host_service.py']," phase_admission(C,entry_start)",
  " phase_admission(C,entry_start)\n import shared_phase_clock as PHASE_CLOCK\n PHASE_CLOCK.bind_parent(C,sr,m,entry_start)")
 out['external025.py']=once(out['external025.py']," return dict(HOME=",
  " import shared_phase_clock as PHASE_CLOCK\n return dict(PHASE_CLOCK.environment(e),HOME=")
 out['owned_create.py']=once(out['owned_create.py'],
  " import contract090 as C,guest_readset_coverage as GC\n required=GC.required(C,sr,readset)",
  " import contract090 as C,guest_readset_coverage as GC\n import shared_phase_clock as PHASE_CLOCK\n PHASE_CLOCK.prepare_mount(C,sr,ctl,role,mounts)\n required=GC.required(C,sr,readset)")
 out['owned_create.py']=once(out['owned_create.py']," c.write(leaf/'GUEST_CPU.json',cv);return ref",
  " c.write(leaf/'GUEST_CPU.json',cv)\n PHASE_CLOCK.publish(C,sr,ctl,x,ref)\n return ref")
 delta={n:dict(before=files.get(n),after=b)for n,b in out.items()if files.get(n)!=b}
 return out,delta
def inverse(files,delta):
 out=dict(files)
 for n,r in delta.items():
  need(out[n]==r['after'],'exact phase inverse '+n)
  if r['before']is None:del out[n]
  else:out[n]=r['before']
 return out
def manifest(m):
 import copy,shared_phase_clock as P
 out=copy.deepcopy(m);need('phase_clock_contract'not in out,'new phase protocol only')
 out['phase_clock_contract']=dict(P.CONTRACT);return out
