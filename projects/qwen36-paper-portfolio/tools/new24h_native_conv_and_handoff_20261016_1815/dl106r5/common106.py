"""Caller must use this SAME policy on dense and candidate before plugins."""
POLICY=dict(graph=False,async_scheduling=False,prefix_caching=False,mamba_cache_mode='none',PCP=1,TP=4,matmul_allow_hf32=False,conv_allow_hf32=False)
def apply_precision(torch):
 for group in('matmul','conv'):
  p=getattr(torch.npu,group)
  if type(p.allow_hf32)is not bool:raise ValueError('real common HF32 property')
  p.allow_hf32=False
  if p.allow_hf32 is not False:raise ValueError('common HF32 OFF not applied')
 return dict(POLICY)
def check_shape(*,prompt_tokens,sequences,decode_tokens=1):
 if type(prompt_tokens)is not int or prompt_tokens!=2048 or sequences!=1 or decode_tokens!=1:raise ValueError('106 only actual101 2048-token C1 / one-token decode domain; new evidence required')
 return dict(prefill_tokens=2048,sequences=1,decode_tokens=1)
def request_geometry(meta,step):
 q=step['query']['values']
 if type(q)is not tuple or not all(type(x)is int for x in q)or meta.num_decodes+meta.num_prefills!=1:raise ValueError('actual bound CPU query tuple and C1 only')
 expected=(0,2048)if meta.num_prefills else(0,1)
 if q!=expected:raise ValueError('new shape evidence required; no silent native fallback with deferred state')
 return q
