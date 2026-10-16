"""Opt-in B1 three-node *model-object* bridge; not a vLLM service installer.

The scheduler/worker must register real arenas and retain an exclusive request
window. No allocation, device initialization, thread or owner is created here.
"""
import contextvars,inspect,os,types
from dataclasses import dataclass,field

BUS=contextvars.ContextVar('bole_actual_model_tree',default=None)
def need(v,s):
 if not v:raise ValueError(s)
def code_source(C,fn,expected):
 fn=getattr(fn,'__func__',fn)
 need(C.ref(inspect.getsourcefile(fn))==expected,'actual model callable source identity')
def tensor_id(x):
 return (x.untyped_storage().data_ptr(),x.data_ptr(),x.storage_offset(),tuple(x.shape),tuple(x.stride()),str(x.dtype),str(x.device))

@dataclass(frozen=True)
class Owner:
 request:str
 generation:int
 slot:int
 length:int
 version:int

@dataclass
class Context:
 owner:Owner
 tokens:tuple
 positions:tuple
 mode:str
 captures:dict=field(default_factory=dict)
 order:list=field(default_factory=list)
 phase:str='NEW'
 ar_caches:dict=field(default_factory=dict)
 first_fault:object=None
 secondary_faults:tuple=()
 def visit(self,index,kind):
  need(self.phase=='FORWARD'and index==len(self.order)and index not in self.captures,'all64 layers exactly once and ordered')
  self.order.append((index,kind))

