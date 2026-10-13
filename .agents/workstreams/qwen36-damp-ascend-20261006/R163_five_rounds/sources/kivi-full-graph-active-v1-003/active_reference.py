"""Independent AUTHOR CPU byte codec + unchanged FP64 oracle. No candidate import."""
import ast, hashlib, importlib.util, json, struct
from pathlib import Path
FIELDS=('key_codes','key_scales','key_minima','value_codes','value_scales','value_minima','key_residual','value_residual')
AUTHOR='3678af0e34a0ba18e5d80a4128acf11d4070667c800a15540a16d07253a4f75e'
ORACLE='5d6278c20800e6b90b9e0fc5869fbaf9b5fdce5d4d652d7725cb68e8c4fed444'
def need(v,m):
 if not v: raise ValueError(m)
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'} and type(r['bytes'])is int and 0<r['bytes']<=256*1024**2,'strict bounded Ref3')
 p=Path(r['path']);need(p.is_absolute() and p.resolve()==p and p.is_file() and not p.is_symlink(),'ordinary exact source/raw')
 a=p.stat();b=p.read_bytes();z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns) and len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'whole stable bytes');return b
def load(r,name):
 s=importlib.util.spec_from_file_location(name,r['path']);m=importlib.util.module_from_spec(s);exec(compile(checked(r),r['path'],'exec',dont_inherit=True),m.__dict__);return m
def author(torch,r):
 raw=checked(r);need(r['sha256']==AUTHOR,'exact released author byte codec')
 names={'quant_and_pack_kcache','quant_and_pack_vcache','pack_tensor'}
 nodes=[n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name in names]
 need({n.name for n in nodes}==names and all(not n.decorator_list for n in nodes),'complete original CPU functions; no rewritten math')
 ns={'torch':torch};exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),r['path'],'exec',dont_inherit=True),ns);return ns
def tensor_bytes(t):return t.contiguous().view(__import__('torch').uint8).numpy().tobytes()
def inputs(torch):
 # Dyadic BF16 values; every 32-token/channel group is nonconstant. No RNG or model claim.
 k=torch.tensor([((i*7+d*3)%31-15)/16 for i in range(258) for d in range(256)],dtype=torch.bfloat16).reshape(258,256)
 v=torch.tensor([((i*11+d*5)%29-14)/16 for i in range(258) for d in range(256)],dtype=torch.bfloat16).reshape(258,256)
 q=torch.tensor([((h*13+d*7)%23-11)/32 for h in range(6) for d in range(256)],dtype=torch.bfloat16).reshape(1,6,256)
 return q,k,v
class State:
 def __init__(self,t,ar):
  self.t=t;self.a=author(t,ar);self.free_k=list(range(8));self.free_v=list(range(1024));self.epoch=0;self.live=False
  self.pool=dict(key_codes=t.zeros((8,8,256),dtype=t.int32),key_scales=t.zeros((8,4,256),dtype=t.bfloat16),key_minima=t.zeros((8,4,256),dtype=t.bfloat16),value_codes=t.zeros((1024,16),dtype=t.int32),value_scales=t.zeros((1024,8),dtype=t.bfloat16),value_minima=t.zeros((1024,8),dtype=t.bfloat16),key_residual=t.zeros((16,128,256),dtype=t.bfloat16),value_residual=t.zeros((16,129,256),dtype=t.bfloat16))
 def kseal(self,x,p):
  c,s,m=self.a['quant_and_pack_kcache'](x.reshape(1,1,128,256),32,2)
  self.pool['key_codes'][p].copy_(c[0,0]);self.pool['key_scales'][p].copy_(s.reshape(4,256));self.pool['key_minima'][p].copy_(m.reshape(4,256))
 def vseal(self,x,p):
  c,s,m=self.a['quant_and_pack_vcache'](x.reshape(1,1,-1,256),32,2)
  for j,i in enumerate(p):
   self.pool['value_codes'][i].copy_(c[0,0,j]);self.pool['value_scales'][i].copy_(s.reshape(-1,8)[j]);self.pool['value_minima'][i].copy_(m.reshape(-1,8)[j])
 def start(self,k,v,rid):
  need(not self.live,'no live-slot replacement');self.epoch+=1;self.live=True;self.rid=rid;self.n=255;self.kt=127;self.vt=128;self.gen=1
  self.kp=[self.free_k.pop(0)];self.vp=self.free_v[:127];del self.free_v[:127]
  self.pool['key_residual'][0].zero_();self.pool['value_residual'][0].zero_()
  self.kseal(k[:128],self.kp[0]);self.vseal(v[:127],self.vp)
  self.pool['key_residual'][0,:127].copy_(k[128:255]);self.pool['value_residual'][0,:128].copy_(v[127:255])
 def pending(self,k,v):
  need(self.live and self.kt<128 and self.vt==128,'actual ordered active tail')
  self.pool['key_residual'][0,self.kt].copy_(k);self.pool['value_residual'][0,self.vt].copy_(v)
  return dict(slot=0,epoch=self.epoch,generation=self.gen,request_id=self.rid,computed=self.n,controls=[self.n+1,len(self.kp)*128,len(self.vp),0],kp=list(self.kp),vp=list(self.vp))
 def finish(self):
  if self.kt==127:
   p=self.free_k.pop(0);self.kseal(self.pool['key_residual'][0].clone(),p);self.kp.append(p)
  p=self.free_v.pop(0);self.vseal(self.pool['value_residual'][0,:1].clone(),[p]);self.vp.append(p)
  self.pool['value_residual'][0,:128].copy_(self.pool['value_residual'][0,1:129].clone())
  self.n+=1;self.gen+=1;self.kt=(self.kt+1)%128
 def release(self):
  need(self.live,'actual release');self.free_k.extend(self.kp);self.free_v.extend(self.vp);self.live=False
 def bytes(self):return {n:tensor_bytes(self.pool[n]) for n in FIELDS}
