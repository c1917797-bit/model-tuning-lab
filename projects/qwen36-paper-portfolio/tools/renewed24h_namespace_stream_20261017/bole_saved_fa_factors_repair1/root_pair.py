"""Source-derived native root repeat comparison on original CPU saved raw.

No claim that post-export CPU storage identity reconstructs NPU workspace
lifetime. Saved value equality/differences are reported without an epsilon gate.
"""
import hashlib
def need(v,s):
 if not v:raise ValueError(s)
def tensor(t,a,b):
 need(type(a)is t.Tensor and type(b)is t.Tensor,'actual saved Tensor leaves')
 shape=tuple(a.shape)==tuple(b.shape);dtype=a.dtype==b.dtype
 def sha(x):return hashlib.sha256(x.contiguous().view(t.uint8).numpy().tobytes()).hexdigest()
 out=dict(shape_left=list(a.shape),shape_right=list(b.shape),dtype_left=str(a.dtype),dtype_right=str(b.dtype),
   sha_left=sha(a),sha_right=sha(b),bitwise_equal=shape and dtype and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8)))
 if shape:
  finite=bool(t.isfinite(a).all()and t.isfinite(b).all());out['finite']=finite
  if finite:
   delta=a.double()-b.double();out.update(peak_abs=float(delta.abs().max())if delta.numel()else 0.,relative_l2=float(t.linalg.vector_norm(delta))/max(float(t.linalg.vector_norm(b.double())),1e-30),changed_elements=int((a!=b).sum()))
 return out
def leaves(t,name,a,b,out):
 if type(a)is t.Tensor or type(b)is t.Tensor:
  out.append(dict(field=name,**tensor(t,a,b)));return
 if type(a)in(tuple,list)and type(b)in(tuple,list):
  need(len(a)==len(b),'same actual tuple length')
  for i,(x,y)in enumerate(zip(a,b)):leaves(t,name+'.%d'%i,x,y,out)
  return
 out.append(dict(field=name,bitwise_equal=type(a)is type(b)and a==b,left=a,right=b))
