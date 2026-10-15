"""Bind actual010/012 receipts into mechanism-specific production admission; no fake PASS."""
import argparse,ast,hashlib,importlib.util,json,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent
OLD={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/_draft_damp_operator_reuse/NEW48H/mxr-observerless-gdn-e2e-v1-004/SOURCE_MANIFEST.json','bytes':16278,'sha256':'3ccb0dcec3d67043f9736cc3266bef7b320b99d48facf791376519811d72b9f2'}
HELPER='96c345308723ebf32e6817b2289466aaca6ca964897abf97fa23941da6ac8d8d'
MATH_FILES=('eager_receiver.py','event_backend.py','lifetime.py','metadata_association.py','metadata_certificate.py','safe_eager.py')
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and Path(r['path']).is_absolute()and not Path(r['path']).is_symlink()and ref(r['path'])==r,'actual complete immutable Ref3');return Path(r['path'])
def obj(r):
 p=checked(r);need(r['bytes']<=16*1024**2,'bounded JSON receipt');return json.loads(p.read_bytes())
def exclusive(p,v):
 with Path(p).open('x',encoding='utf8')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
def equivalents(source):
 m=obj(source);old=obj(OLD);need(m['schema']=='mxr.observerless-source/v1'and m['root']==str(P)and m['default_enabled']is False,'actual production005 source')
 fingerprints={}
 for name in MATH_FILES:
  checked(m['files'][name]);checked(old['files'][name]);need(m['files'][name]['sha256']==old['files'][name]['sha256'],'unchanged exact algorithm file '+name);fingerprints[name]=m['files'][name]['sha256']
 def selected(r):
  tree=ast.parse(checked(r).read_bytes());install=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='install')
  names=('core','fwd','producer','attach','solver_for','pool_for','backend_for','metadata')
  found={n.name:ast.dump(n,include_attributes=False)for n in install.body if isinstance(n,ast.FunctionDef)and n.name in names}
  need(set(found)==set(names),'all original math/metadata/core functions')
  return found
 a,b=selected(m['files']['observerless_install.py']),selected(old['files']['observerless_install.py']);need(a==b,'exact original004 algorithm function ASTs')
 fingerprints.update({k:hashlib.sha256(v.encode()).hexdigest()for k,v in a.items()})
 return dict(original_source=OLD,production_source=source,math_fingerprints=fingerprints,timed_extra_wrapper=False,diagnostic_outer_wrapper_removed=True,target_method_is_same_algorithm_core=True)
def terminal(t,sr,result_ref):
 v=obj(t);need(v.get('exitCode',v.get('exit_code'))==0 and v.get('state','completed')=='completed','actual completed parent exit0')
 need(not('exitCode'in v and 'exit_code'in v and v['exitCode']!=v['exit_code']),'noncontradictory exit fields')
 argv=[v['command'],*v['args']];need(argv[:4]==['/usr/bin/python3','-I','-B',str(Path(sr['path']).parent/'host_ticket.py')]and '--execute'in argv,'actual exact source parent invocation')
 need(argv.count('--source-sha256')==1 and argv[argv.index('--source-sha256')+1]==sr['sha256'],'actual source SHA command')
 publications=[]
 for line in v['stdout'].splitlines():
  try:record=json.loads(line)
  except (ValueError,TypeError):continue
  if type(record)is dict and record.get('result')==result_ref['path']:publications.append(record)
 need(len(publications)==1,'one actual parent published result path')
 return argv
