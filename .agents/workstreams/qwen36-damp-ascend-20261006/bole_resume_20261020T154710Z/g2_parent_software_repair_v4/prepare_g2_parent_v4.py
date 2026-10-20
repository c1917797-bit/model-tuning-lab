"""Fresh G2-v4 software-envelope repair only; failed-v3 and original math stay immutable."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

FAILED_SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v3/SOURCE_BOUND.json',bytes=220181,sha256='91002bf0dbda04826db5a1c4d3264b36da0bfaf4f4464feb50ce8ee05435c874')
FAILED_OWNER=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v3-CPU/RESULT.json',bytes=240698,sha256='2835f03e31170405c093f900b0d02d3518bffba042e50f2442cb64bda6c6fe96')
OVERLAY=('service_entry.py','parent_software_output.py','test_g2_parent_output.py','prepare_g2_parent_v4.py')


def need(value,message):
 if not value:raise ValueError(message)

def ref(path):
 p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary exact absolute file')
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def obj(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'exact input Ref3');return json.loads(Path(r['path']).read_bytes())

def write(path,value):
 with Path(path).open('x')as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n')

def replace(path,value):
 if path.exists():path.unlink()
 write(path,value)

def unique(refs):
 by_path={}
 for r in refs:
  need(ref(r['path'])==r,'actual prerequisite Ref3');need(r['path']not in by_path or by_path[r['path']]==r,'no conflicting exact prerequisite');by_path[r['path']]=r
 return list(by_path.values())

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def inventory(overlay,name,advisory):
 need(Path(name).name==name and Path(advisory['path']).name==name,'flat reviewed overlay filename')
 actual=ref(Path(overlay)/name)
 need(all(actual[k]==advisory[k]for k in('bytes','sha256')),'reviewed exact bytes/SHA; advisory path is lineage only '+name)
 return actual

def outputs(text,output):
 tree=ast.parse(text)
 for name,value in(('OUTPUT_POSIX',output),('CPU_OUTPUT_POSIX',output+'-CPU')):
  nodes=[n for n in tree.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id==name]
  need(len(nodes)==1 and isinstance(nodes[0].value,ast.Constant)and type(nodes[0].value.value)is str,'exact output assignment')
  segment=ast.get_source_segment(text,nodes[0]);text=text.replace(segment,name+'='+repr(value),1);tree=ast.parse(text)
 return text

# READSET_PROGRAM is the exact generic corrected source-owned collector from
# the separately reviewed v4 audit; old contracts themselves remain unchanged.
READSET_PROGRAM = r'''
import hashlib,json,re,sys
from pathlib import Path

def need(v,s):
 if not v:raise ValueError(s)
def actual(path):
 p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),"ordinary absolute file/no symlink")
 before=p.stat();h=hashlib.sha256();size=0
 with p.open('rb')as f:
  for block in iter(lambda:f.read(2**20),b''):h.update(block);size+=len(block)
 after=p.stat();need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)and size==after.st_size,"stable file read")
 return dict(path=str(p),bytes=size,sha256=h.hexdigest())
def check(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['path'])is str and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and re.fullmatch('[0-9a-f]{64}',r['sha256']),"exact typed Ref3")
 need(actual(r['path'])==r,"exact supplied path/bytes/SHA before any import")
 return Path(r['path'])
provided=json.loads(sys.argv[1]);raw=check(provided).read_bytes();m=json.loads(raw)
root=Path(m['root']);need(root.is_absolute()and root==Path(provided['path']).parent,"source Ref is its exact owned root")
for name,r in m['files'].items():
 need(Path(r['path'])==root/name,"exact source-owned file operand");check(r)
for name in('sourceio.py','bind_model.py','command_contract.py'):need(name in m['files'],"explicit source-owned audit helper pin")
sys.path.insert(0,str(root))
import sourceio as C,bind_model as B,command_contract as CC
for name,module in(('sourceio.py',C),('bind_model.py',B),('command_contract.py',CC)):
 need(actual(module.__file__)==m['files'][name],"imported exact original source-owned helper")
C.checked(provided)
sr=C.ref(provided['path'])
need(sr==provided and list(sr)==['path','bytes','sha256'],"same fully validated Ref rebuilt by exact source-owned C.ref")
commands_ref=C.ref(root/'COMMANDS.json');commands=C.obj(commands_ref)
proofs={}
for key in('model','CPU'):
 argv=commands[key];need(type(argv)is list and argv.count('--source-ref')==1,"single exact source argv")
 value=argv[argv.index('--source-ref')+1]
 need(json.loads(value)==provided,"original COMMANDS argv Ref has same exact source semantics")
 need(value==json.dumps(sr),"original COMMANDS argv remains exact canonical source-owned C.ref serialization")
 proofs[key]=dict(argument=value,semantic_equal=True,literal_equal_to_sourceio_ref=True,
  literal_equal_to_supplied_serialization=value==json.dumps(provided))
# These are the original source functions, with no monkeypatch or relaxed contract.
refs=[*B.readset(sr),*m['dependencies'],*CC.validate(C,sr,m)]
serialization_differs=any(not item['literal_equal_to_supplied_serialization']for item in proofs.values())
try:
 CC.validate(C,provided,m)
except ValueError as error:
 need(serialization_differs,"provided original contract failed beyond the diagnosed serialization order")
 old_call=dict(rejected=True,reason=str(error),serialization_differs=True)
else:
 need(not serialization_differs,"original contract unexpectedly accepted altered literal source argv")
 old_call=dict(rejected=False,reason=None,serialization_differs=False)
by_path={} 
for r in refs:
 check(r);C.checked(r)
 need(r['path']not in by_path or by_path[r['path']]==r,"no conflicting exact prerequisite path")
 by_path[r['path']]=r
for r in by_path.values():check(r)
need(actual(sr['path'])==sr and actual(commands_ref['path'])==commands_ref,"unchanged source and COMMANDS after original functions")
print(json.dumps(dict(source=sr,refs=list(by_path.values()),commands=commands_ref,
 helper_sources={name:m['files'][name]for name in('sourceio.py','bind_model.py','command_contract.py')},
 supplied_key_order=list(provided),sourceio_key_order=list(sr),original_command_source_arguments=proofs,
 source_owned_original_functions=['bind_model.readset','command_contract.validate'],
 serialization_only_reconstruction=True,original_unreconstructed_call=old_call,source_and_commands_unchanged=True)))
'''

def collect(sr):
 obj(sr)
 q=subprocess.run(['/usr/bin/python3','-I','-B','-c',READSET_PROGRAM,json.dumps(sr)],capture_output=True,text=True,timeout=120)
 need(q.returncode==0,'exact source-owned readset/COMMANDS failed '+q.stderr[-6000:]);value=json.loads(q.stdout)
 need(value['source']==sr,'same original source identity');unique(value['refs']);return value


def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for key in('failed-source-ref','failed-owner-result-ref','repair-manifest-ref'):p.add_argument('--'+key)
 for key in('repair-overlay','new-root','output-root'):p.add_argument('--'+key,type=Path)
 a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 need(all(vars(a).values()),'actual retained failure, externally reviewed repair manifest and fresh output operands')
 fs=json.loads(a.failed_source_ref);fo=json.loads(a.failed_owner_result_ref)
 need(fs==FAILED_SOURCE and fo==FAILED_OWNER,'only the exact preserved actual G2-v3 CPU failure')
 failed=obj(fs);owner=obj(fo);old=Path(failed['root'])
 need(owner['source']==fs and owner['primary']is not None and owner['secondary']==[]and owner['cpu_only']is True and
  owner['source_before']==owner['source_after'],'actual failed CPU owner, clean release and unchanged source; never a parent PASS')
 need(failed['prepared_only']is False and failed['default_enabled']is False and
  failed['service_experiment']==dict(schema='bole.c1-two-request-stream-service/v2',profile='smoke4',prefix=131,request_count=2,
   max_steps_per_request=3,max_output_tokens=4,capture_protocol='every-frame-independent-CPU-ACK/v1')and
  failed['service_required_sameimage_software_cases']==242 and failed['service_software_scope']['parent_exact_cases']==214 and
  failed['service_software_scope']['new_current_cases']==28,'same original214+28 smoke4 scope, no runtime promotion')
 mr=json.loads(a.repair_manifest_ref);manifest=obj(mr)
 need(mr==ref(a.repair_overlay/'MANIFEST.json')and manifest['overlay_files']==list(OVERLAY),'exact externally reviewed minimal repair manifest')
 actual_overlay={name:inventory(a.repair_overlay,name,manifest['inventory'][name])for name in OVERLAY}
 for name in OVERLAY:compile((a.repair_overlay/name).read_bytes(),name,'exec')
 need(actual_overlay['prepare_g2_parent_v4.py']==ref(Path(__file__).absolute()),'exact executing reviewed repair builder')
 baseline=collect(fs);g1=failed['g2_predecessor'];parent=obj(g1['source']);historical=collect(g1['source'])
 new,out=a.new_root,a.output_root
 need(new.parent==out.parent==Path('/opt/host/vnf/austinov')and
  new.name=='bole-g2-stream-smoke4-20261020T154710Z-v4'and out.name=='run-'+new.name and
  not new.exists()and not out.exists()and not Path(str(out)+'-CPU').exists(),'unique explicit NEW-v4 source/model/CPU leaves; failed-v3 retained')
 shutil.copytree(old,new,ignore=shutil.ignore_patterns('__pycache__'))
 (new/'SOURCE_BOUND.json').rename(new/'FAILED_G2_V3_SOURCE_BOUND.json')
 for name in('COMMANDS.json',failed['command_scope']['compatibility_file']):(new/name).rename(new/('FAILED_G2_V3_'+name))
 for name in OVERLAY:shutil.copyfile(a.repair_overlay/name,new/name)
 shutil.copyfile(a.repair_overlay/'MANIFEST.json',new/'G2_PARENT_SOFTWARE_REPAIR_V4_MANIFEST.json')
 contract=new/'contract090.py';before=(old/'contract090.py').read_text();contract.write_text(outputs(before,str(out)))
 need(outputs(contract.read_text(),failed['output_root'])==before,'contract only changes exact output assignments')
 changed={'service_entry.py','contract090.py','G2_STREAM_EDITS_V1.json'}
 for name,r in failed['files'].items():
  need(ref(r['path'])==r,'unchanged failed-v3 source operand '+name)
  if name not in changed:need((new/name).read_bytes()==Path(r['path']).read_bytes(),'all original runtime/math/stream/CPUbudget/tests byteexact '+name)
 # Rebuild the current exact inverse directly against the same successful G1-v2.
 delta={}
 for name,r in parent['files'].items():
  if(new/name).is_file()and Path(r['path']).is_relative_to(Path(parent['root'])):
   prior=Path(r['path']).read_text();after=(new/name).read_text()
   if prior!=after:delta[name]=dict(before=r,after=ref(new/name),edits=[dict(before=prior,after=after)])
 replace(new/'G2_STREAM_EDITS_V1.json',dict(schema='bole.exact-G2-stream-inverse-to-G1v2/v1',baseline=g1['source'],files=delta,
  original_math_unchanged=True,original_G1v2_full_controls_rerun_separately=True))
 m=json.loads(json.dumps(failed));m.update(root=str(new),output_root=str(out),model_receipt_root=str(out/'dense/receipts'),prepared_only=True,default_enabled=False)
 m.pop('prepared_template',None)
 def remap(r):return ref(new/Path(r['path']).relative_to(old))if Path(r['path']).is_relative_to(old)else r
 for name,r in list(m['files'].items()):m['files'][name]=remap(r)
 for name in(*OVERLAY,'G2_PARENT_SOFTWARE_REPAIR_V4_MANIFEST.json'):m['files'][name]=ref(new/name)
 for key in('service_runtime_source_snapshots','g1_overlay','g1_repair_v2_overlay','g2_overlay'):
  m[key]={k:remap(r)for k,r in m.get(key,{}).items()}
 m['g2_v3_portability_history']=m['g2_builder_portability_v2']
 m['g2_builder_portability_v2']=json.loads(json.dumps(m['g2_v3_portability_history']))
 for name,row in m['g2_builder_portability_v2']['inventory'].items():row['actual_bound']=m['files'][name]
 added=sum(isinstance(n,ast.FunctionDef)and n.name.startswith('test_')for n in ast.walk(ast.parse((new/'test_g2_parent_output.py').read_bytes())))
 need(added==14,'exact fourteen new output-envelope controls')
 m['service_software_scope']=dict(m['service_software_scope'],new_current_cases=28+added)
 m['service_required_sameimage_software_cases']=214+28+added
 m['stream_channel_root']=str(out/'dense/receipts/STREAM');m['stream_channel_contract_path']=str(out/'dense/receipts/STREAM/CHANNEL.json')
 m['stream_consumer_source']=m['files']['g2_consumer.py']
 m['g2_parent_software_repair_v4']=dict(failed_source=fs,failed_CPU_owner=fo,manifest=mr,
  actual_preparer=actual_overlay['prepare_g2_parent_v4.py'],current_preparer=m['files']['prepare_g2_parent_v4.py'],
  overlay={name:m['files'][name]for name in OVERLAY},parent_stdout_stderr_returncode_persist_before_parse=True,
  parent_summary_schema='bole.g1-cold-aggregate-software/v1',original_parent_cases_rerun=214,original_current_cases_rerun=28,
  new_wrapper_cases=added,runtime_math_stream_CPUbudget_unchanged=True,prior_failure_is_not_qualification=True)
 m['dependencies']=unique([*failed['dependencies'],*baseline['refs'],*historical['refs'],fs,fo,mr,*actual_overlay.values()])
 for name in('SOURCE_TEMPLATE.json','SOURCE.json'):replace(new/name,m)
 template=ref(new/'SOURCE_TEMPLATE.json')
 q=subprocess.run(['/usr/bin/python3','-I','-B',str(new/'bind_model.py'),'--execute','--reviewed-template-ref',json.dumps(template),
  '--component-refs-json',json.dumps(m['component_refs'])],capture_output=True,text=True,timeout=40)
 need(q.returncode==0,'fresh exact source binding failed '+q.stdout+q.stderr)
 sr=ref(new/'SOURCE_BOUND.json');bound=obj(sr)
 sys.path.insert(0,str(new));cc=module('_reviewed_v4_commands',new/'command_contract.py')
 oldcommands=obj(m['command_scope']['historical_ref'])
 commands=dict(schema='bole.G1-actual-bound-commands/v2',source=template,bound_source=sr,
  **cc.expected(str(new),str(out),sr,template,m['component_refs']),required_sameimage_software_cases=m['service_required_sameimage_software_cases'],
  historical_required_sameimage_software_cases=oldcommands['required_sameimage_software_cases'],
  legacy_entrypoints_retained_for_inverse_tests_only=True,actual_G1_execution_claimed=False,G2_stream_protocol=True,actual_G2_execution_claimed=False)
 replace(new/'COMMANDS.json',commands)
 replace(new/m['command_scope']['compatibility_file'],dict(source=sr,template=template,commands=ref(new/'COMMANDS.json'),model=commands['model'],
  CPU=commands['CPU'],required_sameimage_software_cases=m['service_required_sameimage_software_cases']))
 cc.validate(cc.C,sr,bound)
 current=collect(sr);required=unique([*baseline['refs'],*historical['refs'],fs,fo,mr,*actual_overlay.values()]);present={r['path']:r for r in current['refs']}
 missing=[r for r in required if present.get(r['path'])!=r];need(not missing,'full exact failed/qualified parent readset closure missing '+json.dumps(missing))
 for f in new.rglob('*.py'):compile(f.read_bytes(),str(f),'exec')
 print(json.dumps(dict(source=sr,commands=ref(new/'COMMANDS.json'),prospective_sameimage_cases=258,
  original214_and28_fresh_rerun_required=True,new_wrapper_controls=14,exact_readset_closure=dict(missing=[],required_count=len(required),current_count=len(present),
   required_sha256=hashlib.sha256(json.dumps(sorted(required,key=lambda r:r['path']),sort_keys=True).encode()).hexdigest()),
  runtime_math_stream_CPUbudget_unchanged=True,actual_sameimage_executed=False,model_ready=False,NPU=False)))
 return 0

if __name__=='__main__':raise SystemExit(main())
