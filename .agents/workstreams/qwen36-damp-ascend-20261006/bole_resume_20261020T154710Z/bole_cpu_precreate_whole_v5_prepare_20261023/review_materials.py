"""Generate unapproved exact V5 review operands; no source binding or owner."""
import ast,hashlib,importlib.util,json,os,resource,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
def need(v,label):
 if not v:raise ValueError(label)
def ref(path,raw=None):
 p=Path(path);raw=p.read_bytes()if raw is None else raw
 return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def write(name,value):
 raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
 with(HERE/name).open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
 return ref(HERE/name,raw)
def main():
 need(144 in os.sched_getaffinity(0),'fresh MAIN-reserved CPU144 must be available')
 os.sched_setaffinity(0,{144})
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
 resource.setrlimit(resource.RLIMIT_CPU,(175,175))
 names=['REVIEW_OPERANDS_ONLY.json','FILE_TABLE.json','SOURCE_DELTA_AND_PRESERVATION.json','BINDING_CONTRACT.json']
 need(all(not(HERE/n).exists()for n in names),'exclusive fresh materials only')
 S=load(HERE/'runtime_lossless_imports.py','_V5review_exact_renderer')
 b=S.render();S.inverse(b);m=b['manifest']
 need(m['qualification_authority_ref']is None,'no authority fabricated')
 need(m['root']==str(HERE/'prepared-source-short8-v5'),'exact new source root')
 need(not Path(m['root']).exists(),'unmaterialized source preserved')
 files={}
 for n,raw in b['files'].items():
  need(m['files'][n]==ref(Path(m['root'])/n,raw),'exact real file operand '+n)
  files[n]=m['files'][n]
 need(len(files)==458,'actual458sourcefiles')
 scope_nodes=[n.value for n in ast.parse(b['files']['qualification_source_validate.py']).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='SCOPE'for t in n.targets)]
 need(len(scope_nodes)==1,'actual same-source FSV SCOPE definition')
 scope=eval(compile(ast.Expression(scope_nodes[0]),'<same-source-FSV-SCOPE>','eval'),{'__builtins__':{},'dict':dict})
 need(type(scope)is dict,'literal source-owned FSV SCOPE')
 helpers={n:ref(HERE/n)for n in ['runtime_lossless_imports.py','cpu_release_policy.py','cpu_precreate_policy.py','adapt_cpu_precreate.py']}
 protected=['resources','input_resource_profile32k','fastpath_numeric_qualification','runtime_joint_capture_ledger','fa_lossless_capture','short_state_digest_profile','profile','service_experiment','performance_profile','performance_client_contract','native_speculative_config','common']
 F=load(HERE/'formal_runtime.py','formal_composer');P=load(HERE/'short8_source_pin.py','_V5review_pin')
 D=F.module(F.DELTA,'_V5review_original_delta');old_m,old_files=D.parent()
 changed=P.unchanged(old_files,b['files'],old_m,m)
 parent=b['parent']['manifest']['files']
 for n,raw in b['parent']['files'].items():need(parent[n]==ref(Path(b['parent']['manifest']['root'])/n,raw),'exact immediate parent file '+n)
 file_table=write('FILE_TABLE.json',dict(schema='bole.V5-exact-file-table/v1',source_root=m['root'],files=files,source_materialized=False))
 preservation=write('SOURCE_DELTA_AND_PRESERVATION.json',dict(schema='bole.V5-source-preservation/v1',original_source=F.DELTA,parent_source_root=old_m['root'],parent_files=parent,changed_files=changed,complete_inverse=True,original_source_gate_unchanged=True,protected_contracts_equal={k:P.normalized(old_m[k],old_m)==P.normalized(m[k],m)for k in protected},cpu_precreate_intent=m['cpu_precreate_intent'],deviceless_cpu_release=m['deviceless_cpu_release'],helperRefs=helpers,math_qualification=False,NPU=False))
 binding=write('BINDING_CONTRACT.json',dict(schema='bole.V5-unapproved-binding-contract/v1',source_root=m['root'],output_root=m['output_root'],source_template_path=str(Path(m['root'])/'SOURCE_TEMPLATE.json'),source_bound_path=str(Path(m['root'])/'SOURCE_BOUND.json'),authority_ref=None,approved=False,source_materialized=False,window_cutoff_epoch=1792827353,source_owned_producer='qualification_source_producer.py',prepare_argv=['/usr/bin/python3','-I','-B',str(HERE/'runtime_lossless_imports.py'),'--prepare','--authority-ref','<MAIN_ACTUAL_AUTHORITY_REF3>'],bind_argv=['/usr/bin/python3','-I','-B',str(Path(m['root'])/'qualification_source_producer.py'),'--bind','--template-ref','<ACTUAL_SOURCE_TEMPLATE_REF3>'],execution_commands='source-owned COMMANDS.json only after actual MAIN review and bind',NPU=False))
 operands=dict(scope=scope,source_root=m['root'],output_root=m['output_root'],files=files,parent_preparation_readset=m['qualification_parent_preparation_readset'],historical_short_source=m['qualification_historical_short_source'],short2k_helper_refs=m['short2k_helper_refs'])
 review=write('REVIEW_OPERANDS_ONLY.json',operands)
 print(json.dumps(dict(approved=False,authority=None,files=len(files),source_root=m['root'],output_root=m['output_root'],materials=[review,file_table,preservation,binding],affinity=sorted(os.sched_getaffinity(0)),NPU=False)))
if __name__=='__main__':main()
