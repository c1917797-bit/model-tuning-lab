"""Complete prospective BOLE current runtime closure composition; no approval/device execution."""
import argparse,ast,copy,hashlib,json,os,sys,types
from pathlib import Path
from contextlib import contextmanager
WORK=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
PREP=WORK/'bole2k_runtime_complete_prepare_v4'
OUT=Path("/opt/host/vnf/austinov/run-bole2k-short8-runtime-v4")
# Filled only after MAIN reads the stable independent implementations.
PINS={"parent":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_2k_joint_composition_prepare_v1/joint_blueprint.py","bytes":6540,"sha256":"e9ed51c440073cae3cc0cb776fb2226995911ac39bda9432f3a2b73ee652c52c"},"joint_renderer":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/runtime_joint_budget_v2_prepare_v1/render_budget_v2.py","bytes":6240,"sha256":"3a20eec06d524ce7e908c255caa77e4d2c581f78cd19a755869a3fa8bfefcaa2"},"resource":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/runtime_joint_budget_v2_prepare_v1/worker_resource_v2.py","bytes":12478,"sha256":"16694f7472c09d5d186f928e3ff5f23203ef06caa5b17d69d997de19d758c452"},"admission_renderer":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/runtime_admission_2k_prepare_v1/render_runtime_admission.py","bytes":6768,"sha256":"a2e8fc448e7b169ff1e5cb3254e9f5a25393329425d52cb48df1ddc269cc68e3"},"admission_helper":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/runtime_admission_2k_prepare_v1/runtime_admission_2k.py","bytes":9171,"sha256":"e67fc1b356fe71326ec1785edb95698d36c6a10fed9fd39e54856e85ed94beb5"},"test_renderer":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/short2k_software_domain_repair_v1/render_software_domain.py","bytes":7534,"sha256":"143d39cc8a274012c377cdbd1b3cf89f8a8981cb82bf89f4d71c2200f8325959"},"terminal_renderer":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/ram_terminal_join_prepare_v1/render_ram_terminal.py","bytes":2831,"sha256":"68e39e2e12a93f8ba1be129074045483db2a0f756f13ffefecdcede8be322aff"},"terminal_helper":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/ram_terminal_join_prepare_v1/ram_terminal_join.py","bytes":6354,"sha256":"a7f6e0b4e7966b3ce65f6f52ebb215c3b93485761b061ff336ed95c5d7a8d317"},"guest_coverage":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_mount_coverage_prepare_v2/coverage_v2.py","bytes":16488,"sha256":"e52e0817385e1c7a9c84c27cfe7fa5f7e067dd157b4ab1cbeacf55c27bc5a0d4"},"command_renderer":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/runtime_command_ref_normalization_prepare_v1/command_ref_delta.py","bytes":4151,"sha256":"a059be4aa80df56d088f95b45b20e1f5297a397489993429f4c4f45604bea2e4"}}
def need(v,s):
 if not v:raise ValueError(s)
