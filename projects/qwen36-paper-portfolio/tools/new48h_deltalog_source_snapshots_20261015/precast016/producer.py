"""Actual eager kernels with request lifecycle; explicit owned ARM required."""
import argparse,hashlib,json,math,os,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import io_contract as C
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for k in('source-ref','authority-ref','meta-ref','numeric-ref','plan-ref','output'):p.add_argument('--'+k,required=True)
 a=p.parse_args();sr,ar,mr,nr,pr=[json.loads(getattr(a,k))for k in('source_ref','authority_ref','meta_ref','numeric_ref','plan_ref')];m=C.source(sr);ad=C.admissions(m,ar,mr,nr);plan=C.obj(pr)
 C.need(plan['source']==sr and plan['physical']==5 and plan['logical']==0 and plan['admissions']==ad and plan['graph']is False,'exact new ownedplan eager/physical5')
 out=Path(a.output);C.need(out.is_absolute()and out.parent.is_dir()and not out.exists(),'new output');out.mkdir();(out/'blobs').mkdir();start=time.monotonic();rows=[];primary=None
 import torch,torch_npu
 from vllm_ascend.utils import enable_custom_op
 from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
 import vllm_ascend.ops.gdn as gdn
 C.need(C.ref(gdn.__file__)['sha256']=='d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816'and enable_custom_op(),'actual native source/ops')
 torch.set_num_threads(1);torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0);init_device_properties_triton()
 h=C.load(m['probe_ref'],'actual_frozen_probe');R=C.load(m['files']['oracle.py'],'independent_request_oracle');S=C.load(m['files']['scenarios.py'],'frozen_scenarios')
 canary=(torch.tensor([1.,2.],device='npu:0')+3).cpu().tolist();C.need(torch.npu.device_count()==1 and canary==[4.,5.]and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0','singleton actual canary')
 C.write(out/'DEVICE.json',dict(pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),logical=0,visible='0',physical=5,plan=pr,canary=canary))
 end=time.monotonic()+30
 while not(out/'MAIN_ARM.json').exists():C.need(time.monotonic()<end,'bounded real ownership ARM');time.sleep(.2)
 C.need(C.obj(C.ref(out/'MAIN_ARM.json'))==dict(schema='deltalog.lifecycle-owned-arm/v007',pid=os.getpid(),plan_sha256=pr['sha256'],physical=5),'source/physical ARM')
 ops={};maps=[]
 for arm,r in m['libraries'].items():
  torch.ops.load_library(r['path']);name='qwen36_deltalog_'+arm;ops[arm]=getattr(torch.ops,name).decode
  C.need(torch._C._dispatch_has_kernel_for_dispatch_key(name+'::decode','PrivateUse1'),'loaded native registration')
  C.need(any(r['path']in line for line in Path('/proc/self/maps').read_text().splitlines()),'actual mapped library');maps.append(dict(arm=arm,library=r,schema=str(ops[arm].default._schema)))
 debuglib=m['debug_library'];torch.ops.load_library(debuglib['path']);debugop=torch.ops.qwen36_deltalog_readout_sidecar_v015.decode
 C.need(torch._C._dispatch_has_kernel_for_dispatch_key('qwen36_deltalog_readout_sidecar_v015::decode','PrivateUse1')and any(debuglib['path']in x for x in Path('/proc/self/maps').read_text().splitlines()),'actual debug mapping/registration');maps.append(dict(arm='debug',library=debuglib,schema=str(debugop.default._schema)))
 from precast import evaluate,pair,regression_run
 stored_bytes=0
 def account(path):
  nonlocal stored_bytes
  stored_bytes+=path.stat().st_size;C.need(stored_bytes<=m['resources']['raw_disk_cap_bytes'],'actual accumulated raw disk cap')
 def tensor_blob(t):
  t=t.detach().cpu().contiguous();digest=hashlib.sha256(str(t.dtype).encode()+str(list(t.shape)).encode()+t.view(torch.uint8).numpy().tobytes()).hexdigest();path=out/'blobs'/(digest+'.pt')
  if not path.exists():
   C.need(stored_bytes+t.numel()*t.element_size()+2097152<=m['resources']['raw_disk_cap_bytes'],'pre-write raw disk reserve')
   with path.open('xb')as f:torch.save(t,f)
   account(path)
  return C.ref(path)
 def snapshot(st):return {k:tensor_blob(v)for k,v in st.items()}
 def save_raw(path,value):
  def size(v):
   if isinstance(v,torch.Tensor):return v.numel()*v.element_size()
   if isinstance(v,dict):return sum(size(x)for x in v.values())
   if isinstance(v,(list,tuple)):return sum(size(x)for x in v)
   return 0
  C.need(stored_bytes+size(value)+2097152<=m['resources']['raw_disk_cap_bytes'],'pre-write raw disk reserve')
  with path.open('xb')as f:torch.save(value,f)
  account(path)
  return C.ref(path)
 try:
  for phase,batch,steps in(('smoke',16,4),('full',1,160),('full',16,160)):
   case_start=time.monotonic()
   scenario=S.plan(batch);gen=torch.Generator().manual_seed(2610151601+batch+(10000 if phase=='full'else 0));initial=(torch.randn((scenario['slots'],12,128,128),generator=gen)*.005).float();native=initial.npu();states={arm:h.allocate_state(initial)for arm in ops};ledger={f'initial-{s}':initial[s].double().clone()for s in range(batch)};activearms={arm:True for arm in ops}
   debugstate=h.allocate_state(initial);debugptr={k:t.data_ptr()for k,t in debugstate.items()}
   for st in [*states.values(),debugstate]:
    for t in st.values():t[-2:].fill_(13)
   pointers={arm:{k:t.data_ptr()for k,t in st.items()}for arm,st in states.items()};initial_ref=save_raw(out/('%s-B%d-initial.pt'%(phase,batch)),initial);C.write(out/('%s-B%d-plan.json'%(phase,batch)),scenario)
   for e in scenario['events'][:steps]:
    C.need(time.monotonic()-start<1800 and time.monotonic()-case_start<(600 if batch==1 else 1200)and time.time()<1792135097-690,'per-case/child/cutoff budget');joins={}
    for action in e['actions']:
     if action['op']=='retire':ledger.pop(action['request']);continue
     s=action['slot'];v=(torch.randn((12,128,128),generator=gen)*.005).float()if action['initial']=='nonzero'else torch.zeros((12,128,128));joins[s]=v;ledger[action['request']]=v.double().clone();native[s].copy_(v.npu())
     for arm,st in [*states.items(),('debug',debugstate)]:
      if activearms.get(arm,True):
       st['base'][s].copy_(v.npu())
       for k in('k_log','u_log','lambda_log','decay','length'):st[k][s].zero_()
    ids=e['ids'];inputs=None;nativeout=None;seq=None;expected=[];native_seq=None
    if ids:
     inp=h.make_inputs(len(ids),scenario['slots'],e['step'],gen);inp['indices']=torch.tensor(ids,dtype=torch.int32,device='npu:0');inputs={k:t.cpu()for k,t in inp.items()};seq=torch.arange(len(ids)+1,dtype=torch.int32,device='npu:0');native_seq=torch.cat((torch.zeros(1,dtype=torch.int32),torch.ones(len(ids),dtype=torch.int32))).npu();nativeout=h.native_step(native,inp,native_seq);torch.npu.synchronize()
     for row,request in enumerate(e['requests']):ledger[request],o=R.advance(torch,ledger[request],inputs,row);expected.append(o)
    for arm,st in states.items():
     if not activearms[arm]:continue
     before={k:t.cpu()for k,t in st.items()};before_refs=snapshot(before);debug_before={k:t.cpu()for k,t in debugstate.items()};actual=None;debugout=None;side=None
     if ids:actual=ops[arm](inp['query'],inp['key'],inp['value'],inp['g'],inp['beta'],st['base'],st['k_log'],st['u_log'],st['lambda_log'],st['decay'],st['length'],seq,inp['indices']);torch.npu.synchronize()
     if ids:
      side_back=torch.full((len(ids)*1536+256,),13.,dtype=torch.float32,device='npu:0');side=side_back[128:-128].view(len(ids),12,128);side.fill_(float('nan'));debugout=debugop(inp['query'],inp['key'],inp['value'],inp['g'],inp['beta'],debugstate['base'],debugstate['k_log'],debugstate['u_log'],debugstate['lambda_log'],debugstate['decay'],debugstate['length'],seq,inp['indices'],side);torch.npu.synchronize()
     debug_after={k:t.cpu()for k,t in debugstate.items()}
     after={k:t.cpu()for k,t in st.items()};inv=R.invariant(torch,before,after,ids);pointer_ok=pointers[arm]=={k:t.data_ptr()for k,t in st.items()};guard_ok=all(torch.equal(after[k][-2:],torch.full_like(after[k][-2:],13))for k in after);input_ok=not ids or all(torch.equal(inp[k].cpu(),v)for k,v in inputs.items());state_rel=0.;output_error=0.;finite=True
     for row,(s,request)in enumerate(zip(ids,e['requests'])):
      value=R.restore(torch,after,s);state_rel=max(state_rel,float((value-ledger[request]).norm()/ledger[request].norm().clamp_min(1e-30)));finite &=bool(torch.isfinite(value).all())
     peer_native=None;readout_diagnostic=None
     if ids:
      from direct_round import peer_error
      peer_native=float((actual.cpu().float()-nativeout.cpu().float()).abs().max())/max(float(nativeout.cpu().float().abs().max()),1e-30)
      old_point_error,old_point_diagnostic=peer_error(torch,actual.cpu(),torch.stack(expected));readout_diagnostic=evaluate(torch,side.cpu(),actual.cpu(),torch.stack(expected));readout_diagnostic['old_BF16_point_error']=old_point_error;readout_diagnostic['old_BF16_point_diagnostic']=old_point_diagnostic;output_error=readout_diagnostic['peak'] if readout_diagnostic['peak']is not None else float('inf');finite &=bool(torch.isfinite(actual).all().cpu())and bool(torch.isfinite(nativeout).all().cpu())
     native_rel=None
     if e['checkpoint'] and ids:
      native_cpu=native.cpu();native_rel=max(float((native_cpu[s].double()-ledger[request]).norm()/ledger[request].norm().clamp_min(1e-30))for s,request in zip(ids,e['requests']))
     side_guards=not ids or bool((side_back[:128]==13).all().cpu())and bool((side_back[-128:]==13).all().cpu())
     pair_ok=all(torch.equal(before[k].view(torch.uint8),debug_before[k].view(torch.uint8))and torch.equal(after[k].view(torch.uint8),debug_after[k].view(torch.uint8))for k in before)if not ids else pair(torch,before,debug_before,after,debug_after,actual.cpu(),debugout.cpu(),inputs,{k:t.cpu()for k,t in inp.items()})
     debug_pointer_ok=debugptr=={k:t.data_ptr()for k,t in debugstate.items()}
     passed=debug_pointer_ok and side_guards and pair_ok and(not ids or readout_diagnostic['passed'])and(native_rel is None or native_rel<=R.STATE_LIMIT) and finite and state_rel<=R.STATE_LIMIT and output_error<=R.OUTPUT_LIMIT and all(inv.values())and pointer_ok and guard_ok and input_ok
     raw=save_raw(out/('%s-%s-B%d-%03d.pt'%(phase,arm,batch,e['step'])),dict(debug_pointers_before=debugptr,debug_pointers_after={k:t.data_ptr()for k,t in debugstate.items()},sidecar_redzones=None if not ids else side_back.cpu(),sidecar_guards=side_guards,debug_before=snapshot(debug_before),debug_after=snapshot(debug_after),debug_output=None if debugout is None else debugout.cpu(),actual_precast_FP32=None if side is None else side.cpu(),event=e,initial=initial_ref,joins=joins,inputs=inputs,inputs_after=None if not ids else {k:t.cpu()for k,t in inp.items()},sequence=None if seq is None else seq.cpu(),native_sequence=None if native_seq is None else native_seq.cpu(),before=before_refs,after=snapshot(after),candidate_output=None if actual is None else actual.cpu(),native_output=None if nativeout is None else nativeout.cpu(),native_state=None if not(e['checkpoint']or not passed)else native.cpu(),pointers_before=pointers[arm],pointers_after={k:t.data_ptr()for k,t in st.items()}))
     rows.append(dict(production_debug_bitwise=pair_ok,phase=phase,batch=batch,arm=arm,step=e['step'],raw=raw,state_relative_l2=state_rel if math.isfinite(state_rel)else None,output_error=output_error if math.isfinite(output_error)else None,peer_native_output_error=peer_native,readout_diagnostic=readout_diagnostic,finite=finite,native_CPU64_checkpoint_relative_l2=native_rel,invariants=inv,pointers_stable=pointer_ok,guards=guard_ok,inputs_unchanged=input_ok,passed=passed));activearms[arm]=passed
    if not activearms['key_projection']:raise ValueError('first lifecycle candidate failure; raw saved')
  regression=regression_run(torch,C,m,ops['key_projection'],debugop,lambda value:save_raw(out/'original137-regression.pt',value),snapshot,R,S)
  C.need(regression['passed'],'original137 actual replay/new empirical contract')
 except BaseException as exc:primary=repr(exc)
 finally:C.write(out/'RESULT.json',dict(schema='deltalog.actual-lifecycle-kernel/v007',source=sr,admissions=ad,plan=pr,rows=rows,regression=locals().get('regression'),primary=primary,mapped=maps,raw_stored_bytes=stored_bytes,NPU=True,graph_qualified=False,actual_runtime_copy_qualified=False,model_ready=False,elapsed_seconds=time.monotonic()-start))
 return 3 if primary else 0
if __name__=='__main__':raise SystemExit(main())
