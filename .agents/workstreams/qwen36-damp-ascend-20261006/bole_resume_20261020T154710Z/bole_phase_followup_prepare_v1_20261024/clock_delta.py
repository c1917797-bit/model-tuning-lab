"""Distinct related160/formal clock successor; parent math and authority schemas intact."""
import hashlib
WINDOW=(1792828303,1792914703)
def need(v,s):
 if not v:raise ValueError(s)
def once(raw,a,b):
 s=raw.decode();need(s.count(a)==1,'one exact followup clock seam');return s.replace(a,b,1).encode()
def helper(raw):
 # Formal manifests retain a historical qualification_authority_ref. Never use
 # that slot for formal execution: source-owned formal schema selects its own.
 s=raw.decode()
 need(s.count("m['qualification_authority_ref']")==2,'exact two custody authority operands')
 s=s.replace("m['qualification_authority_ref']","authority_reference(m)")
 marker='def clock_contract(C,m):'
 need(s.count(marker)==1,'one source clock contract')
 s=s.replace(marker,"""def authority_reference(m):
 if 'formal_source_schema'in m:
  need(m['formal_source_schema']=='bole.current32k-fixed1024-whole/v1','exact formal clock domain')
  r=m.get('formal_authority_ref')
 else:
  need(m.get('qualification_source_schema')in('bole.fastpath-short8-qualification-whole-source/v1','bole.fastpath-32k160-lossless-whole-source/v1'),'exact qualified clock domain')
  r=m.get('qualification_authority_ref')
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'source-specific actual authority Ref')
 return r
def current_window(a):
 need((a['start_epoch'],a['cutoff_epoch'])=="""+repr(WINDOW)+""",'exact approved new campaign; no implicit renewal')
 return a
"""+marker)
 s=s.replace('authority=V.execution_window(m,clock=True,require_phase=False)','authority=current_window(V.execution_window(m,clock=True,require_phase=False))')
 s=s.replace('a=V.execution_window(m,clock=True,require_phase=False)','a=current_window(V.execution_window(m,clock=True,require_phase=False))')
 s=s.replace('return V.execution_window(m,clock=True,require_phase=True)','return current_window(V.execution_window(m,clock=True,require_phase=True))')
 return s.encode()
def adapt(files,domain,adapter,helper_bytes):
 need(domain in('related160','formal'),'explicit distinct source domain')
 before=dict(files)
 out,phase_delta=adapter.adapt(files)
 need(adapter.inverse(out,phase_delta)==before,'exact original four shared custody seams')
 out['shared_phase_clock.py']=helper(helper_bytes)
 if domain=='formal':
  old='1792740953<=a[\'start_epoch\']<a[\'cutoff_epoch\']<=1792827353'
  new="(a['start_epoch'],a['cutoff_epoch'])=="+repr(WINDOW)
  # Both runtime aliases are original formal validator bytes.
  for name in('formal_validator.py','followup_source_validate.py'):
   out[name]=once(out[name],old,new)
  need(out['formal_validator.py']==out['followup_source_validate.py'],'one actual formal authority implementation')
 delta={n:dict(before=before.get(n),after=b)for n,b in out.items()if before.get(n)!=b}
 allowed={'contract090.py','host_service.py','external025.py','owned_create.py','shared_phase_clock.py'}
 if domain=='formal':allowed|={'formal_validator.py','followup_source_validate.py'}
 need(set(delta)==allowed,'only exact clock/authority binding deltas')
 return out,delta
def inverse(files,delta):
 out=dict(files)
 for n,r in delta.items():
  need(out[n]==r['after'],'exact clock inverse')
  if r['before']is None:out.pop(n)
  else:out[n]=r['before']
 return out
