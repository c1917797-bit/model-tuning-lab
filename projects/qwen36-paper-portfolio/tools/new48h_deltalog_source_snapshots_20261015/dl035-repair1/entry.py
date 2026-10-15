"""DefaultOFF same-image CPU oracle qualification or actual singleton child."""
import argparse,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--stage',choices=('cpu-preflight','numeric'),required=True)
 for k in('source-ref','authority-ref','lifecycle-ref','output'):p.add_argument('--'+k,required=True)
 p.add_argument('--plan-ref');p.add_argument('--cpu-preflight-ref');p.add_argument('--steps',type=int,choices=(16,160),default=16);a=p.parse_args();sr,ar,lr=[json.loads(getattr(a,k))for k in('source_ref','authority_ref','lifecycle_ref')];m=C.source(sr);C.window(ar)
 from qwen36_deltalog_fresh.provider import source_admission
 source_admission(sr,lr);out=Path(a.output)
 if a.stage=='cpu-preflight':
  C.need(not list(Path('/dev').glob('davinci*'))and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','actual Devices[] CPU stage')
  import torch
  C.need('torch_npu'not in sys.modules,'CPU reference no backend import');torch.set_num_threads(1)
  R=C.load(m['files']['oracle.py'],'independent_cpu64');S=C.load(m['files']['consume.py'],'independent_bridge');boundary=R.boundary_tests(torch)
  z=torch.zeros((1,4,128),dtype=torch.bfloat16);C.need(torch.equal(S.normalized(torch,z),z),'eps zero input finite')
  x=torch.full((1,4,128),1e-5,dtype=torch.bfloat16);actual=S.normalized(torch,x);expected=(x.float()/((x.float().square().sum(-1,keepdim=True)+1e-6).sqrt())).to(x.dtype)
  C.need(torch.equal(actual,expected)and not torch.equal(actual,torch.nn.functional.normalize(x.float(),dim=-1).to(x.dtype)),'independent eps boundary differs from F.normalize')
  C.need(out.parent.is_dir()and not out.exists(),'new CPU leaf');out.mkdir()
  import subprocess
  actual=subprocess.run([sys.executable,'-I','-B',str(P/'copy_bootstrap_probe.py'),'--execute','--output',str(out)],capture_output=True,text=True,timeout=120)
  C.write(out/'COPY_IMPORT_CPU.json',dict(argv=[sys.executable,'-I','-B',str(P/'copy_bootstrap_probe.py'),'--execute','--output',str(out)],returncode=actual.returncode,stdout=actual.stdout,stderr=actual.stderr))
  C.need(actual.returncode==0,'actual same-image Devices[] official copy import; no allocation')
  lines=[x for x in actual.stdout.splitlines(keepends=True)if x.startswith('MAIN_DL_COPY_IMPORT ')];C.need(len(lines)==1 and lines[0].endswith('\n'),'one complete actual copy import marker')
  imported=json.loads(lines[0][len('MAIN_DL_COPY_IMPORT '):]);C.need(imported['Devices']==[] and imported['NPU']is False and imported['copy_executed']is False,'actual CPU import scope')
  controls=subprocess.run([sys.executable,'-I','-B',str(P/'real_process_controls.py'),'--execute','--output',str(out/'REAL_PROCESS_CONTROLS.json')],capture_output=True,text=True,timeout=60)
  C.write(out/'REAL_PROCESS_EXEC.json',dict(returncode=controls.returncode,stdout=controls.stdout,stderr=controls.stderr))
  C.need(controls.returncode==0,'actual same-image short-process and live-negative controls required')
  C.write(out/'STAGE_RESULT.json',dict(schema='deltalog.fresh-bridge-stage/v5',source=sr,authority=ar,lifecycle=lr,pass_gate=True,NPU=False,model_ready=False,boundary=boundary,actual_copy_import=C.ref(out/'COPY_IMPORT_CPU.json'),actual_terminal_process_controls=C.ref(out/'REAL_PROCESS_CONTROLS.json')));return 0
 cpu=C.obj(json.loads(a.cpu_preflight_ref));C.need(cpu['source']==sr and cpu['lifecycle']==lr and cpu['pass_gate']is True and cpu['NPU']is False,'actual same-source CPU preflight')
 C.need(C.obj(cpu['actual_terminal_process_controls'])['software_controls_pass']is True,'same-source real-process controls were executed before NPU')
 child=C.load(m['files']['producer.py'],'actual_mixed_copy_producer');old=sys.argv;sys.argv=[str(P/'producer.py'),'--execute','--source-ref',a.source_ref,'--authority-ref',a.authority_ref,'--lifecycle-ref',a.lifecycle_ref,'--plan-ref',a.plan_ref,'--output',a.output,'--steps',str(a.steps)]
 try:code=child.main()
 finally:sys.argv=old
 rr=C.ref(out/'RESULT.json');v=C.obj(rr);C.write(out/'STAGE_RESULT.json',dict(schema='deltalog.fresh-bridge-stage/v5',source=sr,authority=ar,lifecycle=lr,actual_result=rr,observation_complete=bool(v['records']),producer_exit=code,NPU=True,model_ready=False));return 0 if v['records']else code
if __name__=='__main__':raise SystemExit(main())
