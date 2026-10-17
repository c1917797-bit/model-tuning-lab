"""CPU-only independent math and complete native-AR discrepancy diagnostics.

No whole-model hidden/logit epsilon is asserted. Existing component bounds
are retained unchanged. Full vectors are returned for bounded persistence.
"""
from model_entry import need


def bits(t,a,b):return a.shape==b.shape and a.dtype==b.dtype and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8))


def difference(t,a,b):
 need(a.shape==b.shape and bool(t.isfinite(a).all()and t.isfinite(b).all()),'finite same-shape actual/native numerical tensors')
 delta=a.double()-b.double();peak=float(delta.abs().max())
 norm=float(t.linalg.vector_norm(b.double()));rel=float(t.linalg.vector_norm(delta)/max(norm,1e-30))
 return dict(peak_abs=peak,relative_l2=rel,reference_l2=norm),delta


def old112(t,actual,truth):
 need(actual.dtype==t.float32 and actual.shape==truth.shape,'original112 actual FP32 ABI')
 metric,_=difference(t,actual,truth);scale=float(truth.abs().max())
 metric['passed']=metric['peak_abs']<=2e-5+2e-4*scale and metric['relative_l2']<=2e-4
 return metric


def conv(t,row,anchor):
 trial=row['conv_trial'];initial=anchor['full_conv_slot'][0,:3]
 need(bits(t,initial,anchor['native_prefill_raw_last3'])and
      bits(t,anchor['full_conv_slot'][0,3:],anchor['native_extra_before'])and
      bits(t,trial['initial'][0],initial), 'actual native prefill tail/extras/isolated tree anchor join')
 x=row['raw_projected'];w=row['weight'].double();truth=[];tails=[]
 for path in((0,),(0,1),(0,2)):
  history=t.cat((initial,t.stack([x[n]for n in path])),dim=0)
  local=history[-4:].double();value=(local*w.T).sum(0)
  if row['activation']:value=value/(1+(-value).exp())
  truth.append(value);tails.append(history[-3:])
 truth=t.stack(truth);tails=t.stack(tails)
 need(row['actual_convolved'].dtype==t.bfloat16 and row['actual_convolved'].shape==truth.shape,'actual unchanged native conv BF16 ABI')
 error=(row['actual_convolved'].double()-truth).abs()
 return dict(output_bound_pass=bool(t.isfinite(row['actual_convolved']).all()and(error<=.001+.01*truth.abs()).all()),
             state_bitwise=bits(t,row['actual_conv_tail'],tails),peak_abs=float(error.max()))


