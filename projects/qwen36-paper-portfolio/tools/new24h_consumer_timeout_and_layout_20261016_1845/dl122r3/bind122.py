import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import api122 as A
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-ref');p.add_argument('--production-source-ref');p.add_argument('--production-qualification-ref');p.add_argument('--health-owner-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 tr=json.loads(a.template_ref);m=A.obj(tr);A.need(m['root']==str(P)and m['prepared_only']is True,'own prepared template')
 for n,r in m['files'].items():A.need(r==A.ref(P/n),'actual declared own file')
 m.update(prepared_only=False,prepared_template=tr,production_source_ref=json.loads(a.production_source_ref),production_qualification_ref=json.loads(a.production_qualification_ref))
 A.qualify_production(m)
 if a.health_owner_ref:
  hr=json.loads(a.health_owner_ref);h=A.obj(hr);v=A.obj(h['source']);A.need(v['files']==m['files']and v['stage']=='validation'and v['production_source_ref']==m['production_source_ref'],'same exact runtime health source')
  report=A.obj(h['numeric']);A.health_gate(h,report,h['source'],m['production_source_ref'],m['production_qualification_ref']);A.health_input_join(m,report);cleanup=A.obj(h['cleanup']);A.need(cleanup['stopped']is True and cleanup['retained']is True and cleanup['errors']==[],'actual health owner cleanup');m.update(stage='pair',health_owner_ref=hr)
 else:m.update(stage='validation',health_owner_ref=None)
 A.need(a.output.parent==P and a.output.name in('VALIDATION_SOURCE.json','PAIR_SOURCE.json')and not a.output.exists(),'unique typed bound source output')
 A.need((a.output.name=='PAIR_SOURCE.json')==(m['stage']=='pair'),'no validation source masquerading pair')
 A.write(a.output,m);print(json.dumps(A.ref(a.output)));return 0
if __name__=='__main__':raise SystemExit(main())
