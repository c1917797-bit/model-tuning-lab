"""Source-only CPU then real4canary/normal parser/DL register, no weights."""
import argparse,importlib,importlib.util,json,os,sys,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
def load(n):
 s=importlib.util.spec_from_file_location('_dl004_probe_'+n[:-3],P/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true');ap.add_argument('--mode',choices=['cpu','n1']);ap.add_argument('--source-ref');ap.add_argument('--output',type=Path);a=ap.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return
 E=load('entry.py');sr=json.loads(a.source_ref);m=E.current(sr);o=E.overlay();native=o.native_argv(E.LOW/'kivi-direct-d8-fp32-model-boundary-r87-v1-011',8252)
 E.need(a.output.parent.is_dir()and not a.output.exists(),'new preflight output');canaries=[]
 if a.mode=='cpu':
  E.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not list(Path('/dev').glob('davinci[0-9]*')),'actual Devices[]')
  for r in m['component_readset']:E.need(load('prerequisite.py').ref(r['path'])==r,'source/reference pins')
  for r in json.loads((P/'PLATFORM_SOURCES.json').read_bytes())['files']:
   b=Path(r['path']).read_bytes();E.need((len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'actual installed platform source')
  sys.path.insert(0,str(Path(m['plugin_source']['path']).parent));from qwen36_deltalog_service import register
  E.need(os.environ.get('QWEN36_DELTALOG_SERVICE003_ENABLE')!='1','CPU real defaultOFF');register();E.need('torch'not in sys.modules and 'torch_npu'not in sys.modules,'OFF imports no backend')
  v=dict(source=sr,mode='cpu',pass_preflight=True,NPU=False,canaries=[],actual_default_off_import=True,argv=native)
 else:
  E.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0,1,2,3','real TP4 visible scope')
  import torch,torch_npu
  E.need(torch.npu.device_count()==4,'actual4 device canary count')
  for i in range(4):
   torch.npu.set_device(i);x=(torch.tensor([1.,2.],device='npu:%d'%i)+3).cpu().tolist();E.need(x==[4.,5.],'actual tiny');canaries.append(dict(logical=i,value=x))
  audit=a.output.parent/'parser-audit';audit.mkdir();receipts=a.output.parent/'parser-worker-receipts';receipts.mkdir()
  o.environment_original=o.environment;env=E.environment(o,sr,os.environ,E.LOW/'mxr-r118-capture-20261013-001',audit,m['runtime_identity']['run_id']);env.update(MST_MXR_NATIVE_WORKER_RECEIPT='1',MST_MXR_NATIVE_WORKER_ROOT=str(receipts),MST_MXR_NATIVE_WORKER_RUN_ID=m['runtime_identity']['run_id']);os.environ.update(env)
  for root in(P,E.WORKER,Path(m['plugin_source']['path']).parent):
   if str(root)not in sys.path:sys.path.insert(0,str(root))
  guest=E.private(o);cann=guest.installed_cann(E.LOW/'kivi-direct-d8-fp32-model-boundary-r87-v1-011');proof=o.load_source(E.LOW/'kivi-direct-d8-fp32-model-boundary-r87-v1-011','config_cpu.py');api=importlib.import_module('vllm.entrypoints.openai.api_server');api.cli_env_setup()
  from vllm.plugins import load_general_plugins
  load_general_plugins();args=proof.parse(api,native)
  from vllm.platforms import current_platform
  from vllm_ascend.platform import NPUPlatform
  from qwen36_deltalog_service import runtime as R
  E.need(type(current_platform)is NPUPlatform and args.worker_cls==o.NATIVE_WORKER and R._OP is not None and R._SOURCE==m['plugin_source'],'actual native platform/parser/DL receiver')
  E.need(args.load_format=='safetensors'and args.safetensors_load_strategy=='lazy'and args.model_loader_extra_config.get('enable_multithread_load')is False,'same normal lazy loader actual args')
  v=dict(source=sr,mode='n1',pass_preflight=True,canaries=canaries,real_plugin_registered=True,NPU=True,engine_constructed=False,weights_loaded=False,performance_ready=False,actual_namespace=R.C.NAMESPACE,cann=cann,argv=native)
 with a.output.open('x',encoding='utf8')as f:json.dump(v,f,sort_keys=True);f.write('\n')
if __name__=='__main__':main()
