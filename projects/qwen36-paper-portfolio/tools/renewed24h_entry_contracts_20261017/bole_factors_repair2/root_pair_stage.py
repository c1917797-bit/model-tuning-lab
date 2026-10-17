"""Devices[] CPU pre-diagnostic on the same source-closed four old raws."""
import gc,json,os
import decision_gate as G,root_pair as R
def run(t,C,m,sr,out):
 proof=G.consume(C,m['actual_diagnostic_source'],m['actual_diagnostic_owner']);reports=[]
 for pair in proof['ranks']:
  blob=t.load(C.checked(pair['raw']),map_location='cpu',weights_only=False)
  C.need(blob['schema']=='bole.model-diagnostic-primitives/v1'and blob['logical_tensor_bytes']<=2**30,'original bounded saved raw')
  raw=blob['payload'];C.need(raw['source']==G.ORIGINAL_SOURCE and raw['rank']==pair['rank'],'exact source and rank before saved-root comparison')
  result=R.run(t,raw);C.need(result['tree_input_comparison_available']is True,'actual all64 B3-tree/Q1-native input comparison required')
  result.update(diagnostic_source=sr,original_raw=pair['raw'],producer=pair['producer'],NPU=False)
  payload=(json.dumps(result,sort_keys=True,allow_nan=False)+'\n').encode();C.need(len(payload)<=2*2**20,'bounded scalar root-repeat2MiB/rank')
  target=out/('ROOT-PAIR-RANK-%d.json'%pair['rank'])
  with target.open('xb')as f:f.write(payload);f.flush();os.fsync(f.fileno())
  reports.append(C.ref(target));del blob,raw,result;gc.collect()
 return dict(schema='bole.actual-native-root-repeat-pre-diagnostic/v1',source=sr,reports=reports,
   diagnostic_complete=True,NPU=False,operator_executed=False,qualified=False,
   tensor_differences_are_not_automatically_alias_or_nondeterminism_proof=True)
