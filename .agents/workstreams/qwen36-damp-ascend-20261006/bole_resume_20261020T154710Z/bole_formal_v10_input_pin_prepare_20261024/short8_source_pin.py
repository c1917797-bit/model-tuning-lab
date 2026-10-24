"""Reopen reviewed CPU-cleanup successor, preserving every original short8 gate."""
import copy,json,sys,types
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import formal_composer as R
CPU_RENDERER=dict(path=str(R.WS/'bole_client_input_v10_prepare_20261024/runtime_lossless_imports.py'),bytes=11591,sha256='3f4ac564768f3931492a23756083dc14f3e29efc8b354e7e62ad45a6cf7570e2')
CPU_ASSETS=R.WS/'bole_textonly_v8_prepare_20261024'
INPUT_ADAPTER=dict(path=str(R.WS/'bole_client_input_v10_prepare_20261024/adapt_input_preflight.py'),bytes=3152,sha256='4d35ac101c6384e63ad3bf76cce91e85406cf121d2911692d01aa7c2ecd157cb')
CPU_HELPER=dict(path=str(R.WS/'bole_textonly_v8_prepare_20261024/cpu_release_policy.py'),bytes=3952,sha256='a7da0a2ef2116b80f18d4d00c1646e8d190aede11df5411aa382a93b7e4b4895')
TARGET_ROOT=Path(CPU_RENDERER['path']).parent/'prepared-source-short8-v10'
TEXT_ADAPTER=dict(path=str(R.WS/'bole_textonly_v8_prepare_20261024/adapt_textonly.py'),bytes=2397,sha256='ff0b41b104115bc4f071180320a423b70827f2c1f8cb6920c217041108bcaa83')
TEXT_HELPER=dict(path=str(R.WS/'bole_textonly_v8_prepare_20261024/text_only_profile.py'),bytes=1276,sha256='0ae4161808a08f03085184d27307e6c53263022448c6abcd6ba054571da972cb')
ALLOWED={'hypic32k_input.py','input_preflight.py','adapt_input_preflight.py','bole_performance_profile.py','preflight114.py','text_only_profile.py','adapt_textonly.py','observer_race_repair.py','host_service.py','owned_create.py','cpu_precreate_policy.py','adapt_cpu_precreate.py','contract090.py','qualification_source_validate.py','qualification_source_producer.py','runtime_lossless_imports.py','owned_substrate.py','cpu_release_policy.py'}
CONTRACTS=('resources','input_resource_profile32k','fastpath_numeric_qualification','runtime_joint_capture_ledger','fa_lossless_capture','short_state_digest_profile','profile','service_experiment','performance_profile','performance_client_contract','native_speculative_config','common')
def exact_target(sr):
 R.need(type(sr)is dict and Path(sr['path'])==TARGET_ROOT/'SOURCE_BOUND.json','only distinct reviewed V10 client-input source, never old-pin substitution')
def normalized(v,m):
 if type(v)is dict:
  if set(v)=={'path','bytes','sha256'}:
   hits=[n for n,r in m['files'].items()if r==v]
   if hits:return dict(source_file=hits[0],bytes=v['bytes'],sha256=v['sha256'])
  return{k:normalized(x,m)for k,x in v.items()}
 if type(v)is list:return[normalized(x,m)for x in v]
 if type(v)is str:
  for old,new in((m['root'],'$SOURCE'),(m['output_root'],'$OUTPUT')):
   if v==old or v.startswith(old+'/')or v==old+'-CPU'or v.startswith(old+'-CPU/'):return new+v[len(old):]
 return v
