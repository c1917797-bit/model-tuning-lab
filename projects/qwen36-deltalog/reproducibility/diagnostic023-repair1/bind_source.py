"""No-device one-shot binder to actual022 lightweight owned certificate API."""
import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from qwen36_deltalog_service import admission as A
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-sha256')
 for name in('composite-api-ref','composite-source-ref','composite-certificate-ref','composite-cpu-owner-ref'):p.add_argument('--'+name)
 a=p.parse_args()
 if not a.execute:print('disabled');return 0
 tr=A.ref(P/'SOURCE_TEMPLATE.json');A.need(tr['sha256']==a.template_sha256,'MAIN reviewed template')
 m=A.obj(tr);A.need(m['prepared_only']is True and m['root']==str(P),'deployed actual023 root')
 fields={k:json.loads(getattr(a,k))for k in('composite_api_ref','composite_source_ref','composite_certificate_ref','composite_cpu_owner_ref')}
 A.need(fields['composite_api_ref']==m['composite_api_ref'],'only source-reviewed actual022 API, no replacement verifier')
 for r in fields.values():A.need(A.ref(r['path'])==r,'actual immutable external admission inputs')
 bound=dict(m,**fields,prepared_only=False,prepared_template=tr)
 candidate=P/'BOUND_CANDIDATE_SOURCE.json';final=P/'SOURCE_MANIFEST.json'
 A.need(not candidate.exists()and not final.exists(),'new one-shot source binding, no overwrite')
 with candidate.open('x',encoding='utf8')as f:json.dump(bound,f,sort_keys=True,allow_nan=False);f.write('\n')
 sr=A.ref(candidate);ad,_=A.consume(sr,bound['composite_source_ref'])
 A.need('torch_npu'not in sys.modules,'binder must remain noNPU backend')
 with final.open('xb')as f:f.write(candidate.read_bytes())
 print(json.dumps(dict(source=A.ref(final),component_only=True,model_ready=False,performance_ready=False,NPU=False)))
 return 0
if __name__=='__main__':raise SystemExit(main())
