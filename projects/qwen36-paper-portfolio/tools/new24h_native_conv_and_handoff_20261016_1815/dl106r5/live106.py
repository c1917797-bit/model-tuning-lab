"""Outside-timing receiver; any sticky failure rejects the entire run."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));import qualification106 as Q
def validate_snapshot(value,sr,qref,*,minimum_candidate=1):
 Q.qualify(qref,sr);Q.need(value['schema']=='deltalog.production-worker/v106'and value['source_ref']==sr and value['qualification_ref']==qref,'actual source-qualified worker snapshot')
 Q.need(value['mode']=='bounded-production'and value['tensor_capture']is False and value['native_peer']is False and all(value[k]is False for k in('graph','async_scheduling','PDC')),'no diagnostic/graph contamination')
 Q.need(value['synchronization_outside_timing']is True and value['tensor_snapshot']is False and value['receipt_trigger']=='SIGUSR1 outside timed client interval','no snapshot synchronization in timed requests')
 h=value['health'];Q.need(h['outside_timing']is True and h['all_finite']is True and h['rows']and all(v['finite']is True and v['observations']>0 for v in h['rows'].values()),'sticky health invalidates entire run, never clear for next request')
 Q.need(value['actual_common_precision']==dict(matmul_allow_hf32=False,conv_allow_hf32=False),'actual common HF32 policy')
 Q.need(value['mapped_rows']and value['library']==Q.source(sr)['library_ref']and len(value['prefixes'])==48,'real051 mapping and all48')
 Q.need(all(r['candidate']>=minimum_candidate and r['finished_steps']>0 for r in value['prefixes'].values()),'all48 actually executed and finished')
 return dict(schema='deltalog.production-worker-validation/v106',source=sr,qualification=qref,pass_gate=True,all48=True,health_never_failed=True)
def validate_delta(before,after,sr,qref,*,expected_decode_calls):
 Q.need(type(expected_decode_calls)is int and expected_decode_calls>0,'actual HTTP-produced decode count required')
 validate_snapshot(before,sr,qref);validate_snapshot(after,sr,qref)
 Q.need(before['pid']==after['pid']and before['actual_core_id']==after['actual_core_id']and before['actual_target']==after['actual_target']and set(before['prefixes'])==set(after['prefixes']),'same actual worker/target over measured interval')
 for prefix,b in before['prefixes'].items():
  a=after['prefixes'][prefix];Q.need(a['self_id']==b['self_id']and a['arena']==b['arena']and a['core_id']==b['core_id']and a['candidate']-b['candidate']==expected_decode_calls and a['finished_steps']>b['finished_steps'],'exact actual all48 measured dispatch delta; no event-count performance substitute')
 Q.need(after['ordinal']>before['ordinal'],'ordered outside-timing snapshots')
 return dict(schema='deltalog.production-dispatch-delta/v106',source=sr,pass_gate=True,all48=True,actual_decode_calls_per_layer=expected_decode_calls)
