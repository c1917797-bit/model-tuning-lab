"""Actual same-current-ENV parser precheck, Devices[]; no model/driver init."""
import argparse,hashlib,importlib,importlib.util,inspect,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def load(name):
 s=importlib.util.spec_from_file_location('_mxr044_parser_'+name[:-3],P/name);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def platform_sources():
 value=json.loads((P/'PLATFORM_SOURCES.json').read_bytes());out=[]
 for r in value['files']:
  p=Path(r['path']);b=p.read_bytes();need(p.is_file()and not p.is_symlink()and (len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'actual installed platform source whole bytes');out.append(dict(r))
 return out
def parser_contract(platform,ascend_platform,torch,args,native_worker):
 need(platform is not None and type(platform)is ascend_platform.NPUPlatform and platform.device_type=='npu','actual registered NPUPlatform, no forced device/platform override')
 need(not torch.npu.is_initialized(),'Devices[] parser must not initialize NPU')
 need(args.worker_cls==native_worker,'actual parser native worker unchanged')

def parser_environment(E,o,sr,pr,base,source,output,run):
 # The original environment helper specifies a future TP4 server. Its device
 # predicate stays intact. Only a dictionary is constructed here; it grants no
 # mapped device, PID ownership, canary or NPU permission to this CPU process.
 need(base.get('ASCEND_RT_VISIBLE_DEVICES')=='','actual Devices[] CPU visibility must remain empty')
 need(base.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','actual CPU backend autoload must be disabled')
 planned_base=dict(base);planned_base['ASCEND_RT_VISIBLE_DEVICES']='0,1,2,3'
 planned=E.environment(o,sr,pr,planned_base,source,output,run)
 need(planned['ASCEND_RT_VISIBLE_DEVICES']=='0,1,2,3','original unadmitted TP4 server plan')
 actual=dict(planned);actual['ASCEND_RT_VISIBLE_DEVICES']=base['ASCEND_RT_VISIBLE_DEVICES']
 need(actual['TORCH_DEVICE_BACKEND_AUTOLOAD']=='0','CPU import must not autoload device backend')
 evidence=dict(schema='mxr.cpu-parser-server-plan-separation/v1',actual_cpu_visible_devices='',actual_cpu_devices=[],planned_server_visible_devices='0,1,2,3',planned_server_devices_not_admitted=True,hardware_ownership_proved=False,NPU_initialized=False)
 return actual,evidence
def tiny_canaries():
 # This process has real host-admitted TP4 devices. ENV alone grants nothing.
 need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0,1,2,3','host mapped all4 visibility required')
 import torch
 import torch_npu
 need(not torch.npu.is_initialized(),'no context before intentional tiny')
 need(torch.npu.device_count()==4,'actual device count4, not server geometry')
 rows=[]
 for device in range(4):
  torch.npu.set_device(device)
  x=torch.tensor([1.,2.],device='npu:%d'%device);y=x+3
  torch.npu.synchronize();value=y.cpu().tolist()
  need(value==[4.,5.],'actual all4 tiny arithmetic')
  rows.append(dict(logical=device,value=value))
 print('MXR067_STAGE actual-all4-tiny-complete',flush=True)
 return rows

def native_argv_contract(native,o,upstream):
 # Compare the COMPLETE source-bound argv mapping. Cap48 intentionally appends
 # load scalars after --worker-cls, so worker position is not an end sentinel.
 original=o.load_source(upstream,'server_entry.py').native_argv(8252,6*1024**3)
 need(type(original)is list and original[-2:]==['--worker-cls','kivi_firstdecode_bootstrap.FirstDecodeWorker'],'exact source-pinned original worker ABI')
 expected=list(original);expected[-1]=o.NATIVE_WORKER
 for key,old,new in (('--max-model-len','33792','4096'),('--max-num-batched-tokens','32768','2048'),('--max-num-seqs','1','1')):
  need(expected.count(key)==1 and expected[expected.index(key)+1]==old,'original registered long scalar '+key)
  expected[expected.index(key)+1]=new
 cap=load('cap48_provider.py');expected=cap.explicit_lazy_argv(expected)
 need(type(native)is list and all(type(x)is str for x in native)and native==expected,'complete native argv only registered three scalars, sole worker replacement and cap48 lazy options')
 need(native.count('--worker-cls')==1 and native.index('--worker-cls')+1<len(native)and native[native.index('--worker-cls')+1]==o.NATIVE_WORKER,'unique exact original native worker argument')
 return dict(schema='mxr.complete-native-argv-contract/v062',argv=list(native),original_argv=list(original),worker_cls=o.NATIVE_WORKER,complete_registered_mapping=True,worker_cls_unique=True,append_load_options_after_worker=True,NPU=False)

def cpu_static(E,sr,pr,a):
 need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','actual Devices[] CPU environment')
 need(not list(Path('/dev').glob('davinci[0-9]*')),'actual CPU no numbered NPU nodes')
 before=platform_sources();o=E.overlay();native=o.native_argv(a.upstream,8252)
 # source-pinned helper constructs argv using only stdlib. No runtime parser,
 # platforms, receiver, SchedulerConfig or ModelConfig is imported in this phase.
 proof=o.load_source(a.upstream,'config_cpu.py')
 argv_proof=native_argv_contract(native,o,a.upstream)
 need(not any(n=='torch'or n.startswith(('torch.','torch_npu','vllm'))for n in sys.modules),'source/argv gate imported no model/device modules')
 registry_root=a.output.parent/'planned-N1-registry-child'
 env,separation=parser_environment(E,o,sr,pr,dict(os.environ),E.OLD,registry_root,E.current(sr)['runtime_identity']['run_id'])
 # Real imported GDN queries Ascend architecture; Devices[] cannot satisfy it.
 # Keep source/argv/environment controls here, actual registration in admitted N1.
 child=None
 after=platform_sources();need(before==after,'source hashes unchanged')
 E.current(sr)
 value=dict(schema='mxr.devicefree-source-argv-pending-registry/v073r5',source=sr,component_prerequisite=pr,mode='cpu',pass_preflight=True,argv=native,complete_argv_contract=argv_proof,actual_CPU_registry_plugin_child=child,actual_registry_pending=True,CPU_device_plan_separation=separation,platform_sources_before=before,platform_sources_after=after,Devices=[],canaries=[],runtime_parser_executed=False,receiver_registered=False,NPU_initialized=False,hardware_ownership_proved_by_this_child=False,model_config_constructed=False,full_engine_config_constructed=False,full_model_qualified=False,candidate_numerical_qualified=False,graph_qualified=False,performance_ready=False,task_ready=False,deferred_installed_source_pins=proof.PINS,current_environment=dict(ASCEND_RT_VISIBLE_DEVICES=os.environ['ASCEND_RT_VISIBLE_DEVICES'],TORCH_DEVICE_BACKEND_AUTOLOAD=os.environ['TORCH_DEVICE_BACKEND_AUTOLOAD']),next_mandatory_stage='actual-four-tiny-then-real-registry-child-before-parser-and-weights')
 with a.output.open('x',encoding='utf8')as handle:json.dump(value,handle,sort_keys=True);handle.write('\n')
 print('MAIN_MXR_SAME_ENV_PARSER '+json.dumps(load('prerequisite.py').ref(a.output)),flush=True)
 return 0

def main(argv=None):
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true');ap.add_argument('--mode',choices=('cpu','n1'),default='cpu');ap.add_argument('--source-ref');ap.add_argument('--prerequisite-ref');ap.add_argument('--source3',type=Path);ap.add_argument('--upstream',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args(argv)
 if not a.execute:print(json.dumps(dict(enabled=False,Devices=[],NPU=False)));return 0
 need(all(x is not None for x in(a.source_ref,a.prerequisite_ref,a.source3,a.upstream,a.output)),'explicit same-current source/prerequisite/parser inputs')
 E=load('entry.py');sr,pr=map(json.loads,(a.source_ref,a.prerequisite_ref));m=E.current(sr)
 need(a.source3==E.OLD and a.upstream==E.LOW/'kivi-direct-d8-fp32-model-boundary-r87-v1-011','actual003/config011 source, no alternate parser')
 load('prerequisite.py').gate(pr)
 need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists()and not a.output.is_symlink(),'sole new CPU output')
 if a.mode=='cpu':return cpu_static(E,sr,pr,a)
 root=a.output.parent/'parser-capture';receipt=a.output.parent/'parser-worker-receipts'
 need(not root.exists()and not receipt.exists(),'parser evidence directories absent');root.mkdir();receipt.mkdir()
 o=E.overlay()
 canaries=tiny_canaries()
 env=E.environment(o,sr,pr,os.environ,a.source3.parent/'mxr-r118-capture-20261013-001',root,m['runtime_identity']['run_id'])
 device_plan=dict(scope='actual-four-tiny-before-parser',canaries=canaries)
 env.update(MST_MXR_NATIVE_WORKER_RECEIPT='1',MST_MXR_NATIVE_WORKER_ROOT=str(receipt),MST_MXR_NATIVE_WORKER_RUN_ID=m['runtime_identity']['run_id'])
 need('ascend'in env['VLLM_PLUGINS'].split(',')and env['MXR_DIAG16_GDN_SHADOW_ENABLE']=='1','same enabled receiver and platform registration as new server')
 os.environ.update(env)
 need(os.environ['ASCEND_RT_VISIBLE_DEVICES']=='0,1,2,3','actual mapped TP4 visibility, ownership is host proof')
 from plugin_discovery import component
 component_root,_=component(m['plugin_source'])
 for p in(P,E.WORKER,component_root):
  if str(p)not in sys.path:sys.path.insert(0,str(p))
 registry_child=load('registry_child_probe.py').run(sr,a.output.parent/'N1_REGISTRY_CHILD.json',env)
 before=platform_sources()
 # EXACT original003 server sequence through parse; no EngineConfig/registry/weights.
 guest=E.private('guest_capture_entry.py',o)
 cann=guest.installed_cann(a.upstream)
 proof=o.load_source(a.upstream,'config_cpu.py')
 import torch
 import torch_npu
 need(torch.npu.is_initialized(),'intentional canary preceded original API import')
 api=importlib.import_module('vllm.entrypoints.openai.api_server')
 installed=proof.actual_sources()
 api.cli_env_setup()
 from vllm.plugins import load_general_plugins
 from plugin_discovery import static_discovery
 # Backend already intentionally initialized by canary here; source/metadata
 # discovery was independently completed in the preceding Devices[] CPU stage.
 from plugin_discovery import EXPECTED
 import importlib.metadata as plugin_metadata
 available={ep.name:ep.value for dist in plugin_metadata.distributions(path=[str(component_root)])for ep in dist.entry_points if ep.group=='vllm.general_plugins'and ep.name in EXPECTED}
 need(available==EXPECTED,'same real044 entrypoint map in initialized parser')
 load_general_plugins()
 from vllm_ascend.worker.worker import NPUWorker
 need(hashlib.sha256(Path(inspect.getsourcefile(NPUWorker)).read_bytes()).hexdigest()=='c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3','original mapped native worker source unchanged')
 native=o.native_argv(a.upstream,8252)
 argv_proof=native_argv_contract(native,o,a.upstream)
 args=proof.parse(api,native)
 from vllm.platforms import current_platform
 ascend_platform=importlib.import_module('vllm_ascend.platform')
 need(type(current_platform)is ascend_platform.NPUPlatform and current_platform.device_type=='npu'and args.worker_cls==o.NATIVE_WORKER,'real platform/parser/native worker after tiny, no override')
 need(hashlib.sha256(Path(inspect.getfile(ascend_platform)).read_bytes()).hexdigest()==proof.PINS['vllm_ascend.platform'],'genuine installed Ascend platform class source')
 from vllm.config.scheduler import SchedulerConfig
 scalar=proof.require_cpu_policy(args,proof.cpu_scheduler_config(args,SchedulerConfig),6*1024**3)
 # General plugin registration must also have run in this same CPU process.
 receiver=sys.modules.get('_mxr042_entry_receiver')
 need(receiver is not None and Path(receiver.__file__).resolve()==P/'worker.py'and receiver._registration is not None and receiver._installed_bridge is None,'actual current source registration pending real first core; not a worker receipt')
 need('_mxr044_source_bound_installer'not in sys.modules,'no alternate block plugin installer in diagnostic process')
 need('mxr_common_precision044'in sys.modules,'actual common policy package loaded from discovered entrypoint')
 runtime=root/'REGISTRATION_ONLY.json'
 registration=receiver._registration.receipt()
 need(registration['pending_actual_first_core']is True and registration['actual_worker_installed']is False,'no fake worker install/evidence in parser')
 with runtime.open('x')as f:json.dump(registration,f,sort_keys=True);f.write('\n')
 need(torch.npu.is_initialized(),'canary NPU context remains intentional; no engine/weights')
 after=platform_sources();need(before==after,'installed platform source before/after unchanged')
 E.current(sr);runtime_ref=load('prerequisite.py').ref(runtime)
 need(os.environ['ASCEND_RT_VISIBLE_DEVICES']=='0,1,2,3','mapped visibility unchanged')
 value=dict(schema='mxr.actual-native-preflight/v073r5',source=sr,component_prerequisite=pr,mode='n1',pass_preflight=True,actual_N1_registry_plugin_child=registry_child,registry_stage='N1-after-all4-tiny-before-parser-and-weights',runtime_parser_executed=True,receiver_registered=True,canary_preceded_parser=True,pid=os.getpid(),cgroup=Path('/proc/self/cgroup').read_text(),argv=native,complete_argv_contract=argv_proof,installed=installed,cann=cann,cpu_scalar_policy=scalar,canaries=canaries,device_environment_separation=device_plan,current_environment=dict(ASCEND_RT_VISIBLE_DEVICES=env['ASCEND_RT_VISIBLE_DEVICES'],TORCH_DEVICE_BACKEND_AUTOLOAD=env['TORCH_DEVICE_BACKEND_AUTOLOAD'],VLLM_PLUGINS=env['VLLM_PLUGINS'],MXR_DIAG16_GDN_SHADOW_ENABLE=env['MXR_DIAG16_GDN_SHADOW_ENABLE'],MXR_DIAG16_GDN_STAGE=env['MXR_DIAG16_GDN_STAGE'],MXR_DIAG16_GDN_SOURCE_REF=sr,MXR_DIAG16_GDN_PREREQUISITE_REF=pr,MST_MXR_NATIVE_WORKER_RECEIPT='1'),platform_class=type(current_platform).__module__+'.'+type(current_platform).__qualname__,platform_device_type=current_platform.device_type,platform_sources_before=before,platform_sources_after=after,receiver_registration_only=runtime_ref,NPU_initialized=True,model_config_constructed=False,full_engine_config_constructed=False,hardware_ownership_proved_by_this_child=False,full_model_qualified=False,candidate_numerical_qualified=False,model_ready=False,graph_qualified=False,performance_ready=False,task_ready=False)
 with a.output.open('x',encoding='utf8')as f:json.dump(value,f,sort_keys=True);f.write('\n')
 print('MAIN_MXR_SAME_ENV_PARSER '+json.dumps(load('prerequisite.py').ref(a.output)),flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
