import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common112 as C


def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--reviewed-template-ref');p.add_argument('--profile',choices=['smoke','full']);p.add_argument('--smoke-consumer-owner-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false}');return 0
 tr=json.loads(a.reviewed_template_ref);m=C.obj(tr);C.need(tr==C.ref(P/'SOURCE_TEMPLATE.json')and m['prepared_only']is True and m['profile']is None,'reviewed exact prepared template')
 C.need(Path(m['root'])==P and a.profile is not None,'actual deployed root and explicit frozen profile')
 for rr in m['files'].values():C.checked(rr)
 prerequisite=[]
 if a.profile=='full':
  C.need(a.smoke_consumer_owner_ref is not None,'actual released smoke independent CPU owner required before full bind')
  cr=json.loads(a.smoke_consumer_owner_ref);cv=C.obj(cr);smoke_sr=cv['source'];sm=C.obj(smoke_sr)
  C.need(cv['schema']=='bole.tree-owned-CPU/v112'and cv['primary']is None and cv['secondary']==[]and cv['resource_release_verified']is True and cv['NPU']is False,'actual released smoke consumer')
  C.need(sm['schema']==m['schema']and sm['profile']=='smoke'and sm['prepared_template']==tr and sm['files']==m['files']and sm['root']==m['root'],'exact same-math smoke source')
  report=C.obj(cv['stage_result']);nv=C.obj(cv['numeric_owner']);stage=C.obj(cv['stage_ref'])
  C.need(nv['schema']=='bole.tree-owned/v112'and nv['source']==smoke_sr and nv['primary']is None and nv['secondary']==[]and nv['stopped_retained']is True and nv['result']==cv['stage_ref'],'actual released smoke NPU owner')
  C.need(stage['schema']=='bole.tree-stage/v112'and stage['source']==smoke_sr and stage['primary']is None and stage['NPU']is True,'actual smoke stage')
  C.need(report['schema']=='bole.tree-independent/v112'and report['source']==smoke_sr and report['pass_gate']is True and not report['failures']and len(report['rows'])==6,'actual all-six smoke independent result')
  prerequisite=[cr,smoke_sr,cv['stage_result'],cv['numeric_owner'],cv['stage_ref']]
 else:C.need(a.smoke_consumer_owner_ref is None,'smoke cannot borrow future proof')
 m['prepared_only']=False;m['profile']=a.profile;m['prepared_template']=tr;m['output_root']+='/'+a.profile;m['smoke_prerequisite_refs']=prerequisite;C.window(m)
 output=P/('SOURCE_'+a.profile.upper()+'.json');C.write(output,m);print(json.dumps(C.ref(output)));return 0

if __name__=='__main__':raise SystemExit(main())