def attention(t,row,anchor):
 q=row['query'].reshape(3,6,256);k=row['key'].reshape(3,1,256);v=row['value'].reshape(3,1,256)
 need(q.dtype==k.dtype==v.dtype==row['output'].dtype==t.bfloat16,'actual model FA input/output BF16')
 table=list(anchor['physical_pages']);need(len(table)==2 and len(set(table))==2,'actual131token physical prefix pages')
 pages_k={p:anchor['key'][i]for i,p in enumerate(table)};pages_v={p:anchor['value'][i]for i,p in enumerate(table)}
 pk=t.stack([pages_k[table[p//128]][p%128,0]for p in range(131)])
 pv=t.stack([pages_v[table[p//128]][p%128,0]for p in range(131)])
 refs=[]
 for dtype in(t.float64,t.float32):
  values=[]
  for node,path in enumerate(((0,),(0,1),(0,2))):
   keys=t.cat((pk,t.stack([k[j,0]for j in path]))).to(dtype)
   vals=t.cat((pv,t.stack([v[j,0]for j in path]))).to(dtype);heads=[]
   for h in range(6):
    logits=keys.mv(q[node,h].to(dtype))*(256**-.5);prob=(logits-logits.max()).exp();prob/=prob.sum();heads.append(vals.T.mv(prob))
   values.append(t.stack(heads))
  refs.append(t.stack(values))
 output=row['output'];results=[]
 for ref in refs:
  need(output.shape==ref.shape,'actual three-node FA output shape')
  error=(output.double()-ref.double()).abs()
  results.append(dict(pointwise_pass=bool(t.isfinite(output).all()and(error<=.001+.01*ref.double().abs()).all()),peak_abs=float(error.max())))
 return dict(double=results[0],float=results[1])


def consume(t,raw,oracle):
 need(raw['schema']=='bole.actual-three-node-model-capture/v1'and raw['scheduler_committed']is False,'actual bounded model diagnostic, not service commit')
 tree=raw['tree_context'];captures=tree['captures']
 observed=raw['actual_native_prefill_input'];ids=raw['actual_native_prefill_ids']
 need(ids.dtype==t.int32 and ids.shape==(131,)and bits(t,observed['actual_token_ids'],ids)and
      ids.tolist()==observed['actual_CPU_token_ids']==observed['request_prompt_token_ids']and
      observed['no_mm_features']is True and observed['no_soft_prompt']is True,'source-bound actual native int32 token inputs/strong request/CPU row')
 need(observed['actual_input_mode']in('native-token-ids','native-text-embeddings'),'only source-proven native text route')
 if observed['actual_input_mode']=='native-text-embeddings':
  need(bits(t,observed['actual_native_embeddings'],observed['independent_token_embeddings'])and
       observed['actual_native_embeddings'].shape==(131,5120)and observed['actual_native_embeddings'].dtype==t.bfloat16,
       'actual native BEFORE-forward embeddings equal independently source-pinned text-token lookup')
 expected=[(i,'fa'if i%4==3 else'gdn')for i in range(64)]
 need([tuple(x)for x in tree['order']]==expected and set(captures)==set(range(64)),'all actual64 layers exactly once')
 owner=raw['request'];need(owner['length']==131 and tree['owner']==owner,'same actual first prefix/owner')
 native=raw['native'];need([p['child']for p in native]==[1,2]and all([s['node']for s in p['steps']]==[0,p['child']]for p in native),'two actual native root-child paths')
 for path in native:
  for step in path['steps']:
   need([tuple(x)for x in step['context']['order']]==expected,'each native AR token visited all64 actual layers')
 initial_g={r['layer']:r for r in raw['actual_native_initial_GDN']};initial_f={r['layer']:r for r in raw['initial_FA_pages']}
 need(len(initial_g)==48 and len(initial_f)==16,'complete actual independent prefill anchors')
 rows=[];vectors={};component=True
 for i,kind in expected:
  row=captures[i];metrics=dict(layer=i,kind=kind);vector={}
  if kind=='gdn':
   anchor=initial_g[i];base=anchor['initial_native_state'].transpose(-1,-2).unsqueeze(0)
   need(bits(t,row['state'],base),'candidate before independently joined to actual native prefill state')
   q,k,v,beta,gamma=row['normalized_inputs']
   need(q.shape==k.shape==v.shape==(1,12,3,128)and beta.shape==gamma.shape==(1,12,3)and
        all(x.dtype==t.float32 for x in(q,k,v,beta,gamma))and
        row['precast_output'].shape==(1,12,3,128)and row['actual_node_states'].shape==(3,1,12,128,128),
        'complete actual TP4 GDN4QK→12V/D128 three-node FP32 math')
   truth,states,updates=oracle.sequential(t,q.double(),k.double(),v.double(),beta.double(),gamma.double(),base.double(),(-1,0,0),return_updates=True)
   metrics['FP32_output']=old112(t,row['precast_output'],truth)
   metrics['U']=old112(t,row['factors'][1],updates)
   gd=gamma.double();product=t.stack((gd[...,0],gd[...,0]*gd[...,1],gd[...,0]*gd[...,2]),dim=-1)
   metrics['P']=old112(t,row['factors'][0],product)
   metrics['local_states']=[old112(t,row['actual_node_states'][node],states[node])for node in range(3)]
   metrics['conv']=conv(t,row,anchor)
   need(bits(t,row['output'],row['precast_output'].permute(0,2,1,3).squeeze(0).to(t.bfloat16)),'actual model output copied from actual FP32 tree output')
   component=component and metrics['FP32_output']['passed']and metrics['U']['passed']and metrics['P']['passed']and all(x['passed']for x in metrics['local_states'])and metrics['conv']['output_bound_pass']and metrics['conv']['state_bitwise']
  else:
   metrics['attention']=attention(t,row,initial_f[i]);component=component and all(x['pointwise_pass']for x in metrics['attention'].values())
  metrics['whole_native_discrepancies']=[]
  for path in native:
   for step in path['steps']:
    node=step['node'];control=step['context']['captures'][i]
    a=row['output'][node]if kind=='gdn'else row['output'][node]
    n=control['output'].reshape_as(a)
    value,delta=difference(t,a,n);item=dict(path=path['child'],node=node,output=value)
    vector[(path['child'],node,'output')]=delta
    if kind=='gdn':
     a=row['actual_node_states'][node,0];n=control['state_after'][0].transpose(-1,-2)
     value,delta=difference(t,a,n);item['state']=value;vector[(path['child'],node,'state')]=delta
    metrics['whole_native_discrepancies'].append(item)
  vectors[i]=vector;rows.append(metrics)
 hidden=raw['tree_hidden'][0]if type(raw['tree_hidden'])in(tuple,list)else raw['tree_hidden']
 target=raw['staged']['actual_target_logits'];whole=[];greedy=True
 need(hidden.shape==(3,5120)and target.ndim==2 and target.shape[0]==3 and target.dtype==t.float32,
      'actual target final normalized hidden and three complete vocabulary rows')
 mtp=raw['genuine_MTP']
 need(bits(t,raw['actual_native_prefill_ids'],mtp['target_token_ids'])and
      bits(t,raw['actual_native_prefill_positions'],mtp['target_positions'])and
      bits(t,raw['actual_native_prefill_hidden'],mtp['target_hidden_states']),
      'genuine original MTP consumed exactly this actual native target prefill')
 for path in native:
  for step in path['steps']:
   node=step['node'];h=step['hidden'][0]if type(step['hidden'])in(tuple,list)else step['hidden']
   hm,hd=difference(t,hidden[node:node+1],h);lm,ld=difference(t,target[node:node+1],step['logits'])
   same=int(target[node].argmax())==int(step['logits'][0].argmax());greedy=greedy and same
   whole.append(dict(path=path['child'],node=node,hidden=hm,logits=lm,argmax_equal=same))
   vectors[('whole',path['child'],node)]=dict(hidden=hd,logits=ld)
 # Independently derive the inclusive accepted path from actual target logits.
 tokens=tree['tokens'];next_root=int(target[0].argmax());terminal=1 if next_root==tokens[1]else 2 if next_root==tokens[2]else 0
 path=(0,)if terminal==0 else(0,terminal);staged=raw['staged']
 need(tuple(staged['processed_nodes'])==path and tuple(staged['decision']['processed_nodes'])==path,
      'actual staged accepted path independently matches genuine target logits')
 writes=staged['writes'];transaction=raw['transaction']
 expected_dest={(i,k)for i,kind in expected for k in(('state','conv')if kind=='gdn'else('key','value'))}
 need(len(writes)==128 and {(r['layer'],r['kind'])for r in writes}==expected_dest and
      len(transaction['actual_applied'])==len(transaction['actual_restored'])==128 and
      transaction['scheduler_committed']is False, 'complete actual128 destination write/restore ledger')
 for n,write in enumerate(writes):
  layer=write['layer'];kind=write['kind'];row=captures[layer]
  if kind=='state':value=row['actual_node_states'][terminal,0].transpose(-1,-2).contiguous()
  elif kind=='conv':value=row['actual_conv_tail'][terminal]
  else:
   value=row[kind].reshape(3,1,256)[list(path)]
   anchor=initial_f[layer];table=list(anchor['physical_pages']);indices=[table[(131+j)//128]*128+(131+j)%128 for j in range(len(path))]
   need(write['indices'].tolist()==indices,'actual accepted physical cache destinations')
   before=t.stack([anchor[kind][table.index(index//128),index%128]for index in indices])
   need(bits(t,write['before'],before),'actual original selected cache bytes independently joined')
  if kind=='state':need(bits(t,write['before'],initial_g[layer]['initial_native_state']),'actual selected recurrent preimage')
  if kind=='conv':need(bits(t,write['before'],initial_g[layer]['full_conv_slot'][0,:3]),'actual selected logical conv preimage')
  need(bits(t,write['after'],value)and bits(t,transaction['actual_applied'][n],value)and
       bits(t,transaction['actual_restored'][n],write['before']),
       'actual complete accepted-path values applied and restored bitwise')
 fg={r['layer']:r for r in raw['actual_native_final_GDN']};ff={r['layer']:r for r in raw['actual_native_final_FA']}
 need(set(fg)==set(initial_g)and set(ff)==set(initial_f),'full selected final state/cache set')
 for i,anchor in initial_g.items():
  need(bits(t,anchor['full_conv_slot'],fg[i]['full_conv_slot'])and
       bits(t,anchor['initial_native_state'],fg[i]['native_state']), 'whole selected conv extras/recurrent bytes restored')
 for i,anchor in initial_f.items():
  need(bits(t,anchor['key'],ff[i]['key'])and bits(t,anchor['value'],ff[i]['value']),
       'whole selected actual pages including inactive/padding bytes restored')
 import hashlib
 digest=hashlib.sha256(owner['request'].encode('utf8')).digest()
 request_hash=[int.from_bytes(digest[i:i+8],'big',signed=True)for i in range(0,32,8)]
 for phase,value in[(0,raw['initial_agreement']),
                     (1,transaction['before_agreement']),
                     (2,transaction['applied_agreement']),
                     (3,transaction['restored_agreement'])]:
  values=[*request_hash,owner['generation'],owner['slot'],owner['length'],owner['version'],
          *tokens,-1 if phase==0 else terminal,phase,48,16]
  need(value['rank']==raw['rank']and value['phase']==phase and value['scheduler_committed']is False and
       value['rows'].dtype==t.int64 and value['rows'].tolist()==[values]*4,
       'all actual TP4 phases source/request/tree/path exact agreement')
 return dict(schema='bole.actual-model-three-node-independent-diagnostic/v1',rows=rows,
    component_checks_pass=bool(component),whole_discrepancies=whole,greedy_identity_pass=bool(greedy),
    whole_numerical_threshold=None,whole_numerical_qualified=False,model_ready=False,
    accepted_path_writeback_restore_pass=True,production_ready=False,scheduler_committed=False),vectors
