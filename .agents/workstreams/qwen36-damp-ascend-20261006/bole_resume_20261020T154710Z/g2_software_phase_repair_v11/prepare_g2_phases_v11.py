"""New immutable source: only software allocation/entry/lineage, never math."""
import argparse,ast,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v10/SOURCE_BOUND.json',bytes=752323,sha256='af907e01b7143a476459095fad32db5110a940392584c40a4886763a03a9081c')
FAILED=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v10-CPU/RESULT.json',bytes=957044,sha256='f2e0233bc5d13c0ac66d407568c5e09a7aee7d7a8601963783f0b008911dbbb9')
FAULT=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v10-CPU/HOST-FIRST-FAULT.json',bytes=2042,sha256='7e08fc3cc1381429aec42738623e507fb6b58f8c72da22b600c499cb054616b4')
ROOT=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v11');OUT=ROOT.with_name('run-'+ROOT.name)
CHANGED=('host_service.py','service_entry.py','contract090.py','G2_STREAM_EDITS_V1.json')
OLD_SOFTWARE="summary['actual_software_child']=child(cpu,'SOFTWARE',[str(P/'service_entry.py'),'--software'],120)"
NEW_SOFTWARE="summary['actual_software_child']=software_host(C,c,H,cpu,sr,entry_start)"


def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary full exact Ref3 source')
 a=p.stat();h=hashlib.sha256();size=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b);size+=len(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and size==z.st_size,'stable whole source read')
 return dict(path=str(p),bytes=size,sha256=h.hexdigest())
def checked(r):need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'full input path/size/SHA exact');return Path(r['path'])
def obj(r):return json.loads(checked(r).read_bytes())
def legacy(r):
 need(type(r)is dict and set(r)in({'path','sha256'},{'path','bytes','sha256'}),'only actual producerRef2/3');a=ref(r['path']);need(all(a[k]==v for k,v in r.items()),'actual complete Ref2 normalization');return a
def write(p,v):
 with Path(p).open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
 return ref(p)
def replace(p,v):
 if Path(p).exists():Path(p).unlink()
 return write(p,v)
