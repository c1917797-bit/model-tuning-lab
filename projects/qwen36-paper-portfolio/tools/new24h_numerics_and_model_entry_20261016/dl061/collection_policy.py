"""Registered diagnostic capture policy; never a numerical qualification."""
import math
POLICY=dict(schema='deltalog.BF16-point-deferred-collection/v043-repair3',old_BF16_output_point_diagnostic_only=True,old_output_limit=.00303,state_limit=7.92e-7,finite_and_byte_guards_hard=True,raw_collection_only=True,qualified=False)
FLAGS=('finite','untouched_bitwise','pointers_stable','inputs_unchanged','copy_source_unchanged','owner_isolated','redzones_unchanged')

def reject(output_error,state_error,row,diagnostics,output_limit,state_limit):
 # This is not changed device arithmetic. Only the former BF16 point gate may
 # be deferred, under the explicit producer-only diagnostic opt-in. A complete
 # raw set still has to pass the separate real FP32/domain CPU consumer.
 if type(output_error)not in(int,float)or type(state_error)not in(int,float)or not all(math.isfinite(x)and x>=0 for x in(output_error,state_error)):return True
 if state_error>state_limit or not all(row[n]for n in FLAGS):return True
 deferred=diagnostics is not None and getattr(diagnostics,'defer_BF16_point_gate',False)is True
 return output_error>output_limit and not deferred

def require_complete(C,producer,sr):
 C.need(producer['schema']=='deltalog.actual-fresh-bridge/v5'and producer['source']==sr and producer['primary']is None and producer['steps']in(16,160),'actual completed producer; partial/old failed output retained but not qualified')
 C.need(producer['collection_policy']==POLICY and producer['NPU']is True and producer['graph']is False and producer['fullmodel']is False,'only explicit registered collection, never numerical/model PASS')
 steps=producer['steps'];records=producer['records']
 C.need(len(records)==2*steps+8,'complete actual mixed/flush/copy record count')
 for batch in(1,16):
  C.need([r['step']for r in records if r['kind']=='mixed'and r['batch']==batch]==list(range(steps)),'every original per-batch mixed step; no gap/duplicate/partial promotion')
  C.need(len([r for r in records if r['kind']=='dead_flush'and r['batch']==batch])==2,'both actual zero/partial dead flush records')
  C.need([r['length']for r in records if r['kind']=='copy'and r['batch']==batch]==[1,7],'both actual copy1/7 records')
 side=producer['actual_sidecar_records'];mixed=producer['actual_mixed_sidecar_records'];controls=producer['boundary_controls']
 C.need(len(side)==2*steps+31 and len({r['path']for r in side})==len(side)and len(mixed)==2*steps and len({r['path']for r in mixed})==len(mixed),'complete unique actual sidecar ledger; 345 required at160')
 C.need([r['case']for r in controls]==['normal','tiny','subnormal','positive-zero','negative-zero','cancellation','overflow','finite-final-normalized-query','finite-final-unscaled-query','cancellation-permuted','gqa-vtile-witness','original-B16-step80','original-B16-step137'],'all13 actual boundary controls retained')
 C.need({r['path']for r in mixed}|{r['raw']['path']for r in controls}<={r['path']for r in side},'actual mixed/control membership in complete sidecar ledger')
 return True
