"""Saved raw only: persist original sidecar predicates before any aggregate assert."""
import argparse,hashlib,importlib.util,json,os,sys,time,traceback
from pathlib import Path

def need(v,msg):
 if not v:raise ValueError(msg)
def checked(r):
 need(set(r)=={'path','bytes','sha256'},'exact Ref3')
 p=Path(r['path']);h=hashlib.sha256();n=0
 with p.open('rb')as f:
  while True:
   b=f.read(4*1024*1024)
   if not b:break
   n+=len(b);h.update(b)
 need(n==r['bytes']and h.hexdigest()==r['sha256'],'actual source/raw bytes '+str(p));return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,name):
 p=checked(r);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def write(p,v):
 with p.open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
def safe(v):
 if isinstance(v,float)and not __import__('math').isfinite(v):return repr(v)
 if isinstance(v,dict):return{k:safe(x)for k,x in v.items()}
 if isinstance(v,(tuple,list)):return[safe(x)for x in v]
 return v
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--producer-ref');p.add_argument('--output');a=p.parse_args()
 if not a.execute:print('disabled');return 0
 need(not list(Path('/dev').glob('davinci*'))and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='','actual Devices[] CPU environment')
 sr=json.loads(a.source_ref);pr=json.loads(a.producer_ref);m=obj(sr);producer=obj(pr)
 need(m['schema']=='deltalog.deadpayload-native-bridge-source/v024'and m['default_enabled']is False and m['prepared_only']is False,'actual immutable R3 target')
 need(producer['schema']=='deltalog.actual-fresh-bridge/v5'and producer['source']==sr and producer['primary']is None and producer['steps']==16 and producer['NPU']is True and producer['graph']is False and producer['fullmodel']is False,'actual saved complete16 producer; not model qualification')
 out=Path(a.output);need(out.is_absolute()and out.parent.is_dir()and not out.exists(),'fresh exclusive CPU diagnostic directory');out.mkdir()
 for r in m['files'].values():checked(r)
 # Use the actual frozen modules and actual static proof, never copied math.
 sys.path.insert(0,str(checked(m['files']['domain_consumer.py']).parent))
 domain=load(m['files']['domain_consumer.py'],'actual_R3_domain_diagnostic')
 proof=domain.static_proof(m)
 R=load(m['files']['oracle.py'],'actual_R3_independent_oracle')
 load(m['files']['direct_round.py'],'direct_round')
 P=load(m['files']['precast.py'],'actual_R3_precast')
 A=load(m['files']['sidecar_audit.py'],'actual_R3_sidecar_audit')
 import torch
 torch.set_num_threads(1)
 codec=load(m['files']['raw_codec.py'],'raw_codec');codec.install(torch)
 mixed={r['path']for r in producer['actual_mixed_sidecar_records']};controls=producer['boundary_controls'];overflow={x['raw']['path']for x in controls if x['case']=='overflow'}
 refs=producer['actual_sidecar_records'];need(len(refs)==57 and len(mixed)==32 and len({r['path']for r in refs})==57,'all57 exact sidecars /32 mixed')
 need([x['case']for x in controls]==['normal','tiny','subnormal','positive-zero','negative-zero','cancellation','overflow'],'same actual seven boundary controls')
 labels={x['raw']['path']:x['case']for x in controls};rows=[];start=time.monotonic()
 for i,r in enumerate(refs):
  need(time.monotonic()-start<600,'original bounded CPU600s')
  row=dict(index=i,raw=r,numeric=r['path']not in mixed,overflow=r['path']in overflow,boundary_case=labels.get(r['path']))
  try:
   raw=torch.load(checked(r),map_location='cpu',weights_only=False)
   row['original_audit']=A.audit(torch,R,P,raw,overflow=row['overflow'],numeric=row['numeric'])
   row['original_predicate_pass']=row['original_audit']['passed']
   row['metadata']=dict(input_shapes=[list(x.shape)for x in raw['before']],input_dtypes=[str(x.dtype)for x in raw['before']],sequence=raw['before'][11].flatten().tolist(),ids=raw['before'][12].flatten().tolist(),length_before=raw['before'][10].flatten().tolist(),output_shape=list(raw['production_output'].shape),output_dtype=str(raw['production_output'].dtype),sidecar_dtype=str(raw['actual_precast_FP32'].dtype))
  except Exception as e:
   row.update(original_predicate_pass=False,error_type=type(e).__name__,error=repr(e),traceback=traceback.format_exc())
  write(out/('ROW-%03d.json'%i),safe(row));rows.append(row)
 summary=dict(schema='deltalog.saved-sidecar-predicate-diagnostic/v1',source=sr,producer=pr,static_proof=proof,rows=safe(rows),failed_indices=[r['index']for r in rows if not r['original_predicate_pass']],diagnostic_complete=True,NPU_reexecuted=False,old_failed_owner_unchanged=True,numeric16_qualified=False,numeric160_qualified=False,model_ready=False,performance_ready=False,task_ready=False)
 write(out/'DIAGNOSIS.json',summary);print(json.dumps(dict(diagnostic_complete=True,failed_indices=summary['failed_indices'],NPU=False)));return 0
if __name__=='__main__':raise SystemExit(main())