def module(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def tests(p):return sum(isinstance(n,ast.FunctionDef)and n.name.startswith('test_')for n in ast.walk(ast.parse(Path(p).read_bytes())))
def inverse_host(t):
 line=' from g2_software_stages import host_run as software_host\n';need(t.count(line)==1 and t.count(NEW_SOFTWARE)==1,'exact two software-only host substitutions')
 return t.replace(line,'',1).replace(NEW_SOFTWARE,OLD_SOFTWARE,1)


def evidence():
 m=obj(SOURCE);o=obj(FAILED);f=obj(FAULT);need(o['source']==SOURCE and o['cpu_only']is True and o['primary']==f['error_repr']=="ValueError('bounded original child; never retry')"and o['secondary']==[]and o['source_before']and o['source_before']==o['source_after']and o['summary']['first_host_fault']=={k:FAULT[k]for k in('path','bytes')}and f['phase']==dict(phase='cpu-preflight',step='child-SOFTWARE',ordinal=5),'actual retained source-stable SOFTWARE outer120 timeout, never software/model qualification')
 leaf=Path(FAILED['path']).parent/'cpu-preflight';terminal=legacy(dict(path=str(leaf/'G2-V9-PARENT-V8-SOFTWARE/TERMINAL.json'),sha256='71723c003d7a1ea6869e1da8d1b053333fa9b053a87153be5294484b76d427e8'));t=obj(terminal)
 need(t['source_ref']==SOURCE and t['parent_source_ref']==m['g2_cold_clock_v9']['parent_source']and t['returncode']==0 and t['primary']is None and t['timed_out']is False and t['elapsed_seconds']==96.67428704001941 and t['cached_PASS_reused']is False,'actual fresh279 exact original terminal elapsed, not an invented upper bound')
 stderr=ref(leaf/'SOFTWARE.stderr');need(stderr['bytes']==4873 and stderr['sha256']=='a062c5134e85ccefb5e93a25f4e48f9ad200a5937de10be5bc17e3ef0a6971c0','whole actual current25 stderr');text=checked(stderr).read_text();need('Ran 25 tests in 1.660s\n\nOK\n'in text and'can not use command: npu-smi info'in text,'observed current25 complete; final installed metadata has no completion receipt')
 need('actual_software_child'not in o['summary']and m['service_required_sameimage_software_cases']==304,'outer SOFTWARE never completed; no actual304/parser/cold pass asserted')
 refs=[SOURCE,FAILED,FAULT,terminal,stderr,*[legacy(t[n])for n in('stdout','stderr')]]
 return m,refs,dict(actual_parent279_elapsed_seconds=t['elapsed_seconds'],actual_current25_reported_seconds=1.660,outer120_remaining_strictly_less_than_seconds=120-t['elapsed_seconds']-1.660,metadata_completed=False,specific_metadata_import_fault_identified=False,failed_source=SOURCE,failed_owner=FAILED,first_fault=FAULT,parent279_terminal=terminal,actual_current25_stderr=stderr)


def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--manifest-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 parent,observed,cause=evidence();mr=json.loads(a.manifest_ref);manifest=obj(mr);need(mr==ref(P/'MANIFEST.json'),'actual reviewed new packet manifest')
 for n,r in manifest['overlay_files'].items():need(Path(r['path']).name==n and all(ref(P/n)[k]==r[k]for k in('bytes','sha256')),'portable new ordinary overlay whole bytes '+n)
 old=Path(parent['root']);need(not any(p.exists()for p in(ROOT,OUT,Path(str(OUT)+'-CPU'))),'all new source/output leaves exclusive; every previous failure retained')
 need(inverse_host((P/'host_service.py').read_text())==checked(parent['files']['host_service.py']).read_text(),'whole host inverse is only software orchestration; actual clock/cleanup/model/parser untouched')
 collector=next(r for r in parent['dependencies']if r['sha256']=='ce4f5c41be679f0f969b7178e02667461a7f2f601d7c5c8f19c04dabb8f23dd3');H=module(checked(collector),'_g2_v11_original_canonical_collector');baseline=H.collect(SOURCE)
 shutil.copytree(old,ROOT,ignore=shutil.ignore_patterns('__pycache__'));(ROOT/'SOURCE_BOUND.json').rename(ROOT/'FAILED_G2_V10_SOURCE_BOUND.json')
 for n in('COMMANDS.json',parent['command_scope']['compatibility_file']):(ROOT/n).rename(ROOT/('FAILED_G2_V10_'+n))
 for n in manifest['overlay_files']:shutil.copyfile(P/n,ROOT/n)
 (ROOT/'contract090.py').write_text(H.outputs((old/'contract090.py').read_text(),str(OUT)));shutil.copyfile(P/'MANIFEST.json',ROOT/'G2_PHASES_V11_MANIFEST.json')
 for n,r in parent['files'].items():
  if n not in CHANGED:need((ROOT/n).read_bytes()==checked(r).read_bytes(),'all original304 tests/math128/metadata/argv/mount/atomic/caps/resource sources unchanged '+n)

 g1=parent['g2_predecessor']['source'];g1m=obj(g1);delta={}
 for n,r in g1m['files'].items():
  if(ROOT/n).is_file()and Path(r['path']).is_relative_to(Path(g1m['root'])):
   before=checked(r).read_text();after=(ROOT/n).read_text()
   if before!=after:delta[n]=dict(before=r,after=ref(ROOT/n),edits=[dict(before=before,after=after)])
 replace(ROOT/'G2_STREAM_EDITS_V1.json',dict(schema='bole.exact-G2-stream-inverse-to-G1v2/v1',baseline=g1,files=delta,original_math_unchanged=True,original_G1v2_full_controls_rerun_separately=True))
 ledger=replace(ROOT/'G2_PHASES_EDITS_V11.json',dict(schema='bole.exact-software-allocation-whole-inverse/v11',baseline=SOURCE,files={n:dict(before=parent['files'][n],after=ref(ROOT/n),edits=[dict(before=checked(parent['files'][n]).read_text(),after=(ROOT/n).read_text())])for n in CHANGED},original_phase3600_cleanup180_cutoff_unchanged=True,only_software_orchestration_changed=True))
 m=json.loads(json.dumps(parent));m.pop('prepared_template',None);m.update(root=str(ROOT),output_root=str(OUT),model_receipt_root=str(OUT/'dense/receipts'),prepared_only=True,default_enabled=False)
 def remap(r):return ref(ROOT/Path(r['path']).relative_to(old))if Path(r['path']).is_relative_to(old)else r
 m['files']={n:remap(r)for n,r in m['files'].items()}
 for n in(*manifest['overlay_files'],'G2_PHASES_V11_MANIFEST.json','G2_PHASES_EDITS_V11.json'):m['files'][n]=ref(ROOT/n)
 for key in('service_runtime_source_snapshots','g1_overlay','g1_repair_v2_overlay','g2_overlay'):m[key]={n:remap(r)for n,r in m.get(key,{}).items()}
 for row in m['g2_builder_portability_v2']['inventory'].values():row['actual_bound']=m['files'][Path(row['actual_bound']['path']).name]
 m['stream_channel_root']=str(OUT/'dense/receipts/STREAM');m['stream_channel_contract_path']=str(OUT/'dense/receipts/STREAM/CHANNEL.json');m['stream_consumer_source']=m['files']['g2_consumer.py']
 count=sum(tests(ROOT/n)for n in manifest['overlay_files']if n.startswith('test_g2_stage')and n.endswith('.py'));need(count>0,'actual new distinct stage controls')
 m['service_required_sameimage_software_cases']=304+count;m['service_software_scope']=dict(schema='bole.G2-three-source-staged-software-scope/v11',parent_source=parent['service_software_scope']['parent_source'],parent_exact_cases=279,parent_suite_runs_in_separate_exact_source_process=True,controls_source=SOURCE,controls_source_cases=25,controls_run_only_tests_in_exact_source_process=True,current_pattern='test_g2_stage*.py',new_current_cases=count,allocation_seconds=dict(parent279=120.,controls=60.,metadata=120.),aggregate_cap_seconds=300.)
 m['g2_software_phases_v11']=dict(cause,parent_source=SOURCE,manifest=mr,actual_preparer=ref(__file__),whole_current_inverse=ledger,original304_test_files_byteexact=True,software_sources_fresh=dict(source8=279,source10=25,current11=count),current_metadata_original_full_bytes=True,stage_allocation_is_not_success_or_timing_guarantee=True,actual_parser_and_cold_before_NPU_required=True,original_MAIN_first_clock_and_remaining_unchanged=True,no_new_parent_RW_alias=True)
 m['dependencies']=H.unique([*parent['dependencies'],*baseline['refs'],*observed,mr,ref(__file__),*[ref(P/n)for n in manifest['overlay_files']]])
 for n in('SOURCE_TEMPLATE.json','SOURCE.json'):replace(ROOT/n,m)
 tr=ref(ROOT/'SOURCE_TEMPLATE.json');q=subprocess.run(['/usr/bin/python3','-I','-B',str(ROOT/'bind_model.py'),'--execute','--reviewed-template-ref',json.dumps(tr),'--component-refs-json',json.dumps(m['component_refs'])],capture_output=True,text=True,timeout=60);need(q.returncode==0,'new actual source bind failed '+q.stdout+q.stderr)
 sr=ref(ROOT/'SOURCE_BOUND.json');bound=obj(sr);sys.modules.pop('sourceio',None);sys.path.insert(0,str(ROOT));cc=module(ROOT/'command_contract.py','_g2_v11_current_source_owned_commands');need(ref(cc.C.__file__)==bound['files']['sourceio.py'],'actual current source-owned command IO namespace')
 history=obj(m['command_scope']['historical_ref']);commands=dict(schema='bole.G1-actual-bound-commands/v2',source=tr,bound_source=sr,**cc.expected(str(ROOT),str(OUT),sr,tr,m['component_refs']),required_sameimage_software_cases=304+count,historical_required_sameimage_software_cases=history['required_sameimage_software_cases'],legacy_entrypoints_retained_for_inverse_tests_only=True,actual_G1_execution_claimed=False,G2_stream_protocol=True,actual_G2_execution_claimed=False)
 replace(ROOT/'COMMANDS.json',commands);replace(ROOT/m['command_scope']['compatibility_file'],dict(source=sr,template=tr,commands=ref(ROOT/'COMMANDS.json'),model=commands['model'],CPU=commands['CPU'],required_sameimage_software_cases=304+count));cc.validate(cc.C,sr,bound);closure=H.collect(sr)
 present={r['path']:r for r in closure['refs']};need(all(present.get(r['path'])==r for r in baseline['refs']+observed),'all exact historical source10 tests/whole source8/actual failure operands explicitly visible readonly')
 for f in ROOT.rglob('*.py'):compile(f.read_bytes(),str(f),'exec')
 print(json.dumps(dict(source=sr,commands=ref(ROOT/'COMMANDS.json'),prospective_sameimage_cases=304+count,source8_fresh_cases=279,source10_fresh_cases=25,current11_fresh_cases=count,stage_allocation_seconds=m['service_software_scope']['allocation_seconds'],aggregate_cap_seconds=300,original_phase_seconds=3600,cleanup_seconds=180,actual_sameimage_executed=False,actual_cold_handoff_executed=False,actual_model_executed=False,NPU=False)));return 0


if __name__=='__main__':raise SystemExit(main())
