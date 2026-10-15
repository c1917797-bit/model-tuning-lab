"""Typed actual035 receipt for MODEL036 diagnostic load, never model PASS."""
import math
import owner_overlay as C
MODE='actual035-directRNE-domain-diagnostic-only'
CONTRACT=dict(schema='deltalog.independent-CPU64-operational-recurrence-direct-integer-BF16-RNE/v035',output_limit=.00303,state_limit=7.92e-7,per_request_worst=True,seed_base=260815535,uncast_metrics_diagnostic_only=True)

def finite(value,name):
 C.need(type(value)in(int,float)and math.isfinite(value)and value>=0,'finite dimensionless metric '+name)

def metrics(row):
 # state_error is independent relative-L2; output_error is peak-normalized
 # against direct integer-RNE BF16 (independent) or native BF16 (peer).
 # They are dimensionless fractions, NOT percentages or tensor tolerances.
 for key,limit in(('state_error',7.92e-7),('output_error',.00303)):
  value=row[key];finite(value,key);C.need(value<=limit,'original per-request metric '+key)
 C.need(row['request_pass']is True,'actual per-request verdict, not aggregate PASS')
 if row['kind']=='independent-decode':
  for k in('uncast_CPU64_output_error','BF16_RNE_floor'):finite(row[k],k)