def ref(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 p=Path(r['path']);need(p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary exact final composition asset')
 b=p.read_bytes();need(ref(p,b)==r,'independent stable source pin '+str(p));return b
def once(s,a,b):
 need(s.count(a)==1,'one exact final integration seam '+a[:100]);return s.replace(a,b,1)
@contextmanager
def isolated():
 mods=dict(sys.modules);paths=list(sys.path)
 try:yield
 finally:sys.modules.clear();sys.modules.update(mods);sys.path[:]=paths
def module(b,p,n):
 ns={'__file__':str(p),'__name__':n};exec(compile(b,str(p),'exec'),ns);return ns
def assets():
 need(set(PINS)=={'parent','joint_renderer','resource','admission_renderer','admission_helper','test_renderer','terminal_renderer','terminal_helper','guest_coverage','command_renderer'},'all reviewed stable integration assets required')
 raw={k:checked(r)for k,r in PINS.items()}
 mods={k:module(raw[k],PINS[k]['path'],'_complete_'+k)for k in('parent','joint_renderer','admission_renderer','test_renderer','terminal_renderer','command_renderer')}
 return mods,raw
def assigned_string(s,name,old,new):
 a=ast.parse(s);nodes=[n for n in a.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets)]
 need(len(nodes)==1 and isinstance(nodes[0].value,ast.Constant)and nodes[0].value.value==old,'exact original owning output constant '+name)
 v=nodes[0].value;lines=s.splitlines(keepends=True);text=''.join(lines[v.lineno-1:v.end_lineno])
 need(v.lineno==v.end_lineno,'single owning output literal')
 line=lines[v.lineno-1];lines[v.lineno-1]=line[:v.col_offset]+repr(new)+line[v.end_col_offset:]
 return ''.join(lines)
def render(*,base_root=None,permit_materialized=True,parent_pair_preparation_root=None,
 historical_short_source_ref=None,authority_ref=None,parent_preparation_readset=None):
 with isolated():
  mods,raw=assets();JP=mods['parent'];base=PREP if base_root is None else Path(base_root)
  need(base==PREP,'one explicit final preparation/source scope')
  parent=JP['render'](base_root=base,permit_materialized=permit_materialized,
   parent_pair_preparation_root=parent_pair_preparation_root,historical_short_source_ref=historical_short_source_ref,
   authority_ref=authority_ref,parent_preparation_readset=parent_preparation_readset)
  need(len(parent['files'])==427,'complete actual427 predecessor')
  files,joint_delta=mods['joint_renderer']['adapt'](parent['files'])
  need(mods['joint_renderer']['inverse'](files,joint_delta)==parent['files'],'exact entire jointv2 inverse')
  need(files['worker_resource_v2.py']==raw['resource'],'exact independently reviewed resource helper')
  ram=types.ModuleType('worker_resource_v2');ram.__file__=str(PINS['resource']['path'])
  sys.modules['worker_resource_v2']=ram
  exec(compile(raw['resource'],ram.__file__,'exec'),ram.__dict__)
  joint=module(files['runtime_joint_ledger.py'],Path(parent['manifest']['root'])/'runtime_joint_ledger.py','_complete_actual_derived_J_v2')
  admission=mods['admission_renderer']['adapt'](files);admission_parent=files;files=admission['files']
  need(mods['admission_renderer']['inverse'](admission)==admission_parent,'exact entire strong-object admission inverse')
  test_parent=files;files,test_delta=mods['test_renderer']['adapt'](files)
  need(mods['test_renderer']['inverse'](files,test_delta)==test_parent,'exact entire2k test-domain inverse')
  terminal_parent=files;files,terminal_delta=mods['terminal_renderer']['adapt'](files)
  need(mods['terminal_renderer']['inverse'](files,terminal_delta)==terminal_parent,'exact entire saved RAM terminal inverse')
  need(files['ram_terminal_join.py']==raw['terminal_helper'],'exact independent RAM terminal helper')
  before_final=dict(files);files=dict(files)
  selfraw=(PREP/'complete_runtime_blueprint.py').read_bytes()
  need('complete_runtime_blueprint.py'not in files,'fresh complete reconstruction helper only')
  files['complete_runtime_blueprint.py']=selfraw
  need('guest_readset_coverage.py'not in files,'new independent guest coverage helper')
  files['guest_readset_coverage.py']=raw['guest_coverage']
  files['command_contract.py']=mods['command_renderer']['adapt'](files['command_contract.py'])
  s=files['qualification_source_validate.py'].decode()
  s=once(s,"    import joint_blueprint as JP","    import joint_blueprint as JP\n    read_ref(m['files']['complete_runtime_blueprint.py'])\n    import complete_runtime_blueprint as CP\n    need(C.ref(CP.__file__)==m['files']['complete_runtime_blueprint.py'],'actual complete runtime source-owned reconstruction')")
  s=once(s,'    expected=JP.render(','    expected=CP.render(')
  s=once(s,'    JP.inverse(expected)','    CP.inverse(expected)')
  files['qualification_source_validate.py']=s.encode()
  s=files['qualification_source_producer.py'].decode()
  need(s.count('    import qualification_short_prepare as Q')==2,'two actual producer reconstruction paths')
  s=s.replace('    import qualification_short_prepare as Q','    import complete_runtime_blueprint as Q')
  files['qualification_source_producer.py']=s.encode()
  # The real guest reads authority/review through the independently validated
  # complete closure. The old host discarded that closure before create().
  s=files['host_service.py'].decode()
  helper="""def complete_readset(C,original,proof,sr):
 C.need(proof['schema']=='bole.followup-whole-source-validation/v1'and proof['source']==sr and proof['source_validated']is True,'actual independent full source proof')
 import guest_readset_coverage as GC
 required=GC.required(C,sr,original)
 # required() hashes each unique real source/control Ref once in this phase.
 # Add its actual transitive17 missing files to the producer, not just a gate.
 unique={r['path']:r for r in required}
 verified=set(unique)
 for r in [*original,*proof['readset']]:
  C.need(r['path']not in unique or unique[r['path']]==r,'unambiguous complete mounted source/control Ref')
  unique[r['path']]=r
 for path,r in unique.items():
  if path not in verified:C.checked(r)
 GC.index_coverage(required,unique)
 return list(unique.values())
"""
  s=once(s,'def client_terminal(c,ctl,tokens,handled):',helper+'def client_terminal(c,ctl,tokens,handled):')
  s=once(s,"readset=bind_model.readset(sr)+m['dependencies']+command_contract.validate(C,sr,m)",
     "readset=complete_readset(C,bind_model.readset(sr)+m['dependencies']+command_contract.validate(C,sr,m),_g3_source_proof,sr)")
  files['host_service.py']=s.encode()
  s=files['owned_create.py'].decode()
  s=once(s," ctl.expected=dict(cid=None,name=ctl.name,image=c.IMAGE,arm=role,source=sr,",
   " import contract090 as C,guest_readset_coverage as GC\n required=GC.required(C,sr,readset)\n precoverage=GC.mount_coverage(C,required,mounts,source_root)\n c.write(leaf/'MOUNT_COVERAGE_PRECREATE.json',dict(source=sr,coverage=precoverage))\n ctl.expected=dict(cid=None,name=ctl.name,image=c.IMAGE,arm=role,source=sr,")
  s=once(s," x,ref=ctl.inspect()\n if x['State']['Running']",
   " x,ref=ctl.inspect()\n actualcoverage=GC.mount_coverage(C,required,x['Mounts'],source_root)\n c.write(leaf/'MOUNT_COVERAGE_ACTUAL.json',dict(source=sr,coverage=actualcoverage,inspect=ref))\n if x['State']['Running']")
  files['owned_create.py']=s.encode()
  m=copy.deepcopy(parent['manifest']);old_output=m['output_root']
  s=files['contract090.py'].decode()
  s=assigned_string(s,'OUTPUT_POSIX',old_output,str(OUT))
  s=assigned_string(s,'CPU_OUTPUT_POSIX',old_output+'-CPU',str(OUT)+'-CPU')
  files['contract090.py']=s.encode()
  def outputs(x):
   if type(x)is str:
    return str(OUT)+x[len(old_output):]if x==old_output or x.startswith(old_output+'/')or x==old_output+'-CPU'or x.startswith(old_output+'-CPU/')else x
   if type(x)is dict:return{k:outputs(v)for k,v in x.items()}
   if type(x)is list:return[outputs(v)for v in x]
   return x
  m=outputs(m)
  m=JP['assets']()[0]['rebase'](m,files)
  m['runtime_joint_capture_ledger']=copy.deepcopy(joint['CONTRACT'])
  m['short2k_helper_refs'].update({'complete_runtime_'+k:dict(r)for k,r in PINS.items()})
  m['short2k_helper_refs']['complete_runtime_program']=ref(PREP/'complete_runtime_blueprint.py',selfraw)
  paths={r['path']:r for r in m['dependencies']}
  for r in[*m['short2k_helper_refs'].values(),*m['files'].values()]:
   need(r['path']not in paths or paths[r['path']]==r,'unambiguous complete stable runtime dependency');paths[r['path']]=r
  m['dependencies']=list(paths.values())
  m['complete_runtime_2k']=dict(schema='bole.complete-runtime2k-short8/v1',input_tokens=2048,output_tokens=8,
   synthetic_screening_only=True,no_general_gain_claim=True,actual_NPU_qualified=False,
   runtime_resource_fit_measured=False,whole_model_pass=False,formal_performance=False,task_accuracy=False)
  for n,b in files.items():
   if n.endswith('.py'):compile(b,n,'exec')
  inverse_delta={n:dict(before=parent['manifest']['files'].get(n),after=m['files'][n])
   for n,b in files.items()if parent['files'].get(n)!=b}
  return dict(manifest=m,files=files,parent=parent,joint_delta=joint_delta,inverse_delta=inverse_delta,
   admission=admission,test_delta=test_delta,terminal_delta=terminal_delta,before_final=before_final,after_final=dict(files),
   source_bound=False,actual_bound_validated=False,numerical_qualified=False,NPU=False)
def inverse(bundle):
 with isolated():
  mods,_=assets();actual=dict(bundle['files']);before=bundle['before_final']
  need(actual==bundle['after_final'],'complete final source bytes unchanged before inverse')
  changed={n for n in set(actual)|set(before)if actual.get(n)!=before.get(n)}
  need(changed=={'complete_runtime_blueprint.py','qualification_source_validate.py','qualification_source_producer.py','contract090.py','host_service.py','owned_create.py','guest_readset_coverage.py','command_contract.py'},'exact complete owning-integration delta')
  for n in changed:
   if n in before:actual[n]=before[n]
   else:actual.pop(n)
  need(actual==before,'complete pre-final map restored')
  actual=mods['terminal_renderer']['inverse'](actual,bundle['terminal_delta'])
  actual=mods['test_renderer']['inverse'](actual,bundle['test_delta'])
  actual=mods['admission_renderer']['inverse'](dict(bundle['admission'],files=actual))
  actual=mods['joint_renderer']['inverse'](actual,bundle['joint_delta'])
  need(actual==bundle['parent']['files'],'all427 exact parent bytes restored')
  mods['parent']['inverse'](dict(bundle['parent'],files=actual))
  return actual
def write_json(path,value):
 raw=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
 with Path(path).open('xb')as out:out.write(raw);out.flush();os.fsync(out.fileno())
 return ref(path,raw)
def materialize(authority_ref):
 need(authority_ref is not None,'separate actual MAIN authority required; this program creates none')
 checked(authority_ref)
 need(PREP.is_dir()and not any(p.is_symlink()for p in(PREP,*PREP.parents))and not OUT.exists(),
  'ordinary own preparation and fresh external experiment output')
 b=render(base_root=PREP,permit_materialized=False,authority_ref=authority_ref)
 inverse(b);root=Path(b['manifest']['root'])
 need(root==PREP/'prepared-source-short8-qualifier'and not root.exists(),'one fresh derived source root')
 root.mkdir(mode=0o700)
 for name,raw in b['files'].items():
  path=root/name
  need(root in path.parents and '..'not in Path(name).parts,'exact contained generated source file')
  path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
  with path.open('xb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
 template=write_json(root/'SOURCE_TEMPLATE.json',b['manifest'])
 ledger=write_json(root/'SOURCE_DELTA.json',b['inverse_delta'])
 fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:os.fsync(fd)
 finally:os.close(fd)
 return dict(prepared_template=template,inverse_delta=ledger,source_bound=False,authority_created=False,NPU=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False)
 g=p.add_mutually_exclusive_group();g.add_argument('--check',action='store_true');g.add_argument('--materialize',action='store_true')
 p.add_argument('--authority-ref');a=p.parse_args()
 if not(a.check or a.materialize):
  need(a.authority_ref is None,'mode required for authority operand')
  print('{"enabled":false,"NPU":false,"source_bound":false}');return
 if a.check:
  need(a.authority_ref is None,'source check issues no authority')
  b=render();inverse(b);json.dumps(b['inverse_delta'],allow_nan=False)
  print(json.dumps(dict(files=len(b['files']),compiled=sum(n.endswith('.py')for n in b['files']),
   whole_inverse=True,serializable_inverse=True,source_bound=False,numerical_qualified=False,NPU=False)))
 else:
  need(a.authority_ref is not None,'actual independently reviewed authority operand')
  print(json.dumps(materialize(json.loads(a.authority_ref)),sort_keys=True))
if __name__=='__main__':main()
