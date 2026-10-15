"""Reuse the actual042 source-bound Controller/Joint; no new resource framework."""
import json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common as K
def prepare(sr,started):
 m=K.source(sr);donor=K.obj(m['owned042_source']);D=K.load(donor['files']['mainhost.py'],'_owned044_actual042_host')
 base,refs,C,E,O,old,bm,selection=D.prepare(m['owned042_source'],started)
 component=K.obj(m['component044_source']);owner=K.obj(component['actual042_owner']);probe=K.obj(owner['probe'])
 K.need(owner['schema']=='mxr.saved-frame-owned/v042'and owner['source']==m['owned042_source']and owner['primary']is None and owner['secondary']==[]and owner['released']is True and not owner['cpu_preflight'],'real completed042 owned raw producer')
 K.need(probe['source']==m['owned042_source']and probe['primary']is None and probe['candidate_hits']==18 and len(probe['raws'])==9,'actual042 real16/40 seed source')
 K.need(component['schema']=='mxr.observerless-source/v1'and component['actual042_source']==m['owned042_source']and component['default_enabled']is False and component['budgets']==m['component_budgets'],'complete frozen044 callback and original budgets')
 rows=[*refs,sr,*m['files'].values(),m['component044_source'],*component['files'].values(),component['actual042_owner'],owner['probe'],*probe['raws'],component['original_metrics']]
 refs=[];seen={}
 for r in rows:
  K.checked(r);K.need(r['path']not in seen or seen[r['path']]==r,'unambiguous combined immutable readset')
  if r['path']not in seen:refs.append(r);seen[r['path']]=r
 C.input_refs=lambda unused:refs;C.ROOT=P;C.OWNER='mxr-block-refinement-owned044'
 for f in(C.labels,C.create_argv,C.inspect_owned):f.__globals__.update(ROOT=P,OWNER=C.OWNER,PHYSICAL=4)
 K.load(m['files']['environment.py'],'_owned044_env').install(C)
 m.update(_base=base,_probe_contract=K.load(m['files']['probe_contract.py'],'_owned044_probe_contract'),_actual_lifecycle_integration=base['_actual_lifecycle_integration'],_actual_environment_cold=base['_actual_environment_cold'])
 return m,refs,C,E,O,old,dict(bm,numeric_script=m['files']['replay.py']),selection
