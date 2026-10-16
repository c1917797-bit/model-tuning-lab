# Appended before execution by the thin generator; oracle is unchanged.
def per_request_metrics(torch,R,raw,D):
 import precast
 old=original_per_request_metrics(torch,R,raw,D);cap=raw['captures']['decode'][0];side=torch.load(checked(cap['actual_sidecar043']),map_location='cpu',weights_only=False);i=cap['inputs'];slots=i['ssm_state_indices'].flatten().tolist();truth=[]
 truth=[row['_independent_truth043']for row in old if row['kind']=='independent-decode']
 for row in old:row.pop('_independent_truth043',None)
 expected=torch.stack(truth)
 need(len(side['before'])==len(side['after'])==len(side['debug_after'])==13,'complete all13 operand capture')
 need(len(side['debug_before'])==13 and all(same(torch,a,b)for a,b in zip(side['before'],side['debug_before'])),'actual production/debug before byte join')
 need(all(same(torch,a,b)for a,b in zip(side['after'],side['debug_after'])),'actual production/debug operands and six states bytes')
 need(all(same(torch,side['before'][k],side['after'][k])for k in(0,1,2,3,4,11,12)),'actual input/sequence/slot byte immutability')
 need(all(same(torch,side['before'][5+k],cap['before'][name])for k,name in enumerate(FIELDS)),'debug before joins actual captured before')
 need(all(same(torch,side['before'][k],i[name])for k,name in enumerate(('query','key','value','g','beta'))),'actual kernel input joins independent oracle')
 need(same(torch,side['before'][11],i['actual_seq_lengths'])and same(torch,side['before'][12],i['ssm_state_indices']),'actual kernel metadata joins oracle row/slot mapping')
 need(all(same(torch,side['after'][5+k][slots],raw['state'][name][slots])for k,name in enumerate(FIELDS)),'actual postdecode states join whole-core selected slots')
 need(same(torch,side['production_output'],cap['output'])and same(torch,side['production_output'],side['debug_output']),'production/debug and wholecore output joins')
 need(side['pointers_before']==side['pointers_after'] and side['sidecar_redzones_pass']is True,'actual pointer/sidecar guard capture')
 need(same(torch,side['sidecar_guards_before'],side['sidecar_guards_after']),'actual sidecar guard bytes independent')
 result=precast.evaluate(torch,side['actual_precast_FP32'],cap['output'],expected)
 for row in old:
  row['old_point_pass']=row['request_pass'];row['old_output_error']=row['output_error']
  if row['kind']=='independent-decode':
   q=result['requests'][row['request']];row['actual_precast']=q;row['cast_bitwise']=result['cast_bitwise'];row['request_pass']=q['passed']and result['cast_bitwise']and result['finite']and row['state_error']<=R.STATE_LIMIT
  else:row['request_pass']=bounded(row,R)if row['request']==len(slots)else row['state_error']<=R.STATE_LIMIT # unchanged native prefill peer remains hard; decode peer point stays diagnostic.
 return old