def unchanged(old_files,new_files,old_m,new_m):
 R.need(set(new_files)==set(old_files)|{'cpu_release_policy.py','cpu_precreate_policy.py','adapt_cpu_precreate.py','text_only_profile.py','adapt_textonly.py','input_preflight.py','adapt_input_preflight.py'},'only exact reviewed CPU cleanup/precreate helpers')
 changed={n for n in new_files if old_files.get(n)!=new_files[n]}
 R.need(changed<=ALLOWED,'no mathematical/input/FA/GDN/conv/state/collector/geometry/threshold/source change outside reviewed cleanup seam')
 for n in set(old_files)-ALLOWED:R.need(old_files[n]==new_files[n],'complete original unchanged file '+n)
 expected=old_files['owned_substrate.py'].decode();marker=' observer_race_repair.install(S,C)'
 added=marker+"\n raw(current['files']['cpu_release_policy.py'])\n import cpu_release_policy as CPU_RELEASE\n CPU_RELEASE.install(S,C,current)"
 expected_files=dict(old_files);expected_files['owned_substrate.py']=R.once(expected,marker,added).encode()
 with R.isolated():
  R.module(R.ref(CPU_ASSETS/'cpu_precreate_policy.py'),'cpu_precreate_policy')
  A=R.module(R.ref(CPU_ASSETS/'adapt_cpu_precreate.py'),'_exact_pin_initial_adapter')
  expected_files,_=A.adapt(expected_files)
 G=R.module(R.GUARD_DELTA,'_exact_pin_V7_guard_delta')
 expected_files,_guard=G.adapt(expected_files)
 with R.isolated():
  TEXT=R.module(TEXT_ADAPTER,'_exact_pin_V8_textonly')
  expected_files,_text=TEXT.adapt(expected_files)
 expected_files['adapt_textonly.py']=R.checked(TEXT_ADAPTER)
 with R.isolated():
  INPUT=R.module(INPUT_ADAPTER,'_exact_pin_V10_input');expected_files,_input=INPUT.adapt(expected_files)
 expected_files['adapt_input_preflight.py']=R.checked(INPUT_ADAPTER)
 R.need(new_files['text_only_profile.py']==R.checked(TEXT_HELPER),'actual source-owned V8 text-only helper')
 for n in('hypic32k_input.py','input_preflight.py','adapt_input_preflight.py','owned_substrate.py','host_service.py','owned_create.py','cpu_precreate_policy.py','observer_race_repair.py','bole_performance_profile.py','preflight114.py','text_only_profile.py','adapt_textonly.py'):
  R.need(expected_files[n]==new_files[n],'exact reviewed CPU precreate installation '+n)
 R.need(new_files['adapt_cpu_precreate.py']==R.checked(R.ref(CPU_ASSETS/'adapt_cpu_precreate.py')),'exact source-owned adapter bytes')
 before=old_files['contract090.py'].decode()
 before=before.replace(repr(old_m['output_root']),repr(new_m['output_root'])).replace(repr(old_m['output_root']+'-CPU'),repr(new_m['output_root']+'-CPU'))
 R.need(before.encode()==new_files['contract090.py'],'only exact output identity constants')
 R.need(new_files['runtime_lossless_imports.py']==R.checked(CPU_RENDERER)and new_files['cpu_release_policy.py']==R.checked(CPU_HELPER),'exact reviewed cleanup renderer/helper bytes')
 R.need(new_m['cpu_precreate_intent']==A.manifest({})['cpu_precreate_intent'],'exact source-owned CPU precreate contract')
 for key in CONTRACTS:R.need(normalized(old_m[key],old_m)==normalized(new_m[key],new_m),'unchanged original protected contract '+key)
 return sorted(changed)
def private_D(original,sr):
 # The old function body/default and every assertion stay byte-for-byte.
 # Only its expected-source view is rebound after exact full source validation.
 view=types.SimpleNamespace(**vars(original));view.PARENT_REF=copy.deepcopy(sr);return view
def _consume(m):
 p=m.get('formal_prerequisites')
 R.need(type(p)is dict and 'short8_scope'in p and 'short8_host'in p,'MAIN-pinned actual prerequisite Refs')
 # Actual original formal ticket pins these exact report operands before lookup.
 V=R.module(R.ref(R.WS/'bole32k_fixed1024_performance_prepare_v1_20261023/whole_v2/formal_validator.py'),'_actual_formal_ticket_pin')
 V.execution_window(m,clock=True,require_phase=True)
 report=json.loads(R.checked(p['short8_scope']));sr=report['source'];exact_target(sr)
 actual=json.loads(R.checked(sr));root=Path(actual['root']);R.need(root==TARGET_ROOT,'exact reviewed successor root')
 with R.isolated():
  C=R.module(CPU_RENDERER,'_actual_cpu_cleanup_renderer')
  expected=C.render(base_root=Path(actual['qualification_preparation_root']),permit_materialized=True,
   parent_pair_preparation_root=Path(actual['qualification_parent_pair_preparation_root']),
   historical_short_source_ref=actual['qualification_historical_short_source'],
   authority_ref=actual['qualification_authority_ref'],
   parent_preparation_readset=actual['qualification_parent_preparation_readset'])
  C.inverse(expected)
  template=json.loads(R.checked(actual['prepared_template']))
  R.need(template==expected['manifest'],'complete reviewed successor template')
  bound=dict(template,prepared_only=False,qualification_source_binding_pending=False,prepared_template=actual['prepared_template'])
  R.need(bound==actual,'only original reviewed source binding transition')
  for n,raw in expected['files'].items():R.need(R.checked(actual['files'][n])==raw,'every exact successor source byte '+n)
  D=R.module(R.DELTA,'_original_performance_delta');old_m,old_files=D.parent()
  changes=unchanged(old_files,expected['files'],old_m,actual)
  S=R.module(R.PREREQ,'_immutable_original_short8_consumer')
  with S.source_modules(root,actual['files']):
   import sourceio as IO
   import qualification_source_validate as FSV
   R.need(IO.ref(FSV.__file__)==actual['files']['qualification_source_validate.py'],'actual source-owned FSV')
   FSV.validate(sr)
   ticket=FSV.execution_window(actual,clock=False,require_phase=False)
   R.need(ticket['cutoff_epoch']==1792827353 and 1792740953<=ticket['start_epoch']<ticket['cutoff_epoch'],'unchanged approved window, no renewal')
  S.D=private_D(S.D,sr)
  result=S.consume(p['short8_scope'],p['short8_host'],source_ref=sr)
 return dict(result,source_pin_successor=True,reviewed_cleanup_only_changes=changes,
  original_consumer_assertions_unchanged=True,numerical_qualified=False,performance_admitted=False)
def consume(m):
 with R.isolated():return _consume(m)
