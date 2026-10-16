"""MAIN-only source binding. Missing actual model/component evidence refuses."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P));import qualification106 as Q
def write(p,v):
 with p.open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for n in('template-ref','model-source-ref','model-owner-ref'):p.add_argument('--'+n)
 a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 tr=json.loads(a.template_ref);Q.need(Q.ref(P/'SOURCE_TEMPLATE.json')==tr,'actual reviewed106 template')
 m=Q.obj(tr);Q.need(m['root']==str(P)and m['prepared_only']is True and m['default_enabled']is False,'immutable prepared source')
 for r in m['files'].values():Q.checked(r)
 ms=json.loads(a.model_source_ref);mo=json.loads(a.model_owner_ref);model=Q.obj(ms)
 m.update(prepared_only=False,prepared_template=tr,model_source_ref=ms,model_owner_ref=mo,component_source_ref=model['bridge024_source_ref'],component_owner_ref=model['bridge024_owner_ref'],library_ref=model['library_ref'],operator_schema=Q.obj(model['plugin_source'])['operator_schema'])
 Q.model_gate(m) # actual original gates, before source publication
 write(P/'SOURCE_MANIFEST.json',m);sr=Q.ref(P/'SOURCE_MANIFEST.json');q=Q.consume(sr);write(P/'QUALIFICATION106.json',q);qr=Q.ref(P/'QUALIFICATION106.json')
 print(json.dumps(dict(source=sr,qualification=qr,execution_admitted=True,performance_measured=False,task_scores_measured=False,NPU=False)));return 0
if __name__=='__main__':raise SystemExit(main())
