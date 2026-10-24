"""Exact-guard observation V7 successor verification and unapproved review operands."""
import ast,hashlib,importlib.util,json,os,resource,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'bole_cpu_precreate_whole_v5_prepare_20261023'
V6=HERE.parent/'bole_cpu_precreate_whole_v6_prepare_20261024'
def need(v,label):
 if not v:raise ValueError(label)
def ref(p,raw=None):
 p=Path(p);raw=p.read_bytes()if raw is None else raw
 return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def put(name,v):
 raw=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode();p=HERE/name
 with p.open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
 return ref(p,raw)
def main():
 need(144 in os.sched_getaffinity(0),'fresh allowed CPU144')
 os.sched_setaffinity(0,{144});resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(175,175))
 S=load(HERE/'runtime_lossless_imports.py','_V6identity')
 old_renderer=ref(OLD/'runtime_lossless_imports.py')
 need(old_renderer['bytes']==9769 and old_renderer['sha256']=='2c9723f7e87d9d30d1f2486908fe34daeb7307c8cb173f0c78bb79b228ae8cd7','exact frozen V5 renderer')
 expected=(V6/'runtime_lossless_imports.py').read_bytes().replace(b'bole_cpu_precreate_whole_v6_prepare_20261024',b'bole_guard_observation_prepare_v7_20261024').replace(b'prepared-source-short8-v6',b'prepared-source-short8-v7').replace(b'run-bole32k-lossless-cpu-precreate-short8-v6-20261024',b'run-bole32k-lossless-guard-observation-short8-v7-20261024')
 expected=expected.replace(b" files['adapt_cpu_precreate.py']=(PREP/'adapt_cpu_precreate.py').read_bytes()",b" files['adapt_cpu_precreate.py']=(PREP/'adapt_cpu_precreate.py').read_bytes()\\n G=module((PREP/'guard_failure_delta.py').read_bytes(),PREP/'guard_failure_delta.py','_exact_guard_observation_delta')\\n files,guard_delta=G.adapt(files)".replace(b'\\n',b'\n'))
 expected=expected.replace(b"m['short2k_helper_refs'].update(external)",b"external['guard_failure_delta']=ref(PREP/'guard_failure_delta.py',(PREP/'guard_failure_delta.py').read_bytes())\\n m['short2k_helper_refs'].update(external)".replace(b'\\n',b'\n'))
 need(expected==(HERE/'runtime_lossless_imports.py').read_bytes(),'only exact identities and guard observation renderer seams')
 for n in ['cpu_release_policy.py','cpu_precreate_policy.py','adapt_cpu_precreate.py']:need((HERE/n).read_bytes()==(OLD/n).read_bytes(),'unchanged helper '+n)
 b=S.render();S.inverse(b);m=b['manifest']
 need(m['qualification_authority_ref']is None,'no authority inherited')
 need(not Path(m['root']).exists()and not Path(m['output_root']).exists(),'source/output unmaterialized')
 old_sr=ref(OLD/'prepared-source-short8-v5/SOURCE_BOUND.json')
 old=json.loads(Path(old_sr['path']).read_bytes())
 need(set(m['files'])==set(old['files']),'identical file set458')
 changed=[];unchanged=[]
 for n,r in old['files'].items():
  raw=Path(r['path']).read_bytes();need(ref(r['path'],raw)==r,'full actual V5 Ref '+n)
  if raw==b['files'][n]:unchanged.append(n);continue
  changed.append(n)
  if n=='runtime_lossless_imports.py':need(b['files'][n]==expected,'exact renderer identities only')
  elif n=='contract090.py':
   want=raw.replace(repr(old['output_root']+'-CPU').encode(),repr(m['output_root']+'-CPU').encode()).replace(repr(old['output_root']).encode(),repr(m['output_root']).encode())
   need(want==b['files'][n],'only two exact output constants')
  elif n=='observer_race_repair.py':
   G=load(HERE/'guard_failure_delta.py','_guard_exact_whole_delta');derived,d=G.adapt({n:raw})
   need(derived[n]==b['files'][n]and G.inverse(derived,d)[n]==raw,'exact observer delta and inverse')
  else:raise ValueError('unapproved source change '+n)
 need(set(changed)=={'contract090.py','runtime_lossless_imports.py','observer_race_repair.py'},'only identities plus exact guard observer file')
 keys=['resources','input_resource_profile32k','fastpath_numeric_qualification','runtime_joint_capture_ledger','fa_lossless_capture','cpu_precreate_intent','deviceless_cpu_release']
 for k in keys:need(m[k]==old[k],'unchanged exact protected contract '+k)
 for n,raw in b['files'].items():
  if n.endswith('.py'):compile(raw,n,'exec')
 negative=[]
 for f in [lambda:S.render(base_root=OLD),lambda:S.materialize(None)]:
  try:f()
  except ValueError:negative.append(True)
  else:raise ValueError('old preparation or missing authority accepted')
 nodes=[n.value for n in ast.parse(b['files']['qualification_source_validate.py']).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='SCOPE'for t in n.targets)]
 need(len(nodes)==1,'exact source FSV SCOPE')
 scope=eval(compile(ast.Expression(nodes[0]),'<actualV6FSVscope>','eval'),{'__builtins__':{},'dict':dict})
 seven=dict(scope=scope,source_root=m['root'],output_root=m['output_root'],files=m['files'],parent_preparation_readset=m['qualification_parent_preparation_readset'],historical_short_source=m['qualification_historical_short_source'],short2k_helper_refs=m['short2k_helper_refs'])
 rr=put('REVIEW_OPERANDS_ONLY.json',seven)
 dd=put('OBSERVATION_DELTA_AND_INVERSE.json',dict(schema='bole.V7-exact-guard-observation/v1',not_authority=True,approved=False,V5_source_ref=old_sr,V5_renderer_ref=old_renderer,V6_renderer_ref=ref(HERE/'runtime_lossless_imports.py'),changed_files=changed,unchanged_files=unchanged,exact_contracts_unchanged=keys,whole_inverse=True,helper_refs={n:ref(HERE/n)for n in['cpu_release_policy.py','cpu_precreate_policy.py','adapt_cpu_precreate.py']},no_foreign_PID_gate_change=True,no_mathematics_or_resource_change=True,NPU=False))
 bb=put('BINDING_CONTRACT.json',dict(not_authority=True,approved=False,authority_ref=None,source_root=m['root'],output_root=m['output_root'],cutoff_epoch=1792827353,prepare_argv=['/usr/bin/python3','-I','-B',str(HERE/'runtime_lossless_imports.py'),'--prepare','--authority-ref','<ACTUAL_NEW_MAIN_REF3>'],bind_argv=['/usr/bin/python3','-I','-B',str(Path(m['root'])/'qualification_source_producer.py'),'--bind','--template-ref','<ACTUAL_NEW_TEMPLATE_REF3>'],commands='only actual source-owned COMMANDS.json',NPU=False))
 cc=put('SOFTWARE_REUSE_BOUNDARY.json',dict(not_authority=True,V5_actual_source_ref=old_sr,semantic_unchanged_test_fixture_files=[n for n in unchanged if n.startswith('test_')or n.startswith('fixtures/')],large_software_tests_rerun=False,V5_CPU25_may_support_unchanged_semantics_only=True,V6_requires_new_actual_source_bound_CPU_preflight_receipts=True,old_PASS_not_actual_V6_receipt=True,NPU_branch_and_foreign_PID_rejection_unchanged=True,external_resource_change_evidence_and_MAIN_approval_required_before_dispatch=True,NPU=False))
 print(json.dumps(dict(PASS=True,files=len(m['files']),unchanged=len(unchanged),changed=changed,whole_inverse=True,negative_guards=len(negative),affinity=sorted(os.sched_getaffinity(0)),materials=[rr,dd,bb,cc],source_materialized=False,authority=None,NPU=False)))
if __name__=='__main__':main()
