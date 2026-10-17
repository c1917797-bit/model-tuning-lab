"""Read-only saved-input attribution, NEVER an attention qualification gate.

No native import, operator, device or candidate helper is called. Independent
CPU double/float softmax is evaluated on the actual saved native arguments.
"""
import argparse,gc,hashlib,json,os,sys,traceback
from pathlib import Path
P=Path(__file__).resolve().parent
SOURCE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-model-three-node-entry-new24h-v1-131-repair17/SOURCE_BOUND.json',bytes=59418,sha256='1a6a1e1b6be6afa5ca91bd2909bcdc5fe3a821b4968b5cf04f9e2b2752977552')
RAWROOT=Path('/opt/host/vnf/austinov/run-bole-model131repair17-MAIN-NEW24H_001/dense/receipts')
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);a=p.stat();h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b);n+=len(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and n==z.st_size,'stable immutable file')
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact Ref3')
 p=Path(r['path']);need(p.is_absolute()and p.is_file()and all(not x.is_symlink()for x in(p,*p.parents))and ref(p)==r,'ordinary exact evidence bytes');return p
def bits(t,a,b):return a.shape==b.shape and a.dtype==b.dtype and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8))
def metric(t,a,b):
 need(a.shape==b.shape and bool(t.isfinite(a).all()and t.isfinite(b).all()),'finite same-shaped diagnostic operands')
 d=a.double()-b.double();scale=max(float(t.linalg.vector_norm(b.double())),1e-30)
 error=d.abs();bound=.001+.01*b.double().abs()
 return dict(peak_abs=float(error.max()),relative_l2=float(t.linalg.vector_norm(d))/scale,
   old_pointwise_pass=bool((error<=bound).all()),old_pointwise_fail_count=int((error>bound).sum()),elements=a.numel())
def direct(t,q,k,v,dtype,*,bf16_logits=False,bf16_prob=False):
 q=q.to(dtype);k=k.to(dtype);v=v.to(dtype)
 logits=k.mv(q)*(256**-.5)
 if bf16_logits:logits=logits.to(t.bfloat16).to(dtype)
 p=(logits-logits.max()).exp();p/=p.sum()
 if bf16_prob:p=p.to(t.bfloat16).to(dtype)
 return v.T.mv(p)
def matrix(t,q,keys,values,mask,dtype,**policy):
 result=[]
 for node in range(3):
  allow=~mask[node];need(bool(allow.any()),'nonempty independent ancestor domain')
  result.append(t.stack([direct(t,q[node,h],keys[allow],values[allow],dtype,**policy)for h in range(6)]))
 return t.stack(result)