def consume(m):
 C.need(m.get('admission_mode')==MODE,'explicit035 diagnostic optin')
 pins=m.get('reviewed_domain_files');C.need(type(pins)is dict and pins,'MAIN reviewed035 exact source pins absent')
 C.need(m.get('prepared_only')is False,'unbound template cannot authorize model loading')
 sr=m['bridge024_source_ref'];source=C.obj(sr);reviewed=C.obj(m['reviewed_domain_template_ref'])
 C.need(source['schema']=='deltalog.deadpayload-native-bridge-source/v024'and source['default_enabled']is False and source['prepared_only']is False and source['files']==pins,'only reviewed035 bound source')
 C.need(reviewed['files']==pins and source['prepared_template']==m['reviewed_domain_template_ref']and source['root']==reviewed['root'],'actual035 final template binding')
 expected_source=dict(CONTRACT);expected_source.pop('uncast_metrics_diagnostic_only');expected_source.update(direct_round_sha256='60f64d53aae1e126f1a4de244a3cb224facc881e277386bf120d6a5b2988278d',uncast_original_strict_preserved=True,old_failed16_diagnostic_only=True)
 C.need(source['validation_contract']==reviewed['validation_contract']==expected_source,'exact035 reference/units/seed contract, not old031')
 C.need(source['library_ref']==m['library_ref'],'same unchanged B010 library')
 for r in pins.values():C.obj_file(r)
 v=C.obj(m['bridge024_owner_ref']);owner_source=C.obj(v['source'])
 C.need(owner_source['files']==pins and v['target_source']==sr,'actual reviewed035 owner/target')
 C.need(v['schema']=='deltalog.diagnostic-owned-host/v035'and v['stage']=='numeric'and v['steps']==160 and v['physical']==[5]and v['NPU']is True,'actual035 singleton160 owner')
 C.need(v['primary']is None and v['secondary']==[]and v['stopped_retained']is True and v['resource_admitted']is True and v['diagnostic_capture_complete']is True,'actual successful original owner/release, no recovery promotion')
 C.need(v['bridge_primitive_gate_pass']is False and v['model_ready']is False,'old component gate not relabelled')
 producer=C.obj(v['result']);r=C.obj(v['independent_consumer'])
 C.need(producer['source']==sr and producer['steps']==160 and producer['primary']is None and producer['NPU']is True and producer['graph']is False and producer['fullmodel']is False,'actual complete035 producer160')
 C.need(r['schema']=='deltalog.diagnostic-consumption/v035'and r['source']==sr and r['actual_result']==v['result']and r['diagnostic_capture_complete']is True and r['domain_checks_pass']is True and r['complete_proof']is False and r['NPU_reexecuted']is False,'actual independent035 consumption')
 old=C.obj(r['original_strict_consumer']);d=C.obj(r['domain_consumer'])
 C.need(old['schema']=='deltalog.fresh-bridge-consumption/v5'and old['source']==sr and old['producer']==v['result']and type(old['pass_gate'])is bool,'actual retained original uncast strict result')
 retained=dict(pass_gate=old['pass_gate'],primary=old['primary'])
 C.need(r['original_strict_result_preserved']==d['original_strict_result_preserved']==retained,'old uncast FAIL unchanged in both reports')
 C.need(d['schema']=='deltalog.direct-RNE-domain-audit/v035'and d['source']==sr and d['producer']==v['result']and d['original_strict_consumer']==r['original_strict_consumer'],'exact035 domain/raw join')
 C.need(r['validation_contract']==d['validation_contract']==CONTRACT,'actual035 independent reference contract')
 C.need(d['domain_checks_pass']is True and d['missing_evidence']==[]and d['failures']==[]and d['prefill_CPU64_diagnostic_only']is True and d['old_thresholds_unchanged']is True,'complete unchanged native-prefill boundary domain')
 C.need(all(d[k]is False for k in('complete_proof','diagnostic_qualified','model_ready','performance_ready','NPU_reexecuted','MXR_qualification')),'diagnostic scope not promoted')
 C.need(set(d['anchors'])=={'1','16'}and r['initial_anchor_refs']==d['anchors'],'both source-bound independently seeded anchors')
 rows=d['rows'];C.need(len(rows)==328 and [x['record']for x in rows]==producer['records'],'all328 ordered records, no substituted raw')
 for b in(1,16):
  mixed=[x for x in rows if x['record']['kind']=='mixed'and x['record']['batch']==b]
  C.need([x['record']['step']for x in mixed]==list(range(160)),'all160 perbatch steps')
  for row in mixed:
   C.need(row['domain_checks_pass']is True and row['all_requests_pass']is True and row['runtime_operand_immutability_pass']is True and not row.get('failure'),'every-step runtime/operand/numeric verdict')
   C.need(all(row['metrics'][k]is True for k in('conv_bitwise','untouched_bitwise','guard_bitwise','inputs_bitwise','pointers_bitwise','prefill_aux_reset_bitwise')),'original independent raw byte verdicts')
   values=row['per_request'];expected=[('independent-decode',j)for j in range(b)]+[('whole-core-native-peer',j)for j in range(b+1)]
   C.need([(x['kind'],x['request'])for x in values]==expected,'all independent and native-peer request identities')
   for x in values:metrics(x)
   C.need(row['transition']['local_transition_pass']is True and row['transition']['missing']==[],'complete anchor/state/slotreset/native-runtime transition')
  flush=[x for x in rows if x['record']['kind']=='dead_flush'and x['record']['batch']==b]
  copy=[x for x in rows if x['record']['kind']=='copy'and x['record']['batch']==b]
  C.need(len(flush)==2 and all(x['domain_checks_pass']is True for x in flush)and any(x['metrics']['length0']for x in flush)and any(x['metrics']['partial_live']for x in flush),'both zero/partial deadflush')
  C.need([x['record']['length']for x in copy]==[1,7]and all(x['domain_checks_pass']is True and x['metrics']['descriptors_exact']is True for x in copy),'actual copy1/7 descriptor and byte gates')
 return dict(schema='deltalog.model-directRNE-diagnostic-load-admission/v036',source=sr,owner=m['bridge024_owner_ref'],consumer=v['independent_consumer'],domain=r['domain_consumer'],original_strict=r['original_strict_consumer'],validation_contract=CONTRACT,library=m['library_ref'],actual_NPU=True,diagnostic_smoke_admitted=True,independent_local_decode_flush=True,unchanged_native_prefill_boundary=True,model_ready=False,model_numeric_qualified=False,performance_ready=False,task_ready=False,graph=False,PDC=False)

def closure(m):
 refs=[m['bridge024_source_ref'],m['bridge024_owner_ref'],m['reviewed_domain_template_ref']]
 source=C.obj(refs[0]);refs.extend(source['files'].values())
 v=C.obj(refs[1]);refs.extend([v['source'],v['result'],v['independent_consumer']]);refs.extend(C.obj(v['source'])['files'].values())
 r=C.obj(v['independent_consumer']);refs.extend([r['original_strict_consumer'],r['domain_consumer']])
 return refs
