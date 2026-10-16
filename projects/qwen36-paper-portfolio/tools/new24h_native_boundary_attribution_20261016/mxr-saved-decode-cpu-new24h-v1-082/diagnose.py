"""Retained actual native decode vs independent CPU64/RNE; no qualification."""
import argparse,hashlib,importlib.util,json,math,os,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
SOURCE={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-2k-memory32-model-new24h-v1-073-repair6/SOURCE_MANIFEST.json','bytes':111072,'sha256':'8d0608cd3fe3814359fc8141a39afe4b14baa77290d20fd8e57e73bcab4799ab'}
REPORT={'path':'/opt/host/vnf/austinov/run-mxr-2k-memory32-model073repair6-main-NEW24H_MXR073R6_001/cpu-consumer/rank-0/BRIDGE_RESULT.json','bytes':551214,'sha256':'05e92014d4576e16f37c0d1f3016c4885816cbe5e4cf9c0c7859604714714126'}
WORKER='/opt/host/vnf/austinov/run-mxr-2k-memory32-model073repair6-main-NEW24H_MXR073R6_001/candidate/model/capture/worker-425'
ORIGINAL={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-r118-capture-20261013-001/consume_capture.py','bytes':10097,'sha256':'7c31e87b409ef095e5789a2bc1b71a987a69dc237789c125ad749a69fecec6c3'}
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
 p=Path(r['path']);need(set(r)=={'path','bytes','sha256'}and p.is_absolute()and all(not q.is_symlink()for q in(p,*p.parents))and ref(p)==r,'exact immutable Ref3');return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,name):
 s=importlib.util.spec_from_file_location(name,checked(r));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def select(report):
 need(report['capture_source']==SOURCE and report['worker_root']==WORKER,'exact actual rank0 source/worker')
 rows=report['decode_rows'];prefixes=report['layer_prefixes'];keys=[(r['prefix'],r['prefill_tokens'],r['step'])for r in rows]
 need(len(prefixes)==len(set(prefixes))==48 and len(rows)==len(set(keys))==432 and set(keys)=={(p,2048,s)for p in prefixes for s in range(9)},'complete actual432 coverage')
 selected=[r for r in rows if r['pass_gate']is False];need(len(selected)==34,'actual fixed34 failed decode rows')
 need(all(type(r['pass_gate'])is bool for r in rows),'no truthy substitute')
 return selected
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('disabled');return 0
 need(sys.platform=='linux'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not list(Path('/dev').glob('davinci*')),'real Devices[] only')
 need(time.time()+1000<1792220533 and a.output.parent.is_dir()and not a.output.exists(),'bounded new exclusive output')
 m=obj(SOURCE);report=obj(REPORT);selected=select(report)
 import torch as t
 t.set_num_threads(1);import direct_round as D
 controls=D.controls(t);R=load(m['files']['independent_block_reference.py'],'_independent082block');codec=load(m['files']['lossless_raw.py'],'_retained082codec');O=load(ORIGINAL,'_original082metrics')
 rows=[];primary=None;start=time.monotonic()
 try:
  for row in selected:
   need(time.monotonic()-start<600,'child600s');rr=row['raw'];need(Path(rr['path']).parent==Path(WORKER)/'raw','exact worker raw leaf');checked(rr);d=codec.read(t,rr['path']);lens=d['actual_seq_lengths'].tolist();need(lens==[0,1],'same actualB1 metadata')
   need(d['output'].dtype==t.bfloat16 and d['final_state'].dtype==d['initial_state'].dtype==t.float32,'actual output/state dtypes')
   x={n:d[k].unsqueeze(0)for n,k in(('q','query'),('k','key'),('v','value'),('g','g'),('beta','beta'))};x.update(scale=d['scale'],cu_seqlens=t.tensor([0,1]),initial_state=d['initial_state'].transpose(-1,-2).contiguous(),already_normalized=True)
   truth,state=R.recurrence(t,x);actual=d['output'].unsqueeze(0);rounded=D.round_bf16(t,truth);via32=truth.float().bfloat16();uncast=O.metrics(t,actual,truth)
   need(bool(t.isfinite(actual).all()and t.isfinite(truth).all()and t.isfinite(rounded).all()),'finite measured decode')
   rawbits=lambda v:v.contiguous().view(t.int16)
   rows.append(dict(prefix=row['prefix'],step=row['step'],raw=rr,original_output=row['output'],original_state=row['state'],recomputed_uncast_output=uncast,actual_vs_direct_RNE=O.metrics(t,actual,rounded.double()),BF16_rounding_floor=O.metrics(t,rounded,truth),FP32_double_round_vs_direct_RNE=O.metrics(t,via32,rounded.double()),FP32_double_round_cells=int((rawbits(via32)!=rawbits(rounded)).sum()),actual_equals_direct_RNE_cells=int((rawbits(actual)==rawbits(rounded)).sum()),total_cells=actual.numel(),state_vs_CPU64=O.metrics(t,d['final_state'].transpose(-1,-2).contiguous(),state)))
 except BaseException as e:primary=repr(e)
 result=dict(schema='mxr.actual-native-decode-RNE-diagnosis/v082',source=SOURCE,report=REPORT,worker_root=WORKER,coverage_count=432,selected_failed_count=34,rows=rows,controls=controls,primary=primary,reference='same original independent CPU64 recurrence followed by independent integer binary64 BF16 RNE; no new numeric acceptance gate',old_FAIL_unchanged=True,qualification=False,NPU_reexecuted=False)
 with a.output.open('x',encoding='utf8',newline='\n')as f:json.dump(result,f,sort_keys=True,allow_nan=False);f.write('\n')
 return 0 if primary is None else 2
if __name__=='__main__':raise SystemExit(main())
