"""Complete source producer over the original GE singleton owner; default OFF."""
import argparse,ast,copy,hashlib,json,os,sys
from pathlib import Path
WORK=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
PREP=WORK/'good_enough_layer37_renew_v2_20261024'
ROOT=PREP/'prepared-source'
PARENT=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/ge-layer37-stability-v1-001')
LOW=Path('/opt/host/vnf/austinov')
OUTPUTS=dict(CPU=str(LOW/'run-mxr-event-single6-owned-main-RENEW24H_GEL37STABILITY_20261024_CPU_V2'),
 NPU=str(LOW/'run-mxr-event-single6-owned-main-RENEW24H_GEL37STABILITY_20261024_NPU_V2'))
START,CUT=1792828303,1792914703
PARENT_REF=dict(path=str(PARENT/'SOURCE_MANIFEST.json'),bytes=16909,sha256='a262c2d8465d5d51d7541f003a4275136b2de387b269346f66c84c7b25076c9b')
WINDOW_REF={'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/renew24_20261024T075143Z/BACKUP_PREPARATION_WINDOW_V1.json', 'bytes': 721, 'sha256': '245827bb2bfef8f24d5d92116315a58847355230f01b745fa04067f6fd2f64f8'}
RESOURCES=dict(guest_bytes=8*2**30,host_bytes=512*2**20,host_reserve_bytes=8*2**30,
 disk_reserve_bytes=4*2**30,output_budget_bytes=4*2**30,cache_budget_bytes=512*2**20,raw_shard_bytes=432*2**20,evidence_bytes=512*2**20,
 phase_seconds=600,child_seconds=300,cleanup_seconds=90,physical=[6],logical=[0],protected=[0,1,2,3])
def need(v,s):
 if not v:raise ValueError(s)
def reference(path):
 p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary complete source/input Ref')
 h=hashlib.sha256();before=p.stat()
 with p.open('rb')as f:
  while b:=f.read(2**20):h.update(b)
 after=p.stat();need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
 (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'stable complete byte hash')
 return dict(path=str(p),bytes=before.st_size,sha256=h.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and r['bytes']>=0,
  'typed complete Ref3');need(reference(r['path'])==r,'unchanged full Ref3');return Path(r['path'])
def obj(r):return json.loads(checked(r).read_text())
def raw_ref(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def load(raw,path,name):
 ns=dict(__file__=str(path),__name__=name);exec(compile(raw,str(path),'exec'),ns);return ns
def once(text,a,b):
 need(text.count(a)==1,'one exact successor source seam '+a[:80]);return text.replace(a,b,1)
def current_contract(raw):
 s=raw.decode()
 s=once(s,'START,CUT=1792226600,1792313000','START,CUT=1792828303,1792914703')
 tree=ast.parse(s);auth=next(n for n in tree.body if isinstance(n,ast.Assign)and
  any(isinstance(t,ast.Name)and t.id=='AUTHORITY_REF'for t in n.targets))
 old=ast.get_source_segment(s,auth);s=once(s,old,'AUTHORITY_REF=None  # populated only after actual MAIN authority validation')
 tree=ast.parse(s);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='current')
 new="""def current(reference_value,root):
    global AUTHORITY_REF
    manifest=obj(reference_value)
    need(reference_value['path']==str(Path(root)/'SOURCE_MANIFEST.json')and
         manifest['root']==str(root),'actual current successor source identity')
    for name,r in manifest['files'].items():
        need(Path(r['path'])==Path(root)/name,'sole new source file path')
        checked(r)
    helper=manifest['files']['successor_bindings.py']
    namespace={'__file__':helper['path'],'__name__':'_mxr_current_source_gate'}
    exec(compile(checked(helper),helper['path'],'exec'),namespace)
    namespace['validate_source'](reference_value,manifest,Path(root),clock=True)
    AUTHORITY_REF=manifest['authority_ref']
    return manifest"""
 s=once(s,ast.get_source_segment(s,fn),new)
 return s.encode()
