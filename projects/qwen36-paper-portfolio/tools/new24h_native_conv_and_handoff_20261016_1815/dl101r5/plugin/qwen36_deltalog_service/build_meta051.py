"""Typed actual035 receipt for MODEL036 diagnostic load, never model PASS."""
import math
C=None
MODE='actual052-split-scale-diagnostic-only'
CONTRACT=dict(schema='deltalog.actual-FP32-precast-per-request-empirical/v043',precast_peak=.00303,precast_relative_L2=2**-13,output_limit=.00303,state_limit=7.92e-7,per_request_worst=True,seed_base=2610165101,uncast_metrics_diagnostic_only=True)
SOURCE_CONTRACT=dict(schema=CONTRACT['schema'],precast_peak=.00303,precast_relative_L2=2**-13,output_limit=.00303,state_limit=7.92e-7,per_request_worst=True,seed_base=2610165101,direct_round_sha256='60f64d53aae1e126f1a4de244a3cb224facc881e277386bf120d6a5b2988278d',old035_failed_unchanged=True,old_failed16_diagnostic_only=True,uncast_original_strict_preserved=True,scope='mixed diagnostic component; no graph/model/task qualification')

def finite(value,name):
 C.need(type(value)in(int,float)and math.isfinite(value)and value>=0,'finite dimensionless metric '+name)

def metrics(row,batch):
 # state_error is independent relative-L2; output_error is peak-normalized
 # against direct integer-RNE BF16 (independent) or native BF16 (peer).
 # They are dimensionless fractions, NOT percentages or tensor tolerances.
 finite(row['state_error'],'state_error');C.need(row['state_error']<=7.92e-7,'original per-request metric state_error')
 finite(row['output_error'],'retained old point output_error')
 C.need(row['request_pass']is True,'actual per-request verdict, not aggregate PASS')
 if row['kind']=='independent-decode':
  for k in('uncast_CPU64_output_error','BF16_RNE_floor'):finite(row[k],k)
  p=row['actual_precast'];C.need(p['request_row']==row['request']and p['passed']is True and row['cast_bitwise']is True,'actual per-request FP32/cast verdict')
  for k,limit in(('peak',.00303),('relative_l2',2**-13)):
   finite(p[k],k);C.need(p[k]<=limit,'actual per-request empirical FP32 '+k)
 elif row['kind']=='whole-core-native-peer':
  # Native prefill remains unmodified and keeps both original peer gates.
  # Decode BF16 point discrepancy is retained, not re-used as FP32 error.
  if row['request']==batch:C.need(row['output_error']<=.00303,'unchanged native prefill whole-core output peer')
 else:raise ValueError('unknown request kind')

