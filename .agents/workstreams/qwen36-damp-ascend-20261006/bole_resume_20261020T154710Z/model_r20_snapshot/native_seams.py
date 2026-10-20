"""Source-preparation seam, not a vLLM installer or model qualification."""
from dataclasses import dataclass

def need(v,s):
 if not v:raise ValueError(s)

def bits(t,a,b):
 return a.shape==b.shape and a.dtype==b.dtype and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8))

def gdn_canonical_view(t,arena,*,layout):
 """Never infer orientation because both state dimensions happen to be128."""
 need(layout=='slot,H,Dv,Dk','explicit installed GDN arena orientation')
 need(arena.ndim==4 and tuple(arena.shape[1:])==(12,128,128)and arena.dtype==t.float32,'actual TP4 GDN FP32 state geometry')
 need(arena.stride(-1)==1 and arena.stride(-2)==128 and arena.stride(-3)==16384 and arena.stride(0)>=196608,'nonoverlapping native GDN slots; no fabricated contiguous arena')
 return arena.transpose(-1,-2)

def conv_call_arguments(t,trial,weight,bias,*,activation):
 """Same12-arg SD one-token ABI as the actual118c calibration.

 All nodes are one batch of independent ancestor tails; no flattened sibling
 convolution and no persistent cache mutation happens during verification.
 """
 n,c=trial.inputs.shape
 need(n==3 and c==2560 and trial.histories.shape==(3,3,2560),'B1 root+two siblings, real local channel geometry')
 need(weight.shape==(2560,4)and weight.dtype==trial.inputs.dtype==trial.histories.dtype==t.bfloat16,'native weight/input/cache BF16; no implicit casts')
 need(bias is None,'only actual calibrated no-bias domain')
 need(type(activation)is bool and not trial.closed,'live trial and explicit activation')
 scratch=trial.histories.clone();output=t.full_like(trial.inputs,float('nan'))
 kwargs=dict(conv_state=scratch,bias_opt=None,
  query_start_loc_opt=t.arange(4,dtype=t.int32,device=trial.inputs.device),
  cache_indices_opt=t.arange(3,dtype=t.int32,device=trial.inputs.device),
  initial_state_mode_opt=None,num_accepted_tokens_opt=None,activation_mode=int(activation),pad_slot_id=-1,run_mode=1)
 return (output,trial.inputs,weight.transpose(0,1)),kwargs

def native_tree_conv(t,C,tree_module,predecessor,actual118c,trial,weight,bias,*,activation,op,actual_abi,arm_verified=False):
 """Actual on-device seam only; caller must supply the existing owned stage.

 No owner/device selector is created here. The real118c reader reopens numeric,
 consumer and exact raw chains. No nonexistent layout/v118 certificate is used.
 """
 need(arm_verified is True and trial.inputs.device.type=='npu','existing actual device/ARM stage required')
 predecessor.join(C,dict(actual_118c=actual118c))
 cap=C.obj(actual118c['capture']);abi_ref=cap['actual_device_abi_ref'];abi=C.obj(abi_ref)
 import model_calibration131r12 as MC
 new=C.obj(actual_abi);MC.own_module(C,C.obj(new['source']),MC)
 new=MC.validate(C,actual_abi,abi_ref,new['source'])
 need(new['actual_schema_family']==abi['actual_schema_family'],'new actual model calibration keeps original118c ABI family')
 family={k:dict(schema=str(v),name=v.name,argument_names=[a.name for a in v.arguments],is_mutable=v.is_mutable)for k,v in t.ops._C_ascend.npu_causal_conv1d_custom._schemas.items()}
 need(family==abi['actual_schema_family']and str(op._schema)==family['']['schema'],'actual registered native family/callable')
 args,kwargs=conv_call_arguments(t,trial,weight,bias,activation=activation)
 saved=[x.clone()for x in(args[1],args[2],kwargs['query_start_loc_opt'],kwargs['cache_indices_opt'])]
 returned=op(*args,**kwargs)
 need(returned.data_ptr()==args[0].data_ptr()and bits(t,returned,args[0]),'actual output return alias/bytes')
 for before,after in zip(saved,(args[1],args[2],kwargs['query_start_loc_opt'],kwargs['cache_indices_opt'])):
  need(bits(t,before,after),'native modified readonly operand')
 need(bits(t,kwargs['conv_state'],trial.after),'native gathered ancestor tail chronology')
 need(bool(t.isfinite(args[0]).all()),'actual finite tree convolution')
 return args[0],kwargs['conv_state']

@dataclass(frozen=True)
class NodeRows:
 request:str
 generation:int
 slot:int
 committed_length:int
 tokens:tuple
 parents:tuple=(-1,0,0)
 def metadata(self,Tree):
  need(type(self.request)is str and self.request and all(type(x)is int and x>=0 for x in(self.generation,self.slot,self.committed_length)),'actual scheduler request/generation/slot/length')
  need(len(self.tokens)==3 and self.parents==(-1,0,0)and self.tokens[1]!=self.tokens[2],'root+two distinct siblings; not linear MTP')
  return Tree((self.request,),(self.generation,),(self.slot,),(self.committed_length,),(0,3),self.parents,self.tokens,(0,1,1),(self.committed_length,self.committed_length+1,self.committed_length+1)).validate(node_budget=3,max_depth=2,topk=2)
