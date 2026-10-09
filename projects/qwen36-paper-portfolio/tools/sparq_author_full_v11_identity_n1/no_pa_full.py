"""Source-bound original FULL-ACL composition for Torch author ANN, NOT PA.
No device/global patch by import. This adapter calls ORIGINAL backend POST once;
its registered PA lists must be empty because ANN has no native PA task. Never
claims16 PA updates. Dense must retain original stock16PA handles/events.
"""
from pathlib import Path
import ast,hashlib
FA=tuple(range(3,64,4));BATCHES=tuple(range(1,17))
PINS={
 "/cache/cch/flashinfer-native-abi-v1-20261007-1716-001/source_snapshots/attention_v1.py":"80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390",
 "/cache/cch/flashinfer-native-abi-v1-20261007-1716-001/source_snapshots/model_runner_v1.py":"94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-aclgraph-input-source-v1-001/acl_graph.py":"27f3b838f223dec86113649625f65b158969a30ce0265271d6a3ce1403db2491"}
def require(ok,msg):
 if not ok:raise ValueError(msg)
def verified_sources():
 texts={}
 for name,digest in PINS.items():
  p=Path(name);raw=p.read_bytes()
  require(p.is_absolute() and p.is_file() and not p.is_symlink() and hashlib.sha256(raw).hexdigest()==digest,"actual three deployed stock source bytes")
  texts[p.name]=raw.decode()
 return texts
def method(source,cls,name):
 tree=ast.parse(source)
 owner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
 return next(n for n in owner.body if isinstance(n,ast.FunctionDef) and n.name==name)
def original_post_order(source):
 node=method(source,"NPUModelRunner","_model_forward")
 branch=next(n for n in node.body if isinstance(n,ast.If) and isinstance(n.test,ast.Attribute) and n.test.attr=="enable_enpu")
 calls=[]
 for statement in branch.orelse:
  for n in ast.walk(statement):
   if isinstance(n,ast.Call):
    if isinstance(n.func,ast.Name) and n.func.id=="run_model":calls.append("original_run_model")
    if isinstance(n.func,ast.Attribute) and n.func.attr=="_update_full_graph_params_if_needed":calls.append("original_POST_update")
 require(calls==["original_run_model","original_POST_update"],"actual !enable_enpu original runner POST order, no alternative pre-update")
 return calls
def empty_pa(params,batch):
 require(type(batch) is int and batch in BATCHES and all(batch in m for m in
  (params.attn_params,params.handles,params.events)) and
  all(type(m[batch]) is list and len(m[batch])==0 for m in (params.attn_params,params.handles,params.events)),
  "genuine authorANN FULL composition has zero PA tasks/handles/events; no fake16 updated claim")
 return True
def pointer(t):
 return (t.data_ptr(),t.untyped_storage().data_ptr(),t.storage_offset(),tuple(t.shape),tuple(t.stride()),str(t.dtype),str(t.device))
