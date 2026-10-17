"""Source-bound, current-thread AR root witnesses; never changes model returns.

Line events observe the exact installed eager Python bodies. No module forward,
norm, projection, sampling, cache or tensor is replaced. A retained source tensor
may legitimately be reused; a private GPU clone must not change. CPU snapshots
are owned immediately, not at the later common diagnostic export.
"""
import ast,hashlib,inspect,json,sys,threading,os

TENSOR_CAP=2*2**20-64*2**10 # Leaves128KiB scratch inside combined4MiB.
SCALAR_CAP=256*2**10
DECODER={104:('input_norm',('hidden_states','residual')),
 127:('attention_complete',('self_attention_output','residual')),
 136:('post_norm_input',('hidden_states','residual')),
 137:('post_norm_output',('hidden_states','residual')),
 139:('mlp_output',('hidden_states','residual'))}
GDN={119:('projection_complete',('mixed_qkv','z','b','a')),
 137:('core_complete',('core_attn_out','z')),
 142:('gated_norm_input',('core_attn_out','z')),
 143:('gated_norm_output',('core_attn_out','z')),
 145:('out_proj_input',('core_attn_out',))}

def need(v,s):
 if not v:raise ValueError(s)

def bits(t,x,y):
 return x.dtype==y.dtype and tuple(x.shape)==tuple(y.shape) and t.equal(x.contiguous().view(t.uint8),y.contiguous().view(t.uint8))

def ident(x):
 return dict(storage=x.untyped_storage().data_ptr(),pointer=x.data_ptr(),offset=x.storage_offset(),
  storage_bytes=x.untyped_storage().nbytes(),shape=list(x.shape),stride=list(x.stride()),dtype=str(x.dtype),device=str(x.device),
  inference_tensor=x.is_inference(),version=None if x.is_inference()else x._version)

def source_contract(C,refs):
 """Pure stdlib mandatory preflight of actual complete source and line seams."""
 patch=C.checked(refs['qwen_patch']);gdn=C.checked(refs['gdn']);qwen=C.checked(refs['qwen_next'])
 texts={k:open(p,'rb').read().decode('utf8')for k,p in [('decoder',patch),('gdn',gdn),('model',qwen)]}
 expected={('decoder',104):'if self.layer_idx == 0 and _EXTRA_CTX.flash_comm_v1_enabled:',
 ('decoder',127):'hidden_states = self_attention_output',
 ('decoder',136):'hidden_states, residual = self.post_attention_layernorm(hidden_states, residual)',
 ('decoder',137):'hidden_states = self.mlp(hidden_states)',('decoder',139):'if self.layer_scale:',
 ('gdn',119):'core_attn_out = torch.zeros(',('gdn',137):'maybe_save_kv_layer_to_connector("", [])',
 ('gdn',142):'core_attn_out = self.norm(core_attn_out, z)',('gdn',143):'core_attn_out = core_attn_out.reshape(z_shape_og)',
 ('gdn',145):'output[:num_tokens], _ = self.out_proj(core_attn_out)'}
 for(k,line),text in expected.items():need(texts[k].splitlines()[line-1].strip()==text,'exact complete actual source line seam '+k+':'+str(line))
 for text in texts.values():ast.parse(text)
 return texts

def cpu_preflight(C,m,P):
 paths={'qwen_patch':'evidence/root_witness_actual_patch.py','gdn':'evidence/gdn.py','qwen_next':'evidence/qwen3_next.py'}
 refs={}
 for key,name in paths.items():
  r=C.ref(P/name);expected=m['runtime_sources'][key]
  need((r['bytes'],r['sha256'])==(expected['bytes'],expected['sha256']),'exact original-byte installed source snapshot '+key)
  refs[key]=r
 source_contract(C,refs)
 for key,name in [('qwen_gdn','evidence/qwen_gdn_linear_attn.py'),('gdn_base','evidence/gdn_base.py')]:
  actual=C.ref(P/name);expected=m['runtime_sources'][key]
  need((actual['bytes'],actual['sha256'])==(expected['bytes'],expected['sha256']),'exact known-copy receiver source snapshot '+key)
 return dict(NPU=False,actual_runtime=False,exact_source_lines=True)

