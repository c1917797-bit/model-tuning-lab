"""Bounded primitive-only saved043 subnormal bytes; no torch or device access."""
import argparse,decimal,hashlib,importlib.util,json,math,struct,sys,time
from pathlib import Path
RAW=dict(path='/opt/host/vnf/austinov/deltalog-mixed-precast-new48h-043-repair3/run-numeric16-MAIN-20261015-001/numeric/result/sidecar-call-0002.pt',bytes=210733,sha256='aea805c097a6e20841bdabcf90cfb759cf5c382daffbe2fb0a5697eff596e911')
READER=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog043r3-sidecar-cpu-recovery-new48h-v1-001-repair3/raw_closure043.py',bytes=1372,sha256='276cdbc1e6f15f49390fec9890958cfc6e0d3930c7e26d29425387d3d052632a')
def need(v,s):
 if not v:raise ValueError(s)
def checked(r):
 p=Path(r['path']);need(set(r)=={'path','bytes','sha256'}and p.is_absolute()and not p.is_symlink(),'ordinary exact Ref3');h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 need(n==r['bytes']and h.hexdigest()==r['sha256'],'Ref bytes '+str(p));return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,n):
 s=importlib.util.spec_from_file_location(n,checked(r));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def tensor(t,root):
 need(set(t)=={'__tensor043__','dtype','shape','chunks'}and t['__tensor043__']is True,'actual tensor descriptor')
 width={'torch.float32':4,'torch.bfloat16':2,'torch.int32':4}[t['dtype']];n=math.prod(t['shape']);need(n*width<=16*1024**2,'bounded tensor bytes16MiB')
 parts=[]
 for r in t['chunks']:
  need(Path(r['path']).parent==root/'tensor-blobs','same actual owned blob root');parts.append(checked(r).read_bytes())
 b=b''.join(parts);need(len(b)==n*width,'exact shape/byte geometry')
 if t['dtype']=='torch.bfloat16':values=[struct.unpack('<f',struct.pack('<I',x[0]<<16))[0]for x in struct.iter_unpack('<H',b)]
 else:values=[x[0]for x in struct.iter_unpack('<f'if t['dtype']=='torch.float32'else'<i',b)]
 fmt='<H'if width==2 else'<I';bits={}
 for x in struct.iter_unpack(fmt,b):
  k=('%04x'if width==2 else'%08x')%x[0];bits[k]=bits.get(k,0)+1
 return values,dict(dtype=t['dtype'],shape=t['shape'],bit_patterns=bits,unique_values=sorted(set(values)))
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--reader-ref');p.add_argument('--output');a=p.parse_args()
 if not a.execute:print('disabled');return 0
 start=time.monotonic();sr=json.loads(a.source_ref);m=obj(sr);rr=json.loads(a.reader_ref)
 need(m['root']=='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-mixed-precast-new48h-v1-043-repair3'and m['prepared_only']is False and m['default_enabled']is False,'actual unchanged R3 source')
 for k in('npu_controls.py','oracle.py','precast.py','sidecar_audit.py','raw_codec.py'):checked(m['files'][k])
 need(rr==READER,'exact existing audited primitive-only reader')
 R=load(rr,'actual_primitive043_reader');raw=R.metadata(RAW,checked);root=Path(RAW['path']).parent;b=raw['before'];need(len(b)==13,'original13 args')
 arrays=[];meta=[]
 for x in b:
  v,t=tensor(x,root);arrays.append(v);meta.append(t)
 y,ym=tensor(raw['actual_precast_FP32'],root);z,zm=tensor(raw['production_output'],root)
 base=arrays[5][:12*128*128]
 recipe=dict(query_BF16_ones=meta[0]['dtype']=='torch.bfloat16'and set(arrays[0])=={1.},key_zero=set(arrays[1])=={0.},value_zero=set(arrays[2])=={0.},g_zero=set(arrays[3])=={0.},beta_zero=set(arrays[4])=={0.},base_FP32_active_exact_2neg140=meta[5]['dtype']=='torch.float32'and set(base)=={2.**-140},ids_zero=arrays[12]==[0],sequence_0_1=arrays[11]==[0,1],length_zero=set(arrays[10][:12*16])=={0},decay_zero=set(arrays[9][:12*16])=={0.})
 with decimal.localcontext()as c:
  c.prec=80;D=decimal.Decimal;truth=D.from_float(2.**-140)*D(128)/D(128).sqrt();qs=f32(128**-.5);term=f32(2.**-140*qs);summed=0.
  for _ in range(128):summed=f32(summed+term)
  late=f32(f32(2.**-140*128)*qs)
  comparisons=[dict(coord=[0,(i//128)%12,i%128],actual_FP32=v,actual_exact_decimal=str(D.from_float(v)),ideal_exact_decimal=str(truth),absolute_error=str(abs(D.from_float(v)-truth)),relative_error=float(abs(D.from_float(v)-truth)/abs(truth)),FP32_subnormal_units=v/2.**-149)for i,v in enumerate(y)]
  report=dict(schema='deltalog.saved-subnormal-bit-diagnostic/v1',source=sr,reader=rr,raw=RAW,actual_recipe=recipe,recipe_complete=all(recipe.values()),inputs=meta,precast=ym,BF16_output=zm,model=dict(independent_Decimal80_closed_form=str(truth),qscale_FP32=qs,per_term_FP32=term,per_term_units=term/2.**-149,ordered_FP32_sum=summed,ordered_FP32_sum_units=summed/2.**-149,late_scale_FP32=late,observed_equals_ordered_sum=all(v==summed for v in y),observed_zero_FTZ=all(v==0 for v in y),predicted_relative_error=float(abs(D.from_float(summed)-truth)/abs(truth))),cells=comparisons,old_gate_FAIL_unchanged=True,numeric_qualified=False,model_ready=False,NPU_reexecuted=False)
 need(time.monotonic()-start<30 and not any(n in sys.modules for n in('torch','torch_npu','vllm','vllm_ascend')),'bounded30s stdlib only')
 out=Path(a.output);need(out.is_absolute()and out.parent.is_dir()and not out.exists(),'new exclusive diagnostic JSON')
 with out.open('x',encoding='utf8')as f:json.dump(report,f,sort_keys=True,allow_nan=False);f.write('\n')
 print(json.dumps(dict(diagnostic_complete=True,recipe_complete=report['recipe_complete'],observed_equals_ordered_sum=report['model']['observed_equals_ordered_sum'],NPU=False)))
if __name__=='__main__':raise SystemExit(main())
