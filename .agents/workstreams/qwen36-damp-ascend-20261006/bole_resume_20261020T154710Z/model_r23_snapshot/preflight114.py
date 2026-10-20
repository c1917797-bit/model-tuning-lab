"""Real Devices[] native parser + lazy MTP registry; no fabricated ModelConfig."""
import argparse,ast,hashlib,importlib,inspect,json,os,sys,traceback
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import contract090 as C
def actual_source(module,r):
 p=Path(inspect.getfile(module)).resolve();b=p.read_bytes();C.need(str(p)==r['path']and(len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'actual installed source '+module.__name__);return dict(r)
def run(sr,m):
 C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','actual Devices[] CPU environment')
 C.need(not list(Path('/dev').glob('davinci[0-9]*')),'Devices[] no numbered device nodes')
 for n,r in m['files'].items():
  if n.endswith('.py'):ast.parse(C.checked(r).read_bytes())
 argv=C.server_command();C.need(argv[1:3]==['-m','vllm.entrypoints.openai.api_server'],'actual server frontend argv prefix')
 api=importlib.import_module('vllm.entrypoints.openai.api_server')
 p=Path(inspect.getfile(api));C.need(hashlib.sha256(p.read_bytes()).hexdigest()=='6d8df133280618a1afffa9d03e4655af011f2f94ced0f90c15f7fc8b0afc538f','actual660 API source SHA')
 api.cli_env_setup();parser=api.make_arg_parser(api.FlexibleArgumentParser(description=__doc__));args=parser.parse_args(argv[3:]);api.validate_parsed_serve_args(args)
 engine_mod=importlib.import_module('vllm.engine.arg_utils');C.need(hashlib.sha256(Path(inspect.getfile(engine_mod)).read_bytes()).hexdigest()=='3ade2488897d08b5c1fd4ddb815eb5743169907d59741a47867185caab7f250d','actual660 EngineArgs source')
 engine=engine_mod.AsyncEngineArgs.from_cli_args(args)
 cache_memory=C.cache_memory_config(argv,m,args=args,engine=engine)
 expected=dict(method='mtp',num_speculative_tokens=8);C.need(args.speculative_config==expected and engine.speculative_config==expected,'actual parser and EngineArgs same native MTP config, not fake SpeculativeConfig/model')
 spec=importlib.import_module('vllm.config.speculative');registry=importlib.import_module('vllm.model_executor.models.registry')
 sources=dict(spec=actual_source(spec,m['installed_sources']['spec_config']),registry=actual_source(registry,m['installed_sources']['registry']))
 C.need('qwen3_5_mtp'in spec.MTPModelTypes.__args__,'actual installed MTP type')
 C.need('Qwen3_5MTP'in registry.ModelRegistry.get_supported_archs(),'actual lazy registered MTP architecture')
 row=registry.ModelRegistry.models['Qwen3_5MTP'];C.need(row.module_name=='vllm.model_executor.models.qwen3_5_mtp'and row.class_name=='Qwen3_5MTP','actual lazy MTP registry module/class')
 index=C.obj(m['checkpoint_index_ref']);names=sorted(n for n in index['weight_map']if n.startswith('mtp.'));config=C.obj(m['checkpoint_config_ref'])
 C.need(len(names)==15 and config['text_config']['mtp_num_hidden_layers']==1,'actual exact checkpoint MTP15/one-layer source metadata')
 import torch,torch_npu
 C.need(not torch.npu.is_initialized(),'parser/registry enumeration cannot initialize device')
 schema=torch.ops.npu.npu_fused_infer_attention_score.default._schema
 fia=dict(schema=str(schema),argument_names=[q.name for q in schema.arguments],operator_executed=False,torch_version=torch.__version__,torch_npu_file=str(Path(torch_npu.__file__).resolve()),torch_npu_python_ref=C.ref(Path(torch_npu.__file__).resolve()))
 C.need(not list(Path('/dev').glob('davinci[0-9]*')),'CPU devices remain absent')
 return dict(schema='bole.actual-devicefree-native-MTP-parser/v114',source=sr,Devices=[],NPU=False,pass_preflight=True,native_runtime_parser_checked=True,registry_arch_enumerated=True,registry_class_imported=False,model_config_constructed=False,full_engine_config_constructed=False,weights_loaded=False,BOLE=False,argv=argv,actual_speculative_config=expected,actual_cache_memory_config=cache_memory,installed_sources=sources,actual_FIA_dispatch_schema=fia,api_source=C.ref(p),lazy_registry=dict(module=row.module_name,cls=row.class_name),checkpoint_index_ref=m['checkpoint_index_ref'],checkpoint_config_ref=m['checkpoint_config_ref'],actual_checkpoint_mtp_names=names,torch_NPU_initialized=False,next_required='original owned TP4 canary then actual ModelConfig/QwenMTP class/weights load; CPU lazy registry is not runtime class proof')
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=C.source(sr)
 try:value=run(sr,m)
 except BaseException as e:
  C.write(a.output,dict(schema='bole.actual-devicefree-native-MTP-parser/v114',source=sr,Devices=[],NPU=False,pass_preflight=False,primary=repr(e),traceback=traceback.format_exc(),BOLE=False));raise
 C.write(a.output,value);return 0
if __name__=='__main__':raise SystemExit(main())
