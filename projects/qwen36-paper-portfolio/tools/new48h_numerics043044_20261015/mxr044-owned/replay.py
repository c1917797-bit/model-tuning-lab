"""Actual original bootstrap/DEVICE->SMI->ARM then immutable044 callback."""
import argparse,importlib,json,os,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common as C
def main():
 p=argparse.ArgumentParser(allow_abbrev=False)
 for key in('source-ref','selection-ref','plan-ref','output'):p.add_argument('--'+key)
 p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 child_deadline=time.monotonic()+900
 sr,selr,pr=map(json.loads,(a.source_ref,a.selection_ref,a.plan_ref));m=C.source(sr);component=C.obj(m['component044_source']);old=C.obj(m['owned042_source']);plan=C.obj(pr);out=Path(a.output)
 C.need(os.environ.get('MXR_BLOCK_REFINEMENT044_ENABLE')=='1'and os.environ.get('MXR_ORIGINAL_A32_RESIDUAL027_ENABLE')=='1'and os.environ.get('MXR_Y16_EXPERIMENT_ENABLE')=='1'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0'and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','explicit same owned physical environment')
 C.need(plan==dict(schema='mxr.saved-frame-replay-plan/v044',source=m['component044_source'],physical=4,logical=0,output=str(out/'cases')),'literal044 callback plan')
 C.need(out.parent.is_dir()and not out.exists(),'new numeric leaf');out.mkdir()
 early=C.load(old['reused']['early_vendor.py'],'_owned044_early');C.write(out/'EARLY_VENDOR.json',early.before_device())
 import torch,torch_npu
 torch.set_num_threads(1);C.need(torch.npu.device_count()==1,'actual singleton');torch.npu.set_device(0)
 C.need((torch.tensor([1.,2.],device='npu:0')+3).cpu().tolist()==[4.,5.],'real owned canary');torch.npu.synchronize()
 C.write(out.parent/'DEVICE.json',dict(schema='mxr.actual-single-replay-process/v1',pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),logical_device=0,visible_devices='0',plan_sha256=pr['sha256'],canary=[4.,5.]))
 limit=time.monotonic()+30
 while not(out.parent/'BEGIN.json').exists():C.need(time.monotonic()<limit,'MAIN fresh physical4 ARM30');time.sleep(.2)
 arm=C.ref(out.parent/'BEGIN.json');C.need(C.obj(arm)==dict(schema='mxr.actual-owned-replay-arm/v1',pid=os.getpid(),plan_sha256=pr['sha256'],physical=4),'actual MAIN ARM')
 boot=C.load(old['reused']['native_bootstrap.py'],'_owned044_boot');value=boot.actual();C.write(out/'NATIVE_IMPORT.json',value);C.need(value['import_pass'],'actual native import/properties')
 u=importlib.import_module('vllm_ascend.utils');C.need(u.enable_custom_op()is True,'real native ops');C.write(out/'VENDOR_ENABLE.json',early.after_enable(u))
 selection=C.obj(selr);capture=C.obj(selection['capture_source']);R=C.load(capture['files']['prerequisite.py'],'_owned044_prereq');passed=R.gate(old['prerequisite_ref']);kernel=C.obj(passed['source']);adapter=C.load(kernel['files']['adapter.py'],'_owned044_adapter');_,_,solver=adapter.instances(torch,passed['source'],passed['build'],torch.device('npu:0'))
 L=C.load(component['files']['lifetime.py'],'_owned044_pool');B=C.load(component['files']['event_backend.py'],'_owned044_events');policy=C.load(component['files']['common_precision.py'],'_owned044_precision');C.write(out/'PRECISION.json',policy.apply(torch))
 identity=solver.experiment_identity;mapped=[s for s in Path('/proc/self/maps').read_text().splitlines()if identity['library']['path']in s];C.need(mapped,'actual compensated037 DSO mapped, not a replacement solver')
 pool=L.KeepalivePool(512*1024**2,2);backend=B.EventBackend(torch,torch_npu);Q=C.load(component['files']['qualification_probe.py'],'_owned044_callback');actual=None;primary=None;pool_released=False
 try:actual=Q.produce(solver,pool,backend,source_ref=m['component044_source'],actual042_probe_ref=m['actual042_probe'],owner_arm_ref=arm,plan_ref=pr,output=out/'cases',deadline_monotonic=child_deadline)
 except BaseException as exc:primary=repr(exc)
 finally:
  try:pool.finish();pool_released=True
  except BaseException as exc:primary=primary or repr(exc)
  if actual is None and(out/'cases/RESULT.json').exists():actual=C.ref(out/'cases/RESULT.json')
  v=C.obj(actual)if actual else{'raws':[]}
  C.write(out/'PROBE.json',dict(schema='mxr.block-refinement-owned-probe/v044',source=sr,component_source=m['component044_source'],actual_result=actual,raws=v['raws'],primary=primary,outputs_per_case=3,pool_released=pool_released,actual_algorithm_identity=identity,mapped_library=mapped,NPU=True,model_ready=False,performance_ready=False,plan=pr))
 C.need(primary is None,'preserved callback failure '+str(primary));return 0
if __name__=='__main__':raise SystemExit(main())
