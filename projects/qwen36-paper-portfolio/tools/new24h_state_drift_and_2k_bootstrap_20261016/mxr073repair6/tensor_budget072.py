"""Conservative full logical tensor budget; no dedup/alias savings assumed."""
T,HQ,HV,D=2048,4,12,128
LAYERS,RANKS,DECODE_STEPS=48,4,9
def bounds():
 qkv=T*(2*HQ+HV)*D*2
 gates=2*T*HV*4
 state=HV*D*D*4
 metadata=64*1024
 # Full raw input and normalized copies, output/final, A32+BF16 solve,
 # exact physical returned/writeback, and9 full native decode before/after.
 prefill=2*(qkv+gates+state+metadata)+T*HV*D*2+state+T*HV*64*(4+2)+metadata+2*state+metadata
 decode=2*state+(2*HQ+HV)*D*2+2*HV*4+metadata
 per_layer=prefill+DECODE_STEPS*decode
 return dict(tokens=T,Hq=HQ,Hv=HV,D=D,layers=LAYERS,ranks=RANKS,decode_steps=DECODE_STEPS,prefill_logical_bound=prefill,decode_logical_bound=decode,all_tensor_logical_bound=per_layer*LAYERS*RANKS,raw_and_control_cap=12*2**30,no_dedup_savings_assumed=True,cache_log_fit_guaranteed=False)
def validate_inputs(torch,v):
 for name,heads in(('q',HQ),('k',HQ),('v',HV)):
  x=v[name]
  if tuple(x.shape)!=(1,T,heads,D)or x.dtype!=torch.bfloat16:raise ValueError('registered2K actual BF16 q/k/v tensor geometry')
 s=v['initial_state']
 if tuple(s.shape)!=(1,HV,D,D)or s.dtype!=torch.float32:raise ValueError('registered single2K FP32 initial state')
 # All less-obvious metadata are counted explicitly, not silently omitted.
 other=sum(x.numel()*x.element_size()for k,x in v.items()if torch.is_tensor(x)and k not in('q','k','v','initial_state','g','beta'))
 if other>64*1024:raise ValueError('registered2K metadata64KiB bound')
 for k in('g','beta'):
  if v[k].numel()>T*HV or v[k].element_size()>4:raise ValueError('registered gate size/dtype bytes')
 return bounds()
