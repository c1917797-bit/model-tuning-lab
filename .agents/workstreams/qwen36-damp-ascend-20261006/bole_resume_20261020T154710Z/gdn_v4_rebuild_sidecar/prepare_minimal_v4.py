"""MAIN source-only GDN v4: two fixture literals, exact original builder."""
import ast,hashlib,json,os,pathlib,resource,shutil,subprocess,sys,time
P=pathlib.Path;T=P(__file__).resolve().parents[1];stage=P(__file__).resolve().parent
os.sched_setaffinity(0,{166});_,hard=resource.getrlimit(resource.RLIMIT_AS);resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=P(p);need(p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)),'ordinary source');b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 need(ref(r['path'])==r,'full source ref '+r['path']);return P(r['path']).read_bytes()
def write(p,v):
 need(not p.exists(),'new metadata only');p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');return ref(p)
def methods(b):
 rows={}
 for c in ast.parse(b).body:
  if isinstance(c,ast.ClassDef):
   for f in c.body:
    if isinstance(f,ast.FunctionDef)and f.name.startswith('test'):
     need(c.name+'.'+f.name not in rows,'unique test');rows[c.name+'.'+f.name]=ast.dump(f,include_attributes=False)
 return rows
old=T/'gdn_service_probe_g1_v3';packet=T/'gdn_service_probe_g1_v4'
sr=dict(path='/opt/host/vnf/austinov/bole-gdn-g1-probe-matched-v3/SOURCE_BOUND.json',bytes=112215,sha256='f1c1c96aee26844daaf538d516bd65791d83ada35737f3b10aef198329d69e88')
m=json.loads(checked(sr));need(m['service_required_sameimage_software_cases']==240 and m['gdn_service_extension']['mode']=='matched_original','original matched240')
need(not packet.exists(),'new packet')
added=('gdn_service_gate.py','gdn_service_seam.py','consume_gdn_service.py','gdn_probe_contract.py','gdn_probe_runtime.py','test_gdn_service_pure.py','test_gdn_probe_pure.py','prepare_gdn_probe.py','gdn_probe_clock.py','test_gdn_probe_clock.py','CLOCK_INVERSE_AUTHORITY.json')
raw={n:checked(r)for n,r in m['files'].items()};tests={n:b for n,b in raw.items()if n.startswith('test_')and n.endswith('.py')}
need(len(tests)==51 and sum(len(methods(b))for b in tests.values())==240,'complete original 51/240')
for n in added:need((old/n).read_bytes()==raw[n],'actual source/packet operand '+n)
need(ref(old/'prepare_gdn_probe.py')['bytes']==15140 and ref(old/'prepare_gdn_probe.py')['sha256']=='e38dcf3bd1b638fc63d200eb68bb06d28b1597b348e51099cbeae2a5e028583b','exact unchanged builder')
inputs=old/'ACTUAL_INPUT_REFS.json';need(ref(inputs)['bytes']==3166 and ref(inputs)['sha256']=='698c56803ba2593d29604b1928a143c2989c25b993b585dede532c91a601bbc0','actual frozen prior refs')
before=raw['test_gdn_probe_pure.py'];a='with tempfile.TemporaryDirectory(dir=P)as directory:';b="with tempfile.TemporaryDirectory(dir='/adakv-results')as directory:"
need(before.decode().count(a)==2,'two exact fixture literals');after=before.decode().replace(a,b).encode();need(len(after)==9539 and after.decode().replace(b,a).encode()==before,'whole two-literal inverse')
ma,mb=methods(before),methods(after);need(ma.keys()==mb.keys(),'same test methods');changed={n for n in ma if ma[n]!=mb[n]};need(changed=={'Tests.test_synthetic_CPU_handoff_join_and_wrong_terminal_reject','Tests.test_exact_ref_skip_only_and_drift_fails'},'exact two methods')
packet.mkdir(mode=0o700)
for n in added:(packet/n).write_bytes(after if n=='test_gdn_probe_pure.py'else raw[n])
shutil.copyfile(inputs,packet/inputs.name)
for p in packet.glob('*.py'):compile(p.read_bytes(),str(p),'exec',dont_inherit=True)
ledger=write(packet/'FIXTURE_INVERSE_V4.json',dict(schema='bole.GDN-v4-exact-fixture-inverse/v1',old_source=sr,old_test=m['files']['test_gdn_probe_pure.py'],new_test=ref(packet/'test_gdn_probe_pure.py'),before_text=before.decode(),after_text=after.decode(),whole_inverse=True,test_files=51,methods=240,unchanged_methods=238,changed_methods=sorted(changed),all_original_test_refs={n:m['files'][n]for n in tests},original_methods={n:{k:hashlib.sha256(v.encode()).hexdigest()for k,v in methods(z).items()}for n,z in tests.items()},actual_sameimage_executed=False))
manifest=write(packet/'ADVISORY_MANIFEST.json',dict(schema='bole.GDN-v4-two-fixture-literals-source-only/v1',parent_source=sr,files={n:ref(packet/n)for n in(*added,'ACTUAL_INPUT_REFS.json')},inverse=ledger,required_sameimage_software_cases=240,runtime_math_resource_clock_changes=False,actual_v4_SOURCE=None,actual_CPU=None,actual_MODEL=None,formal_success=False))
root=P('/opt/host/vnf/austinov/bole-gdn-g1-probe-matched-v4');out=root.with_name('run-'+root.name)
need(not any(p.exists()for p in(root,out,P(str(out)+'-CPU'))),'new source/output')
cold=[]
for flags,expected in(([],True),(['--help'],True),(['--execute'],False)):
 argv=['/usr/bin/python3','-I','-B',str(packet/'prepare_gdn_probe.py'),*flags];p=subprocess.run(argv,capture_output=True,text=True,timeout=30)
 cold.append(dict(argv=argv,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));need((p.returncode==0)==expected,'actual isolated defaultOFF/help/missing-args CLI')
