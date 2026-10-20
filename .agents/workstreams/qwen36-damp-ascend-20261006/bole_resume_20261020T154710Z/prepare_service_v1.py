"""Freeze a new bounded service experiment; never edits the qualified r23 tree."""
from pathlib import Path
import ast,hashlib,json,shutil,subprocess

BASE=Path('/opt/host/vnf/austinov')
TASK=BASE/'model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z'
OLD=BASE/'bole-model-fa64-fp16-20261020T154710Z-r23'
ORIGINAL=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-model-root-repeat-witness-renew24h-v1-20261020-006-repair12-workerledger')
NEW=BASE/'bole-continuous-service-20261020T154710Z-v1'
OUT=BASE/'run-bole-continuous-service-20261020T154710Z-v1'

def ref(p):
 p=Path(p);b=p.read_bytes()
 return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def write(p,value):
 p.write_text(json.dumps(value,sort_keys=True,allow_nan=False)+'\n')

def replace(path,before,after,*,count=1):
 s=path.read_text();assert s.count(before)==count,(str(path),before[:100],s.count(before))
 path.write_text(s.replace(before,after))

def main():
 assert not NEW.exists()and not OUT.exists()
 parent=json.loads((OLD/'SOURCE_BOUND.json').read_bytes())
 shutil.copytree(OLD,NEW,ignore=shutil.ignore_patterns('__pycache__'))
 (NEW/'SOURCE_BOUND.json').rename(NEW/'PARENT_SOURCE_BOUND_R23.json')
 for p in sorted((TASK/'service_v1').glob('*.py')):shutil.copyfile(p,NEW/p.name)
 required={'service_runner.py','consume_service.py','service_client.py','service_bridge.py',
  'service_fia.py','transaction.py','eligibility.py','live_owner.py','host_service.py','service_entry.py'}
 assert all((NEW/n).is_file()for n in required),'complete service implementation before freeze'
 # Legacy host090 and mathematical modules remain exact for their inverse gates.
 for n in ('host090.py','model_entry.py','independent_model.py','oracle112.py','core112.py',
           'adapter.py','treeconv118.py','native_seams.py','worker_entry.py'):
  assert (NEW/n).read_bytes()==(OLD/n).read_bytes(),n
 replace(NEW/'contract090.py',str(BASE/'run-bole-model-fa64-fp16-20261020T154710Z-r23'),str(OUT),count=2)
 replace(NEW/'contract090.py','HTTP_output_tokens=10','HTTP_output_tokens=4')
 replace(NEW/'worker_bootstrap.py',' model_smoke.install(worker,torch,torch_npu,C,source_ref=sr,',
  " if m.get('service_experiment')is not None:\n"+
  "  C.need(os.environ.get('BOLE_CONTINUOUS_SERVICE_ENABLE')=='1','explicit continuous-service opt-in')\n"+
  "  import service_runner\n"+
  "  for name in('service_runner','service_bridge','service_fia','live_owner','transaction','eligibility'):\n"+
  "   module=sys.modules.get(name)\n"+
  "   C.need(module is not None and C.ref(module.__file__)==m['files'][name+'.py'],'exact private service module '+name)\n"+
  "  install=service_runner.install\n"+
  " else:install=model_smoke.install\n"+
  ' install(worker,torch,torch_npu,C,source_ref=sr,')
 replace(NEW/'server090.py'," C.need(str(receipt)==m['model_receipt_root'],'actual guest physical output, not alias')",
  " if m.get('service_experiment')is not None:\n"+
  "  C.need(m['service_experiment']==dict(schema='bole.c1-service-prefix-experiment/v1',prefix=131,max_steps=3,max_output_tokens=4),'exact bounded service scope')\n"+
  "  e['BOLE_CONTINUOUS_SERVICE_ENABLE']='1'\n"+
  " C.need(str(receipt)==m['model_receipt_root'],'actual guest physical output, not alias')")
 m=json.loads((OLD/'SOURCE_TEMPLATE.json').read_bytes())
 m['root']=str(NEW);m['output_root']=str(OUT);m['model_receipt_root']=str(OUT/'dense/receipts')
 m['profile']['HTTP_output_tokens']=4
 m['service_experiment']=dict(schema='bole.c1-service-prefix-experiment/v1',prefix=131,max_steps=3,max_output_tokens=4)
 m['service_activation']=dict(callback='service_runner.install',enable_environment='BOLE_CONTINUOUS_SERVICE_ENABLE',
  first_request_only=True,subsequent_retirement_barrier_native=True,formal_performance=False,
  formal_task_accuracy=False,model_ready=False,actual_scheduler_executed=False)
 evidence=TASK/'service_v1/evidence'
 paths={
  'outputs':('/vllm-workspace/vllm/vllm/v1/outputs.py','outputs.py'),
  'base_proposer':('/vllm-workspace/vllm/vllm/v1/spec_decode/llm_base_proposer.py','base_proposer.py'),
  'sampling_params':('/vllm-workspace/vllm/vllm/sampling_params.py','sampling_params.py'),
  'sampling_metadata':('/vllm-workspace/vllm/vllm/v1/sample/metadata.py','sampling_metadata.py'),
  'gpu_input_batch':('/vllm-workspace/vllm/vllm/v1/worker/gpu_input_batch.py','gpu_input_batch.py'),
  'npu_input_batch':('/vllm-workspace/vllm-ascend/vllm_ascend/worker/npu_input_batch.py','npu_input_batch.py'),
  'completion_protocol':('/vllm-workspace/vllm/vllm/entrypoints/openai/completion/protocol.py','completion_protocol.py'),
  'rotary':('/vllm-workspace/vllm-ascend/vllm_ascend/ops/rotary_embedding.py','rotary_embedding.py'),
  'torch_contextlib':('/usr/local/python3.12.13/lib/python3.12/site-packages/torch/utils/_contextlib.py','torch_contextlib.py'),
  'torch_grad_mode':('/usr/local/python3.12.13/lib/python3.12/site-packages/torch/autograd/grad_mode.py','torch_grad_mode.py')}
 ed=NEW/'evidence/service_runtime';ed.mkdir()
 for p in sorted(evidence.glob('*.py')):shutil.copyfile(p,ed/p.name)
 for key,(actual,name)in paths.items():
  snap=ref(ed/name);m['runtime_sources'][key]=dict(snap,path=actual)
 m['service_runtime_source_snapshots']={k:ref(ed/n)for k,(_,n)in paths.items()}
 # Extend exact predecessor inverse ledger to every modified legacy file.
 original=json.loads((ORIGINAL/'SOURCE_TEMPLATE.json').read_bytes());ledger={}
 for name,r in original['files'].items():
  if r['path'].startswith(str(ORIGINAL)+'/')and(NEW/name).is_file():
   before=Path(r['path']).read_text();after=(NEW/name).read_text()
   if before!=after:ledger[name]=dict(before=ref(r['path']),after=ref(NEW/name),edits=[dict(before=before,after=after)])
 write(NEW/'FA_BOUNDARY_EDITS_R14.json',ledger)
 for name,r in list(m['files'].items()):
  if r['path'].startswith(str(OLD)+'/'):m['files'][name]=ref(NEW/name)
 added=[]
 for p in sorted((TASK/'service_v1').glob('*.py')):
  m['files'][p.name]=ref(NEW/p.name);added.append(p.name)
 for p in sorted(ed.glob('*.py')):m['files'][str(p.relative_to(NEW))]=ref(p)
 for i,r in enumerate(m['dependencies']):
  if r['path'].startswith(str(OLD)+'/'):m['dependencies'][i]=ref(NEW/Path(r['path']).relative_to(OLD))
 m['dependencies'] += [ref(OLD/'SOURCE_BOUND.json'),ref(TASK/'AUDIT_R23.json'),ref(TASK/'MODEL_R23_STAGE.json')]
 m['service_predecessor']=dict(source=ref(OLD/'SOURCE_BOUND.json'),audit=ref(TASK/'AUDIT_R23.json'),
  original_bounds_unchanged=True,native_AR_replay_not_substituted_for_new_service_prefixes=True,
  changed_existing=[n for n in m['files']if(OLD/n).is_file()and(NEW/n).read_bytes()!=(OLD/n).read_bytes()],added=added)
 m['service_required_sameimage_software_cases']=sum(
  1 for p in NEW.glob('test*.py')for n in ast.walk(ast.parse(p.read_bytes()))
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))and n.name.startswith('test_'))
 # Test discovery is the real execution; AST count is a frozen completeness expectation.
 for p in NEW.rglob('*.py'):ast.parse(p.read_bytes(),filename=str(p))
 write(NEW/'SOURCE_TEMPLATE.json',m);write(NEW/'SOURCE.json',m)
 commands=json.loads((OLD/'COMMANDS.json').read_bytes())
 def convert(v):
  if type(v)is str:return v.replace(str(OLD),str(NEW)).replace(str(BASE/'run-bole-model-fa64-fp16-20261020T154710Z-r23'),str(OUT))
  if type(v)is list:return[convert(x)for x in v]
  if type(v)is dict:return{k:convert(x)for k,x in v.items()}
  return v
 commands=convert(commands);commands['source']=ref(NEW/'SOURCE_TEMPLATE.json')
 commands['bind'][commands['bind'].index('--reviewed-template-ref')+1]=json.dumps(commands['source'])
 commands['legacy_entrypoints_retained_for_inverse_tests_only']=True
 commands['service_required_sameimage_software_cases']=m['service_required_sameimage_software_cases']
 write(NEW/'COMMANDS.json',commands)
 q=subprocess.run(['/usr/bin/python3','-I','-B',str(NEW/'bind_model.py'),'--execute',
  '--reviewed-template-ref',json.dumps(commands['source']),'--component-refs-json',json.dumps(parent['component_refs'])],
  cwd=NEW,capture_output=True,text=True,timeout=25)
 print('BIND',q.returncode,q.stdout,q.stderr);assert q.returncode==0
 sr=ref(NEW/'SOURCE_BOUND.json')
 commands['service_source']=sr
 for key,extra,output in(('service_model',[],str(OUT)),('service_CPU',['--cpu-only'],str(OUT)+'-CPU')):
  commands[key]=['/usr/bin/python3','-I','-B',str(NEW/'host_service.py'),'--execute',*extra,
   '--source-ref',json.dumps(sr),'--output',output]
 write(NEW/'COMMANDS.json',commands)
 write(TASK/'SERVICE_V1_FREEZE.json',dict(source=sr,output=str(OUT),tests=m['service_required_sameimage_software_cases'],
  changed_existing=m['service_predecessor']['changed_existing'],added=added,prepared=True,
  actual_scheduler_executed=False,model_ready=False,final_success=False))
 print('SOURCE_REF',json.dumps(sr))

if __name__=='__main__':main()
