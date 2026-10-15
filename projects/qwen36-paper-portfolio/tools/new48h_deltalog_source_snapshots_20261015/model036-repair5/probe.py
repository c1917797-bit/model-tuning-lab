"""Real017 native parser reuse, CPU discovery separate from model weight load."""
import argparse,importlib,importlib.util,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import owner_overlay as O
def main():
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true');ap.add_argument('--mode',choices=('cpu','parser'));ap.add_argument('--source-ref');ap.add_argument('--output',type=Path);a=ap.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=O.current(sr);O.need(a.output.parent.is_dir()and not a.output.exists(),'new owned preflight output')
 ep=O.obj_file(m['entry017_ref']);s=importlib.util.spec_from_file_location('_dl025_actual017_entry',ep);E=importlib.util.module_from_spec(s);s.loader.exec_module(E);O.configure(E)
 native=E.overlay().native_argv(E.LOW/'kivi-direct-d8-fp32-model-boundary-r87-v1-011',8252)
 if a.mode=='cpu':
  O.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not list(Path('/dev').glob('davinci[0-9]*')),'actual Devices[] CPU contract')
  platform=O.obj(m['platform_source_ref'])
  for r in platform['files']:O.obj_file(r)
  for r in m['request_identity_guest_refs']:O.obj_file(r)
  runtime_ref=m['plugin_source']or m['plugin_template_ref'];sys.path.insert(0,str(Path(runtime_ref['path']).parent))
  from qwen36_deltalog_service import register
  O.need(os.environ.get('QWEN36_DELTALOG_SERVICE023_ENABLE')!='1'and os.environ.get('QWEN36_DELTALOG_TRACE025_ENABLE')!='1','actual cold defaultOFF');register()
  O.need('torch'not in sys.modules and'torch_npu'not in sys.modules,'no compute backend in CPU discovery')
  os.environ['DL025_DONOR017_LOCAL']=str(Path(m['host017_ref']['path']).parent);os.environ['DL025_DONOR008_LOCAL']=m['donor008_host_ref']['path']
  os.environ['DL025_CAPTURE_CLIENT_LOCAL']=m['capture_client_ref']['path']
  import unittest,io
  suite=unittest.defaultTestLoader.discover(str(P),pattern='test_*.py');count=suite.countTestCases();stream=io.StringIO();controls=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
  O.need(count==m['software_cases']and controls.testsRun==count and controls.wasSuccessful(),'sameimage complete actual cold software contracts: '+stream.getvalue())
  result=dict(source=sr,mode='cpu',pass_preflight=True,CPU_source_discovery_pass=True,NPU=False,engine_constructed=False,model_ready=False,actual_library_loaded=False,software_controls=dict(discovered=count,executed=controls.testsRun,passed=True,log=stream.getvalue()))
 else:
  O.model_gate(m)
  O.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0,1,2,3','owned physical4–7→logical0–3 required')
  import torch,torch_npu
  O.need(torch.npu.device_count()==4,'actual scoped4 device count');canaries=[]
  for i in range(4):
   torch.npu.set_device(i);v=(torch.tensor([1.,2.],device='npu:%d'%i)+3).cpu().tolist();O.need(v==[4.,5.],'actual canary');canaries.append(dict(logical=i,value=v))
  audit=a.output.parent/'parser-audit';audit.mkdir();receipts=a.output.parent/'parser-worker-receipts';receipts.mkdir()
  o=E.overlay();o.environment_original=o.environment
  env=O.environment(E,o,sr,os.environ,E.LOW/'mxr-r118-capture-20261013-001',audit,m['runtime_identity']['run_id'],stage='parser')
  env.update(MST_MXR_NATIVE_WORKER_RECEIPT='1',MST_MXR_NATIVE_WORKER_ROOT=str(receipts),MST_MXR_NATIVE_WORKER_RUN_ID=m['runtime_identity']['run_id']);os.environ.update(env)
  for root in(P,E.WORKER,Path(m['plugin_source']['path']).parent):sys.path.insert(0,str(root))
  guest=E.private(o);cann=guest.installed_cann(E.LOW/'kivi-direct-d8-fp32-model-boundary-r87-v1-011')
  proof=o.load_source(E.LOW/'kivi-direct-d8-fp32-model-boundary-r87-v1-011','config_cpu.py');api=importlib.import_module('vllm.entrypoints.openai.api_server');api.cli_env_setup()
  from vllm.plugins import load_general_plugins
  load_general_plugins();args=proof.parse(api,native)
  from vllm.platforms import current_platform
  from vllm_ascend.platform import NPUPlatform
  from qwen36_deltalog_service import runtime as R
  O.need(type(current_platform)is NPUPlatform and args.worker_cls==o.NATIVE_WORKER and R._OP is not None and R._SOURCE==m['plugin_source'],'actual native receiver/parser source, not a fixture')
  O.need(args.load_format=='safetensors'and args.safetensors_load_strategy=='lazy'and args.model_loader_extra_config.get('enable_multithread_load')is False,'original common MEM48/lazy contract')
  result=dict(source=sr,mode='parser',pass_preflight=True,real_plugin_registered=True,receiver_discovery_pass=True,NPU=True,canaries=canaries,cann=cann,actual_namespace=R.C.NAMESPACE,engine_constructed=False,weights_loaded=False,model_ready=False,model_numeric_qualified=False)
 with a.output.open('x',encoding='utf8')as f:json.dump(result,f,sort_keys=True);f.write('\n')
 return 0
if __name__=='__main__':raise SystemExit(main())
