"""Execute exact source AST bodies, not a rewritten reference or fake module.
Never construct a Transformers model. Literal reference is EAGER ONLY outside
candidate capture; its torch.tensor(1.0, device=...) is not GLOBAL capturable.
"""
import ast,dataclasses,functools,sys,types,typing
from contract import ANN,CAUSAL,read_ref,require
ANN_NODES=("gather","LowRank","SparseQ","Settings","AnnAttention")
CAUSAL_NODES=("score_to_mask","causal_index")
def extracted(raw,names):
 tree=ast.parse(raw.decode("utf-8"));nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
 require(set(n.name for n in nodes)==set(names) and len(nodes)==len(names),"complete exact author AST body selection")
 pre=ast.ImportFrom(module="__future__",names=[ast.alias(name="annotations")],level=0)
 module=ast.Module(body=[pre]+nodes,type_ignores=[])
 ast.fix_missing_locations(module)
 return module
def build(torch):
 common={"torch":torch,"Tensor":torch.Tensor,"nn":torch.nn,"dataclass":dataclasses.dataclass,
  "partial":functools.partial,"__builtins__":__builtins__}
 common.update({n:getattr(typing,n) for n in ("Any","List","Optional","Tuple","Union","cast")})
 causal_module=types.ModuleType("frozen_causal_math_AST_excerpt");sys.modules[causal_module.__name__]=causal_module
 causal=causal_module.__dict__;causal.update(common);causal["__name__"]=causal_module.__name__
 exec(compile(extracted(read_ref(CAUSAL),CAUSAL_NODES),CAUSAL["path"],"exec"),causal)
 ann_module=types.ModuleType("frozen_ann_math_AST_excerpt");sys.modules[ann_module.__name__]=ann_module
 ann=ann_module.__dict__;ann.update(common);ann["__name__"]=ann_module.__name__;ann["sparse_attention"]=types.SimpleNamespace(causal_index=causal["causal_index"])
 ann["ScoreSettings"]=typing.Union # annotations only; original constructor checks real classes.
 exec(compile(extracted(read_ref(ANN),ANN_NODES),ANN["path"],"exec"),ann)
 return ann,causal
def observed_call(ann,module,query,key,value,mask):
 """Transparent eager observation of the EXACT invocation, never graph capture.
 Two first gather calls are SparseQ(query/channel, key/channel); subsequent
 gathers belong to AnnAttention. No returned operand/value is replaced.
 Restores namespace and removes hook even on the original first exception.
 """
 original=ann["gather"];channels=[];scores=[]
 def observing_gather(t,dim,i):
  if len(channels)<2:channels.append(i.detach().clone())
  return original(t,dim,i)
 def score_hook(_module,_args,result):scores.append(result.detach().clone())
 hook=module.score.register_forward_hook(score_hook)
 ann["gather"]=observing_gather
 try:output,weights=module(query,key,value,mask)
 finally:
  ann["gather"]=original
  hook.remove()
 require(len(channels)==2 and len(scores)==1,"one exact literal selector invocation, two actual SparseQ channel gathers")
 return output,weights,channels,scores[0]
def reference(torch,objects,q,k,v,reallocation,outside_capture):
 require(outside_capture is True and q.ndim==3 and k.ndim==3 and v.shape==k.shape,"literal source reference explicitly outside original GLOBAL graph")
 ann,causal=objects
 settings=ann["Settings"](k=127,local_k=0,reallocate_to_mean_value=bool(reallocation),score="sparse_q",rank=32)
 module=ann["AnnAttention"](settings,n_kv_heads=1,head_size=256)
 module.debug_indices=[]
 # Here the full native domain is explicitly gathered independently by caller.
 key=k[:,None,:,:];value=v[:,None,:,:];query=q[:,:,None,:]
 mask=torch.zeros((q.shape[0],6,1,k.shape[1]),dtype=q.dtype,device=q.device)
 output,weights,channel_trace,score_trace=observed_call(ann,module,query,key,value,mask)
 require(channel_trace[0].shape==(q.shape[0],1,1,1,32) and torch.equal(channel_trace[0],channel_trace[1]) and
  score_trace.shape==(q.shape[0],1,6,1,k.shape[1]) and len(module.debug_indices)==1,
  "actual original SparseQ gather channels and score paired with the same AnnAttention debug support")
 return {"output":output.squeeze(-2),"weights":weights,"indices":module.debug_indices[-1].view(q.shape[0],-1),
  "channels":channel_trace[0].view(q.shape[0],32),"score_observation":score_trace.view(q.shape[0],6,k.shape[1]),
  "observation":"eager transparent gather and SparseQ forward hook; output never modified; hook/namespace restored",
  "literal_class_source":ANN,"literal_causal_source":CAUSAL,"outside_capture":True,
  "zero_query_guard":"none; literal author has 0/0 outside nonzero-coverage domain"}