def replay(index_ref,source_ref):
 m=json.loads(checked(source_ref));idx=json.loads(checked(index_ref));need(idx['source']==source_ref and idx['schema']=='kivi.active128-slot-reuse-raw/v1' and idx['primary']is None and idx['actual_graph_captured']is True,'source-bound actual new raw')
 import torch
 need(not torch.npu.is_initialized() if hasattr(torch,'npu') else True,'CPU independent process not NPU initialized')
 O=load(m['oracle'],'_active128_original_fp64');need(m['oracle']['sha256']==ORACLE,'unchanged independent FP64 fsum oracle')
 st=State(torch,m['author']);q,k,v=inputs(torch);metrics=[];need(len(idx['cases'])==2,'both epochs')
 for ci,case in enumerate(idx['cases']):
  st.start(k,v,'active128-epoch%d'%(ci+1));need(case['request_id']==st.rid and case['epoch']==st.epoch and len(case['steps'])==3,'actual unique RID/slot epoch')
  for j,event in enumerate(case['steps']):
   need(event['actual_graph_replayed']is True and event['actual_error_zero']is True,'actual completed captured writer, not eager substitution')
   row=st.pending(k[255+j],v[255+j]);need(event['pending_row']==row,'full independent pending topology')
   golden=O.attention(st.bytes(),row,[[O.scalar(tensor_bytes(q),h*256+d,'bfloat16') for d in range(256)] for h in range(6)],2,'bfloat16')
   raw=checked(event['output_ref']);need(len(raw)==3072,'all1536 output bytes');metric=O.compare([O.scalar(raw,i,'bfloat16')for i in range(1536)],[x for r in golden['mathematical_attention_final_a16_output']for x in r]);metrics.append(metric)
   st.finish();need(set(event['pool_refs'])==set(FIELDS),'all fields including inactive bytes')
   for n,b in st.bytes().items():need(checked(event['pool_refs'][n])==b,'independent author complete packed/min/scale/tail byte parity '+n)
  need(case['retired_by_probe_finished_callback'] is True and case['stale_request_rejected'] is True,'explicit standalone finish callback and stale epoch control')
  st.release()
 return dict(schema='kivi.active128-slot-reuse-independent/v1',source=source_ref,raw_ref=index_ref,all6_outputs=9216,active_k_seals=2,value_shifts=6,epochs=[1,2],metrics=metrics,byte_reference='source-exact original author CPU quant+packing',attention_reference='softmax-fp64-fsum-exp-QK-over16-V-final-A16/v1',native_scheduler_qualified=False,full640=False,model_ready=False,performance_ready=False,task_ready=False,run_authority=False)
