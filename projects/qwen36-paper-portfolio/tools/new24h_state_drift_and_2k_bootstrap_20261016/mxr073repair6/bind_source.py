"""Exclusive typed actual044+043 bootstrap -> newlong source; no future PASS."""
import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import admission047 as A

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-ref');p.add_argument('--prerequisite-plan-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 tr,pr=map(json.loads,(a.template_ref,a.prerequisite_plan_ref));m=A.obj(tr);plan=A.obj(pr)
 A.need(m['root']==str(P)and m['new_prerequisites']is None and m['source_template']is True,'unbound new source only')
 for r in m['files'].values():A.checked(r)
 import authority_contract
 authority_contract.verify(m['authority_ref'])
 gate=A.consume(plan);short=A.obj(plan['short_source']);binding=short['files']['prefix_binding.py']
 A.need((binding['bytes'],binding['sha256'])==(5811,'96c345308723ebf32e6817b2289466aaca6ca964897abf97fa23941da6ac8d8d'),'exact realQwen copied-method helper')
 m.update(new_prerequisites=plan,actual_short_admission=dict(source=plan['short_source'],result=plan['short_owner'],terminal=plan['short_terminal'],bootstrap_not044_numeric=True),actual_core_binding_ref=binding,source_template=False,activation_template_ref=tr,READY=False,NPU_ready=False)
 refs={r['path']:r for r in m['dependencies']}
 for r in[tr,pr,binding,*gate['readset'],*short['files'].values()]:
  if r['path']in refs:A.need(refs[r['path']]==r,'same immutable source reference at same path')
  refs[r['path']]=r
 m['dependencies']=list(refs.values());target=P/'SOURCE_MANIFEST.json'
 with target.open('x',encoding='utf8')as f:json.dump(m,f,sort_keys=True,indent=2);f.write('\n')
 b=target.read_bytes();print(json.dumps(dict(path=str(target),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),NPU=False,long_qualified=False)));return 0
if __name__=='__main__':raise SystemExit(main())