write(stage/'COLD_CLI.json',cold)
refs=json.loads(inputs.read_text());argv=['/usr/bin/python3','-I','-B',str(packet/'prepare_gdn_probe.py'),'--execute','--prior-G1-refs-json',json.dumps(refs['prior_G1']),'--replay-refs-json',json.dumps(refs['replay']),'--mode','matched_original','--new-root',str(root),'--output-root',str(out)]
p=subprocess.run(argv,capture_output=True,text=True,timeout=180);prep=write(stage/'PREPARATION.json',dict(argv=argv,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));need(p.returncode==0,'new source prepare failed; retained '+str(prep))
newref=ref(root/'SOURCE_BOUND.json');nm=json.loads(checked(newref));need(nm['files'].keys()==m['files'].keys()and nm['service_required_sameimage_software_cases']==240,'actual new source complete same file/test scope')
newraw={n:checked(r)for n,r in nm['files'].items()};changedpy={n for n in raw if n.endswith('.py')and raw[n]!=newraw[n]};need(changedpy=={'test_gdn_probe_pure.py','contract090.py'},'only fixture and registered output contract changed')
need(newraw['test_gdn_probe_pure.py']==after,'actual new fixture')
need(raw['contract090.py'].decode().count(m['output_root'])==2 and raw['contract090.py'].decode().replace(m['output_root'],str(out)).encode()==newraw['contract090.py'],'two output literal inverse')
changes={n:dict(before=m['files'][n],after=nm['files'][n],before_text=raw[n].decode(),after_text=newraw[n].decode())for n in raw if raw[n]!=newraw[n]}
whole=write(stage/'WHOLE_SOURCE_INVERSE.json',dict(old_source=sr,new_source=newref,all_files=len(raw),all_test_files=51,all_methods=240,methods_whole_exact=238,explicit_changed_methods=sorted(changed),whole_file_changes=changes,only_two_python_files_changed=True,runtime_math_resource_clock_byteexact=True,actual_CPU=None,actual_MODEL=None,formal_success=False))
argv=['/usr/bin/python3','-I','-B',str(root/'host_service.py'),'--source-audit','--source-ref',json.dumps(newref)];p=subprocess.run(argv,capture_output=True,text=True,timeout=180);audit=write(stage/'SOURCE_AUDIT.json',dict(argv=argv,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));need(p.returncode==0,'source audit failed; retained '+str(audit))
need(not out.exists()and not P(str(out)+'-CPU').exists(),'no owner resources/output')
print(json.dumps(dict(manifest=manifest,source=newref,commands=ref(root/'COMMANDS.json'),preparation=prep,source_audit=audit,whole_inverse=whole,required_sameimage_software_cases=240,actual_CPU=False,actual_MODEL=False,NPU=False)),flush=True)
