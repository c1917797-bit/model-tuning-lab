"""MAIN-only actual captured-input experiment. No owner/controller or new oracle."""
import argparse,contextlib,hashlib,importlib.util,json,os,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent
CUT=1792002456
def need(v,m):
 if not v:raise ValueError(m)
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and r['bytes']>0,'strict actual Ref3');p=Path(r['path']);need(p.is_absolute()and p.is_file()and not p.is_symlink(),'ordinary exact source/input');b=p.read_bytes();need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'whole pinned bytes');return b
def obj(r):return json.loads(checked(r))
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def load(r,name):
 checked(r);s=importlib.util.spec_from_file_location(name,r['path']);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);need(Path(v.__file__).resolve()==Path(r['path']),'actual source module');return v
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--build-ref');p.add_argument('--input-ref');p.add_argument('--plan-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False,matrix_gate_pass=False)));return 0
 need(os.environ.get('MXR_Y16_EXPERIMENT_ENABLE')=='1'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0'and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and time.time()+210<=CUT,'MAIN singleton currentR118 experiment only')
 sr,br,ir,pr=[json.loads(x)for x in(a.source_ref,a.build_ref,a.input_ref,a.plan_ref)];m=obj(sr);b=obj(br);plan=obj(pr)
 need(m['schema']=='mxr.y16.compensated-source/v1'and m['root']==str(P)and m['default_enabled']is False and m['window']==dict(start=1791916056,cutoff=CUT),'one current frozen025 source')
 need(ir==m['dependencies']['recovery_inputs']and plan['schema']=='mxr.y16.main-single-card-plan/v1'and plan['source']==sr and plan['build']==br and plan['input_ref']==ir and plan['physical']==5 and plan['logical']==0 and plan['output']==str(a.output)and plan['rank_order']==[2,0,1,3],'explicit MAIN one5 plan/all4 order, no inherited partial PASS')
 need(b['schema']=='mxr.y16.compensated-build/v1'and b['source']==sr and b['status']=='compiled_no_device'and b['error']is None,'real unique new build prerequisite')
 B=load(m['files']['build.py'],'_mxr025_actual_source_validator');need(B.source(sr)==m,'actual whole inverse-derived C++ source validation before runtime import')
 refs=[sr,br,ir,pr,*m['files'].values(),*m['dependencies'].values(),b['library'],*b['header_refs_after'].values()]
 for r in refs:checked(r)
 inputs=obj(ir);refs.extend([*inputs['originals'].values(),*inputs['artifact_refs']])
 observation=obj(m['dependencies']['observation22']);need(observation['schema']=='mxr.rank2-real-workspace-observation/v1'and observation['source']==m['dependencies']['source22']and observation['original_failure_bitwise_reproduced']is True and len(observation['repeats'])==3,'actual three old failed workspace observations')
 refs.extend(x['real_FP32_workspace_ref']for x in observation['repeats'])
 for r in refs:checked(r)
 before={r['path']:r['sha256']for r in refs}
 R=load(m['dependencies']['recovery_validator'],'_mxr025_original_capture_validator');O=R.load_consumer(m['dependencies']['original_consumer']);workers=R.validate(inputs,O)
 need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists(),'sole absent new output, no rerun');a.output.mkdir(mode=0o700)
 # Reuse the actual022 CANN bootstrap, without importing author compile.py.
 boot=m['dependencies']['guest_capture_entry'];sys.path.insert(0,str(Path(boot['path']).parent));from guest_capture_entry import installed_cann
 need(ref(sys.modules['guest_capture_entry'].__file__)==boot,'actual bootstrap provenance');cann=installed_cann(Path(m['upstream_root']))
 import torch
 torch.set_num_threads(1)
 import torch_npu
 need(torch.npu.device_count()==1,'actual onlylogical0');torch.npu.set_device(0);canary=torch.tensor([1.,2.],device='npu:0');need((canary+3).cpu().tolist()==[4.,5.],'actual singleton canary');torch.npu.synchronize()
 with(a.output.parent/'DEVICE.json').open('x',encoding='utf8')as h:json.dump(dict(schema='mxr.actual-single-replay-process/v1',pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),logical_device=torch.npu.current_device(),visible_devices=os.environ['ASCEND_RT_VISIBLE_DEVICES'],plan_sha256=pr['sha256'],canary=[4.,5.],actual_cann=cann),h)
 end=time.monotonic()+30;begin=a.output.parent/'BEGIN.json'
 while not begin.exists():
  need(time.monotonic()<end and time.time()+90<CUT,'bounded actual owner handshake, no lease reset');time.sleep(.2)
 need(obj(ref(begin))==dict(schema='mxr.actual-owned-replay-arm/v1',pid=os.getpid(),plan_sha256=pr['sha256'],physical=5),'exact MAIN PID/card5 authorization; not self-issued')
 A=load(m['files']['adapter.py'],'_mxr025_adapter');original,control,candidate=A.instances(torch,sr,br,torch.device('npu:0'));results=[];raw_outputs=[];prerequisites=[];primary=None;secondary=[];after={};mapped=[];original_rank2_reproduced=False
 def equal(x,y):return x.dtype==y.dtype and x.shape==y.shape and torch.equal(x.contiguous().view(torch.uint8),y.contiguous().view(torch.uint8))
 try:
  for worker in workers:
   out=a.output/('native-prerequisite-rank-%d'%worker['rank']);log=a.output/('native-prerequisite-rank-%d.stdout'%worker['rank'])
   with log.open('x',encoding='utf8')as h,contextlib.redirect_stdout(h):code=O.consume(Path(worker['worker_root']),out,R.RUN,1)
   prerequisites.append(dict(rank=worker['rank'],stdout=ref(log),result=ref(out/'RESULT.json'),exit_code=code));need(code==0,'actual original native FP64 prerequisite, no candidate math')
  by_rank={w['rank']:w for w in workers};need(set(by_rank)=={0,1,2,3},'four disjoint actual original ranks')
  for rank in plan['rank_order']:
   w=by_rank[rank];root=Path(w['worker_root']);raw=torch.load(root/'case-000/RAW.pt',map_location='cpu',weights_only=True)
   rawref={k:next(x for x in inputs['frame_refs']if x['path']==str(root/'case-000/RAW.pt'))[k]for k in('path','bytes','sha256')};checked(rawref)
   actual_A,cu=raw['A'],raw['cu_seqlens'];need(list(actual_A.shape)==[1,129,12,64]and cu.tolist()==[0,129],'exact captured129, not new synthetic/model input')
   E0,_=O.fp64_reference(torch,actual_A,cu.tolist());converted=actual_A.half();need(bool(torch.isfinite(converted).all()),'original full input FP16 finite')
   half=converted.to('npu:0');cu32=cu.to(device='npu:0',dtype=torch.int32);arena=torch.full((actual_A.numel()+128,),65521.,device='npu:0',dtype=torch.float32);workspace=arena[64:-64].view(actual_A.shape);chunks=sum((e-s+63)//64 for s,e in zip(cu.tolist(),cu.tolist()[1:]));minus_before=original.minus_identity.cpu();pointers=(half.data_ptr(),cu32.data_ptr(),arena.data_ptr(),workspace.data_ptr(),original.minus_identity.data_ptr())
   rankroot=a.output/('rank-%d'%rank);rankroot.mkdir();paths={};rows={}
   for mode,adapter in(('original',original),('control',control),('compensated',candidate)):
    output_rows=[];tensors=[]
    for repeat in range(3):
     workspace.zero_();adapter.launch(half,cu32,chunks,workspace);torch.npu.synchronize()
     real=workspace.detach().cpu().clone();actual=workspace.to(raw['original_output'].dtype).cpu();half_after=half.cpu();cu_after=cu32.cpu();minus_after=original.minus_identity.cpu();lo=arena[:64].cpu();hi=arena[-64:].cpu()
     rawpath=rankroot/('%s-repeat-%d.pt'%(mode,repeat))
     # ALWAYS publish complete actual tensors before metric/guard/bitwise rejection.
     with rawpath.open('xb')as h:torch.save(dict(mode=mode,repeat=repeat,workspace=real,actual=actual,half_after=half_after,cu_after=cu_after,minus_identity_after=minus_after,guard_lo=lo,guard_hi=hi,pointers_before=pointers,pointers_after=(half.data_ptr(),cu32.data_ptr(),arena.data_ptr(),workspace.data_ptr(),original.minus_identity.data_ptr())),h)
     rr=ref(rawpath);raw_outputs.append(dict(rank=rank,mode=mode,repeat=repeat,raw=rr));paths.setdefault(mode,[]).append(rr);tensors.append((real,actual))
     finite=bool(torch.isfinite(real).all())and bool(torch.isfinite(actual).all());metric=O.metrics(torch,actual,E0)if finite else dict(finite=False,pass_=False);guard=bool(torch.all(lo==65521.)and torch.all(hi==65521.));unchanged=equal(half_after,converted)and equal(cu_after,cu.int())and equal(minus_after,minus_before);ptr=pointers==(half.data_ptr(),cu32.data_ptr(),arena.data_ptr(),workspace.data_ptr(),original.minus_identity.data_ptr())
     output_rows.append(dict(repeat=repeat,raw=rr,metric=metric,guards=guard,input_unchanged=unchanged,pointers_stable=ptr));need(guard and unchanged and ptr and finite,'full actual buffers/inputs/pointers/finite')
     if mode=='control':need(equal(real,rows['original']['tensors'][repeat][0])and equal(actual,rows['original']['tensors'][repeat][1]),'disabled new namespace whole FP32/BF16 must bitwise olddeployed')
     if mode=='original'and rank==2:
      oldw=torch.load(observation['repeats'][repeat]['real_FP32_workspace_ref']['path'],map_location='cpu',weights_only=True)['real_FP32_workspace'];need(equal(real,oldw),'whole original rank2 real workspace failure reproduction')
    need(all(equal(tensors[0][0],x[0])and equal(tensors[0][1],x[1])for x in tensors[1:]),'all3 FP32/BF16 repeats deterministic')
    rows[mode]=dict(tensors=tensors,reported=output_rows)
    if mode=='original'and rank==2:need(all(not x['metric']['pass']for x in output_rows),'original rank2 failed gate remains failed');original_rank2_reproduced=True
   passed=all(x['metric']['pass']for x in rows['compensated']['reported']);results.append(dict(rank=rank,input_ref=rawref,paths={k:v['reported']for k,v in rows.items()},control_whole_bitwise_old=True,candidate_gate_pass=passed));need(passed,'candidate original fullE0/.002 gate failed; no unchanged rerun or relaxedgold')
 except BaseException as e:primary=e
 finally:
  try:
   for r in refs:checked(r);after[r['path']]=ref(r['path'])['sha256']
   maps=Path('/proc/self/maps').read_text();mapped=[path for path in(m['dependencies']['old_binary']['path'],b['library']['path'])if any(line.split()and line.split()[-1]==path for line in maps.splitlines())];need(len(mapped)==2,'actually mapped old/new libraries')
  except BaseException as e:
   if primary is None:primary=e
   else:secondary.append(repr(e))
  ok=primary is None and before==after and [x['rank']for x in results]==[2,0,1,3]
  value=dict(schema='mxr.y16.actual-captured-frame-gate/v1',source=sr,build_ref=br,input_ref=ir,plan_ref=pr,actual_entry_argv=[sys.executable,'-I','-B',*sys.argv],rank_results=results,raw_outputs=raw_outputs,native_prerequisites=prerequisites,primary=repr(primary)if primary else None,secondary=secondary,original_rank2_failure_retained=True,original_rank2_failure_bitwise_reproduced=original_rank2_reproduced,control_source_inverse_exact=True,actual_mapped_library_paths=mapped,source_hashes_before=before,source_hashes_after=after,matrix_gate_pass=ok,physical_ownership_proved_by_this_child=False,NPU=True,full_gdn_state_qualified=False,graph_qualified=False,model_ready=False,performance_ready=False,task_ready=False)
  path=a.output/'RESULT.json'
  with path.open('x',encoding='utf8')as h:json.dump(value,h,sort_keys=True,allow_nan=False);h.write('\n')
  print('MAIN_MXR_Y16_NUMERIC '+json.dumps(ref(path)),flush=True)
 if primary:raise primary
 return 0
if __name__=='__main__':raise SystemExit(main())
