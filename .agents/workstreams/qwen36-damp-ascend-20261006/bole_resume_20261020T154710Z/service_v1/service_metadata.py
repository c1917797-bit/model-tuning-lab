"""Devices[] installed class/CLI protocol inspection; no model construction."""
import argparse,ast,inspect,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C

def run(sr):
 m=C.obj(sr);refs=m['runtime_sources']
 C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='' and
        os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0' and
        not list(Path('/dev').glob('davinci[0-9]*')),'actual Devices[] metadata inspection')
 import torch,torch_npu
 C.need(not torch.npu.is_initialized(),'metadata imports cannot initialize NPU')
 from vllm.v1.sample.metadata import SamplingMetadata
 from vllm.v1.outputs import SamplerOutput,ModelRunnerOutput
 from vllm.entrypoints.openai.completion.protocol import CompletionRequest,CompletionResponseChoice
 from vllm.sampling_params import SamplingParams
 C.checked(m['files']['service_runner.py'])
 rows=[]
 for cls,key in((SamplingMetadata,'sampling_metadata'),(SamplerOutput,'outputs'),(ModelRunnerOutput,'outputs'),
  (CompletionRequest,'completion_protocol'),(CompletionResponseChoice,'completion_protocol'),
  (SamplingParams,'sampling_params')):
  actual=C.ref(inspect.getsourcefile(cls));C.need(actual==refs[key],'actual installed class source '+key)
  rows.append(dict(cls=cls.__module__+'.'+cls.__qualname__,source=actual))
 compiled=[]
 for key,clsname,names in(
  ('worker','NPUWorker',('load_model',)),
  ('runner','NPUModelRunner',('_prepare_inputs','_sample','propose_draft_token_ids','sample_tokens','_update_states')),
  ('npu_input_batch','NPUInputBatch',('__init__',)),
  ('gpu_input_batch','InputBatch',('no_thinking_budget','_make_sampling_metadata')),
  ('proposer','AscendSpecDecodeBaseProposer',('_propose','set_inputs_first_pass','prepare_inputs_padded')),
  ('base_proposer','SpecDecodeBaseProposer',('_get_positions',))):
  path=C.checked(refs[key]);data=path.read_bytes()
  compile(data,str(path),'exec')
  module=ast.parse(data,filename=str(path));cls=next(n for n in module.body if isinstance(n,ast.ClassDef)and n.name==clsname)
  methods={n.name:n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
  C.need(set(names)<=set(methods),'actual complete compiled native class methods '+key)
  if key=='runner':
   C.need([ast.unparse(x)for x in methods['sample_tokens'].decorator_list]==['torch.inference_mode()'],
          'actual complete native sample method has exact inference-mode decorator')
  if key=='npu_input_batch':
   C.need([ast.unparse(x)for x in cls.bases]==['InputBatch']and'no_thinking_budget'not in methods,
          'source-proved actual NPU batch inherits native no-thinking-budget property')
  compiled.append(dict(source=refs[key],cls=clsname,methods=list(names),full_source_compiled=True,import_executed=False))
 context=torch.inference_mode()
 C.need(type(context)is torch.inference_mode and context.mode is True and
        C.ref(inspect.getsourcefile(type(context)))==refs['torch_grad_mode']and
        C.ref(inspect.getsourcefile(context.clone))==refs['torch_grad_mode'],
        'actual CPU torch inference-mode class and factory source')
 request=CompletionRequest(model='qwen36-mxr-eager',prompt=list(range(131)),max_tokens=4,
  temperature=0,top_p=1,n=1,stream=False,ignore_eos=True,return_token_ids=True)
 params=request.to_sampling_params(max_tokens=4)
 fields=('n','temperature','top_p','top_k','min_p','repetition_penalty','frequency_penalty',
  'presence_penalty','max_tokens','min_tokens','ignore_eos','stop','stop_token_ids','bad_words',
  '_bad_words_token_ids','logprobs','prompt_logprobs','logprob_token_ids','structured_outputs',
  'logit_bias','allowed_token_ids','extra_args','thinking_token_budget','repetition_detection')
 values={key:getattr(params,key)for key in fields}
 C.need(type(params)is SamplingParams and request.return_token_ids is True and
        'token_ids'in CompletionResponseChoice.model_fields,'actual HTTP return-token-ID protocol')
 C.need(not torch.npu.is_initialized()and not list(Path('/dev').glob('davinci[0-9]*')),
        'installed metadata inspection remains Devices[] with uninitialized NPU')
 return dict(schema='bole.service-installed-class-protocol-devicefree/v1',source=sr,
  classes=rows,actual_HTTP_sampling_params=values,complete_native_sources_compiled=compiled,
  actual_inference_mode_wrapper_checked=False,actual_torch_context_class_checked=True,
  native_worker_runtime_class_imported=False,native_runner_runtime_class_imported=False,
  actual_runtime_method_guards_required_after_real_load=True,
  NPU=False,actual_model_constructed=False,actual_batch_constructed=False,
  actual_scheduler_executed=False,model_ready=False)

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 value=run(json.loads(a.source_ref))
 if a.output is not None:C.write(a.output,value)
 print(json.dumps(value));return 0

if __name__=='__main__':raise SystemExit(main())