def plain(C,fn,expected,clsname):
 f=fn.__func__;mod=inspect.getmodule(f);cls=getattr(mod,clsname,None)
 need(C.ref(inspect.getsourcefile(f))==expected and mod is not None and
  f.__globals__ is mod.__dict__ and cls is not None and cls.forward is f and
  isinstance(fn.__self__,cls) and f.__qualname__==clsname+'.forward' and not hasattr(f,'__wrapped__'),
  'exact active native class/receiver/code/globals/source '+clsname)
 return f.__code__

def native_model(C,bridge,own):
 """Only the one already-installed worker-entry closure, never generic unwrap."""
 import worker_entry as W
 method=bridge.model.forward;f=method.__func__
 need(C.ref(W.__file__)==own['files']['worker_entry.py'] and
  C.ref(inspect.getsourcefile(f))==own['files']['worker_entry.py'] and
  f.__globals__ is W.__dict__ and
  f.__code__ is next(c for c in W.install_after_native_prefill.__code__.co_consts
   if inspect.iscode(c)and c.co_name=='forward') and
  method.__self__ is bridge.model,'exact source-owned native prefill wrapper')
 closure=dict(zip(f.__code__.co_freevars,[c.cell_contents for c in f.__closure__]))
 old=closure['old'];need(f.__wrapped__ is old and old.__self__ is bridge.model and closure['inner']is bridge.model,
  'same exact bound original native model closure and wrapper receiver')
 return plain(C,old,own['runtime_sources']['qwen_next'],'Qwen3NextModel')

