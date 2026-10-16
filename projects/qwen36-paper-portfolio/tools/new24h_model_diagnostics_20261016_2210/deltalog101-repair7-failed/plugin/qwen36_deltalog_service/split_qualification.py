"""088 actual eager component -> real-model DIAGNOSTIC permission only."""
import math
import importlib.util
C=None
MODE='actual052-split-scale-diagnostic-only' # inherited routing tag, not evidence schema
CONTRACT=dict(schema='deltalog.eager-sameinitial-native-operational/v088',seed=2610168801,graph_qualified=False)
CONTROLS=['normal','tiny','subnormal','positive-zero','negative-zero','cancellation','overflow','finite-final-normalized-query','finite-final-unscaled-query','cancellation-permuted','gqa-vtile-witness','original-B16-step80','original-B16-step137']
def consume(m):
 N=C.need
 N(m.get('short_model_diagnostic_scope')==SHORT_SCOPE,'explicit new16-only model diagnostic; no160 certificate')
 N(m.get('bridge024_source_ref')==ACTUAL['source']and m.get('bridge024_owner_ref')==ACTUAL['owner']and m.get('component_cpu_owner_ref')==ACTUAL['cpu_owner'],'exact actual16/source/CPU predecessor ticket')
 N(m.get('prepared_only')is False and m.get('admission_mode')==MODE,'bound101 diagnostic optin')
 sr=m['bridge024_source_ref'];s=C.obj(sr);t=C.obj(m['reviewed_domain_template_ref'])
 N(s['schema']=='deltalog.deadpayload-native-bridge-source/v024'and s['prepared_only']is False and s['default_enabled']is False,'actual bound088')
 N(s['prepared_template']==m['reviewed_domain_template_ref']and s['files']==t['files']==m['reviewed_domain_files']and s['root']==t['root']and s['validation_contract']==t['validation_contract'],'reviewed088R2 exact full readset')
 N(s['component_operational088']==dict(seed=2610168801,mode='eager',qualification=False),'088 new independent inputs and domain')
 for r in s['files'].values():C.obj_file(r)
 N(all(s[k]==m[k]for k in('library_ref','debug_library','debug_build_ref','debug_kernel_source_ref')),'same actual051 artifacts')
 o=C.obj(m['bridge024_owner_ref'])
 N(o['source']==o['target_source']==sr and o['schema']=='deltalog.diagnostic-owned-host/v035'and o['stage']=='numeric'and o['steps']==16 and o['physical']==[5]and o['NPU']is True,'actual same-source160 owner')
 N(o['primary']is None and o['secondary']==[]and o['stopped_retained']is True and o['resource_admitted']is True and o['diagnostic_capture_complete']is True,'actual owned complete release')
 N(o['bridge_primitive_gate_pass']is False and o['model_ready']is False,'not component promotion')
 p=C.obj(o['result']);r=C.obj(o['independent_consumer']);META.C=C;META.actual_build_meta(m,s,p)
 N(p['source']==sr and p['steps']==16 and p['primary']is None and p['NPU']is True and p['graph']is False and p['fullmodel']is False,'actual full producer')
 N(r['schema']=='deltalog.eager-component-operational-consumption/v088'and r['source']==sr and r['actual_result']==r['producer']==o['result'],'actual088 consumer join')
 N(all(r[k]is True for k in('diagnostic_capture_complete','domain_checks_pass','observation_complete'))and all(r[k]is False for k in('pass_gate','complete_proof','model_ready','performance_ready','NPU_reexecuted')),'complete bounded component only')
 old=C.obj(r['original_strict_consumer']);N(old['schema']=='deltalog.fresh-bridge-consumption/v5'and type(old['pass_gate'])is bool and old['source']==sr and old['producer']==o['result']and r['original_strict_result_preserved']==dict(pass_gate=old['pass_gate'],primary=old['primary']),'old strict failure retained')
 d=C.obj(r['domain_consumer']);N(d['schema']=='deltalog.eager-component-operational-report/v088'and d['source']==sr and d['producer']==o['result']and d['steps']==16,'actual088 domain')
 N(d['validation_contract']==r['validation_contract']==CONTRACT and d['anchors']==r['initial_anchor_refs']and set(d['anchors'])=={'1','16'},'both independent new anchors')
 for a in d['anchors'].values():C.obj_file(a)
 N(d['primary']is None and d['domain_checks_pass']is True and d['eager_component_operational_pass']is True and d['missing_evidence']==[]and d['failures']==[],'no partial/failing domain')
 N(all(d[k]is False for k in('graph_tested','full_requested_scope_pass','qualified','NPU_reexecuted'))and all(d[k]is True for k in('old069_FAIL_unchanged','native_is_not_mathematical_truth','cumulative_error_not_ignored')),'no full-history/model/graph claim')
 rows=d['rows'];N(len(rows)==40 and [x['record']for x in rows]==p['records'],'all328 ordered actual rows')
 sides=p['actual_sidecar_records'];audits=d['sidecar_results'];N(len(sides)==63 and len({(v['path'],v['bytes'],v['sha256'])for v in sides})==63 and [x['raw']for x in audits]==sides,'all351 distinct raw sidecars')
 N([x['case']for x in p['boundary_controls']]==CONTROLS and len(p['actual_mixed_sidecar_records'])==32,'13boundary/320mixed original calls')
 N(set(x['path']for x in p['actual_mixed_sidecar_records'])|set(x['raw']['path']for x in p['boundary_controls'])<=set(x['path']for x in sides),'all mixed/boundary calls belong to full audited ledger')
 for x in audits:
  a=x['audit'];N(a['passed']is True and all(a[k]is True for k in('production_debug_bitwise','actual_input_immutable','actual_guard_pointer_pass')),'original independent sidecar gates')
 for b in(1,16):
  mixed=[x for x in rows if x['record']['kind']=='mixed'and x['record']['batch']==b];N([x['record']['step']for x in mixed]==list(range(16)),'160complete eachbatch')
  for x in mixed:
   N(x['component_operational_pass']is True and x['decode']['passed']is True and x['prefill']['actual_native_sameinput_bitwise']is True and x['prefill']['qualified']is False,'localdecode and native sameinitial actual controls')
   e=x['prefill']['flush_CPU64_relative_l2'];N(type(e)in(int,float)and math.isfinite(e)and 0<=e<=7.92e-7,'independent flush bound')
   N(all(x['old_cross_history_metrics'][k]is True for k in('conv_bitwise','untouched_bitwise','guard_bitwise','inputs_bitwise','pointers_bitwise','prefill_aux_reset_bitwise')),'all original byte/lifecycle gates')
   N(all(type(x['cross_history'][k])in(int,float)and math.isfinite(x['cross_history'][k])and x['cross_history'][k]>=0 for k in('candidate_vs_independent_cumulative_CPU64','native_vs_independent_cumulative_CPU64','candidate_vs_native')),'full cumulative metrics retained diagnostic')
  flush=[x for x in rows if x['record']['kind']=='dead_flush'and x['record']['batch']==b];copies=[x for x in rows if x['record']['kind']=='copy'and x['record']['batch']==b]
  N(len(flush)==len(copies)==2 and [x['record']['length']for x in copies]==[1,7],'all flush/copy cases')
  for x in flush+copies:
   v=x['unchanged_primitive'];N(math.isfinite(v['state_error'])and 0<=v['state_error']<=7.92e-7 and all(z is True for k,z in v.items()if k.endswith('bitwise')or k=='descriptors_exact'),'original flush/copy gates')
 return dict(schema='deltalog.actual16-to-model-diagnostic-admission/v101-repair7',admission_scope=SHORT_SCOPE,long_history_160_qualified=False,production_admitted=False,source=sr,owner=m['bridge024_owner_ref'],consumer=o['independent_consumer'],domain=r['domain_consumer'],original_strict=r['original_strict_consumer'],validation_contract=CONTRACT,library=m['library_ref'],debug_library=m['debug_library'],actual_NPU=True,diagnostic_smoke_admitted=True,model_ready=False,model_numeric_qualified=False,performance_ready=False,task_ready=False,graph=False,PDC=False)
