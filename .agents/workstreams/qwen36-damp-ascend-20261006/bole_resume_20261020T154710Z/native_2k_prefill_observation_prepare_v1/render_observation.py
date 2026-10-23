"""Pure exact native3 source delta. No bind/authority/device operation."""
import argparse,ast,copy,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
WS=HERE.parent
PARENT=WS/'bound-native-ar-common-v3_20261022T213000Z'
TEMPLATE={'path':str(PARENT/'SOURCE_TEMPLATE.json'),'bytes':1886163,'sha256':'1b5e50c4369a8b27b4915fe26bb1c19b9c67ba88da6e4e76f3293a907917a111'}
ROOT=WS/'bound-native-2k-prefill-observation-v1'
OUT=Path('/opt/host/vnf/austinov/run-native-2k-prefill-observation-v1')
DECL=dict(schema='native.2k-prefill-observation/v1',input_tokens=2048,output_tokens=1,request_count=1,concurrency=1,
 synthetic=True,screening_only=True,no_general_gain_claim=True,numerical_qualified=False,formal_performance=False,task_accuracy=False)
OWN=('native_2k_prefill_observer.py','native_2k_client.py','consume_native_2k.py')
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 p=Path(r['path']);need(set(r)=={'path','bytes','sha256'}and p.is_absolute()and not any(x.is_symlink()for x in(p,*p.parents))and ref(p)==r,'exact ordinary source Ref');return p
def once(s,a,b,count=1):
 need(s.count(a)==count,'exact reviewed fragment count: '+a);return s.replace(a,b)
def numbers(s,old,new,count):
 nodes=[x for x in ast.walk(ast.parse(s))if isinstance(x,ast.Constant)and type(x.value)is int and x.value==old]
 need(len(nodes)==count,'fixed numeric source-delta count')
 lines=s.splitlines(keepends=True);offset=[0]
 for l in lines:offset.append(offset[-1]+len(l))
 for x in sorted(nodes,key=lambda n:(n.lineno,n.col_offset),reverse=True):
  a=offset[x.lineno-1]+x.col_offset;b=offset[x.end_lineno-1]+x.end_col_offset;s=s[:a]+str(new)+s[b:]
 return s
def derive(name,s):
 if name=='worker_entry.py':
  s=once(s,'BOLE_MODEL_OBJECT_AUDIT_ENABLE','NATIVE_2K_PREFILL_OBSERVE_ENABLE',2)
 elif name=='input_identity.py':
  s=numbers(s,131,2048,6);s=once(s,'exact actual131-token prompt','exact actual2048-token synthetic observation prompt')
 elif name=='bole_performance_profile.py':
  for a,b in [('"input_tokens": 131','"input_tokens": 2048'),('"output_tokens": 8','"output_tokens": 1'),('"warmup_requests": 1','"warmup_requests": 0'),
              ('input_tokens: int = 131','input_tokens: int = 2048'),('output_tokens: int = 8','output_tokens: int = 1'),('warmup_requests: int = 1','warmup_requests: int = 0'),
              ('only reviewed C1/131/1024, two-generation scope','only native C1/2048/1 single-prefill observation')]:s=once(s,a,b)
 elif name=='server090.py':
  s=once(s,"DENSE_OPPORTUNITY090_RECEIPT_ROOT=str(receipt),\n    PYTHONPATH=", "DENSE_OPPORTUNITY090_RECEIPT_ROOT=str(receipt),\n    NATIVE_2K_PREFILL_OBSERVE_ENABLE='1',\n    PYTHONPATH=")
  s=once(s,"'BOLE_', 'BOLE111_', 'DENSE_OPPORTUNITY090_')","'BOLE_', 'BOLE111_', 'DENSE_OPPORTUNITY090_', 'NATIVE_2K_')")
  s=once(s,"  identity_journal.install_frontend(sr)\n sys.argv=",
   "  identity_journal.install_frontend(sr)\n else:\n  C.need(C.ref(P/'native_2k_prefill_observer.py')==m['files']['native_2k_prefill_observer.py'],'source-bound native frontend observer before import')\n  import native_2k_prefill_observer as N2\n  C.need(C.ref(N2.__file__)==m['files']['native_2k_prefill_observer.py'],'no cached foreign native frontend observer')\n  N2.install_frontend(C,sr)\n sys.argv=")
 elif name=='native_receipt090.py':
  s=once(s,' ordinal=0\n',""" import contract090 as C
 m=C.obj(sr);need(C.ref(Path(__file__).parent/'native_2k_prefill_observer.py')==m['files']['native_2k_prefill_observer.py'],'native observer source before import')
 import native_2k_prefill_observer as N2
 need(C.ref(N2.__file__)==m['files']['native_2k_prefill_observer.py'],'no cached foreign native observer')
 N2.register(C,sr)
 ordinal=0
""")
  s=once(s,'observed_epoch=time.time(),tensor_capture=False','observed_epoch=time.time(),native_2k_observation=N2.status(C,sr),tensor_capture=False')
 elif name=='performance_host.py':
  s=once(s,"'input_tokens': 131, 'output_tokens': 8, 'concurrency': 1,","'input_tokens': 2048, 'output_tokens': 1, 'concurrency': 1,")
  s=once(s,"'warmup_requests': 1, 'measured_requests': 1,","'warmup_requests': 0, 'measured_requests': 1,")
  s=once(s,"'AFTER-PERFORMANCE-BARRIER'","'AFTER-NATIVE2K-PREFILL'")
 elif name=='performance_client_consumer.py':
  s=once(s,"  return NA.consume(C=C,source=source,manifest=manifest,client_output=client_output,receipt_root=receipt_root)",
   "  import consume_native_2k as N2\n  C.need(C.ref(N2.__file__)==manifest['files']['consume_native_2k.py'],'source-owned native2k independent consumer')\n  return N2.consume(C=C,source=source,manifest=manifest,client_output=client_output,receipt_root=receipt_root)")
 return s