def consume(m):
 C.need(m.get('admission_mode')==MODE,'explicit035 diagnostic optin')
 pins=m.get('reviewed_domain_files');C.need(type(pins)is dict and pins,'MAIN reviewed035 exact source pins absent')
 C.need(m.get('prepared_only')is False,'unbound template cannot authorize model loading')
 sr=m['bridge024_source_ref'];source=C.obj(sr);reviewed=C.obj(m['reviewed_domain_template_ref'])
 C.need(source['schema']=='deltalog.deadpayload-native-bridge-source/v024'and source['default_enabled']is False and source['prepared_only']is False and source['files']==pins,'only reviewed035 bound source')
 C.need(reviewed['files']==pins and source['prepared_template']==m['reviewed_domain_template_ref']and source['root']==reviewed['root'],'actual035 final template binding')
 expected_source=SOURCE_CONTRACT
 C.need(source['validation_contract']==reviewed['validation_contract']==expected_source,'exact035 reference/units/seed contract, not old031')
 C.need(source['library_ref']==m['library_ref'],'same unchanged B010 library')
 C.need(all(source[k]==m[k]for k in('debug_library','debug_build_ref','debug_kernel_source_ref')),'same actual015 debug source/build/library')
 for r in pins.values():C.obj_file(r)
 v=C.obj(m['bridge024_owner_ref']);owner_source=C.obj(v['source'])
 C.need(v['source']==sr and owner_source['files']==pins and v['target_source']==sr,'actual reviewed035 owner/target')
 C.need(v['schema']=='deltalog.diagnostic-owned-host/v035'and v['stage']=='numeric'and v['steps']==160 and v['physical']==[5]and v['NPU']is True,'actual035 singleton160 owner')
 C.need(v['primary']is None and v['secondary']==[]and v['stopped_retained']is True and v['resource_admitted']is True and v['diagnostic_capture_complete']is True,'actual successful original owner/release, no recovery promotion')
 C.need(v['bridge_primitive_gate_pass']is False and v['model_ready']is False,'old component gate not relabelled')
 producer=C.obj(v['result']);r=C.obj(v['independent_consumer'])
 actual_build_meta(m,source,producer)
 C.need(producer['source']==sr and producer['steps']==160 and producer['primary']is None and producer['NPU']is True and producer['graph']is False and producer['fullmodel']is False,'actual complete035 producer160')
 C.need(r['schema']=='deltalog.diagnostic-consumption/v043'and r['source']==sr and r['actual_result']==v['result']and r['diagnostic_capture_complete']is True and r['domain_checks_pass']is True and r['complete_proof']is False and r['NPU_reexecuted']is False,'actual independent043 consumption')
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
 sidecars=producer['actual_sidecar_records'];mixed_sidecars=producer['actual_mixed_sidecar_records'];audits=d['actual_sidecar_rows']
 C.need(len(sidecars)==351 and len(mixed_sidecars)==320 and len(audits)==351 and [x['raw']for x in audits]==sidecars,'all351 ordered actual sidecar refs/320 mixed')
 C.need(len({(x['path'],x['bytes'],x['sha256'])for x in sidecars})==351 and all(x['passed']is True for x in audits),'distinct actual raw sidecar independent transparency/numeric gates')
 controls=('normal','tiny','subnormal','positive-zero','negative-zero','cancellation','overflow','finite-final-normalized-query','finite-final-unscaled-query','cancellation-permuted','gqa-vtile-witness','original-B16-step80','original-B16-step137')
 C.need(d['boundary_controls']==producer['boundary_controls']and [x['case']for x in d['boundary_controls']]==list(controls),'all7 actual NPU boundary controls')
 C.need(set(x['path']for x in mixed_sidecars)|set(x['raw']['path']for x in d['boundary_controls']) <= set(x['path']for x in sidecars),'actual mixed/control refs are in audited full call ledger')
 for b in(1,16):
  mixed=[x for x in rows if x['record']['kind']=='mixed'and x['record']['batch']==b]
  C.need([x['record']['step']for x in mixed]==list(range(160)),'all160 perbatch steps')
  for row in mixed:
   C.need(row['domain_checks_pass']is True and row['all_requests_pass']is True and row['runtime_operand_immutability_pass']is True and not row.get('failure'),'every-step runtime/operand/numeric verdict')
   C.need(all(row['metrics'][k]is True for k in('conv_bitwise','untouched_bitwise','guard_bitwise','inputs_bitwise','pointers_bitwise','prefill_aux_reset_bitwise')),'original independent raw byte verdicts')
   values=row['per_request'];expected=[('independent-decode',j)for j in range(b)]+[('whole-core-native-peer',j)for j in range(b+1)]
   C.need([(x['kind'],x['request'])for x in values]==expected,'all independent and native-peer request identities')
   for x in values:metrics(x,b)
   C.need(row['transition']['local_transition_pass']is True and row['transition']['missing']==[],'complete anchor/state/slotreset/native-runtime transition')
  flush=[x for x in rows if x['record']['kind']=='dead_flush'and x['record']['batch']==b]
  copy=[x for x in rows if x['record']['kind']=='copy'and x['record']['batch']==b]
  C.need(len(flush)==2 and all(x['domain_checks_pass']is True for x in flush)and any(x['metrics']['length0']for x in flush)and any(x['metrics']['partial_live']for x in flush),'both zero/partial deadflush')
  C.need([x['record']['length']for x in copy]==[1,7]and all(x['domain_checks_pass']is True and x['metrics']['descriptors_exact']is True for x in copy),'actual copy1/7 descriptor and byte gates')
 return dict(schema='deltalog.model-actual-precast-diagnostic-load-admission/v045',source=sr,owner=m['bridge024_owner_ref'],consumer=v['independent_consumer'],domain=r['domain_consumer'],original_strict=r['original_strict_consumer'],validation_contract=CONTRACT,library=m['library_ref'],debug_library=m['debug_library'],actual_NPU=True,diagnostic_smoke_admitted=True,independent_local_decode_flush=True,unchanged_native_prefill_boundary=True,model_ready=False,model_numeric_qualified=False,performance_ready=False,task_ready=False,graph=False,PDC=False)