def diagnose(t,raw):
 need(raw['schema']=='bole.actual-three-node-model-capture/v1'and raw['scheduler_committed']is False,'saved bounded actual tree, no committed scheduler claim')
 anchors={v['layer']:v for v in raw['initial_FA_pages']};result=[]
 for layer in range(3,64,4):
  row=raw['tree_context']['captures'][layer];trial=row['trial'];before=trial['native_before'];anchor=anchors[layer]
  q=row['query'].reshape(3,6,256);k=row['key'].reshape(3,1,256);v=row['value'].reshape(3,1,256)
  need(q.dtype==k.dtype==v.dtype==row['output'].dtype==t.bfloat16,'unchanged real D256 BF16 inputs/output')
  pages=list(anchor['physical_pages']);need(len(pages)==2 and len(set(pages))==2,'actual131 prefix page identities')
  pk=t.stack([anchor['key'][p//128,p%128,0]for p in range(131)])
  pv=t.stack([anchor['value'][p//128,p%128,0]for p in range(131)])
  expected_k=t.cat((pk,k[:,0]));expected_v=t.cat((pv,v[:,0]))
  actual_q=before['query'].squeeze(0).permute(1,0,2).contiguous()
  actual_k=before['key'].permute(0,2,1,3).reshape(-1,1,256)[:,0]
  actual_v=before['value'].permute(0,2,1,3).reshape(-1,1,256)[:,0]
  mask=before['atten_mask'][0,0]
  need(mask.dtype==t.bool and mask.shape==(3,actual_k.shape[0]),'actual native complete padded mask')
  expected_mask=t.ones_like(mask);expected_mask[:,:132]=False;expected_mask[1,132]=False;expected_mask[2,133]=False
  joins=dict(q=bits(t,actual_q,q),kv_prefix_and_nodes=bits(t,actual_k[:134],expected_k)and bits(t,actual_v[:134],expected_v),
    full_ancestor_padding_mask=bits(t,mask,expected_mask),
    scratch_to_actual=bits(t,before['key'],trial['scratch_k'].permute(0,2,1,3).contiguous())and bits(t,before['value'],trial['scratch_v'].permute(0,2,1,3).contiguous()),
    block_table=before['block_table'].dtype==t.int32 and before['block_table'].tolist()==[list(range(before['key'].shape[0]))])
  # False joins remain evidence, not silently fixed before computing diagnostics.
  need(all(bool(t.isfinite(x).all())for x in(actual_q,actual_k,actual_v,row['output'])),'all actual native input/output finite')
  refs={}
  for name,dtype,policy in(('double',t.float64,{}),('float',t.float32,{}),
      ('hypothesis_BF16_QK',t.float32,dict(bf16_logits=True)),
      ('hypothesis_BF16_QK_and_probability',t.float32,dict(bf16_logits=True,bf16_prob=True))):
   truth=matrix(t,actual_q,actual_k,actual_v,mask,dtype,**policy)
   refs[name]=dict(whole=metric(t,row['output'],truth),nodes=[metric(t,row['output'][n],truth[n])for n in range(3)],
       heads=[[metric(t,row['output'][n,h],truth[n,h])for h in range(6)]for n in range(3)])
  canonical_mask=expected_mask[:,:134]
  independent=matrix(t,q,expected_k,expected_v,canonical_mask,t.float64)
  native_input_truth=matrix(t,actual_q,actual_k,actual_v,mask,t.float64)
  controls=[]
  for path in raw['native']:
   for step in path['steps']:
    control=step['context']['captures'][layer];node=step['node']
    cq=control['query'].reshape(6,256);ck=control['after_key'].reshape(-1,256);cv=control['after_value'].reshape(-1,256)
    truth=t.stack([direct(t,cq[h],ck,cv,t.float64)for h in range(6)])
    controls.append(dict(path=path['child'],node=node,
       native_AR_against_own_CPU64=metric(t,control['output'].reshape(6,256),truth),
       tree_vs_AR_query=metric(t,q[node],cq),tree_vs_AR_new_key=metric(t,k[node,0],control['key'].reshape(256)),
       tree_vs_AR_new_value=metric(t,v[node,0],control['value'].reshape(256)),
       root_AR_prefix_bits=(bits(t,ck[:-1],pk)and bits(t,cv[:-1],pv))if node==0 else None))
  result.append(dict(layer=layer,input_bit_joins=joins,
      actual_layout=trial.get('native_layout'),saved_native_inputs_vs_canonical_CPU64=metric(t,native_input_truth,independent),
      actual_paged_output_vs_same_input_references=refs,actual_AR_input_and_output_controls=controls))
 return dict(schema='bole.r17.saved-FA-input-attribution/v1',rows=result,qualified=False,
    no_threshold_changed=True,original_owner_pass=False,BOLE_model_ready=False,
    BF16_rounding_variants_are_diagnostic_hypotheses_not_new_gates=True)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--raw-ref');p.add_argument('--rank-receipt-ref');p.add_argument('--rank',type=int);p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false,"qualified":false}');return 0
 need(all((a.source_ref,a.raw_ref,a.rank_receipt_ref,a.output is not None,a.rank is not None)),'complete exact typed diagnostic arguments')
 sr=json.loads(a.source_ref);need(sr==SOURCE,'exact original failed R17 bound source');checked(sr)
 rr=json.loads(a.raw_ref);need(a.rank in range(4)and Path(rr['path'])==RAWROOT/('BOLE-TREE-RANK-%d.pt'%a.rank),'exact actual rank path; never untrusted arbitrary pickle')
 receipt_ref=json.loads(a.rank_receipt_ref)
 need(Path(receipt_ref['path'])==RAWROOT/('BOLE-TREE-RANK-%d.json'%a.rank),'exact actual rank producer receipt')
 receipt=json.loads(checked(receipt_ref).read_bytes())
 need(receipt['source']==sr and receipt['rank']==a.rank and receipt['primary']is None and receipt['raw']==rr,'raw exact hash joins original source-bound completed producer')
 checked(rr);need(rr['bytes']==775440281,'actual complete original captured rank bytes')
 need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not os.environ.get('ASCEND_RT_VISIBLE_DEVICES')and not os.environ.get('ASCEND_VISIBLE_DEVICES')and not list(Path('/dev').glob('davinci*')),'MAIN-admitted Devices[] CPU only')
 need(a.output.is_absolute()and not a.output.exists()and a.output.parent.is_dir()and all(not x.is_symlink()for x in(a.output.parent,*a.output.parent.parents)),'new ordinary non-overwrite output')
 import torch as t
 t.set_num_threads(1);blob=t.load(checked(rr),map_location='cpu',weights_only=False)
 need(blob['schema']=='bole.model-diagnostic-primitives/v1'and blob['logical_tensor_bytes']<=2**30,'original primitive export budget')
 raw=blob['payload'];need(raw['rank']==a.rank and raw['source']==sr,'actual source/rank join')
 report=diagnose(t,raw);report.update(source=sr,raw_ref=rr,rank_receipt=receipt_ref,rank=a.rank,diagnostic_source=ref(__file__),NPU=False)
 data=(json.dumps(report,sort_keys=True,allow_nan=False)+'\n').encode();need(len(data)<=16*2**20,'bounded scalar output, no copied raw')
 with a.output.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 print(json.dumps(ref(a.output)));return 0
if __name__=='__main__':raise SystemExit(main())
