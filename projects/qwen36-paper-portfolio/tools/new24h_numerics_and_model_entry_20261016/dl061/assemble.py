"""Mechanical thin successor generator. No execution or remote operations."""
import ast,hashlib,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parent
BASE=P.parent/'deltalog-diagnostic-bridge-owned-new48h-20261015-035-repair4'
OLD='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-diagnostic-bridge-owned-new48h-v1-035-repair4'
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-split-scale-numeric-new24h-v1-061'
OUTPUT='/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061'
SEED=2610165101
EDITS={}
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,s):
 p=P/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(s.replace('\r\n','\n').encode())
def edit(n,changes):
 s=(P/n).read_text(encoding='utf8')
 for a,b in changes:
  if a not in s:raise ValueError('missing exact seam '+n+':'+a[:80])
  s=s.replace(a,b)
  EDITS.setdefault(n,[]).append([a,b])
 put(n,s)
def main():
 # Unmodified inherited controls remain visible, including historical tests.
 for p in BASE.rglob('*'):
  if p.is_file()and p.suffix in('.py','.json','.md')and p.name not in('BYTE_EXACT_DELIVERY.json','SOURCE_TEMPLATE.json','COMMANDS.json'):
   n=p.relative_to(BASE);put(n,p.read_text(encoding='utf8').replace(OLD,ROOT))
 for n in('precast.py','direct_round.py'):
  put(n,(P.parent/'deltalog-precast-empirical-new48h-20261015-016'/n).read_text(encoding='utf8'))
 edit('producer.py',[("admission=V.configure(sr,lr,explicit=True);h=", "admission=V.configure(sr,lr,explicit=True);import sidecar_capture;sidecar=sidecar_capture.install(torch,V,m,C.checked);h="),
  ("def save(name,value):\n  nonlocal used", "import raw_codec\n store=raw_codec.Store(torch,out,m['resources']['raw_cap_bytes'])\n def save(name,value):\n  nonlocal used\n  rr=store.write(out/name,value);used=store.used;return rr\n def legacy_save_unused(name,value):\n  nonlocal used"),
  ("def emit(name,**fields):", "sidecar.sink=save\n def emit(name,**fields):"),
  ("steps=a.steps,records=records,events=events", "steps=a.steps,records=records,actual_sidecar_records=sidecar.records,actual_mixed_sidecar_records=sidecar.mixed_records,boundary_controls=boundary_controls,events=events"),
  ("try:\n  with F.native_pcp_context(torch):", "boundary_controls=[]\n try:\n  import npu_controls\n  boundary_controls=npu_controls.run(torch,h,sidecar)\n  with F.native_pcp_context(torch):"),
  ("value030=snapshot030();value030['initial_anchor_ref']=self.initial_anchor_ref;return value030", "value030=snapshot030();value030['initial_anchor_ref']=self.initial_anchor_ref;return value030")])
 edit('qwen36_deltalog_fresh/native_fixture.py',[(str(260815535),str(SEED)),
  ("value=_route(torch,legacy,*args,**kwargs)","value=_route(torch,legacy,*args,**kwargs)"),
  ('if captures is not None:captures.setdefault("decode",[]).append(dict(before=before,inputs=args_cpu,output=value.cpu()))', 'if captures is not None:\n            from . import provider as _provider043\n            actual_sidecar043=_provider043._OP.take("mixed")\n            captures.setdefault("decode",[]).append(dict(before=before,inputs=args_cpu,output=value.cpu(),actual_sidecar043=actual_sidecar043))')])
 edit('qwen36_deltalog_fresh/capture_evidence.py',[(str(260815535),str(SEED))])
 edit('domain_consumer.py',[(str(260815535),str(SEED)),
  ("def per_request_metrics(torch,R,raw,D):", "def original_per_request_metrics(torch,R,raw,D):"),
  ("row['request_pass']=bounded(row,R);rows.append(row)", "row['request_pass']=bounded(row,R);row['_independent_truth043']=o;rows.append(row)"),
  ("need(bounded(metrics,R), 'original whole-core native peer gates; uncast decode metrics retained diagnostic')", "need(math.isfinite(metrics['state_error']) and metrics['state_error']<=R.STATE_LIMIT, 'unchanged native peer state gate; old output point gate diagnostic')"),
  ("'per-request direct-RNE decode/state and original native-peer gates'", "'new preregistered actual precast and original state/byte gates'"),
  ("records=producer['records']; seen=set()", "records=producer['records']; seen=set()\n import sidecar_audit,precast\n controls=producer['boundary_controls'];need([x['case']for x in controls]==['normal','tiny','subnormal','positive-zero','negative-zero','cancellation','overflow'],'all real NPU numeric boundary controls')\n overflow={x['raw']['path']for x in controls if x['case']=='overflow'}\n mixed043={x['path']for x in producer['actual_mixed_sidecar_records']};need(len(mixed043)==2*producer['steps'],'one actual sidecar per mixed call')\n all043=producer['actual_sidecar_records'];need(len(all043)==2*producer['steps']+25 and len({x['path']for x in all043})==len(all043),'all unique actual calls: mixed + 2 partial flush + 16 copy warmups + 7 controls')\n need(mixed043|{x['raw']['path']for x in controls} <= {x['path']for x in all043},'actual mixed/boundary raw membership')\n sidecar_rows=[]\n for rr043 in all043:\n  av043=torch.load(checked(rr043),map_location='cpu',weights_only=False)\n  audit043=sidecar_audit.audit(torch,R,precast,av043,overflow=rr043['path']in overflow,numeric=rr043['path']not in mixed043)\n  sidecar_rows.append(dict(raw=rr043,**audit043))\n need(sidecar_rows and all(x['passed']for x in sidecar_rows),'all actual production/debug/precast call predicates')"),
  ("static_source=proof,rows=rows,failures=errors", "static_source=proof,rows=rows,actual_sidecar_rows=sidecar_rows,boundary_controls=controls,failures=errors"),
  ("row['per_request']=per_request_metrics(torch,R,raw,D)", "need(raw['captures']['decode'][0]['actual_sidecar043']in producer['actual_mixed_sidecar_records'],'exact mixed capture membership in actual paired call ledger')\n    row['per_request']=per_request_metrics(torch,R,raw,D)"),
  ("schema='deltalog.independent-CPU64-operational-recurrence-direct-integer-BF16-RNE/v035'", "schema='deltalog.actual-FP32-precast-per-request-empirical/v043',precast_peak=.00303,precast_relative_L2=2**-13")])
 with (P/'domain_consumer.py').open('a',encoding='utf8',newline='\n')as f:f.write('\n'+(P/'per_request_increment.py').read_text(encoding='utf8'))
 # Actual codec loading occurs before old strict/domain code, not a replacement oracle.
 edit('consume_pair.py',[("argv=[sys.executable,'-I','-B',str(P/script)", "argv=[sys.executable,'-I','-B',str(P/'raw_reader_entry.py'),'--script',script"),
  ("DOMAIN035.json","DOMAIN043.json"),('deltalog.diagnostic-consumption/v035','deltalog.diagnostic-consumption/v043')])
 edit('host.py',[("deltalog.diagnostic-consumption/v035","deltalog.diagnostic-consumption/v043"),
  ("OWNER='deltalog-diagnostic-bridge-new48h-MAIN-035-repair1'", "OWNER='deltalog-mixed-precast-new48h-MAIN-043-repair3'"),
  ("refs.extend([m['composite_api_ref']", "refs.extend([m['debug_library'],m['debug_build_ref'],m['debug_kernel_source_ref']])\n refs.extend([m['composite_api_ref']"),
  ("a.output.resolve().is_relative_to(Path('/cache/cch'))", "a.output.resolve().parent==Path('"+OUTPUT+"').resolve()")])
 edit('preregister.py',[("deltalog.diagnostic-consumption/v035","deltalog.diagnostic-consumption/v043"),
  ("deltalog.independent-CPU64-operational-recurrence-direct-integer-BF16-RNE/v035","deltalog.actual-FP32-precast-per-request-empirical/v043")])
 edit('entry.py',[("R=C.load(m['files']['oracle.py']", "import meta043\n  actual_meta043=meta043.run(torch,m,C)\n  R=C.load(m['files']['oracle.py']"),
  ("boundary=boundary,actual_copy_import=", "boundary=boundary,actual_precast_meta=actual_meta043,actual_copy_import="),
  ("C.need(C.obj(cpu['actual_terminal_process_controls'])", "C.need(cpu['actual_precast_meta']['pass_gate']is True and cpu['actual_precast_meta']['debug_library']==m['debug_library'],'same-source debug actual Meta prior to NPU')\n C.need(C.obj(cpu['actual_terminal_process_controls'])")])
 # Historical controls are retained, explicitly scoped to the original predicate;
 # current sidecar-specific correctness is tested in test_043, never by faking raw.
 for n in('test_031.py','test_producer_frontdoor.py'):
  edit(n,[("deltalog.diagnostic-consumption/v035","deltalog.diagnostic-consumption/v043"),("deltalog.independent-CPU64-operational-recurrence-direct-integer-BF16-RNE/v035","deltalog.actual-FP32-precast-per-request-empirical/v043")])
 n='test_031.py';s=(P/n).read_text(encoding='utf8');a=s.index("  s=(P/'host.py').read_text()",s.index('def test_host_inverse'));b=s.index("  current=",a);s=s[:a]+"  import inverse043\n  self.assertTrue(inverse043.verify('host.py'))\n"+s[b:];put(n,s)
 edit('test_035.py',[("C.per_request_metrics(","C.original_per_request_metrics("),(str(260815535),str(SEED)),("deltalog.diagnostic-consumption/v035","deltalog.diagnostic-consumption/v043"),("direct-integer-BF16-RNE/v035","actual-FP32-precast-per-request-empirical/v043")])
 n='test_producer_frontdoor.py';s=(P/n).read_text(encoding='utf8');a=s.index('  old=',s.index('def test_producer_inverse'));b=s.index("if __name__",a);s=s[:a]+"  import inverse043\n  self.assertTrue(inverse043.verify('producer.py'))\n"+s[b:];put(n,s)
 # Pins are generated from exact reviewed local sources; CPU static proof checks them.
 n='domain_consumer.py';s=(P/n).read_text(encoding='utf8');tree=ast.parse(s);node=next(x for x in tree.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PINNED'for t in x.targets));pins=ast.literal_eval(node.value)
 for k in pins:pins[k]=sha((P/k).read_bytes())
 lines=s.splitlines(keepends=True);s=''.join(lines[:node.lineno-1])+'PINNED = '+repr(pins)+'\n'+''.join(lines[node.end_lineno:]);put(n,s)
 for n in EDITS:put(Path('fixtures043')/n,(BASE/n).read_text(encoding='utf8'))
 put('DELTA043.json',json.dumps(dict(base=str(BASE),old_root=OLD,new_root=ROOT,edits=EDITS),indent=2)+'\n')
 m=json.loads((BASE/'SOURCE_TEMPLATE.json').read_text(encoding='utf8'));m=json.loads(json.dumps(m).replace(OLD,ROOT));m['root']=ROOT
 original=json.loads((P.parent/'deltalog040-actual016-bound-source.json').read_text(encoding='utf8'))
 for k in('debug_library','debug_build_ref','debug_kernel_source_ref'):m[k]=original[k]
 m['validation_contract'].update(schema='deltalog.actual-FP32-precast-per-request-empirical/v043',seed_base=SEED,precast_peak=.00303,precast_relative_L2=2**-13,old035_failed_unchanged=True,scope='mixed diagnostic component; no graph/model/task qualification')
 m['exact_output_root']=OUTPUT;m['prepared_only']=True
 m['files']={}
 for p in sorted(P.rglob('*')):
  if p.is_file()and p.suffix in('.py','.json','.md')and p.name not in('SOURCE_TEMPLATE.json','BYTE_EXACT_DELIVERY.json','COMMANDS.json','SOURCE_MANIFEST.json','BYTE_EXACT_DELIVERY043.json','COMMANDS043.json','LOCAL_TEST_RESULT043.json'):
   n=p.relative_to(P).as_posix();b=p.read_bytes();m['files'][n]=dict(path=ROOT+'/'+n,bytes=len(b),sha256=sha(b))
 put('SOURCE_TEMPLATE.json',json.dumps(m,indent=2,sort_keys=True)+'\n')
 print('assembled; no execution/qualification')
if __name__=='__main__':main()
