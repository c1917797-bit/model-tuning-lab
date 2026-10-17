"""Independent CPU comparison of saved immediate owning witnesses.

No recomputation or altered epsilon. This is earliest observed *boundary*
attribution, not proof of native correctness or a BOLE qualification.
"""
def need(v,s):
 if not v:raise ValueError(s)

def same(t,a,b):
 return a.dtype==b.dtype and tuple(a.shape)==tuple(b.shape)and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8))

def consume(t,raw,m):
 w=raw['root_repeat_witness']
 need(w['schema']=='bole.immediate-native-root-witness/v1'and w['numerical_qualification']is False and
  w['owner']==raw['request']and w['owner']['length']==131,'original strong owner joined to saved root witnesses')
 need(w['source_refs']=={k:m['runtime_sources'][k]for k in('qwen_patch','gdn','qwen_next')},'exact active installed source pins')
 need([c['node']for c in w['calls']]==[0,1,0,2]and
  [c['tokens'][0]for c in w['calls']]==[raw['tree_context']['tokens'][i]for i in(0,1,0,2)]and
  [c['positions']for c in w['calls']]==[[131],[132],[131],[132]],'original exact four AR calls and root tokens')
 rows=w['rows'];pairs={};used=0;first=None;private_faults=[];source_reuse=[];comparisons=[]
 for r in rows:
  need(r['call']in range(4)and r['kind']in('decoder','gdn','model'),'typed saved witness key')
  key=(r['kind'],r['layer'],r['stage'])
  if r['kind']!='model':need(r['call']in(0,2)and r['layer']in(0,1),'first two actual root layers only')
  for name,v in r['tensors'].items():
   x=v['immediate'];need(x.device.type=='cpu'and x.numel()*x.element_size()<=65536,'small saved CPU owning witness')
   used+=x.numel()*x.element_size()
   need(list(x.shape)==v['source_identity']['shape']and str(x.dtype)==v['source_identity']['dtype'],'source shape/dtype exact, no casts')
   need(v['source_identity']['storage']!=v['private_identity']['storage'],'private GPU clone distinct actual storage')
   expected=[*range(r['call'],4),'before_export'];life=v['lifetime']
   need([a['after_call']for a in life]==expected,'complete future-four-forward clone lifetime observations')
   if any(not a['private_identity_equal']or not a['private_bits_equal']for a in life):private_faults.append(dict(call=r['call'],key=list(key),field=name,lifetime=life))
   if any(not a['original_bits_equal']or not a['original_geometry_equal']for a in life):source_reuse.append(dict(call=r['call'],key=list(key),field=name,lifetime=life))
   if 'changed_private'in v:used+=v['changed_private'].numel()*v['changed_private'].element_size()
  if r['call']in(0,2):
   k=(r['call'],key);need(k not in pairs,'one capture per exact native boundary');pairs[k]=r
 for r in rows:
  if r['call']!=0:continue
  key=(r['kind'],r['layer'],r['stage']);other=pairs.get((2,key));need(other is not None and other['none']==r['none']and set(other['tensors'])==set(r['tensors']),'complete matching native root boundary sets')
  for name,v in r['tensors'].items():
   a=v['immediate'];b=other['tensors'][name]['immediate'];eq=same(t,a,b)
   shape_equal=a.shape==b.shape and a.dtype==b.dtype
   if shape_equal:
    changed=int((a.contiguous().view(t.uint8)!=b.contiguous().view(t.uint8)).sum().item())
    finite=bool(t.isfinite(a).all()and t.isfinite(b).all())
    peak=float((a.double()-b.double()).abs().max().item())if a.numel()and finite else None
   else:changed=None;finite=False;peak=None
   result=dict(key=list(key),field=name,bitwise_equal=eq,changed_bytes=changed,finite=finite,peak_abs=peak)
   comparisons.append(result)
   if not eq and first is None:first=result
 need(used==w['tensor_bytes']<=w['tensor_cap']==2*2**20-64*2**10 and w['retained_cpu_plus_private_gpu_cap']==4*2**20 and w['scratch_cap']==128*2**10,'original additional evidence budget inside rank cap')
 need(set(pairs)=={(call,key)for call in(0,2)for key in {k for c,k in pairs}},'matching exact root boundary chronology')
 for call in(0,2):
  for layer in(0,1):
   for kind,stages in(('decoder',('entry','input_norm','attention_complete','post_norm_input','post_norm_output','mlp_output','return')),
                       ('gdn',('entry','projection_complete','core_complete','gated_norm_input','gated_norm_output','out_proj_input','return'))):
    actual=[r['stage']for r in rows if(r['call'],r['kind'],r['layer'])==(call,kind,layer)]
    need(actual==list(stages),'independent complete per-root boundary traversal')
 need([(r['call'],r['stage'])for r in rows if r['kind']=='model']==[(i,'immediate_final_hidden')for i in range(4)],'all4 immediate final model returns')
 legacy=[];need(len(raw['native'])==2,'both original independent native AR paths retained')
 for path,call in zip(raw['native'],(0,2)):
  need(path['steps'][0]['node']==0,'same original native root step')
  step=path['steps'][0]
  hidden=step['hidden'][0]if type(step['hidden'])in(tuple,list)else step['hidden']
  joins=[('model',None,'immediate_final_hidden','hidden',hidden)]
  for layer in(0,1):
   old=step['context']['captures'][layer]
   joins.extend([('gdn',layer,'projection_complete','mixed_qkv',old['inputs']),
    ('gdn',layer,'projection_complete','a',old['a']),('gdn',layer,'projection_complete','b',old['b']),
    ('gdn',layer,'core_complete','core_attn_out',old['output'])])
  for kind,layer,stage,field,old in joins:
   now=pairs[(call,(kind,layer,stage))]['tensors'][field]['immediate']
   legacy.append(dict(call=call,key=[kind,layer,stage],field=field,late_legacy_equals_immediate=same(t,old,now)))
 return dict(schema='bole.independent-immediate-root-boundary-attribution/v1',diagnostic_complete=True,
  comparisons=comparisons,first_immediate_root_difference=first,private_clone_lifetime_faults=private_faults,
  original_tensor_reuse=source_reuse,late_legacy_capture_joins=legacy,all_original_four_forwards_preserved=True,
  status='private-clone-mutation'if private_faults else'immediate-root-values-differ'if first else'not-reproduced-at-observed-boundaries',
  observer_may_perturb=True,native_mathematical_pass=None,BOLE_qualified=False,
  limits=['boundary attribution only; no new epsilon','equal saved core does not prove equal residual/z/norm/MLP','unreproduced is inconclusive; tracing synchronizes small operands'])
