"""Bind actual completed components to ONE bounded real-worker diagnostic."""
import argparse,json,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C,component_gate as G,predecessor118t as V


def readset(sr):
 m=C.obj(sr);C.need(m['prepared_only']is False and m['schema']=='bole.actual-model-three-node-entry/source-prep-v1','actual bound model diagnostic source')
 G.consume(C,m['component_refs'],gdn_math=m['files']['core112.py'],paged_math=m['files']['adapter.py']);V.join(C,dict(actual_118c=m['actual118c']))
 refs=[sr,m['prepared_template'],m['authority_ref'],*m['files'].values()]
 for kind,p in m['component_refs'].items():
  s=C.obj(p['source']);no=C.obj(p['numeric_owner']);co=C.obj(p['consumer_owner'])
  refs.extend([*p.values(),*s['files'].values(),s['prepared_template'],no['result'],co['stage_result']])
  if kind=='paged':
   stage=C.obj(no['result']);refs.extend([stage['result'],stage['actual_abi_ref']])
 refs.extend(m['actual118c'].values())
 refs.append(C.obj(m['actual118c']['capture'])['actual_device_abi_ref'])
 unique={}
 for r in refs:
  C.checked(r)
  if r['path']in unique:C.need(unique[r['path']]==r,'no conflicting source Ref for one path')
  unique[r['path']]=r
 return list(unique.values())


def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--reviewed-template-ref');p.add_argument('--component-refs-json');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 C.need(a.reviewed_template_ref and a.component_refs_json,'explicit actual reviewed source and component receipts')
 tr=json.loads(a.reviewed_template_ref);m=C.obj(tr)
 C.need(tr==C.ref(P/'SOURCE_TEMPLATE.json')and m['root']==str(P)and m['prepared_only']is True,'actual deployed immutable reviewed model template')
 for r in m['files'].values():C.checked(r)
 authority=C.obj(m['authority_ref']);C.need(authority['start_epoch']==1792226600 and authority['cutoff_epoch']==1792313000 and time.time()+3600<1792313000,'unchanged actual fixed window must contain whole model budget')
 component=json.loads(a.component_refs_json)
 G.consume(C,component,gdn_math=m['files']['core112.py'],paged_math=m['files']['adapter.py']);V.join(C,dict(actual_118c=m['actual118c']))
 m['prepared_only']=False;m['prepared_template']=tr;m['component_refs']=component
 output=P/'SOURCE_BOUND.json';sr=C.write(output,m);readset(sr);print(json.dumps(sr));return 0


if __name__=='__main__':raise SystemExit(main())