class Bridge:
 def __init__(self,t,C,inner_model,bindings,*,qwen_next_ref,gdn_ref,actual118c,
              conv_seam,treeconv,tree_metadata,core112,paged,torch_npu,actual_fia_abi,
              actual_conv_abi,calibration_reader,arm_verified=False,
              component_refs=None,component_gate=None,native_registration=None,own_source_ref=None,position_axes=None,prefill_window=None):
  need(os.environ.get('BOLE_THREE_NODE_MODEL_ENABLE')=='1','default OFF')
  need(os.environ.get('BOLE_PAGED_TREE_ENABLE')=='1','explicit already-qualified paged component opt-in')
  need(arm_verified is True,'existing admitted actual worker boundary required')
  need(component_gate is not None and component_refs is not None and native_registration is not None and own_source_ref is not None,'actual component chains and registered native operator proof required')
  own=C.obj(own_source_ref);need(own['schema']=='bole.actual-model-three-node-entry/source-prep-v1','exact reviewed model seam source')
  need(actual118c==own['actual118c'],'fixed actual native-conv chronology chain, not caller-selected calibration')
  self.own_source=own
  for ref in own['files'].values():C.checked(ref)
  need(qwen_next_ref==own['runtime_sources']['qwen_next']and gdn_ref==own['runtime_sources']['gdn'],'exact installed model callable pins')
  for module in(conv_seam,treeconv,tree_metadata,core112,paged,calibration_reader,component_gate,native_registration):
   name=os.path.basename(module.__file__);need(C.ref(module.__file__)==own['files'][name],'own exact helper import; no ambient namespace')
  need(t.npu.matmul.allow_hf32 is False,'common FP32 HF32OFF policy, not candidate-only')
  need(type(position_axes)is int and position_axes in(1,3),'actual native worker text-position layout must be registered; never guess MRoPE')
  self.position_axes=position_axes
  self.prefill_window=prefill_window
  self.prerequisites=component_gate.consume(C,component_refs,gdn_math=C.ref(core112.__file__),paged_math=C.ref(paged.__file__))
  need(actual_fia_abi==self.prerequisites['components']['paged']['actual_fia_abi'],'exact actual paged-operation ABI, not prepared null or caller choice')
  registration=native_registration.actual(t,C,arm_verified=True);convabi=C.obj(actual_conv_abi)
  self.actual_native_registration=registration
  need(registration['actual_extension_ref']==convabi['registration']['actual_extension_ref']and [r['ref']for r in registration['actual_opapi_mappings']]==[r['ref']for r in convabi['registration']['actual_opapi_mappings']],'same actually loaded native extension/opapi as calibrated ABI')
  need(inner_model.start_layer==0 and inner_model.end_layer==64 and len(inner_model.layers)==64,'real full64 target object, no PP/partial model')
  need(len(bindings)==64 and tuple(b['index']for b in bindings)==tuple(range(64)),'complete actual cache registration')
  self.t=t;self.C=C;self.model=inner_model;self.bindings=tuple(bindings);self.saved=[]
  self.actual118c=actual118c;self.N=conv_seam;self.V=treeconv;self.M=tree_metadata
  self.K=core112;self.A=paged;self.torch_npu=torch_npu;self.fia=actual_fia_abi;self.conv_abi=actual_conv_abi;self.reader=calibration_reader
  counts={'gdn':0,'fa':0};seen=set()
  for index,(layer,b)in enumerate(zip(inner_model.layers,bindings)):
   need(b['index']==index and b['layer'] is layer,'binding uses actual inner.layers object, not matching name only')
   if layer.layer_type=='linear_attention':
    counts['gdn']+=1;obj=layer.linear_attn;need(b['kind']=='gdn','actual configured GDN layer')
    code_source(C,obj._forward_core,gdn_ref)
    need(b['state'] is obj.kv_cache[1],'actual layer-owned recurrent arena')
    if b['conv'] is not obj.kv_cache[0]:
     import prefill_tail as PT
     need(C.ref(PT.__file__)==own['files']['prefill_tail.py']and type(prefill_window)is dict,'source-owned first-prefill wide-tail adapter')
     w=prefill_window
     need(b['tail'].metadata is w['metadata'][obj.prefix],'actual forward-context metadata identity')
     view=PT.unchanged(t,b['tail'],obj=obj,request=w['request'],request_id=w['request_id'],slot=w['slot'],length=w['length'])
     need(b['conv'] is view and b['conv_arena'] is obj.kv_cache[0],'exact leading-tail view of actual native wide cache')
    else:need(obj.kv_cache[0].shape[1]==3,'native wide arena must use reviewed pure-prefill mapping')
    self.N.gdn_canonical_view(t,b['state'],layout='slot,H,Dv,Dk')
    need(b['conv'].ndim==3 and tuple(b['conv'].shape[1:])==(3,2560),'actual calibrated no-spec SD conv only')
   elif layer.layer_type=='full_attention':
    counts['fa']+=1;obj=layer.self_attn;need(b['kind']=='fa','actual configured full attention')
    code_source(C,obj.forward,qwen_next_ref)
    need((obj.num_heads,obj.num_kv_heads,obj.head_dim)==(6,1,256),'actual loaded TP4 FA geometry')
    need(tuple(b['key'].shape)==tuple(b['value'].shape)and b['key'].shape[1:]==(128,1,256),'registered actual ND page128 cache; NZ/other pages not inferred')
    need(type(b['table'])in(tuple,list),'audited scheduler CPU physical block table')
   else:raise ValueError('unsupported actual layer type')
   # Every layer object must be distinct. Cache-sharing policies are not guessed.
   need(id(obj)not in seen,'same model layer registered twice');seen.add(id(obj))
  need(counts==dict(gdn=48,fa=16),'actual target48GDN/16FA')
  self.qwen_ref=qwen_next_ref;self.gdn_ref=gdn_ref

 def _gdn(self,b,obj,mixed_qkv,ba,aa,output):
  ctx=BUS.get();ctx.visit(b['index'],'gdn');t=self.t
  if ctx.mode=='AR':return self._native_gdn_ar(ctx,b,obj,mixed_qkv,ba,aa,output)
  need(mixed_qkv.shape==(3,2560)and output.shape==(3,12,128),'actual model-projected three-node GDN ABI')
  owner=ctx.owner;need(0<=owner.slot<b['state'].shape[0]and owner.slot<b['conv'].shape[0],'actual request slot')
  tree=self.N.NodeRows(owner.request,owner.generation,owner.slot,owner.length,ctx.tokens).metadata(self.M.Tree)
  owners=(self.V.Owner(owner.request,owner.generation,owner.slot,owner.length,owner.version),)
  trial=self.V.prepare(t,tree,owners,b['conv'],mixed_qkv,width=4,node_budget=3)
  weight=obj.conv1d.weight.view(obj.conv1d.weight.size(0),obj.conv1d.weight.size(2))
  ctx.captures[b['index']]=dict(kind='gdn',phase='BEFORE_NATIVE_TREE_CONV',conv_trial=trial,raw_projected=mixed_qkv.clone(),a=aa.clone(),b=ba.clone(),weight=weight.clone(),activation=bool(obj.activation))
  op=t.ops._C_ascend.npu_causal_conv1d_custom.default
  convolved,tail=self.N.native_tree_conv(t,self.C,self.V,self.reader,self.actual118c,trial,weight,obj.conv1d.bias,activation=bool(obj.activation),op=op,actual_abi=self.conv_abi,arm_verified=True)
  ctx.captures[b['index']].update(actual_convolved=convolved.clone(),actual_conv_tail=tail.clone())
  # These are the actual model methods/operators, not a second projection model.
  q,k,v=obj.rearrange_mixed_qkv(convolved)
  # The installed wrapper has its own module; take the frozen original module.
  mod=b['_original_module']
  g,beta=mod.DeviceOperator.fused_gdn_gating(obj.A_log,aa,ba,obj.dt_bias)
  q=mod.l2norm_fwd(q);k=mod.l2norm_fwd(k)
  need(q.shape==(1,3,4,128)and k.shape==q.shape and v.shape==(1,3,12,128)and g.shape==beta.shape==(1,3,12),'actual normalized GQA/gating output ABI')
  qh=q.permute(0,2,1,3).float().repeat_interleave(3,dim=1)*(128**-.5)
  kh=k.permute(0,2,1,3).float().repeat_interleave(3,dim=1)
  vh=v.permute(0,2,1,3).float();bh=beta.transpose(1,2).float();gamma=g.transpose(1,2).float().exp()
  need(bool(t.isfinite(gamma).all()and(gamma>0).all()),'tree product finite positive domain')
  state=self.N.gdn_canonical_view(t,b['state'],layout='slot,H,Dv,Dk')[owner.slot:owner.slot+1].clone()
  ancestor=t.tensor([[False,False,False],[True,False,False],[True,False,False]],device=q.device)
  ctx.captures[b['index']].update(state=state,keys=kh,normalized_inputs=(qh,kh,vh,bh,gamma),phase='BEFORE_TREE_GDN')
  value,factors=self.K.verify(t,qh,kh,vh,bh,gamma,state,ancestor,1)
  need(bool(t.isfinite(value).all()and t.isfinite(factors[0]).all()and t.isfinite(factors[1]).all()),'tree model GDN finite before publication')
  output.copy_(value.permute(0,2,1,3).squeeze(0).to(output.dtype))
  inclusive=ancestor.float()+t.eye(3,device=q.device,dtype=t.float32)
  actual_states=t.stack([self.K.commit(t,state,kh,factors,inclusive,node)for node in range(3)],dim=0)
  ctx.captures[b['index']].update(factors=factors,precast_output=value.clone(),actual_node_states=actual_states,output=output.clone(),phase='TREE_GDN_COMPLETE')

 def _fa(self,b,query,key,value):
  ctx=BUS.get();ctx.visit(b['index'],'fa');t=self.t;o=ctx.owner
  if ctx.mode=='AR':return self._native_fa_ar(ctx,b,query,key,value)
  # Qwen3NextAttention.forward invokes this after native norms and RoPE.
  need(query.shape==(3,1536)and key.shape==value.shape==(3,256),'actual post-RoPE flattened FA input')
  owner=self.A.Owner(o.request,o.generation,o.slot,o.length,o.version)
  # Never clone an entire engine KV pool. Copy only this owned physical prefix
  # plus accepted-path capacity into a compact diagnostic registration.
  pages=(o.length+2+127)//128;physical=tuple(b['table'][:pages])
  need(len(physical)==pages and len(set(physical))==pages,'complete actual selected prefix/destination pages')
  index=t.tensor(physical,dtype=t.long,device=b['key'].device)
  compact_k=t.zeros((pages,128,1,256),dtype=b['key'].dtype,device=b['key'].device);compact_v=t.zeros_like(compact_k)
  source_index=t.tensor([b['table'][pos//128]*128+pos%128 for pos in range(o.length)],dtype=t.long,device=b['key'].device)
  compact_k.reshape(-1,1,256)[:o.length].copy_(b['key'].reshape(-1,1,256).index_select(0,source_index))
  compact_v.reshape(-1,1,256)[:o.length].copy_(b['value'].reshape(-1,1,256).index_select(0,source_index))
  trial=self.A.prepare(t,owner,query.reshape(3,6,256),key.reshape(3,1,256),value.reshape(3,1,256),compact_k,compact_v,tuple(range(pages)))
  ctx.captures[b['index']]=dict(kind='fa',trial=trial,actual_physical_pages=physical,actual_cache_identities=(tensor_id(b['key']),tensor_id(b['value'])),query=query.clone(),key=key.clone(),value=value.clone(),phase='BEFORE_NATIVE_PAGED_FA')
  out,_=self.A.native(t,self.torch_npu,trial,self.fia,sparse_mode=1)
  ctx.captures[b['index']]=dict(kind='fa',trial=trial,actual_physical_pages=physical,actual_cache_identities=(tensor_id(b['key']),tensor_id(b['value'])),query=query.clone(),key=key.clone(),value=value.clone(),output=out.clone())
  return out.reshape(3,1536)

 def _anchors(self,owner):
  rows=[];t=self.t
  need(type(owner)is Owner and type(owner.request)is str and owner.request and all(type(x)is int and x>=0 for x in(owner.generation,owner.slot,owner.length,owner.version)),'typed actual request owner')
  for b in self.bindings:
   if b['kind']=='gdn':need(owner.slot<b['conv'].shape[0]and owner.slot<b['state'].shape[0],'complete actual GDN/conv slot mapping')
   else:
    n=(owner.length+2+127)//128;ids=b['table'][:n]
    need(len(ids)==n and len(set(ids))==n and all(type(i)is int and 0<=i<b['key'].shape[0]for i in ids),'complete exact physical KV page mapping')
   names=(('conv_arena','state')if 'conv_arena'in b else('conv','state'))if b['kind']=='gdn'else('key','value')
   for name in names:
    x=b[name];ids=[owner.slot]if b['kind']=='gdn'else list(b['table'][:(owner.length+2+127)//128])
    index=t.tensor(ids,dtype=t.long,device=x.device)
    rows.append((x,tensor_id(x),index,x.index_select(0,index).clone()))
  return rows

 def _unchanged(self,anchors):
  for x,ident,index,before in anchors:
   need(tensor_id(x)==ident and self.N.bits(self.t,x.index_select(0,index),before),'actual selected committed slots/pages changed during isolated verification')

 def _native_gdn_ar(self,ctx,b,obj,x,ba,aa,output):
  """Source-derived single-token native conv+recurrent path, no112 math."""
  t=self.t;index=b['index'];cache=ctx.ar_caches[index]
  need(x.shape==(1,2560)and output.shape==(1,12,128),'actual AR one-token projected ABI')
  weight=obj.conv1d.weight.view(2560,4);convolved=t.full_like(x,float('nan'))
  ctx.captures[index]=dict(kind='gdn-native-AR',phase='BEFORE_NATIVE_CONV',inputs=x.clone(),a=aa.clone(),b=ba.clone(),weight=weight.clone(),conv_before=cache['conv'].clone(),state_before=cache['state'].clone())
  seq=t.tensor([0,1],dtype=t.int32,device=x.device);ids=t.tensor([0],dtype=t.int32,device=x.device)
  returned=t.ops._C_ascend.npu_causal_conv1d_custom.default(convolved,x,weight.transpose(0,1),conv_state=cache['conv'],bias_opt=obj.conv1d.bias,query_start_loc_opt=seq,cache_indices_opt=ids,initial_state_mode_opt=None,num_accepted_tokens_opt=None,activation_mode=int(bool(obj.activation)),pad_slot_id=-1,run_mode=1)
  need(returned.data_ptr()==convolved.data_ptr(),'native AR conv output alias')
  q,k,v=obj.rearrange_mixed_qkv(convolved);mod=b['_original_module']
  g,beta=mod.DeviceOperator.fused_gdn_gating(obj.A_log,aa,ba,obj.dt_bias)
  q=mod.l2norm_fwd(q);k=mod.l2norm_fwd(k)
  op=t.ops._C_ascend.npu_recurrent_gated_delta_rule.default
  names=[a.name for a in op._schema.arguments]
  need({'query','key','value','g','beta','state','scale','actual_seq_lengths','ssm_state_indices'}<=set(names),'actual registered native recurrent ABI')
  ctx.captures[index].update(phase='BEFORE_NATIVE_RECURRENT',actual_recurrent_schema=str(op._schema),actual_seq=seq.clone(),actual_indices=ids.clone(),normalized_inputs=(q.clone(),k.clone(),v.clone(),g.clone(),beta.clone()))
  state_before=cache['state'].clone();conv_after=cache['conv'].clone()
  value=op(query=q.squeeze(0),key=k.squeeze(0),value=v.squeeze(0),g=g.squeeze(0),beta=beta.squeeze(0),state=cache['state'],scale=128**-.5,actual_seq_lengths=seq,ssm_state_indices=ids)
  need(value.shape==output.shape and value.dtype==output.dtype and bool(t.isfinite(value).all()),'native AR output exact ABI/finite')
  output.copy_(value)
  ctx.captures[index].update(phase='NATIVE_RECURRENT_COMPLETE',state_after=cache['state'].clone(),conv_after=conv_after,output=output.clone())

 def _native_fa_ar(self,ctx,b,query,key,value):
  """Native sequential path with independently gathered prefix, no tree mask."""
  t=self.t;cache=ctx.ar_caches[b['index']]
  need(query.shape==(1,1536)and key.shape==value.shape==(1,256),'actual AR post-RoPE ABI')
  cache['key']=t.cat((cache['key'],key.reshape(1,1,256)),dim=0)
  cache['value']=t.cat((cache['value'],value.reshape(1,1,256)),dim=0)
  q=query.reshape(1,1,6,256).permute(0,2,1,3).contiguous()
  k=cache['key'].permute(1,0,2).unsqueeze(0).contiguous()
  v=cache['value'].permute(1,0,2).unsqueeze(0).contiguous()
  ctx.captures[b['index']]=dict(kind='fa-native-AR',phase='BEFORE_NATIVE_FA',query=query.clone(),key=key.clone(),value=value.clone(),after_key=cache['key'].clone(),after_value=cache['value'].clone())
  out,_=self.torch_npu.npu_fused_infer_attention_score(query=q,key=k,value=v,input_layout='BNSD',num_heads=6,num_key_value_heads=1,scale=256**-.5,actual_seq_lengths=[1],actual_seq_lengths_kv=[cache['key'].shape[0]],sparse_mode=0,pre_tokens=2147483647,next_tokens=2147483647,inner_precise=0)
  need(out.shape==(1,6,1,256)and out.dtype==query.dtype and bool(t.isfinite(out).all()),'native AR contiguous FA output ABI/finite')
  ctx.captures[b['index']].update(phase='NATIVE_FA_COMPLETE',output=out.clone())
  return out.reshape(1,1536)

 def sequential_native_paths(self,owner,tokens,*,current_owner):
  """Same actual weights: independent root->left and root->right native paths.

  Original outer model projection/norm/RoPE/MLP/residual run unchanged. Only
  its cache boundary is redirected to private clones and source-derived native
  no-spec operations. No candidate112 recurrence, factors or tree mask is used.
  """
  need(self.saved and BUS.get()is None and current_owner()==owner,'exclusive native controls')
  need(owner.length in(0,127,128,131),'same initial actual model diagnostic prefix domain')
  need(len(tokens)==3 and tokens[1]!=tokens[2],'same actual root/two children')
  anchors=self._anchors(owner)
  reports=[]
  for child in(1,2):
   caches={}
   for b in self.bindings:
    if b['kind']=='gdn':caches[b['index']]=dict(conv=b['conv'][owner.slot:owner.slot+1].clone(),state=b['state'][owner.slot:owner.slot+1].clone())
    else:
     # Independent CPU metadata walk over physical pages; never candidate scratch.
     physical=[b['table'][pos//128]*128+pos%128 for pos in range(owner.length)]
     index=self.t.tensor(physical,dtype=self.t.long,device=b['key'].device)
     caches[b['index']]=dict(key=b['key'].reshape(-1,1,256).index_select(0,index).clone(),value=b['value'].reshape(-1,1,256).index_select(0,index).clone())
   steps=[]
   for step,node in enumerate((0,child)):
    need(current_owner()==owner,'native AR request ownership stable')
    device=self.bindings[0]['conv'].device if self.bindings[0]['kind']=='gdn'else self.bindings[0]['key'].device
    ids=self.t.tensor([tokens[node]],dtype=self.t.int64,device=device);positions=self.t.tensor([owner.length+step],dtype=self.t.int64,device=device)
    if self.position_axes==3:positions=positions.unsqueeze(0).repeat(3,1)
    ctx=Context(owner,(tokens[node],),(owner.length+step,),'AR',ar_caches=caches);ctx.phase='FORWARD';tok=BUS.set(ctx)
    self.last_native_context=ctx
    try:
     hidden=self.model(input_ids=ids,positions=positions)
     need(len(ctx.order)==len(ctx.captures)==64,'actual native AR all64 traversal')
     steps.append(dict(node=node,hidden=hidden,context=ctx))
    except BaseException as error:
     ctx.phase='FAILED_NATIVE_AR';ctx.first_fault=repr(error);raise
    finally:BUS.reset(tok)
   reports.append(dict(child=child,steps=steps,model_ready=False))
  need(current_owner()==owner,'native controls request ownership stable')
  self._unchanged(anchors)
  return reports

 def stage_selected_path(self,ctx,terminal,*,current_owner):
  """Build all64 layer writes without publishing any cache or scheduler state.

 0=root-only/no accepted draft;1/2=selected child;None=cancel. Actual sampler
 acceptance and TP4 consensus must supply this terminal. No sampled bonus is
 committed here. The returned plan deliberately has no automatic apply method.
 """
  need(ctx.phase=='FORWARD_COMPLETE_NOT_QUALIFIED'and current_owner()==ctx.owner,'fresh complete model context and exact request version')
  need(terminal is None or type(terminal)is int and terminal in(0,1,2),'one actual accepted root path')
  path=()if terminal is None else(0,)if terminal==0 else(0,terminal)
  need(len(ctx.captures)==64,'all layer candidates available')
  writes=[];o=ctx.owner;t=self.t
  inclusive=t.tensor([[1,0,0],[1,1,0],[1,0,1]],dtype=t.float32,device=next(iter(ctx.captures.values()))['output'].device)
  for b in self.bindings:
   row=ctx.captures[b['index']]
   if not path:continue
   if b['kind']=='gdn':
    after=self.K.commit(t,row['state'],row['keys'],row['factors'],inclusive,terminal)[0].transpose(-1,-2).contiguous()
    conv=row['conv_trial'].after[terminal].clone()
    for name,value in(('state',after),('conv',conv)):
     dest=b[name][o.slot];need(dest.shape==value.shape and dest.dtype==value.dtype,'actual staged GDN/conv destination ABI')
     writes.append(dict(layer=b['index'],kind=name,arena=b[name],arena_identity=tensor_id(b[name]),slot=o.slot,before=dest.clone(),after=value))
   else:
    trial=row['trial'];need(trial['owner']==self.A.Owner(o.request,o.generation,o.slot,o.length,o.version),'same actual accepted-path FA owner')
    selected=t.tensor(path,dtype=t.long,device=b['key'].device)
    indices=t.tensor([b['table'][(o.length+i)//128]*128+(o.length+i)%128 for i in range(len(path))],dtype=t.long,device=b['key'].device)
    for name,node in(('key','node_k'),('value','node_v')):
     value=trial[node].index_select(0,selected).clone()
     actual=b[name][indices//128,indices%128]
     writes.append(dict(layer=b['index'],kind=name,arena=b[name],arena_identity=tensor_id(b[name]),indices=indices.clone(),before=actual.clone(),after=value))
  ctx.phase='STAGED_NOT_PUBLISHED'
  return dict(schema='bole.actual-model-selected-path-staging/v1',owner=o,processed_nodes=path,writes=writes,next_length=o.length+len(path),next_version=o.version+int(bool(path)),published=False,model_ready=False)

 def greedy_proposal(self,hidden,ctx,*,compute_logits,acceptance,policy,current_owner,canonical_logits=None):
  """Actual target logits determine the path; no selected-node guess from MTP.

  Returns staged writes only. Independent whole-model numerical consumption
  and unanimous TP4 commit remain mandatory before any real publication.
  """
  need(ctx.phase=='FORWARD_COMPLETE_NOT_QUALIFIED','actual all64 tree forward first')
  code_source(self.C,compute_logits,self.own_source['runtime_sources']['qwen35'])
  need(self.C.ref(acceptance.__file__)==self.own_source['files']['acceptance.py'],'exact reviewed greedy path implementation')
  tensor=hidden[0]if type(hidden)is tuple else hidden
  need(isinstance(tensor,self.t.Tensor)and tensor.shape==(3,5120),'actual target final normalized hidden rows')
  logits=compute_logits(tensor)
  if canonical_logits is not None:
   code_source(self.C,canonical_logits,self.own_source['files']['model_smoke.py'])
   logits=canonical_logits(logits)
  tree=self.N.NodeRows(ctx.owner.request,ctx.owner.generation,ctx.owner.slot,ctx.owner.length,ctx.tokens).metadata(self.M.Tree)
  decisions=acceptance.from_logits(self.t,tree,logits,(0,1,2),(ctx.tokens[0],),policy=policy)
  proposal=self.stage_selected_path(ctx,decisions[0].terminal,current_owner=current_owner)
  return dict(proposal,decision=decisions[0],actual_target_logits=logits,BOLE_model_ready=False)

 def install(self):
  need(not self.saved,'not installed twice')
  # Prevalidate all sources/objects in __init__ before modifying the first object.
  try:
   for b in self.bindings:
    if b['kind']=='gdn':
     obj=b['layer'].linear_attn;old=obj._forward_core;b['_original_module']=inspect.getmodule(old.__func__)
     def wrapper(this,mixed_qkv,b,a,core_attn_out,_binding=b,_old=old):
      ctx=BUS.get()
      if ctx is None:return _old(mixed_qkv=mixed_qkv,b=b,a=a,core_attn_out=core_attn_out)
      return self._gdn(_binding,this,mixed_qkv,b,a,core_attn_out)
     name='_forward_core'
    else:
     obj=b['layer'].self_attn.attn;old=obj.forward
     def wrapper(this,query,key,value,_binding=b,_old=old):
      if BUS.get() is None:return _old(query,key,value)
      return self._fa(_binding,query,key,value)
     name='forward'
    had=name in obj.__dict__;previous=obj.__dict__.get(name)
    self.saved.append((obj,name,had,previous));setattr(obj,name,types.MethodType(wrapper,obj))
  except BaseException:
   self.restore();raise
  return self

 def restore(self):
  need(BUS.get()is None,'cannot restore during model forward')
  for obj,name,had,previous in reversed(self.saved):
   if had:setattr(obj,name,previous)
   else:delattr(obj,name)
  self.saved=[]

 def forward(self,owner,tokens,*,input_ids,positions,current_owner):
  need(self.saved and BUS.get()is None,'installed exclusive nonnested model entry')
  need(type(owner)is Owner and current_owner()==owner,'actual scheduler generation/version retained')
  if self.prefill_window is not None:
   w=self.prefill_window
   need((owner.request,owner.slot,owner.length)==(w['request_id'],w['slot'],w['length']),'wide-tail mapping only same first native pure-prefill request')
  need(owner.length in(0,127,128,131),'initial model seam only actual paged component prefix geometries; no2K/16K extrapolation')
  need(len(tokens)==3 and tokens[1]!=tokens[2]and all(type(x)is int and x>=0 for x in tokens),'actual scheduled root +two distinct MTP tokens')
  need(tuple(input_ids.shape)==(3,)and input_ids.dtype==self.t.int64 and input_ids.cpu().tolist()==list(tokens),'real target input IDs, not synthetic projection rows')
  expected_positions=[owner.length,owner.length+1,owner.length+1]
  shape=(3,)
  if self.position_axes==3:expected_positions=[expected_positions]*3;shape=(3,3)
  need(tuple(positions.shape)==shape and positions.dtype==self.t.int64 and positions.cpu().tolist()==expected_positions,'real tree depth positions passed to actual registered RoPE layout')
  anchors=self._anchors(owner)
  ctx=Context(owner,tuple(tokens),(owner.length,owner.length+1,owner.length+1),'TREE');ctx.phase='FORWARD';token=BUS.set(ctx)
  self.last_context=ctx
  try:
   hidden=self.model(input_ids=input_ids,positions=positions)
   need(len(ctx.order)==64 and len(ctx.captures)==64,'complete genuine model64-layer traversal')
   need(current_owner()==owner,'scheduler request changed during model verification')
   self._unchanged(anchors)
   ctx.phase='FORWARD_COMPLETE_NOT_QUALIFIED';return hidden,ctx
  except BaseException as error:
   ctx.phase='FAILED_NO_COMMIT';ctx.first_fault=repr(error)
   try:self._unchanged(anchors)
   except BaseException as secondary:ctx.secondary_faults=(repr(secondary),)
   raise
  finally:BUS.reset(token)

