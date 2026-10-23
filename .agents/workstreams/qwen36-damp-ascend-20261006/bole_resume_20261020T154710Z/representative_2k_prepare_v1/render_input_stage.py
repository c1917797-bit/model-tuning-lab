"""Exact component-only2k derivative of both existing arms. No complete source/admission."""
import ast,copy,hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT_LINEAGE={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_bound_lineage_prepare_v1/strict_bound_lineage.py","bytes":19746,"sha256":"6a48299188efb5b77da9b9ffd9b3c486922fa8dbc4849abbc4a92262c9aeb134"}
INPUT_COMPONENT_PINS={
  "service_client.py": {
    "bytes": 3080,
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/service_client.py",
    "sha256": "8ac77e09701558ec77928a2c42bdace68bbe8881fb6b4a271409d7b9e4e0481f"
  },
  "input_identity.py": {
    "bytes": 3407,
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/input_identity.py",
    "sha256": "c966413cb66589aa9b8f17a3a35c35657d6fee7a3ddabae2e755430f2ddfa8ea"
  },
  "bole_performance_profile.py": {
    "bytes": 4974,
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/bole_performance_profile.py",
    "sha256": "e046c1c48b02b8c8a701f15dc90c5bf162db652921eeeae1aa2f7558c451fdbd"
  },
  "performance_service_client.py": {
    "bytes": 8049,
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/performance_service_client.py",
    "sha256": "76c43c097eeffb40fdd593127b1c73649602ee7be2bffc28d512863f5bcbca34"
  },
  "strict_token_timing.py": {
    "bytes": 5679,
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/strict_token_timing.py",
    "sha256": "c84ac3234d01473acd9afebf2e15865b201e344fb39776a442fc68e37186225b"
  },
  "formal_token_client.py": {
    "bytes": 6235,
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/formal_token_client.py",
    "sha256": "a0b0c0ac946c62147c12c953338a144a9eac26df3de0de0b4ebc7f07fd596827"
  },
  "formal_token_reader.py": {
    "bytes": 13012,
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/formal_token_reader.py",
    "sha256": "a91770c2c87e05e3b5999cfa5be0ca7c3b957ed6c8e374b5f0265cc1ee06978c"
  },
  "performance_client_consumer.py": {
    "bytes": 4390,
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/performance_client_consumer.py",
    "sha256": "b21d5e0249de8ecc4936331a4e200cbbb318c50fccd4b3e0e0600c72ed7f7a1f"
  },
  "performance_host.py": {
    "bytes": 6751,
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/performance_host.py",
    "sha256": "33ed773aded0bf516b0a90abd960883bbdac452530d36a48a14a480bd5933500"
  }
}
EXPECTED_COUNTS={"service_client.py":4,"input_identity.py":6,"bole_performance_profile.py":3,"performance_service_client.py":3,"strict_token_timing.py":2,"formal_token_client.py":3,"formal_token_reader.py":4,"performance_client_consumer.py":1,"performance_host.py":1}
MESSAGE_DELTAS={"input_identity.py":[["exact actual131-token prompt, not string length","exact actual2048-token prompt, not string length"]],"bole_performance_profile.py":[["only reviewed C1/131/1024, two-generation scope","only declared C1/2048/1024, two-generation input-stage scope"]],"formal_token_client.py":[["Fixed131/input1024-output SSE observer.","Fixed2048/input1024-output SSE observer."],["actual131 tokenizer IDs required by future owner","actual2048 tokenizer IDs required by future owner"]],"formal_token_reader.py":[["complete131 actual input IDs","complete2048 actual input IDs"],["actual full usage, no 2048 or character count","exact2048/1024/3072 token usage, not character count"]]}
def need(v,s):
 if not v:raise ValueError(s)
def refbytes(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary frozen component Ref')
 b=p.read_bytes();need(refbytes(p,b)==r,'whole exact input component Ref');return b
def parent():
 raw=checked(PARENT_LINEAGE);spec=importlib.util.spec_from_file_location('_reviewed_representative_parent',PARENT_LINEAGE['path'])
 m=importlib.util.module_from_spec(spec);exec(compile(raw,PARENT_LINEAGE['path'],'exec'),m.__dict__);return m
def literal_delta(raw,values,*,expected_count):
 text=raw.decode();lines=text.splitlines(keepends=True);offset=[];n=0
 for line in lines:offset.append(n);n+=len(line)
 edits=[]
 for node in ast.walk(ast.parse(text)):
  if isinstance(node,ast.Constant)and type(node.value)is int and node.value in values:
   start=offset[node.lineno-1]+node.col_offset;end=offset[node.end_lineno-1]+node.end_col_offset
   edits.append((start,end,str(values[node.value])))
 need(type(expected_count)is int and len(edits)==expected_count,'exact reviewed numeric input ABI edit count')
 for start,end,value in sorted(edits,reverse=True):text=text[:start]+value+text[end:]
 compile(text,'exact-input-component','exec')
 return text.encode(),len(edits)
def render(base=None):
 base=HERE/'prospective-input-components'if base is None else Path(base)
 L=parent()
 with L.renderer_modules()as modules:
  b=modules['render_strict_timing'].render(base,permit_materialized=True)
 for arm,part in b['arms'].items():
  old=copy.deepcopy(part);files=dict(part['files']);m=copy.deepcopy(part['manifest']);ledger={}
  for n,pin in INPUT_COMPONENT_PINS.items():
   need(len(files[n])==pin['bytes']and hashlib.sha256(files[n]).hexdigest()==pin['sha256'],'same exact reviewed131 component source '+n)
   values={131:2048}
   if n in('strict_token_timing.py','formal_token_reader.py'):values[1155]=3072
   new,count=literal_delta(files[n],values,expected_count=EXPECTED_COUNTS[n])
   for before,after in MESSAGE_DELTAS.get(n,[]):
    text=new.decode();need(text.count(before)==1,'one exact diagnostic message delta')
    new=text.replace(before,after,1).encode()
   if n in('formal_token_client.py','service_client.py'):
    text=new.decode();needle="'Explain how trees grow. '*256"
    need(text.count(needle)==1,'one exact131 input recipe')
    new=text.replace(needle,"'Explain how trees grow. '*1024",1).encode()
   files[n]=new;ledger[n]=dict(before=old['manifest']['files'][n],after=refbytes(Path(m['root'])/n,new),changed_input_literals=count)
  files['representative_input_contract.py']=(HERE/'representative_input_contract.py').read_bytes()
  # These common client/profile fields are a partial stage, not a full model
  # manifest. Remaining131 allocator/math/state/authority gates are unchanged.
  m=L.rebind(m,files)
  m['performance_profile']['scope']['input_tokens']=2048
  m['performance_client_contract']['input_tokens']=2048
  m['representative_input_stage']=dict(input_tokens=2048,output_tokens=1024,source_complete=False,
    native_prefill_qualified=False,attention_state_qualified=False,joint_raw_budget_fit=False,
    input_recipe=dict(text='Explain how trees grow. ',repeat=1024,add_special_tokens=False,take_first_tokens=2048),
    partial_components_only=True)
  m['workload_acceptance_pending']=True # user selected2k; actual frozen token/input Ref still pending
  m['workload_acceptance_ref']=None
  m['performance_ready']=False;m['numerical_qualified']=False
  for n,raw in files.items():
   if n.endswith('.py'):compile(raw,n,'exec')
  restored=dict(files);restored.pop('representative_input_contract.py')
  for n in ledger:restored[n]=old['files'][n]
  need(restored==old['files'],'exact whole original131 byte inverse; no old source edited')
  part.update(files=files,manifest=m,input_inverse=ledger,parent131=old)
 for n in INPUT_COMPONENT_PINS:
  need(b['arms']['native_ar']['files'][n]==b['arms']['bole']['files'][n],'identical2k input/identity/timing change both arms '+n)
 b.update(source_complete=False,source_bound=False,execution_ready=False,NPU=False,formal_performance=False,
  blocked=['native-only actual2048 prefill allocation/table/identity evidence',
   'cache_registry/fa_prefill/g2_state/independent_attention131 geometry',
   'model_entry initial domain and1536 single-physical-block private3 geometry',
   'real2k short8 independent NPU numerical/state/HTTP and joint raw budget',
   'real2k native24/private25 separation/state consumer/whole source renderer/authority',
   '2k threepair consumer/source-bound native worker proof'])
 return b
def main():
 import argparse
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--review',action='store_true');a=p.parse_args()
 if not a.review:print('{"enabled":false,"source_complete":false,"NPU":false}');return
 b=render();print(json.dumps(dict(arms={a:dict(changed=list(p['input_inverse']),new_input=2048,output=1024)for a,p in b['arms'].items()},
  blocked=b['blocked'],source_complete=False,execution_ready=False,formal_performance=False,NPU=False)))
if __name__=='__main__':main()