CHANGED=('worker_entry.py','input_identity.py','bole_performance_profile.py','server090.py','native_receipt090.py','performance_host.py','performance_client_consumer.py')
def render():
 m=json.loads(checked(TEMPLATE).read_bytes());need(m['performance_arm']=='native_ar'and m['prepared_only']is True,'actual prepared native3, never observerOFF')
 for r in m['files'].values():checked(r)
 texts={n:derive(n,checked(m['files'][n]).read_text())for n in CHANGED}
 for n in OWN:texts[n]=(HERE/n).read_text()
 # These gates are INTENTIONALLY unchanged: current131/expired lineage must
 # refuse until MAIN binds a separately reviewed native2k owner/clock seam.
 for n in('contract090.py','bind_model.py','performance_validate.py'):
  texts[n]=checked(m['files'][n]).read_text()
 for n,s in texts.items():compile(s,n,'exec')
 plan=dict(schema='native.2k-prefill-observation-source-plan/v1',parent=TEMPLATE,source_root=str(ROOT),output_root=str(OUT),
  declaration=DECL,performance_arm='native_ar',native_MTP=False,num_speculative_tokens=0,common_configuration=m['common_collective_configuration'],
  original_owner='host_service.py/performance_host.run',phase_seconds=3600,cleanup_seconds=180,
  unchanged_failclosed_gates=['contract090.py','bind_model.py','performance_validate.py'],
  pending=['new native2k source/clock owning gate and MAIN exact source review','new limited user window and bound authority','whole input_processor Ref and completion_serving Ref bound/checked in same image','same-image no-card checks','fresh physical4-7 mapping/owner inspection','actual native NPU observation and raw joint byte accounting'],
  source_complete=False,source_bound_ref=None,authority_ref=None,MAIN_review_ref=None,sameimage_preflight_ref=None,
  NPU=False,numerical_qualified=False,formal_performance=False,task_accuracy=False)
 return texts,plan
def require_complete(plan):
 need(plan['source_complete']is True and all(plan[k]is not None for k in('source_bound_ref','authority_ref','MAIN_review_ref','sameimage_preflight_ref')),'native2k source/window/image admission incomplete; no device or source bind by preparation')
 return True
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--review',action='store_true');a=p.parse_args()
 if not a.review:print('{"enabled":false,"NPU":false}');return 0
 texts,plan=render();print(json.dumps(dict(plan=plan,rendered=[dict(name=n,bytes=len(s.encode()),sha256=hashlib.sha256(s.encode()).hexdigest())for n,s in texts.items()]),sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
