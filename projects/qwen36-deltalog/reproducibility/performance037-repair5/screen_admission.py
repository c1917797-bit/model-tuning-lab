"""DL-specific source/actual032/full031/production-validation admission."""
import importlib.util,json,time,math
from pathlib import Path
from types import SimpleNamespace
from qwen36_deltalog_screen import admission as A
P=Path(__file__).resolve().parent
CUT=1792135097
checked=lambda r: Path(r['path']) if A.ref(r['path'])==r else A.need(False,'exact Ref3')
source=A.source

def load(r,name):
 checked(r);s=importlib.util.spec_from_file_location(name,r['path']);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def terminal(r,entry,sr):
 value=A.obj(r);v=value.get('structuredContent',value);A.need(v.get('routeDecision')in('peer_direct','upstream_local_peer'),'actual terminal direct route')
 rec=v['result']['record'];A.need(rec['state']=='completed'and rec['exitCode']==0 and not rec['cancelled']and not rec['timedOut'],'actual successful terminal')
 args=rec['args'];cmd=rec['command']
 if cmd=='/usr/bin/prlimit':
  A.need(args[:3]==['--as=536870912:unlimited','--','/usr/bin/python3'],'only declared host prlimit wrapper');args=args[3:]
 else:A.need(cmd=='/usr/bin/python3','actual host interpreter')
 A.need(len(args)==6 and args[:5]==['-I','-B',str(P/entry),'--execute','--source-ref']and json.loads(args[5])==sr,'exact source-bound validation command')

def validate_production(owner_ref,terminal_ref,sr):
 m=source(sr)
 o=A.obj(owner_ref);A.need(o['schema']=='deltalog.production-validation-owned/v033'and o['source']==sr and o['primary']is None and o['secondary']==[] and o['stopped_retained']is True,'owned production numeric validation/release')
 cleanup=A.obj(o['cleanup']);A.need(not cleanup['errors'] and cleanup['stopped'] and cleanup['retained'],'actual own cleanup')
 import finite_numeric as F
 v=A.obj(o['numeric']);A.need(v['schema']=='deltalog.production-finite-domain-validation/v037-repair2'and v['source']==sr and v['NPU']is True and v['validation_contract']==F.CONTRACT and v['library']==m['library_ref']and v['decode_direct_RNE_pass']is True and v['decode_health_negative_synthetic_output']is True and v['finite_domain_equal']is True and v['invalid_live_whole_arm_rejected']is True and v['dead_nan_pass']is True and v['steps_checked']>=32 and v['batches']==[1,16],'actual production NPU decode/direct-RNE/health/flush finite validation')
 A.need(v['operator_schema']==m['operator_schema']and v['mapped_library']and all(len(line.split(None,5))==6 and line.split(None,5)[5]==str(Path(m['library_ref']['path']).resolve())for line in v['mapped_library']),'actual same original DSO maps/operator ABI')
 for name,expected in(('valid_health',True),('invalid_health',False),('decode_invalid_health',False)):
  h=v[name];A.need(h['schema']=='deltalog.production-device-health/v033'and h['all_finite']is expected and h['outside_timing']is True and h['synchronization_performed']is True and h['rows'],'actual separate positive/negative health outcomes outside timing')
 A.need(v['inputs']==m['validation_inputs_ref'] and len(v['rows'])==320 and all([x['step']for x in v['rows']if x['batch']==b]==list(range(160)) for b in (1,16)),'whole source-bound160 production replay')
 for row in v['rows']:
  d=row['decode'];A.need(all(d[k]is True for k in('saved_output_bitwise','active_state_bitwise','inactive_guard_bitwise','input_bitwise','health_observed'))and len(d['requests'])==row['batch']and [r['row']for r in d['requests']]==list(range(row['batch']))and all(r['request_pass']is True and all(type(r[k])in(int,float)and math.isfinite(r[k])and r[k]>=0 for k in('state_error','output_error','uncast_CPU64_output_error','BF16_RNE_floor'))and r['state_error']<=7.92e-7 and r['output_error']<=.00303 for r in d['requests']),'complete original320 decode-health independent per-request verdicts')
 terminal(terminal_ref,'host_validate.py',sr);return v