def run(t,raw):
 paths=raw['native'];need([p['child']for p in paths]==[1,2],'two original native AR controls')
 roots=[p['steps'][0]for p in paths];need(all(r['node']==0 for r in roots),'same explicit root node')
 rows=[];first=None;tree_rows=[];initial_equal=True;first_input_equal=None
 for layer in range(64):
  a=roots[0]['context']['captures'][layer];b=roots[1]['context']['captures'][layer];fields=[]
  need(a['kind']==b['kind'],'same native call kind')
  if a['kind']=='gdn-native-AR':
   order=('inputs','a','b','weight','conv_before','state_before','actual_seq','actual_indices',
          'conv_after','normalized_inputs','output','state_after')
  else:
   need(a['kind']=='fa-native-AR','known actual original native kind')
   order=('query','key','value','after_key','after_value','output')
  for name in order:
   need(name in a and name in b,'complete original captured native root field '+name)
   leaves(t,name,a[name],b[name],fields)
  if a['kind']=='gdn-native-AR':
   initial_equal=initial_equal and all(v['bitwise_equal']for v in fields if v['field']in('weight','conv_before','state_before'))
   if layer==0:first_input_equal=all(v['bitwise_equal']for v in fields if v['field']in('inputs','a','b','weight','conv_before','state_before','actual_seq','actual_indices'))
  else:
   prefix=[]
   leaves(t,'prefix_before_root_K',a['after_key'][:-1],b['after_key'][:-1],prefix)
   leaves(t,'prefix_before_root_V',a['after_value'][:-1],b['after_value'][:-1],prefix)
   fields.extend(prefix);initial_equal=initial_equal and all(v['bitwise_equal']for v in prefix)
  changed=[v['field']for v in fields if not v['bitwise_equal']]
  if changed and first is None:first=dict(layer=layer,field=changed[0])
  rows.append(dict(layer=layer,kind=a['kind'],fields=fields,first_differing_field=changed[0]if changed else None))
  if 'tree_context'in raw:
   tree=raw['tree_context']['captures'][layer];comparisons=[]
   for path,root in zip(paths,roots):
    native=root['context']['captures'][layer];fields=[]
    if tree['kind']=='gdn':
     for left,right in(('raw_projected','inputs'),('a','a'),('b','b')):
      leaves(t,left+'.root_B3_vs_Q1',tree[left][:1],native[right],fields)
     leaves(t,'weight',tree['weight'],native['weight'],fields)
     leaves(t,'conv_initial',tree['conv_trial']['initial'],native['conv_before'],fields)
     leaves(t,'state_initial_canonical_DkDv',tree['state'],native['state_before'].transpose(-1,-2),fields)
     leaves(t,'conv_after_root',tree['actual_conv_tail'][0:1],native['conv_after'],fields)
     q,k,v,g,beta=native['normalized_inputs'];tq,tk,tv,tb,tgamma=tree['normalized_inputs']
     need(q.shape==k.shape==(1,1,4,128)and v.shape==(1,1,12,128)and g.shape==beta.shape==(1,1,12),
          'actual source-known native GQA Q/K/V/g/beta layout, no blind reshape')
     # Explicit source-known semantic join: candidate expands4QK->12V,
     # scales Q outside verifier, and stores exp(g) rather than native log-g.
     operands=(tq[:,:,0],tk[:,:,0],tv[:,:,0],tb[:,:,0],tgamma[:,:,0])
     native_operands=(q[:,0].float().repeat_interleave(3,dim=1)*(128**-.5),
       k[:,0].float().repeat_interleave(3,dim=1),v[:,0].float(),beta[:,0].float(),g[:,0].float().exp())
     for name,left,right in zip(('normalized_Q_scaled','normalized_K','normalized_V','beta','gamma_CPU_exp_native_log_g'),operands,native_operands):leaves(t,name,left,right,fields)
     leaves(t,'output_root_B3_vs_Q1',tree['output'][:1],native['output'],fields)
     leaves(t,'state_after_root_canonical_DkDv',tree['actual_node_states'][0],native['state_after'].transpose(-1,-2),fields)
    else:
     for name in('query','key','value'):leaves(t,name+'.root_B3_vs_Q1',tree[name][:1],native[name],fields)
     leaves(t,'output_root_B3_vs_Q1',tree['output'][:1],native['output'].reshape(1,6,256),fields)
    comparisons.append(dict(native_path_child=path['child'],fields=fields,
      comparison_scope='actual B3-tree root versus actual Q1-native control; not a shape-invariant numeric theorem'))
   tree_rows.append(dict(layer=layer,comparisons=comparisons))
 tail=[]
 for name in('hidden','logits'):leaves(t,name,roots[0][name],roots[1][name],tail)
 all_steps=[s for path in paths for s in path['steps']]
 pairwise=[]
 for i in range(4):
  for j in range(i+1,4):
   fields=[];leaves(t,'hidden',all_steps[i]['hidden'],all_steps[j]['hidden'],fields)
   pairwise.append(dict(left_step=i,right_step=j,left_node=all_steps[i]['node'],right_node=all_steps[j]['node'],hidden_fields=fields))
 return dict(schema='bole.actual-native-root-repeat-saved-values/v1',rank=raw['rank'],source=raw['source'],
  first_actual_saved_operand_difference=first,layers=rows,whole_root_hidden_logits=tail,all_four_step_hidden_pairs=pairwise,
  tree_root_vs_each_native=tree_rows,tree_input_comparison_available=len(tree_rows)==64,
  first_root_input_identical=first_input_equal,all_initial_cache_and_weights_identical=initial_equal,
  root_context_positions=[r['context']['positions']for r in roots],root_context_tokens=[r['context']['tokens']for r in roots],
  saved_CPU_storage_is_not_original_NPU_alias_proof=True,qualified=False,original_failures_unchanged=True)