def admit(reader,m):
 global C,META
 C=reader
 C.need(m.get('prepared_only')is False and m.get('reviewed_domain_files'),'bound reviewed088 pins required')
 r=m['files']['qwen36_deltalog_service/build_meta051.py']if 'qwen36_deltalog_service/build_meta051.py'in m['files']else C.obj(m['plugin_source'])['files']['qwen36_deltalog_service/build_meta051.py']
 p=C.obj_file(r);spec=importlib.util.spec_from_file_location('_101_exact051_meta',p);META=importlib.util.module_from_spec(spec);spec.loader.exec_module(META)
 return consume(m)

SHORT_SCOPE={'schema': 'deltalog.actual16-to-nine-decode-model-diagnostic/v101-repair7', 'component_steps': 16, 'model_decode_steps': 9, 'model_requests': 2, 'prompt_tokens': 2048, 'max_sequences': 1, 'long_history_160_qualified': False, 'production_admitted': False, 'performance_ready': False, 'task_ready': False}
ACTUAL={'source': {'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-sameinitial-native-contract-new24h-v1-088-repair6-repair2/SOURCE_MANIFEST.json', 'bytes': 67429, 'sha256': '871c8e32831ee3eebacd43a084e4416bb14d6d06cd9f5ee08017ba459f287cd8'}, 'owner': {'path': '/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/run-numeric16-MAIN-20261016-NEW24H-088-repair6-repair2-001/RESULT.json', 'bytes': 1667, 'sha256': '7b10472808da9c409dca97e4f36ff577cf4d090db95c90b556d0bf680f4d25fe'}, 'cpu_owner': {'path': '/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/run-cpu-MAIN-20261016-NEW24H-088-repair6-repair2-001/RESULT.json', 'bytes': 1426, 'sha256': '1ea2eeff549bb8fb036f0b313e57503a87896302be4836f68dba5641e0e4e35f'}}