def render():
 parent=obj(PARENT_REF);need(parent['root']==str(PARENT)and len(parent['files'])==62,'complete actual62-file GE predecessor')
 files={n:checked(r).read_bytes()for n,r in parent['files'].items()}
 before=dict(files)
 files=dict(files)
 files['event_contract.py']=current_contract(files['event_contract.py'])
 files['event_host.py']=once(files['event_host.py'].decode(),"OWNER='ge-layer37-stability-001'",
  "OWNER='ge-l37-renew24h-20261024-v2'").encode()
 host=files['event_host.py'].decode()
 host=once(host,'for item in[sr,AUTHORITY_REF,*m[\'files\'].values(),*explicit_software_refs,*[x[\'ref\']for x in FRAME_REFS]]:',
  "for item in[sr,AUTHORITY_REF,obj(AUTHORITY_REF)['MAIN_review_ref'],m['prepared_template_ref'],*m['preparation_readset'],*m['files'].values(),*explicit_software_refs,*[x['ref']for x in FRAME_REFS]]:")
 host=once(host,'C.PHASE=PHASE;C.CLEANUP=CLEANUP;C.CUTOFF=CUT;C.ROOT=P;',
  "C.OUTPUT_PARENT=Path('/opt/host/vnf/austinov');C.PHASE=PHASE;C.CLEANUP=CLEANUP;C.CUTOFF=CUT;C.ROOT=P;")
 files['event_host.py']=host.encode()
 for n in('prepare_successor.py','successor_bindings.py'):
  need(n not in files,'fresh source-owned preparation/authority gate only')
  files[n]=(PREP/n).read_bytes()
 # Preserve immutable historical JSON payloads. Their old source/input Refs
 # remain readable through the complete explicit preparation/historical readset.
 oldrefs={r['path']:(n,r)for n,r in parent['files'].items()}
 newrefs={n:raw_ref(ROOT/n,b)for n,b in sorted(files.items())}
 def rebase(x):
  if type(x)is dict:
   if set(x)=={'path','bytes','sha256'}and x['path']in oldrefs:
    n,r=oldrefs[x['path']];need(x==r,'unambiguous original file identity');return dict(newrefs[n])
   return{k:rebase(v)for k,v in x.items()}
  if type(x)is list:return[rebase(v)for v in x]
  return x
 m=rebase(copy.deepcopy(parent))
 prep=[PARENT_REF,WINDOW_REF,*[{'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/good_enough_current_leaf_prepare_v1/prepare_successor.py', 'bytes': 12656, 'sha256': '1b61e5336086610d40e01cc7ccbef30f7d29fdd1e445602fdec11339f41e61be'}, {'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/good_enough_current_leaf_prepare_v1/successor_bindings.py', 'bytes': 4263, 'sha256': '7444033ec7c606999a7c68643e82cb1385c17f46a1f20dadd6f85d65e3c5b6ed'}],*parent['files'].values(),
  reference(PREP/'prepare_successor.py'),reference(PREP/'successor_bindings.py')]
 window=obj(WINDOW_REF);need(window['start_epoch']==START and window['cutoff_epoch']==CUT and
  window['preparation_authorized']is True and window['device_execution_requires_distinct_MAIN_source_review']is True,
  'actual preparation window only, never a device ticket')
 m.update(root=str(ROOT),files=newrefs,outputs=dict(OUTPUTS),window=dict(start=START,cutoff=CUT),
  status='PREPARED_MAIN_AUTHORITY_PENDING',prepared_only=True,authority_ref=None,prepared_template_ref=None,
  preparation_window_ref=dict(WINDOW_REF),preparation_readset=prep,resources=dict(RESOURCES),
  parent_source_ref=dict(PARENT_REF),migration_builder_ref=reference(PREP/'prepare_successor.py'),software_cases=96,software_tests=96,
  scope='one actual layer37, two native/S15/S15-refine calls each; diagnostic only; no all192 or model qualification')
 for n,b in files.items():
  if n.endswith('.py'):compile(b,n,'exec')
 changes={n:dict(before=None if n not in before else before[n].decode(),after=files[n].decode(),
  after_ref=newrefs[n])for n in files if before.get(n)!=files[n]}
 return dict(files=files,manifest=m,parent=parent,before=before,delta=dict(schema='ge.current-window-source-inverse/v1',parent_source_ref=PARENT_REF,
   changed_files=changes,math_thresholds_unchanged=True,old_results_unchanged=True))
def inverse(bundle):
 out=dict(bundle['files']);before=bundle['before']
 need({n for n in set(out)|set(before)if out.get(n)!=before.get(n)}==set(bundle['delta']['changed_files']),
  'exact complete changed file domain')
 for n,d in bundle['delta']['changed_files'].items():
  need(out[n].decode()==d['after']and d['before']==(before[n].decode()if n in before else None),'exact inverse bytes')
  if n in before:out[n]=d['before'].encode()
  else:out.pop(n)
 need(out==before,'all original62 file bytes restored');return out
def write_json(p,value):
 data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
 with Path(p).open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 return reference(p)
def validate_template(r):
 m=obj(r);need(r['path']==str(ROOT/'SOURCE_TEMPLATE.json')and m['prepared_only']is True and
  m['authority_ref']is None and m['prepared_template_ref']is None,'prepared template, not an execution source')
 b=render();need(m==b['manifest'],'actual complete independent source reconstruction')
 for n,v in b['files'].items():need(checked(m['files'][n]).read_bytes()==v,'every materialized source byte')
 inverse(b);return m