class Registry:
 def __init__(self,bindings):
  require(type(bindings) is dict and len(bindings)==16 and {r["layer"] for r in bindings.values()}==set(FA) and
   len({r["impl_id"] for r in bindings.values()})==16,"actual all16 bound FA instances/prefixes, not64 metadata zip")
  self.bindings=bindings;self.captures={};self.active=None
 def capture(self,batch,prefix,impl_id,query,output,table,lengths,params):
  require(prefix in self.bindings and self.bindings[prefix]["impl_id"]==impl_id,"actual original capture instance")
  empty_pa(params,batch);records=self.captures.setdefault(batch,{})
  require(prefix not in records,"one actual capture per truebatch/prefix, not repeated owner")
  require(pointer(output)[1]!=pointer(query)[1],"original model output distinct from Q")
  records[prefix]={"query":pointer(query),"output":pointer(output),"table":pointer(table),"lengths":pointer(lengths),"impl_id":impl_id}
 def complete(self,batch,params):
  empty_pa(params,batch);rows=self.captures.get(batch,{})
  require(set(rows)==set(self.bindings),"all16 FA actually captured while original PA lists stay empty")
  return rows
 def begin_replay(self,batch,epoch,metadata,device_lengths,params,frame):
  records=self.complete(batch,params)
  require(self.active is None and type(epoch) is int and epoch>0 and len(frame)==batch and
   len({r["rid"] for r in frame})==batch,"one original synchronous real request replay, no padded row authority")
  for prefix,row in records.items():
   require(prefix in metadata and pointer(metadata[prefix].block_tables)==row["table"] and
    pointer(device_lengths)==row["lengths"],"actual captured native table/runner device lens pointers unchanged")
  self.active={"batch":batch,"epoch":epoch,"frame":frame,"POST_original_returned":False}
 def post(self,original_backend,stream,ctx,tokens,config,params,spec=None,cp_tokens=None,draft_meta=None):
  require(self.active is not None and tokens==self.active["batch"] and not self.active["POST_original_returned"] and
   spec is None and draft_meta is None and original_backend.__module__=="vllm_ascend.attention.attention_v1",
   "exact original default nondraft source backend POST method after original ACL call")
  self.complete(tokens,params)
  got=original_backend(stream,ctx,tokens,config,spec,cp_tokens,draft_meta) # ORIGINAL, zip zeroPA records.
  self.complete(tokens,params);self.active["POST_original_returned"]=True
  return got
 def end_replay(self,actual_acl_calls,observed_FA_devices):
  require(self.active is not None and self.active["POST_original_returned"] and len(actual_acl_calls)==1 and
   actual_acl_calls[0]["original_call_returned"] is True,"one actual ORIGINAL ACL replay and ORIGINAL post call")
  require(type(observed_FA_devices) is dict and set(observed_FA_devices)==set(self.bindings) and
   all(v.get("epoch")==self.active["epoch"] and v.get("counter_increment")==1 and v.get("guards") is True
    for v in observed_FA_devices.values()),"diagnostic all16 actual device counters/output guards; Python counts are not replay proof")
  out=dict(self.active,original_ACL_replay_count=1,fresh_ANN_device_observations=16,native_PA_tasks=0,
   PA_task_update_count=0,original_POST_called_once=True,model_ready=False)
  self.active=None;return out
def selector_topology(torch,workspace,table,device_lengths):
 """ONLY captured device kernels. No CPU lens, .cpu/.item/H2D copy inside graph.
 Full native domain retained; invalid columns remap first known live native page.
 """
 b=workspace.batch
 require(table.device.type==device_lengths.device.type=="npu" and device_lengths.dtype==torch.int32 and
  table.dtype in (torch.int32,torch.int64) and table.shape==(b,workspace.max_pages) and device_lengths.shape==(b,),
  "source-supported actual native persistent metadata geometry, never selected128 lens")
 page_index=workspace.logical[::128]//128
 live_pages=torch.div(device_lengths.to(torch.int64)+127,128,rounding_mode="floor")
 safe=torch.where(page_index[None,:]<live_pages[:,None],table,table[:,:1]).to(torch.int64)
 workspace.rows.copy_(safe);workspace.lengths.copy_(device_lengths)
 return workspace.rows,workspace.lengths
def author_forward(torch,arena,batch,query,kc,vc,table,device_lengths,original_output,zero_mean,copy_order):
 """Called from opt-in FA forward_impl AFTER untouched original outer KVwriter.
 MeanOFF is an explicit author setting. MeanON is not implemented by a fakezero.
 """
 require(query.shape==(batch,6,256) and query.dtype==kc.dtype==vc.dtype==torch.bfloat16 and
  original_output.shape[0]>=batch and original_output.numel()>=batch*6*256 and zero_mean.shape==(batch,256) and zero_mean.dtype==torch.float32,
  "actual original local6Q/1KV query/output/meanOFF tensors")
 workspace=arena.view(batch)
 require(pointer(original_output)[1]!=pointer(workspace.corrected)[1],"original model output cannot alias shared ANN arena")
 selector_topology(torch,workspace,table,device_lengths)
 got,selected,alpha,channels=workspace.run(query,kc,vc,zero_mean,reallocation=False)
 original_output[:batch].view(batch,6,256).copy_(got)
 # Callback only source order bookkeeping; actual FULL replay additionally needs
 # device snapshots/counters above. Formal timing MUST NOT call .cpu/.item/JSON.
 copy_order()
 return original_output,workspace,selected,alpha,channels
