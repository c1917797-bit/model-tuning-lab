"""Actual general-plugin cold subprocess in admitted N1, never model/CPU PASS."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 b=Path(p).read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def installed_cann(E):
 # This is a new -I interpreter. It cannot inherit its parent's sys.path or
 # use PYTHONPATH as an implicit substitute for the original guest bootstrap.
 upstream=E.LOW/'kivi-direct-d8-fp32-model-boundary-r87-v1-011'
 o=E.overlay();guest=E.private('guest_capture_entry.py',o)
 value=guest.installed_cann(upstream)
 helper=ref(upstream/'cann_python.py')
 need(helper['bytes']==4503 and helper['sha256']==o.UPSTREAM_PINS['cann_python.py']=='cee927f1107fe6714e86ab1dceecafeff800980a00b8df9fcc47ff6831ba5104'and value['helper_sha']==helper['sha256']and value['root']in sys.path,'exact original CANN bootstrap in current isolated child')
 return dict(value,bootstrap_source_ref=helper,isolated_child_explicit_path=True)
def run(sr,output,env=None):
 output=Path(output);need(output.is_absolute()and output.parent.is_dir()and not output.exists(),'new actual registry-child output')
 args=[sys.executable,'-I','-B',str(P/'registry_child_probe.py'),'--execute','--source-ref',json.dumps(sr,separators=(',',':')),'--output',str(output)]
 value=subprocess.run(args,capture_output=True,text=True,timeout=90,env=env)
 need(len(value.stdout.encode())+len(value.stderr.encode())<=256*1024,'bounded registry-plugin subprocess logs')
 with output.with_suffix('.child.json').open('x')as f:json.dump(dict(argv=args,exit_code=value.returncode,stdout=value.stdout,stderr=value.stderr,NPU_numeric=False),f,sort_keys=True);f.write('\n')
 need(value.returncode==0,'actual cold general-plugin registry frontdoor failed; preserved child receipt')
 v=json.loads(output.read_bytes());need(v['source']==sr and v['full_install_deferred']is True and v['no_worker_runtime_receipt']is True and v['model_forward_executed']is False and (v['actual_visible_devices']!=''or v['torch_npu_initialized']is False),'actual cold child did not fabricate worker/forward proof or initialize Devices[]');return ref(output)
def main():
 a=argparse.ArgumentParser(allow_abbrev=False);a.add_argument('--execute',action='store_true');a.add_argument('--source-ref');a.add_argument('--output',type=Path);x=a.parse_args()
 if not x.execute:print('{"enabled":false,"NPU":false}');return 0
 import entry as E
 current,WORKER=E.current,E.WORKER
 sr=json.loads(x.source_ref);m=current(sr)
 visibility=os.environ.get('ASCEND_RT_VISIBLE_DEVICES');need(visibility in('','0,1,2,3')and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','actual CPUempty or MAIN admitted N1 visibility')
 if visibility=='':need(not list(Path('/dev').glob('davinci[0-9]*')),'actual Devices[] no numbered nodes')
 from plugin_discovery import component
 root,_=component(m['plugin_source'])
 for p in(P,WORKER,root):
  if str(p)not in sys.path:sys.path.insert(0,str(p))
 cann=installed_cann(E)
 from vllm.plugins import load_general_plugins
 load_general_plugins()
 receiver=sys.modules.get('_mxr042_entry_receiver');need(receiver is not None and Path(receiver.__file__).resolve()==P/'worker.py','same actual enabled source receiver loaded by real general-plugin entrypoint')
 state=receiver._registration;need(state is not None and receiver._installed_bridge is None and state.receipt()['pending_actual_first_core']is True,'whole installer deferred during real architecture-child registration')
 proof=state.root/('worker-'+str(os.getpid()))/'RUNTIME.json';need(not proof.exists(),'no fake worker RUNTIME at model inspection')
 import torch
 initialized=bool(torch.npu.is_initialized());need(visibility!=''or not initialized,'actual CPU plugin load must not initialize NPU')
 result=dict(schema='mxr.actual-registry-plugin-child/v073r6',source=sr,pid=os.getpid(),actual_cann=cann,full_install_deferred=True,no_worker_runtime_receipt=True,model_forward_executed=False,receiver_registered=True,NPU_numeric=False,actual_visible_devices=visibility,devices_declared_only=[]if visibility==''else[0,1,2,3],torch_npu_initialized=initialized,model_qualified=False)
 with x.output.open('x')as f:json.dump(result,f,sort_keys=True);f.write('\n')
 print(json.dumps(ref(x.output)));return 0
if __name__=='__main__':raise SystemExit(main())