def qualify(qref,sr):
 m=source(sr);q=A.obj(qref)
 A.need(q['schema']=='deltalog.production-screen-prerequisites/v037'and q['source']==sr and q['scope']=='one-sync-eager-screen-only','new actual DL screen qualification')
 A.need(m['mode']=='performance-screen-only' and m['preregistered_domain_component_reuse']is True,'explicit independently reviewed finite-domain component reuse')
 api=m['model_smoke_api_ref'];pins=m['model_smoke_pins_ref'];checked(api);checked(pins)
 A.need(Path(api['path']).with_name('DOMAIN_PINS.json')==Path(pins['path']),'actual032 API adjacent immutable pins')
 module=load(api,'_actual032_smoke_consumer_for033');C=SimpleNamespace(obj=A.obj,checked=checked,need=A.need)
 p=q['smoke_plan'];A.need(p['production_source_ref']==m['diagnostic_predecessor_ref'],'explicit023 predecessor, not a false production-source identity')
 A.need(p==m['model_smoke_plan'],'same actualMODEL036 smoke frozen at source binding')
 s=module.consume(C,p)
 A.need(s['schema']=='deltalog.actualMODEL036R5-model-diagnostic-smoke/v037-repair5'and s['all4x48_dispatch']is True and s['selected_numeric_pass']is True and s['performance_ready']is False and s['model_numeric_qualified']is False,'actual boundedMODEL036 source/dispatch/selected numerical evidence, not full model acceptance')
 b=A.obj(p['qualification_ref']);A.need(b['schema']=='deltalog.diagnostic-owned-host/v035'and b['target_source']==p['bridge_source_ref']and b['steps']==160 and b['primary']is None and not b['secondary'] and b['stopped_retained']is True and b['diagnostic_capture_complete']is True,'actual successful original035 full160 relevant bridge before formal screen')
 d=A.obj(b['independent_consumer']);A.need(d['schema']=='deltalog.diagnostic-consumption/v035'and d['diagnostic_capture_complete']is True and d['domain_checks_pass']is True,'actual closed035 domain bridge evidence')
 domain=A.obj(d['domain_consumer']);A.need(domain['schema']=='deltalog.direct-RNE-domain-audit/v035'and not domain['failures']and not domain['missing_evidence']and domain['domain_checks_pass']is True and domain['diagnostic_qualified']is False,'retain original035 diagnostic scope/oldFAIL; no missing gate')
 A.need(d['validation_contract']==domain['validation_contract']and domain['validation_contract']['schema']=='deltalog.independent-CPU64-operational-recurrence-direct-integer-BF16-RNE/v035','same reviewed new035 reference domain')
 inputs=A.obj(m['validation_inputs_ref']);A.need(inputs['producer_ref']==b['result']and inputs['source031_ref']==p['bridge_source_ref'],'production finite-domain comparison uses SAME actual031 raw')
 A.need(q['composite_source_ref']==m['composite_source_ref'],'same underlying component022')
 validate_production(q['production_validation_owner_ref'],q['production_validation_terminal_ref'],sr)
 return q

def readset(qref):
 q=A.obj(qref);m=source(q['source']);C=SimpleNamespace(obj=A.obj,checked=checked,need=A.need)
 api=load(m['model_smoke_api_ref'],'_actual032_closure_for033');refs=[qref,*m['files'].values(),*m['dependencies'],m['model_smoke_api_ref'],m['model_smoke_pins_ref'],m['diagnostic_predecessor_ref'],q['production_validation_owner_ref'],q['production_validation_terminal_ref']]
 refs.extend(api.closure(C,q['smoke_plan']))
 b=A.obj(q['smoke_plan']['qualification_ref']);refs.extend([b['independent_consumer'],b['result']]);d=A.obj(b['independent_consumer']);refs.extend([d['domain_consumer'],d['original_strict_consumer']])
 owner=A.obj(q['production_validation_owner_ref']);refs.extend([owner['numeric'],owner['cleanup']])
 for r in refs:checked(r)
 return refs