def closure(m):
 refs=[m['bridge024_source_ref'],m['bridge024_owner_ref'],m['reviewed_domain_template_ref']]
 source=C.obj(refs[0]);refs.extend(source['files'].values())
 v=C.obj(refs[1]);refs.extend([v['source'],v['result'],v['independent_consumer']]);refs.extend(C.obj(v['source'])['files'].values())
 r=C.obj(v['independent_consumer']);refs.extend([r['original_strict_consumer'],r['domain_consumer']])
 return refs

def actual_build_meta(m,source,producer):
 br=source['split_build_ref'];C.need(br==source['debug_build_ref']==m['production_build_ref']==m['debug_build_ref'],'one actual051 dual build, not B010 certificate')
 C.need(source['split_kernel_source_ref']==m['split_kernel_source_ref'],'reviewed051 exact kernel source')
 b=C.obj(br);C.need(b['schema']=='deltalog-split-scale-actual-build/v051'and b['primary']is None and b['source_manifest']==m['split_kernel_source_ref']and b['NPU']is False and b['Devices']==[],'actual051 successful immutable build')
 C.need([x['arm']for x in b['artifacts']]==['split_scale_v051','split_scale_sidecar_v051']and [x['library']for x in b['artifacts']]==[m['library_ref'],m['debug_library']]and bool(b['commands'])and all(x['exit_code']==0 and x['error']is None for x in b['commands']),'actual two new libraries and all successful commands')
 for lib in(m['library_ref'],m['debug_library']):C.obj_file(lib)
 cpu_owner=C.obj(m['component_cpu_owner_ref']);C.need(cpu_owner['source']==cpu_owner['target_source']==m['bridge024_source_ref']and cpu_owner['schema']=='deltalog.diagnostic-owned-host/v035'and cpu_owner['stage']=='cpu'and cpu_owner['physical']==[]and cpu_owner['NPU']is False and cpu_owner['primary']is None and cpu_owner['secondary']==[]and cpu_owner['stopped_retained']is True,'actual same-source released CPU owner')
 plan=C.obj(producer['plan']);C.need(plan['source']==m['bridge024_source_ref']and plan['cpu_preflight']==cpu_owner['result'],'actual numerical plan consumed this CPU result')
 cpu=C.obj(cpu_owner['result']);meta=cpu['actual_precast_meta']
 C.need(cpu['source']==m['bridge024_source_ref']and cpu['pass_gate']is True and cpu['NPU']is False,'same-source CPU result, not a template')
 C.need(meta['schema']=='deltalog.split-scale-actual-Meta/v051'and meta['build']==br and meta['source']==m['split_kernel_source_ref']and meta['libraries']==[m['library_ref'],m['debug_library']]and meta['pass_gate']is True and meta['NPU']is False,'actual051 dual Meta ABI before NPU')
 expected=[(a,n,13 if a=='split_scale_v051'else 14)for a in('split_scale_v051','split_scale_sidecar_v051')for n in(1,16)]
 C.need([(x['arm'],x['batch'],x['arguments'])for x in meta['rows']]==expected and all(x['shape']==[x['batch'],12,128]and x['dtype']=='torch.bfloat16'for x in meta['rows']),'all four actual Meta invocation rows')

def admit(reader,m):
 global C
 C=reader
 return consume(m)
