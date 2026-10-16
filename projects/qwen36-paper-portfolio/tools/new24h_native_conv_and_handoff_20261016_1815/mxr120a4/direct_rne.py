"""Independent integer-significand binary64 -> BF16 RNE; no FP32 cast."""
def round_bf16(torch,x):
 if x.device.type!='cpu'or x.dtype!=torch.float64:raise ValueError('CPU64 only')
 bits=x.contiguous().view(torch.int64);sign=(bits>>63)&1;a=bits&0x7fffffffffffffff;e=(a>>52)&2047;frac=a&((1<<52)-1)
 normal=(e>=897)&(e<=1150);sub=(e>=889)&(e<897);top=((e-896)<<7)+(frac>>45);rem=frac&((1<<45)-1)
 n=top+((rem>(1<<44))|((rem==(1<<44))&((top&1)!=0))).to(torch.int64)
 shift=(942-e).clamp(1,63);sig=frac|(1<<52);q=sig>>shift;mask=(torch.ones_like(shift)<<shift)-1;r=sig&mask;half=torch.ones_like(shift)<<(shift-1)
 sq=q+((r>half)|((r==half)&((q&1)!=0))).to(torch.int64)
 out=torch.zeros_like(bits);out=torch.where(normal,n,out);out=torch.where(sub,sq,out);out=torch.where(e>1150,torch.full_like(out,0x7f80),out);out=torch.where((e==2047)&(frac!=0),torch.full_like(out,0x7fc0),out)
 return(out|(sign<<15)).to(torch.int16).view(torch.bfloat16)