class Witness:
 def __init__(self,t,C,bridge,owner,tokens,*,source_ref=None,rank=None):
  # Runtime construction is only reached by the original explicitly ON Session.
  own=bridge.own_source;need(own.get('root_repeat_witness',{}).get('enabled')is True,'explicit source-bound root-repeat experiment')
  source_contract(C,own['runtime_sources'])
  import model_entry as E
  need(C.ref(E.__file__)==own['files']['model_entry.py'],'actual private Bridge/BUS source')
  need(owner.length==131 and len(tokens)==3 and tokens[1]!=tokens[2],'unchanged131/C1 root+siblings scope')
  need(bridge.saved and len(bridge.bindings)==64,'original installed complete64 bridge remains required')
  self.t=t;self.C=C;self.bridge=bridge;self.owner=owner;self.tokens=tokens;self.BUS=E.BUS
  self.model_code=native_model(C,bridge,own)
  self.codes={};self.objects={}
  for i in(0,1):
   layer=bridge.model.layers[i];need(layer.layer_idx==i and layer.layer_type=='linear_attention','actual first two decoder/GDN objects')
   E.patched_source(C,layer.forward,own['runtime_sources']['qwen_patch'],'decoder')
   self.codes[layer.forward.__func__.__code__]='decoder';self.objects[id(layer)]=('decoder',i,layer)
   obj=layer.linear_attn
   import gdn_copy_identity as COPY
   need(C.ref(COPY.__file__)==own['files']['gdn_copy_identity.py'] and type(rank)is int and 0<=rank<4 and C.obj(source_ref)==own,'exact new observer/actual source/rank')
   refs={k:own['runtime_sources'][name]for k,name in [('gdn','gdn'),('patch','qwen_patch'),('target','qwen_gdn'),('base','gdn_base')]}
   def emit(value):
    from pathlib import Path
    C.write(Path(own['model_receipt_root'])/('GDN-IDENTITY-%d-%d-%d.json'%(rank,os.getpid(),i)),dict(value,source=source_ref,rank=rank,layer=i,pid=os.getpid()))
   self.codes[COPY.validate(C,obj.forward,refs,emit)]='gdn'
   self.objects[id(obj)]=('gdn',i,obj)
  self.thread=threading.get_ident();self.frames={};self.rows=[];self.retained=[];self.calls=[];self.used=0;self.fault=None;self.entered=False
  self.active_objects=[]
  for i in(0,1):
   layer=bridge.model.layers[i];obj=layer.linear_attn
   self.active_objects.append(dict(layer=i,decoder_object=id(layer),gdn_object=id(obj),
    decoder_function=id(layer.forward.__func__),gdn_function=id(obj.forward.__func__),
    flash_comm_v1_enabled=bool(layer.forward.__func__.__globals__['_EXTRA_CTX'].flash_comm_v1_enabled),
    layer_scale=bool(layer.layer_scale),tp_size=obj.tp_size,
    projection_branch='separate_qkv_z'if hasattr(obj,'in_proj_qkv')else'fused_interleaved'if obj.gqa_interleaved_layout else'fused_qkvz'))

 def __enter__(self):
  need(not self.entered and sys.gettrace()is None and self.BUS.get()is None,'exclusive current-thread observer; no ambient trace/BUS')
  self.entered=True;self.before_trace=sys.gettrace();self.installed_trace=self.trace;sys.settrace(self.installed_trace);return self

 def __exit__(self,typ,error,tb):
  if sys.gettrace()is not self.installed_trace and not(error is not None and sys.gettrace()is None):
   self.fault='foreign tracer replaced scoped observer';raise ValueError(self.fault)
  sys.settrace(self.before_trace)
  if error is not None:self.fault=repr(error)
  return False

 def _snapshot(self,call,kind,layer,stage,values):
  t=self.t;record=dict(call=call,kind=kind,layer=layer,stage=stage,tensors={},none=[])
  for name,x in values.items():
   if x is None:record['none'].append(name);continue
   need(isinstance(x,t.Tensor)and x.device.type in('cpu','npu'),'tensor or explicit None at exact source boundary')
   n=x.numel()*x.element_size();need(n<=64*2**10 and self.used+n<=TENSOR_CAP,'root witness bounded before clone; no full arena')
   self.used+=n;before=ident(x);private=x.detach().clone();cpu=x.detach().to('cpu',copy=True).contiguous().clone()
   need(ident(x)==before and private.untyped_storage().data_ptr()!=x.untyped_storage().data_ptr() and bits(t,private.detach().cpu(),cpu),'immediate distinct owning clones and original identity')
   fmt=private_fmt=None
   if x.device.type=='npu':
    getter=self.bridge.torch_npu.get_npu_format;fmt=int(getter(x));private_fmt=int(getter(private))
    need(int(getter(x))==fmt,'source actual format stable; clone format recorded separately, not inferred')
   item=dict(immediate=cpu,source_identity=before,private_identity=ident(private),format_code=fmt,private_format_code=private_fmt,lifetime=[])
   record['tensors'][name]=item;self.retained.append((x,private,cpu,item))
  self.rows.append(record)

 def _lifetime(self,call):
  t=self.t
  for original,private,cpu,item in self.retained:
   stable=ident(private)==item['private_identity']
   if private.device.type=='npu':stable=stable and int(self.bridge.torch_npu.get_npu_format(private))==item['private_format_code']
   private_equal=stable and bits(t,private.detach().cpu(),cpu)
   oi=ident(original);same=all(oi[k]==item['source_identity'][k]for k in oi if k!='version')
   if original.device.type=='npu':same=same and int(self.bridge.torch_npu.get_npu_format(original))==item['format_code']
   original_equal=same and bits(t,original.detach().cpu(),cpu)
   item['lifetime'].append(dict(after_call=call,private_identity_equal=stable,private_bits_equal=private_equal,
     original_geometry_equal=same,original_bits_equal=original_equal,original_version=oi['version']))
   if not private_equal and 'changed_private'not in item:
    n=private.numel()*private.element_size();need(self.used+n<=TENSOR_CAP,'preserve changed-private evidence budget')
    item['changed_private']=private.detach().to('cpu',copy=True).contiguous().clone();self.used+=n

 def trace(self,frame,event,arg):
  try:return self._trace(frame,event,arg)
  except BaseException as e:self.fault=repr(e);raise

 def _trace(self,frame,event,arg):
  need(threading.get_ident()==self.thread,'observer current thread stable')
  code=frame.f_code
  if event=='call':
   if code==self.model_code and frame.f_locals.get('self')is self.bridge.model:
    ctx=self.BUS.get();need(ctx is not None and ctx.mode=='AR'and ctx.owner==self.owner,'actual original AR BUS/strong owner at model call')
    ordinal=len(self.calls);expected=(0,1,0,2);need(ordinal<4 and ctx.tokens==(self.tokens[expected[ordinal]],)and ctx.positions==(self.owner.length+ordinal%2,),'original root-left/root-right call chronology')
    self.calls.append(dict(ordinal=ordinal,node=expected[ordinal],tokens=list(ctx.tokens),positions=list(ctx.positions)))
    self.frames[id(frame)]=('model',ordinal,None);return self.trace
   role=self.codes.get(code);obj=frame.f_locals.get('self');binding=self.objects.get(id(obj))
   ctx=self.BUS.get()
   if role is not None and binding is not None and binding[2]is obj and binding[0]==role:
    need(ctx is not None and ctx.mode=='AR'and ctx.owner==self.owner,'exact source body only original AR context')
    call=len(self.calls)-1
    if call in(0,2):
     layer=binding[1];self.frames[id(frame)]=(role,call,layer)
     names=('hidden_states','residual','positions')if role=='decoder'else('hidden_states',)
     self._snapshot(call,role,layer,'entry',{k:frame.f_locals[k]for k in names});return self.trace
   return None
  info=self.frames.get(id(frame))
  if info is None:return None
  role,call,layer=info
  if event=='exception':
   # Even a subsequently caught exception leaves this diagnostic incomplete.
   self.fault='observed native Python exception: '+repr(arg[1]);return self.trace
  if event=='line'and role!='model':
   mapping=DECODER if role=='decoder'else GDN
   if frame.f_lineno in mapping:
    stage,names=mapping[frame.f_lineno]
    # CPython can emit the opening line twice for a multiline call. These exact
    # pinned bodies have no loops; never clone the same boundary twice.
    if not any((r['call'],r['kind'],r['layer'],r['stage'])==(call,role,layer,stage)for r in self.rows):
     self._snapshot(call,role,layer,stage,{k:frame.f_locals[k]for k in names})
  if event=='return':
   if self.fault is not None:self.frames.pop(id(frame));return self.trace
   if role=='model':
    value=arg[0]if type(arg)is tuple else arg
    self._snapshot(call,'model',None,'immediate_final_hidden',dict(hidden=value));self._lifetime(call)
   elif role=='decoder':self._snapshot(call,role,layer,'return',dict(hidden_states=arg[0],residual=arg[1]))
   else:self._snapshot(call,role,layer,'return',dict(output=frame.f_locals['output']))
   self.frames.pop(id(frame))
  return self.trace

 def freeze(self):
  need(not self.frames and sys.gettrace()is self.before_trace and self.fault is None,'completed original bodies and restored tracer; no hidden native exception')
  need(not getattr(self,'frozen',False),'one immutable final witness; never refresh a baseline')
  self._lifetime('before_export')
  need([x['node']for x in self.calls]==[0,1,0,2],'all four original forwards preserved')
  for call in(0,2):
   for layer in(0,1):
    for kind,mapping in(('decoder',DECODER),('gdn',GDN)):
     expected=['entry',*[x[0]for x in mapping.values()],'return']
     actual=[r['stage']for r in self.rows if(r['call'],r['kind'],r['layer'])==(call,kind,layer)]
     need(actual==expected,'every exact first-two-layer root boundary captured in order')
  value=dict(schema='bole.immediate-native-root-witness/v1',calls=self.calls,rows=self.rows,tensor_bytes=self.used,
   tensor_cap=TENSOR_CAP,retained_cpu_plus_private_gpu_cap=4*2**20,scratch_cap=128*2**10,source_refs={k:self.bridge.own_source['runtime_sources'][k]for k in('qwen_patch','gdn','qwen_next')},
   owner=dict(request=self.owner.request,generation=self.owner.generation,slot=self.owner.slot,length=self.owner.length,version=self.owner.version),
   original_four_forwards_unchanged=True,numerical_qualification=False,observer_may_perturb=True)
  value['active_objects']=self.active_objects
  unique={item['source_identity']['storage']:item['source_identity']['storage_bytes']for row in self.rows for item in row['tensors'].values()}
  value['retained_original_storage_bytes']=sum(unique.values())
  scalar={k:v for k,v in value.items()if k!='rows'};scalar['rows']=[{**r,'tensors':{k:{a:b for a,b in v.items()if a not in('immediate','changed_private')}for k,v in r['tensors'].items()}}for r in self.rows]
  need(len(json.dumps(scalar,sort_keys=True,allow_nan=False).encode())<=SCALAR_CAP,'bounded scalar root witness')
  self.frozen=True
  return value
