"""Direct binary64 -> BF16 RNE by integer significand, never FP32 cast."""
def round_bf16(torch,x):
 if x.device.type!='cpu' or x.dtype!=torch.float64:raise ValueError('independent CPU64 required')
 bits=x.contiguous().view(torch.int64);sign=(bits>>63)&1;a=bits&0x7fffffffffffffff;e=(a>>52)&2047;frac=a&((1<<52)-1)
 normal=(e>=897)&(e<=1150);sub=(e>=889)&(e<897)
 top=((e-896)<<7)+(frac>>45);rem=frac&((1<<45)-1)
 inc=(rem>(1<<44))|((rem==(1<<44))&((top&1)!=0));n=top+inc.to(torch.int64)
 shift=(942-e).clamp(1,63);sig=frac|(1<<52);q=sig>>shift;mask=(torch.ones_like(shift)<<shift)-1;r=sig&mask;half=torch.ones_like(shift)<<(shift-1)
 sq=q+((r>half)|((r==half)&((q&1)!=0))).to(torch.int64)
 out=torch.zeros_like(bits);out=torch.where(normal,n,out);out=torch.where(sub,sq,out)
 out=torch.where(e>1150,torch.full_like(out,0x7f80),out);out=torch.where((e==2047)&(frac!=0),torch.full_like(out,0x7fc0),out)
 return (out|(sign<<15)).to(torch.int16).view(torch.bfloat16)
def peer_error(torch,actual,truth):
 if actual.shape!=truth.shape or actual.dtype!=torch.bfloat16 or truth.dtype!=torch.float64:raise ValueError('frozen actualBF16/truthCPU64 shape')
 if not bool(torch.isfinite(actual).all()and torch.isfinite(truth).all()):raise ValueError('nonfinite independent output')
 rounded=round_bf16(torch,truth);a=actual.double();r=rounded.double()
 if not bool(torch.isfinite(r).all()):raise ValueError('BF16 reference overflow')
 den=max(float(r.abs().max()),1e-30)
 # Exact BF16 neighbors are built through integer bitpatterns, no FP32 rounding.
 raw=rounded.contiguous().view(torch.int16).to(torch.int32)&65535
 lower=torch.where(r<0,raw+1,raw-1);upper=torch.where(r<0,raw-1,raw+1)
 lower=torch.where(r==0,torch.full_like(lower,0x8001),lower);upper=torch.where(r==0,torch.full_like(upper,1),upper)
 lv=lower.to(torch.int16).view(torch.bfloat16).double();uv=upper.to(torch.int16).view(torch.bfloat16).double()
 low=(lv+r)*.5;high=(uv+r)*.5;margin=torch.minimum((truth-low).abs(),(high-truth).abs())
 return float((a-r).abs().max())/den,dict(uncast_peak=float((a-truth).abs().max())/max(float(truth.abs().max()),1e-30),rounding_floor_peak=float((r-truth).abs().max())/max(float(truth.abs().max()),1e-30),minimum_CPU64_BF16_midpoint_margin=float(margin.min()),exact_midpoint_count=int((margin==0).sum()),margin_only_diagnostic=True,reference='independent CPU64 direct-integer-RNE BF16',version=13)
def controls(torch):
 x=torch.tensor([1+2**-8+2**-30,1+2**-8-2**-30,1+2**-8,-1-2**-8-2**-30,-1-2**-8+2**-30,-1-2**-8,0.,-0.,2**-134,2**-134+2**-150,2**-134-2**-150,2**-133,-2**-133,2**-126,2**128,-2**128],dtype=torch.float64)
 want=torch.tensor([1+2**-7,1.,1.,-1-2**-7,-1.,-1.,0.,-0.,0.,2**-133,0.,2**-133,-2**-133,2**-126,float('inf'),-float('inf')],dtype=torch.float64)
 got=round_bf16(torch,x).double()
 if not torch.equal(got,want):raise ValueError('direct-RNE positive/negative midpoint/subnormal/overflow controls')
 if round_bf16(torch,x[7:8]).view(torch.int16).item()!=-32768:raise ValueError('signedzero preserved')
 if x[0].float().bfloat16().item()!=1.:raise ValueError('expected explicit double-round negative control')
 for bad in[torch.ones(1,dtype=torch.float32)]:
  try:round_bf16(torch,bad)
  except ValueError:pass
  else:raise ValueError('wrongprecision must reject')
 return dict(direct_RNE=True,FP32_intermediate=False,controls=16,double_round_negative_control=True)
