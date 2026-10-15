"""Real same-image Devices[] dual DSO load and exact Meta call; no fake receipt."""
def run(torch,m,C):
 for k in('library_ref','debug_library','debug_build_ref','debug_kernel_source_ref'):C.checked(m[k])
 for lib in(m['library_ref'],m['debug_library']):torch.ops.load_library(lib['path'])
 ns=('qwen36_deltalog_key_projection','qwen36_deltalog_readout_sidecar_v015');b,s=16,36
 meta=lambda shape,dtype:torch.empty(shape,dtype=dtype,device='meta')
 specs=[((b,4,128),torch.bfloat16),((b,4,128),torch.bfloat16),((b,12,128),torch.bfloat16),((b,12),torch.float32),((b,12),torch.bfloat16),((s,12,128,128),torch.float32),((s,4,7,128),torch.bfloat16),((s,12,7,128),torch.float32),((s,12,16),torch.float32),((s,12,16),torch.float32),((s,12,16),torch.int32),((b+1,),torch.int32),((b,),torch.int32)]
 rows=[]
 for n in ns:
  name=n+'::decode'
  C.need(all(torch._C._dispatch_has_kernel_for_dispatch_key(name,k)for k in('Meta','PrivateUse1')),'actual dual DSO Meta and PrivateUse1')
  op=getattr(torch.ops,n).decode;args=[meta(*v)for v in specs]
  if n==ns[1]:args.append(meta((b,12,128),torch.float32))
  z=op(*args);C.need(z.dtype==torch.bfloat16 and tuple(z.shape)==(b,12,128)and z.device.type=='meta','actual output ABI')
  rows.append(dict(namespace=n,schema=str(op.default._schema),argument_count=len(args),actual_Meta=True))
 return dict(pass_gate=True,NPU=False,debug_library=m['debug_library'],debug_build=m['debug_build_ref'],registrations=rows)
