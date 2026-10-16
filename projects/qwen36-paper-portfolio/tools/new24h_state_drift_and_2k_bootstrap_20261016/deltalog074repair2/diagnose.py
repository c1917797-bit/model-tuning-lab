"""Retained raw only. No backend import, qualification, or changed threshold."""
import argparse, hashlib, importlib.util, json, math, sys, time
from pathlib import Path

def checked(r):
 p=Path(r['path']);h=hashlib.sha256();n=0
 if set(r)!={'path','bytes','sha256'} or not p.is_absolute() or p.is_symlink():raise ValueError('Ref3')
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 if (n,h.hexdigest())!=(r['bytes'],r['sha256']):raise ValueError('immutable bytes')
 return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,name):
 s=importlib.util.spec_from_file_location(name,checked(r));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def metric(t,a,b):
 a,b=a.double(),b.double()
 if not bool(t.isfinite(a).all() and t.isfinite(b).all()):return {'finite':False,'relative_l2':None,'peak':None}
 return dict(finite=True,relative_l2=float((a-b).norm()/max(float(b.norm()),1e-30)),peak=float((a-b).abs().max()/max(float(b.abs().max()),1e-30)))
def main():
 if '--execute' not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for k in ('source-ref','producer-ref','output'):p.add_argument('--'+k,required=True)
 a=p.parse_args();sr,pr=json.loads(a.source_ref),json.loads(a.producer_ref);m,r=obj(sr),obj(pr)
 if r['source']!=sr:raise ValueError('source producer join')
 out=Path(a.output)
 if out.exists() or not out.parent.is_dir():raise ValueError('exclusive new output')
 import torch as t
 t.set_num_threads(1)
 R=load(m['files']['oracle.py'],'independent074_oracle');RC=load(m['files']['raw_codec.py'],'retained074_codec');RC.install(t)
 L=load(m['files']['consume.py'],'independent074_prefill')
 def raw(ref):return t.load(checked(ref),map_location='cpu',weights_only=False)
 rows=[];missing=[];primary=None;ledger=None;prev=None;anchor_ref=None;start=time.monotonic()
 try:
  records=[v for v in r['records'] if v['kind']=='mixed' and v['batch']==1]
  if [v['step'] for v in records]!=list(range(91)):raise ValueError('exact actual B1 steps0..90 required')
  for rec in records:
   if time.monotonic()-start>600:raise ValueError('CPU600s')
   x=raw(rec['raw']);ar=x['initial_anchor_ref']
   if anchor_ref is None:
    anchor_ref=ar;an=raw(ar)
    if an['batch']!=1 or an['before_any_candidate_dispatch'] is not True:raise ValueError('independent initial anchor')
    ledger=an['generated_base'].double().clone()
    if not t.equal(an['native_initial'],an['generated_base']):raise ValueError('native initial differs')
   if ar!=anchor_ref:raise ValueError('anchor changed')
   cap=x['captures']['decode'][0];i=cap['inputs'];slots=i['ssm_state_indices'].tolist();ids=x['ids'].tolist();native=x.get('native_state')
   if native is None:raise ValueError('missing native full state')
   side=raw(cap['actual_sidecar043']);ds=[]
   for j,s in enumerate(slots):
    cb=R.restore(t,cap['before'],s);ca=R.restore(t,x['state'],s)
    conditioned,co=R.advance(t,cb,i,j);independent,io=R.advance(t,ledger[s],i,j)
    native_before=None if prev is None else prev[s].double()
    local_native=None
    if native_before is not None:
     ns,no=R.advance(t,native_before,i,j);local_native=dict(state=metric(t,native[s],ns),output=metric(t,x['native_output'][j],no))
    ds.append(dict(slot=s,candidate_vs_native=metric(t,ca,native[s]),candidate_vs_conditioned_CPU64=metric(t,ca,conditioned),candidate_vs_cumulative_CPU64=metric(t,ca,independent),native_vs_cumulative_CPU64=metric(t,native[s],independent),native_vs_own_previous_CPU64=local_native,precast_vs_conditioned_CPU64=metric(t,side['actual_precast_FP32'][j],co),precast_vs_cumulative_CPU64=metric(t,side['actual_precast_FP32'][j],io),candidate_before_vs_cumulative_CPU64=metric(t,cb,ledger[s])))
    ledger[s]=independent
   pf=x['prefill_slot'];pc=x['captures']['prefill'][0];pi=pc['inputs'];q,k=L.normalized(t,pi['q']),L.normalized(t,pi['k'])
   st=ledger[pf].clone() if x['prefill_has_initial_state'] else t.zeros_like(ledger[pf]);boundary=metric(t,pi['initial_state'][0].transpose(-1,-2),st)
   for token in range(64):
    inp={n:v for n,v in zip(('query','key','value','g','beta'),(q[0,token:token+1],k[0,token:token+1],pi['v'][0,token:token+1],pi['g'][0,token:token+1],pi['beta'][0,token:token+1]))};st,_=R.advance(t,st,inp,0)
   ledger[pf]=st
   restored=t.stack([R.restore(t,x['state'],s) for s in ids]);expected=ledger[ids]
   rows.append(dict(step=rec['step'],raw=rec['raw'],sidecar=cap['actual_sidecar043'],producer_state_error=rec['producer_state_error'],candidate_vs_native=metric(t,restored,native[ids]),candidate_vs_cumulative_CPU64=metric(t,restored,expected),native_vs_cumulative_CPU64=metric(t,native[ids],expected),prefill_initial_vs_independent_ledger=boundary,prefill_candidate_vs_native=metric(t,R.restore(t,x['state'],pf),native[pf]),prefill_candidate_vs_CPU64=metric(t,R.restore(t,x['state'],pf),st),prefill_native_vs_CPU64=metric(t,native[pf],st),decode=ds,conv_peer_bitwise=t.equal(x['state']['conv'],x['native_conv']),inputs_bitwise=all(t.equal(v,x['original_inputs'][n])for n,v in x['inputs'].items()),sidecar_production_debug_bitwise=side['production_debug_bitwise']))
   prev=native.clone()
 except Exception as e:primary=repr(e)
 result=dict(schema='deltalog.retained-state-drift-diagnosis/v074',source=sr,producer=pr,rows=rows,primary=primary,missing=missing,scope='diagnostic only; cumulative ledger uses saved candidate post-convolution operands, original CPU32 normalization boundary and independent CPU64 recurrence; not exact-real normalization nor proof of native transformed operands',native_first_decode_local_missing='initial native state available via anchor but own-previous local metric intentionally null at step0',old_gate_unchanged=True,qualification=False,NPU_reexecuted=False,elapsed=time.monotonic()-start)
 with out.open('x',encoding='utf8',newline='\n')as f:json.dump(result,f,sort_keys=True,allow_nan=False)
 return 0 if primary is None else 2
if __name__=='__main__':raise SystemExit(main())
