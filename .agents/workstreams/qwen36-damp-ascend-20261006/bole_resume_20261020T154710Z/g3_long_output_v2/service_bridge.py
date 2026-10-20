"""Actual model bridge for a bounded first-request service experiment."""
import types
import model_entry as E
import context_identity
import g1_contract as G1
from model_entry import need,tensor_id,resolve_fia,BUS
from service_fia import ServiceFiaBoundary

def _fa(self,b,query,key,value):
 ctx=BUS.get();ctx.visit(b['index'],'fa');t=self.t;o=ctx.owner
 need(ctx.mode=='TREE'and self._bole_live.current()==o,'actual open service TREE frame')
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
 actual_fia=resolve_fia(self.C,self.fia_ref,self.prerequisites['components']['paged']['actual_fia_abi'],self.prerequisites['components']['paged']['source'])
 need(actual_fia==self.fia,'same immutable actual FIA ABI value at each real adapter call')
 boundary=ServiceFiaBoundary(t,self.torch_npu,trial,self.own_source['files']['service_fia.py'])
 out,_=self.A.native(t,boundary,trial,actual_fia,sparse_mode=1)
 ctx.captures[b['index']]=dict(kind='fa',trial=trial,actual_physical_pages=physical,actual_cache_identities=(tensor_id(b['key']),tensor_id(b['value'])),query=query.clone(),key=key.clone(),value=value.clone(),output=out.clone())
 return out.reshape(3,1536)

def _physical(self,binding,owner):
 return self._bole_live.physical(binding,owner)

def _validate(self,owner):
 return self._bole_live.validate(owner)

def install_methods(bridge,live,C,m):
 need(E.BUS.get()is None and len(bridge.saved)==64,'fresh installed actual64-layer bridge')
 need(bridge._fa.__func__ is E.Bridge._fa and bridge._physical_slot.__func__ is E.Bridge._physical_slot,
      'only original qualified bridge methods before service installation')
 scope=m['service_experiment']
 need(scope==G1.SCOPE,
      'explicit bounded experimental service scope')
 need(C.ref(__file__)==m['files']['service_bridge.py'],'exact service bridge source')
 bridge._bole_live=live
 bridge._fa=types.MethodType(_fa,bridge)
 bridge._physical_slot=types.MethodType(_physical,bridge)
 bridge._validate_bindings=types.MethodType(_validate,bridge)
 return bridge

def forward(bridge,frame,native_forward,*,input_ids,positions,intermediate_tensors,inputs_embeds,
            actual_context,enter_context,source_ref):
 t=bridge.t;C=bridge.C;owner=frame.owner
 need(bridge._bole_live.current()==owner and not frame.closed and E.BUS.get()is None,
      'exclusive current native scheduled frame')
 E.code_source(C,native_forward,bridge.own_source['files']['worker_entry.py'])
 need(C.ref(context_identity.__file__)==bridge.own_source['files']['context_identity.py'],
      'exact private native-context identity helper')
 context_identity.enter_source(C,enter_context,bridge.own_source['files']['context_adapter.py'],
                              bridge.own_source['runtime_sources']['contextlib'])
 need(intermediate_tensors is None and 1<=frame.scheduled_nodes<=3,'single PP/no intermediate payload')
 n=frame.scheduled_nodes;device=bridge.bindings[0]['conv'].device
 ids=t.tensor(frame.tokens,dtype=t.int64,device=device)
 if input_ids is not None:
  need(input_ids.shape==(n,)and input_ids.cpu().tolist()==list(frame.real_input_ids),
       'actual native input IDs before any padding')
 need(input_ids is not None or inputs_embeds is not None,'actual native text route')
 expected=[owner.length+i for i in range(n)];depth=[owner.length,owner.length+1,owner.length+1]
 if bridge.position_axes==3:expected=[expected]*3;depth=[depth]*3
 need(positions.dtype==t.int64 and positions.cpu().tolist()==expected,
      'actual native text coordinates before tree-depth substitution')
 padded_positions=t.tensor(depth,dtype=t.int64,device=device)
 frame.original_positions=positions.detach().cpu().clone()
 positions.copy_(padded_positions[...,:n])
 padded_embeddings=None
 if inputs_embeds is not None:
  need(inputs_embeds.shape==(n,5120)and inputs_embeds.dtype==t.bfloat16,
       'actual native text embedding ABI')
  E.code_source(C,bridge.model.embed_input_ids,bridge.own_source['runtime_sources']['qwen_next'])
  padded_embeddings=bridge.model.embed_input_ids(ids)
  need(bridge.N.bits(t,padded_embeddings[:n],inputs_embeds),'actual native admitted embeddings equal exact loaded token lookup')
  frame.input_mode='native-text-embeddings'
 else:frame.input_mode='native-token-ids'
 bridge._validate_bindings(owner)
 anchors=bridge._anchors(owner)
 ctx=E.Context(owner,frame.tokens,(owner.length,owner.length+1,owner.length+1),'TREE')
 ctx.phase='FORWARD';frame.context=ctx
 try:
  with enter_context(actual_context,num_tokens=3,source_ref=source_ref):
   token=E.BUS.set(ctx)
   try:
    hidden=native_forward(ids if input_ids is not None else None,padded_positions,None,padded_embeddings)
   finally:E.BUS.reset(token)
  need(isinstance(hidden,t.Tensor)and hidden.shape==(3,5120),'actual all64 final normalized three-row hidden')
  need(len(ctx.order)==len(ctx.captures)==64 and bridge._bole_live.current()==owner,
       'complete genuine all64 traversal and retained owner')
  bridge._unchanged(anchors)
  ctx.phase='FORWARD_COMPLETE_NOT_QUALIFIED'
  frame.tree_hidden=hidden.detach().clone()
  frame.native_hidden=hidden[:n]
  frame.padded_positions=padded_positions
  return frame.native_hidden
 except BaseException as error:
  ctx.phase='FAILED_NO_PUBLICATION';ctx.first_fault=repr(error)
  try:bridge._unchanged(anchors)
  except BaseException as secondary:ctx.secondary_faults=(repr(secondary),)
  raise