def evidence(sr,rr,tr,kind):
 m=obj(sr);r=obj(rr);terminal(tr,sr,rr)
 need(m['plugin_source']==OLD and any(f['sha256']==HELPER for n,f in m['files'].items()if n.endswith('prefix_binding.py')),'only source-bound fixed010/012 target helper, NOT old007/009')
 schema='mxr.observerless-once-short48-owned-host/v1'if kind=='short'else'mxr.observerless-long48-owned-host/v1'
 need(r['schema']==schema and r['source']==sr and r['primary']is None and r['secondary']==[]and r['all_created_containers_release_verified']is True,'actual complete owned gate/source/release')
 need(0<r['elapsed']<=m['budgets']['phase_seconds'] and 0<=r['cleanup_seconds']<=m['budgets']['cleanup_seconds'],'actual frozen diagnostic wallclock/cleanup')
 gate=r['short_all4_48GDN_gate'if kind=='short'else'long_all4_48GDN_gate'];need(gate['passed']is True,'actual relevant all4 gate')
 rows=r['actual48_GDN_output_state_consumers'];captures=r['capture'];need([x['rank']for x in rows]==[0,1,2,3]and [x['rank']for x in captures]==[0,1,2,3],'actual all4 rank coverage')
 prefixes=None;reports=[];bindings=[]
 for row,capture in zip(rows,captures):
  q=obj(row['result']);need(q['schema']=='mxr.observerless-once-GDN-independent/v1'and q['capture_source']==sr and q['plugin_source_ref']==OLD and q['pid']==capture['namespace_pid']and q['worker_root']==capture['worker_root']and q['run_id']==m['runtime_identity']['run_id'],'source-bound actual independent worker consumer')
  need(q['gdn_frame_gate_pass']is q['pass_stage']is q['full_GDN']is True,'all relevant independent numeric gates')
  ps=set(q['layer_prefixes']);need(len(ps)==48 and(prefixes is None or ps==prefixes),'same48 actual GDN prefixes');prefixes=ps
  need(len(q['rows'])==(48 if kind=='short'else 96)and all(x['pass_gate']is True for x in q['rows']),'complete short/long actual rows')
  if kind=='long':
   need(q['actual_slot_reuse']is True,'actual every-layer request exit/join slot reuse')
   need(q['multistep_state']is q['inference_metadata_lifecycle_pass']is True and len(q['decode_rows'])==192,'actual long 2x48x2 decode + slotreuse lifecycle, not planned')
   need({(x['prefix'],x['tokens'])for x in q['rows']}=={(p,t)for p in ps for t in(32768,40960)},'exact 2x48 long prefill coverage')
   need({(x['prefix'],x['prefill_tokens'],x['step'])for x in q['decode_rows']}=={(p,t,s)for p in ps for t in(32768,40960)for s in(0,1)}and all(x['pass_gate']is True for x in q['decode_rows']),'exact passed 2x48x2 native decode coverage')
  else:need({x['prefix']for x in q['rows']}==ps,'exact all48 short rows')
  if kind=='long':
   binder_ref=m['files']['binding_consumer.py'];checked(binder_ref)
   spec=importlib.util.spec_from_file_location('_actual012_binding_consumer',binder_ref['path']);binder=importlib.util.module_from_spec(spec);spec.loader.exec_module(binder)
   worker=Path(capture['worker_root']);notes=[json.loads(p.read_bytes())for p in sorted(worker.glob('frame-*/FRAME.json'))]
   proof=binder.consume(worker,sr,notes,q['run_id'],m['files']['worker.py'])
   need(proof==dict(actual_target=True,instance_prefixes=48,frames=96,performance=False),'actual012 independent binding consumer rerun, not guessed report flags')
   inputs=[ref(worker/'CORE_BINDING.json'),*[ref(p)for p in sorted(worker.glob('core-binding-*.json'))],*[ref(p)for p in sorted(worker.glob('frame-*/FRAME.json'))]]
   bindings.append(dict(result=proof,readset=[binder_ref,*inputs]))
  reports.append(row['result'])
 return dict(source=sr,result=rr,terminal=tr,reports=reports,bindings=bindings,prefixes=sorted(prefixes),kind=kind)
def build(source,e):
 eq=equivalents(source);short=evidence(e['short_source'],e['short_result'],e['short_terminal'],'short');long=evidence(e['long_source'],e['long_result'],e['long_terminal'],'long')
 need(short['prefixes']==long['prefixes'],'actual short/long same48 prefix identity')
 return dict(schema='mxr.observerless-full-gdn-independent/v1',plugin_source_ref=source,full_GDN=True,multistep_state=True,source_qualified=True,**{'pass':True},
  lengths=[129,32768,40960],source_pins=__import__('observerless_install').PINS,prefixes=short['prefixes'],source_equivalence=eq,evidence=e,diagnostic_short=short,diagnostic_long=long,
  inference_metadata_lifecycle_pass=True,graph_candidate=False,full_physical_cache_qualified=False,model_logits_qualified=False,independent_conv_oracle=False,
  scope='same unchanged solve/core math; all48 post-native-conv GDN + relevant state/metadata lifecycle; not full cache/graph/model logits',
  derived_admission_not_new_NPU_measurement=True,production_untimed_startup_gate_required=True,performance_result=False,task_accuracy=False)
def verify_derived(r,source):
 v=obj(r);expected=build(source,v['evidence']);need(v==expected,'complete recomputed source-equivalent diagnostic admission, not borrowed PASS');return v
def readset(r):
 v=obj(r);refs=[r,OLD]
 for name in('short_source','short_result','short_terminal','long_source','long_result','long_terminal'):refs.append(v['evidence'][name])
 for d in('diagnostic_short','diagnostic_long'):refs.extend(v[d]['reports'])
 for b in v['diagnostic_long']['bindings']:refs.extend(b['readset'])
 return refs
def main():
 if '--execute'not in sys.argv:print(json.dumps(dict(enabled=False,NPU=False)));return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref',required=True);p.add_argument('--evidence-ref',required=True);p.add_argument('--output-root',required=True,type=Path);a=p.parse_args()
 source=json.loads(a.source_ref);e=obj(json.loads(a.evidence_ref));v=build(source,e);out=a.output_root
 need(1791962297<=time.time()and time.time()+3600<1792135097,'unchanged whole-pair budget must still fit')
 need(out.is_absolute()and out.parent==Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit')and out.name.startswith('run-')and not out.exists(),'new immutable admission output')
 out.mkdir(mode=0o700);full=out/'MECHANISM_NUMERIC_ADMISSION.json';exclusive(full,v)
 q=json.loads((P/'QUALIFICATION_TEMPLATE.json').read_bytes());q.update(mode='performance',plugin_source_ref=source,full_numeric_ref=ref(full),lengths=[32768,40960],prefixes=v['prefixes'],template_not_runtime_receipt=False)
 qualification=out/'QUALIFICATION.json';exclusive(qualification,q);print(json.dumps(dict(full_numeric_ref=ref(full),qualification_ref=ref(qualification),NPU=False,boot_allowed=True,measured_interval_requires_actual_startup_gate=True)));return 0
if __name__=='__main__':raise SystemExit(main())