def prepare():
 need(PREP.is_dir()and not ROOT.exists(),'one absent independent prepared root')
 b=render();inverse(b);ROOT.mkdir(mode=0o700)
 for n,v in b['files'].items():
  p=ROOT/n;need(ROOT in p.parents and '..'not in Path(n).parts,'contained ordinary new source')
  p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb')as f:f.write(v);f.flush();os.fsync(f.fileno())
 t=write_json(ROOT/'SOURCE_TEMPLATE.json',b['manifest'])
 d=write_json(ROOT/'SOURCE_DELTA.json',b['delta'])
 plan=write_json(ROOT/'PLAN.pending.json',dict(schema='ge.actual-successor-plan-pending/v1',
  prepared_template_ref=t,authority_ref=None,source_ref=None,outputs=OUTPUTS,resources=RESOURCES,
  input_ref=b['manifest']['actual_input_ref'],selected_shard=0,actual_frame_index=28,actual_layer=37,
  NPU=False,execution_ready=False))
 cmds=write_json(ROOT/'COMMANDS.pending.json',dict(audit_template=[sys.executable,'-I','-B',
  str(ROOT/'prepare_successor.py'),'--audit-template','--template-ref',json.dumps(t)],
  bind_requires_MAIN_authority=True,source_ref=None,execute_commands_generated_only_after_binding=True))
 return dict(template=t,inverse=d,plan=plan,commands=cmds,prepared_only=True,NPU=False)
def bind(template,authority):
 m=validate_template(template)
 helper=m['files']['successor_bindings.py'];S=load(checked(helper).read_bytes(),helper['path'],'_mxr_successor_bind')
 S['validate_authority'](m,template,authority,clock=True)
 need(not(ROOT/'SOURCE_MANIFEST.json').exists(),'fresh source binding, never overwrite')
 actual=dict(m,prepared_only=False,authority_ref=authority,prepared_template_ref=template)
 # The public runtime validator reopens and reconstructs before acceptance.
 S['validate_source'](None,actual,ROOT,clock=True,allow_unwritten=True)
 sr=write_json(ROOT/'SOURCE_MANIFEST.json',actual)
 cmds={}
 for stage in('audit','cpu','numeric'):
  cmds[stage]=['/usr/bin/env','MXR_EVENT_HOST_ENABLE=1','/usr/bin/python3','-I','-B',str(ROOT/'run_stage.py'),'--execute',
   '--source-sha256',sr['sha256'],'--stage',stage]
 cr=write_json(ROOT/'COMMANDS.json',cmds)
 return dict(source=sr,commands=cr,authority_created=False,NPU=False,execution_not_started=True)
def check():
 b=render();inverse(b)
 need(len(b['files'])==64 and all(b['files'][n]==b['before'][n]for n in b['before']
  if n not in('event_contract.py','event_host.py')),'only exact permitted runtime seams changed')
 # No standalone owner, import Torch, approval or device work happens here.
 S=load(b['files']['successor_bindings.py'],ROOT/'successor_bindings.py','_source_only_authority_check')
 for r in(None,WINDOW_REF):
  try:S['validate_authority'](b['manifest'],None,r,clock=False)
  except ValueError:pass
  else:raise ValueError('unbound/preparation-only document accepted as device authority')
 tests=0
 for n,v in b['files'].items():
  if n.startswith('test_')and n.endswith('.py'):
   tests+=sum(isinstance(x,ast.FunctionDef)and x.name.startswith('test_')for x in ast.walk(ast.parse(v)))
 need(tests==96,'original exact96 software case names retained')
 print(json.dumps(dict(files=len(b['files']),original_tests=tests,whole_inverse=True,
  authority_None_and_preparation_doc_rejected=True,source_bound=False,NPU=False)))
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);m=p.add_mutually_exclusive_group()
 for x in('check','prepare','audit-template','bind'):m.add_argument('--'+x,action='store_true')
 p.add_argument('--template-ref');p.add_argument('--authority-ref');a=p.parse_args()
 if not any((a.check,a.prepare,a.audit_template,a.bind)):
  need(a.template_ref is None and a.authority_ref is None,'mode required')
  print('{"enabled":false,"NPU":false,"source_bound":false}');return
 if a.check:need(a.template_ref is None and a.authority_ref is None,'source-only check');check();return
 if a.prepare:need(a.template_ref is None and a.authority_ref is None,'prepare creates no authority');print(json.dumps(prepare()));return
 need(a.template_ref is not None,'actual template Ref required');t=json.loads(a.template_ref)
 if a.audit_template:
  need(a.authority_ref is None,'template audit creates no authority')
  m=validate_template(t);print(json.dumps(dict(template=t,source_files=len(m['files']),source_bound=False,NPU=False)));return
 need(a.authority_ref is not None,'MAIN actual authority required, never preparation window')
 print(json.dumps(bind(t,json.loads(a.authority_ref))))
if __name__=='__main__':main()
