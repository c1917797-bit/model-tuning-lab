"""Fresh -I admitted-device actual003 parser; HAL permitted, no engine/weights."""
import argparse,importlib,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def main():
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true');ap.add_argument('--source-ref');ap.add_argument('--output',type=Path);a=ap.parse_args()
 if not a.execute:print('disabled');return
 import owner_overlay as O,entry as E,bootstrap101r9 as B
 sr=json.loads(a.source_ref);m=O.current(sr)
 O.need(sys.flags.isolated and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0,1,2,3'and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and all((Path('/dev')/('davinci%d'%i)).exists()for i in range(4)),'fresh isolated admitted four-device parser')
 O.need('vllm_ascend.worker.model_runner_v1'not in sys.modules,'no runner prewarm')
 B.install(m,P);B.package_proof(m)
 o=E.overlay();o.environment_original=o.environment
 audit=a.output.parent/'cold-parser-audit';audit.mkdir();receipts=a.output.parent/'cold-parser-workers';receipts.mkdir()
 env=O.environment(type('Entry',(),{'WORKER':E.WORKER}),o,sr,os.environ,E.OLD,audit,m['runtime_identity']['run_id'],stage='parser')
 env.update(MST_MXR_NATIVE_WORKER_RECEIPT='1',MST_MXR_NATIVE_WORKER_ROOT=str(receipts),MST_MXR_NATIVE_WORKER_RUN_ID=m['runtime_identity']['run_id']);os.environ.update(env)
 # Exact actual003 installed_cann -> torch -> torch_npu -> API -> parse order.
 before_modules={k:k in sys.modules for k in('torch','torch_npu','vllm_ascend.worker.model_runner_v1')}
 prior=sys.modules.get('torch');npu=getattr(prior,'npu',None)
 before=bool(npu.is_initialized())if npu is not None else False
 guest=E.private(o);cann=guest.installed_cann(E.LOW/'kivi-direct-d8-fp32-model-boundary-r87-v1-011')
 import torch
 import torch_npu
 proof=o.load_source(E.LOW/'kivi-direct-d8-fp32-model-boundary-r87-v1-011','config_cpu.py')
 api=importlib.import_module('vllm.entrypoints.openai.api_server');api.cli_env_setup()
 args=proof.parse(api,o.native_argv(E.LOW/'kivi-direct-d8-fp32-model-boundary-r87-v1-011',8252))
 after=bool(torch.npu.is_initialized())
 import native_observer_plugin101r12 as plugin
 O.need(plugin._registration_state=='native-installed','actual observer registration receipt')
 result=dict(schema='deltalog.fresh-entry-parser/v101R17',source=sr,isolated=True,before_backend_modules=before_modules,before_NPU_initialized=before,after_NPU_initialized=after,HAL_initialization_permitted=True,cann=cann,engine_constructed=False,weights_loaded=False,registration_state=plugin._registration_state,plugin_ref=O.obj_file(m['files']['native_observer_plugin101r12.py']).as_posix(),worker_cls=args.worker_cls,NPU=True,model_math_executed=False,qualification=False)
 with a.output.open('x',encoding='utf-8')as f:json.dump(result,f,sort_keys=True);f.write('\n')
if __name__=='__main__':main()
