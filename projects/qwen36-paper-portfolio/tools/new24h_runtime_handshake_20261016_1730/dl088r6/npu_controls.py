"""Real-kernel boundary inputs. No mock operator or device fallback."""
CASES=('normal','tiny','subnormal','positive-zero','negative-zero','cancellation','overflow','finite-final-normalized-query','finite-final-unscaled-query','cancellation-permuted','gqa-vtile-witness')
def run(torch,h,capture):
 records=[]
 for name in CASES:
  base=torch.zeros((6,12,128,128),dtype=torch.float32)
  if name in('normal','tiny','subnormal','overflow'):base[0].fill_({'normal':.125,'tiny':2.**-120,'subnormal':2.**-140,'overflow':3.0e38}[name])
  elif name=='negative-zero':base[0].fill_(-0.)
  elif name=='finite-final-normalized-query':base[0].fill_(1e38)
  elif name=='finite-final-unscaled-query':base[0].fill_(1e37)
  elif name=='cancellation-permuted':base[0,:,:,:64]=.125;base[0,:,:,64:]=-.125
  elif name=='gqa-vtile-witness':
   for head in range(12):base[0,head,:64,:]=(head+1)*.0001;base[0,head,64:,:]=-(head+1)*.0002
  elif name=='cancellation':base[0,:,:,::2]=.125;base[0,:,:,1::2]=-.125
  state=h.allocate_state(base);q=torch.ones((1,4,128),dtype=torch.bfloat16,device='npu:0');k=torch.zeros_like(q);v=torch.zeros((1,12,128),dtype=torch.bfloat16,device='npu:0');g=torch.zeros((1,12),device='npu:0');beta=torch.zeros((1,12),dtype=torch.bfloat16,device='npu:0');seq=torch.tensor([0,1],dtype=torch.int32,device='npu:0');ids=torch.tensor([0],dtype=torch.int32,device='npu:0')
  if name=='finite-final-normalized-query':q.fill_(128**-.5)
  if name=='gqa-vtile-witness':
   for head in range(4):q[0,head].fill_(head+1)
  capture(q,k,v,g,beta,*[state[n]for n in('base','k_log','u_log','lambda_log','decay','length')],seq,ids)
  records.append(dict(case=name,raw=capture.take(),expect='reject-nonfinite'if name=='overflow'else'finite-empirical-pass'))
 return records
