"""Immutable v9: cold main-entry clock and original-allowed candidate cold leaf."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
P=Path(__file__).resolve().parent
SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v8/SOURCE_BOUND.json',bytes=612583,sha256='ae03ae1e05711105642b4d07763384f38ed190f1defa4a9ac748389e88daa601')
FAILED_OWNER=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v8-CPU/RESULT.json',bytes=741019,sha256='f95e50f77bf77cdd6ed453596698f84f5152e1fd6f6a17565d9b8813a27b0765')
FAULT=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v8-CPU/HOST-FIRST-FAULT.json',bytes=1403,sha256='daa6512954d145b2c15594e2c5fe905c8d65e9283494a4960ad663df9d1876a4')
AUDIT=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/G2_V8_SOURCE_AUDIT.json',bytes=2301,sha256='f6d942fa73c768efd2bd9b2a780f016e06ac828e43c313a66c33037545291d82')
ROOT=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v9');OUT=ROOT.with_name('run-'+ROOT.name)
COLLECTOR_SHA='ce4f5c41be679f0f969b7178e02667461a7f2f601d7c5c8f19c04dabb8f23dd3'
CHANGED=('host_service.py','owned_create.py','g2_handoff.py','service_entry.py')


def need(v,s):
    if not v:raise ValueError(s)
def ref(path):
    p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary exact absolute file')
    before=p.stat();h=hashlib.sha256();size=0
    with p.open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b);size+=len(b)
    after=p.stat();need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)and size==after.st_size,'stable complete source read')
    return dict(path=str(p),bytes=size,sha256=h.hexdigest())
def checked(r):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'exact full Ref3');return Path(r['path'])
def obj(r):return json.loads(checked(r).read_bytes())
def legacy(r):
    need(type(r)is dict and set(r)in({'path','sha256'},{'path','bytes','sha256'}),'only original Ref2/3');a=ref(r['path']);need(a['sha256']==r['sha256']and('bytes'not in r or a['bytes']==r['bytes']),'full-byte original Ref normalization');return a
def write(p,v):
    with Path(p).open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
    return ref(p)
def replace(p,v):
    if Path(p).exists():Path(p).unlink()
    return write(p,v)
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def tests(p):return sum(isinstance(n,ast.FunctionDef)and n.name.startswith('test_')for n in ast.walk(ast.parse(Path(p).read_bytes())))
def pair(text,old,new):
    need(text.count(new)==1,'one exact declared cold-clock or lifecycle edit');return text.replace(new,old,1)


def inverse(name,text):
    if name=='host_service.py':
        text=pair(text,''," entry_start=time.monotonic()\n")
        text=pair(text,''," from g2_cold_clock import phase_admission,controller_admission\n phase_admission(C,entry_start)\n")
        text=pair(text,'start=time.monotonic();c,S,H,pairs=load(a.output);','start=entry_start;c,S,H,pairs=load(a.output);')
        text=pair(text,"ctl.observe(role+'-admission',initial=True);mark(role,'create-start-inspect');create", "ctl.observe(role+'-admission',initial=True);controller_admission(C,c,S,ctl,entry_start);mark(role,'create-start-inspect');create")
        return pair(text,"coldleaf=H.fresh_leaf(a.output/'handoff-preflight')","coldleaf=H.fresh_leaf(a.output/'candidate')")
    if name=='owned_create.py':
        text=pair(text,''," if role=='cpu-preflight'and leaf.name=='cpu-preflight':\n  from g2_cold_parent_output import parent_alias\n  mounts.update(parent_alias(c,sr,leaf,readset,source_root))\n")
        return pair(text,"if role=='cpu-preflight'and leaf.name=='handoff-preflight':","if role=='cpu-preflight'and leaf.name=='candidate':")
    if name=='g2_handoff.py':
        need(text.count("Path(m['output_root'])/'candidate'")==2 and text.count("Path(m['output_root']+'-CPU')/'candidate'")==2,'exact two complete saved-stage and verification root operands')
        return text.replace("Path(m['output_root'])/'candidate'","Path(m['output_root'])/'handoff-preflight'").replace("Path(m['output_root']+'-CPU')/'candidate'","Path(m['output_root']+'-CPU')/'handoff-preflight'")
    if name=='service_entry.py':
        text=pair(text,'"""Cold G2 controls plus separately rerun exact qualified G1-v2 historical suite."""','"""Cold G2-v9 controls plus separately rerun exact qualified G2 historical suite."""')
        text=pair(text,"scope['schema']=='bole.G2-explicit-historical-plus-current-controls/v1'", "scope['schema']=='bole.G2-cold-clock-historical-plus-current-controls/v9'")
        text=pair(text,"scope['current_pattern']=='test_g2*.py'","scope['current_pattern']=='test_g2_cold*.py'")
        text=pair(text," import parent_software_output as OUTPUT\n C.need(C.ref(OUTPUT.__file__)==m['files']['parent_software_output.py'],'exact fresh-parent output retention/extraction helper')\n output_root,output_binding=OUTPUT.owned_output(C,m)\n prior,parent_evidence=OUTPUT.run(C,source_ref=sr,parent_source_ref=scope['parent_source'],\n    expected_tests=scope['parent_exact_cases'],evidence_root=output_root,output_binding=output_binding,timeout=120)\n", " from g2_cold_parent_output import run as actual_parent\n prior,parent_evidence=actual_parent(sr)\n")
        text=pair(text,"result.wasSuccessful()and result.testsRun", "result.wasSuccessful()and not result.skipped and result.testsRun")
        return pair(text,"schema='bole.G2-explicit-combined-software-gate/v1'", "schema='bole.G2-cold-clock-combined-software-gate/v9'")
    raise ValueError('no implicit whole-source inverse '+name)


def evidence(sr,owner_ref,audit_ref):
    need(sr==SOURCE and owner_ref==FAILED_OWNER and audit_ref==AUDIT,'only actual preserved v8 CPU source/failure/audit')
    m=obj(sr);o=obj(owner_ref);ar=obj(audit_ref);refs=[sr,owner_ref,audit_ref]
    need(ar['exit_code']==0 and ar['stderr']==''and ar['argv']==['/usr/bin/python3','-I','-B',str(Path(m['root'])/'audit_source_v8.py'),'--execute','--source-ref',json.dumps(SOURCE)],'actual exact original source-audit command completed')
    audit=json.loads(ar['stdout'])
    need(m['prepared_only']is False and m['default_enabled']is False and m['service_required_sameimage_software_cases']==279 and m['service_software_scope']['parent_exact_cases']==214 and m['service_software_scope']['new_current_cases']==65,'actual immutable279 parent, no future model qualification')
    need(o['source']==sr and o['cpu_only']is True and o['primary']=="ValueError('exact fresh064 opt stage; no broad opt escape')"and o['secondary']==[]and o['source_before']and o['source_before']==o['source_after']and o['source_before'].get(sr['path'])==sr['sha256'],'actual clean source-stable v8 CPU fresh-leaf failure; old late elapsed remains historical')
    need(audit['schema']=='bole.G2-v8-source-readonly-audit/v1'and audit['source']==sr and audit['exact_metadata_and_lifecycle_inverse']is True and audit['original266_assertions_math_consumer_finalizer_resources_preserved']is True and audit['whole_v7_bind_argv_and8controls_byteexact']is True and audit['original_15_stream_test_bodies_AST_exact']is True and audit['prospective_sameimage_cases']==279 and audit['NPU']is False,'actual source-owned v8 complete inverse audit')
    need(o['summary']['first_host_fault']=={k:FAULT[k]for k in('path','bytes')},'actual original fault receipt declared path+bytes only; normalize only this known full-SHA original')
    fault=FAULT;f=obj(fault);refs.append(fault)
    need('handoff-preflight'in json.dumps(f)and'host_service.py'in json.dumps(f)and'fresh_leaf'in json.dumps(f),'actual preserved aggregate coldleaf first fault')
    need(not any(k in o['summary']for k in('handoff_cold_child','MTP_load','stream_channel','model_release')),'actual failure before cold child and any NPU admission')
    child=legacy(o['summary']['actual_software_child']);v=obj(child);so=legacy(v['stdout_ref']);se=legacy(v['stderr_ref']);refs.extend([child,so,se])
    need(v['exit_code']==0 and v['child_termination_observed']is True,'actual parent child completed, not reused as fresh suite PASS')
    found=[]
    for line in checked(so).read_text().splitlines():
        try:x=json.loads(line)
        except ValueError:continue
        if type(x)is dict and x.get('schema')=='bole.G2-explicit-combined-software-gate/v1':found.append(x)
    need(len(found)==1 and found[0]['source']==sr and found[0]['tests']==279 and found[0]['historical_cases']==214 and found[0]['current_cases']==65 and found[0]['all_tests_passed']is True,'actual279 software result only; current source must rerun all279 freshly')
    cpu=legacy(o['summary']['CPU_report']);report=obj(cpu);need(report['source']==sr and report['pass_preflight']is True and report['Devices']==[]and report['native_runtime_parser_checked']is True and report['registry_arch_enumerated']is True,'actual parent Devices[] parser only')
    release=legacy(o['summary']['CPU_release']);r=obj(release);need(r['stopped']is True and r['retained']is True and r['errors']==[],'actual failed v8 CPU clean retained release');refs.extend([cpu,release])
    cpu_child=legacy(o['summary']['CPU_child']);cc=obj(cpu_child);need(cc['exit_code']==0 and cc['child_termination_observed']is True,'actual native parser child completed, never a cached report only');refs.append(cpu_child)
    leaf=Path(owner_ref['path']).parent/'cpu-preflight';owned=ref(leaf/'OWNED.json');guest=ref(leaf/'GUEST_CPU.json');ov=obj(owned);gv=obj(guest)
    need(ov['source']==sr and ov['arm']=='cpu-preflight'and ov['guest_cpus']==[145]and gv['effective_cpus']==[145]and gv['effective_capacity']==1 and gv['cgroup']=='/docker/'+ov['cid']and r['container']==ov['cid'],'actual retained parent CPU identity/cgroup/cleanup chain, not a live or model qualification');refs.extend([owned,guest])
    need((m['files']['external025.py']['bytes'],m['files']['external025.py']['sha256'])==(5198,'8b65bbd0518a81b194459e087dd6a6003dcfbb07151940c031aaec31d29e3c62'),'original four-name leaf/environment/prepare policy byteexact')
    return m,refs,dict(parent_source=sr,failed_cpu_owner=owner_ref,parent_source_audit=audit_ref,actual279_software_only=True,parent_parser_only=True,actual_saved_handoff_pass=False,actual_model_pass=False,old_elapsed_is_late_and_not_rewritten=True,coldleaf='candidate',cold_arm='cpu-preflight',original_four_leaf_allowlist_unchanged=True)


def main():
    parser=argparse.ArgumentParser(allow_abbrev=False);parser.add_argument('--execute',action='store_true')
    for n in('failed-owner-ref','parent-audit-ref','prior-builder-ref','manifest-ref'):parser.add_argument('--'+n)
    a=parser.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    need(all(vars(a).values()),'exact actual failed CPU/audit/original collector/reviewed packet Refs required')
    parent,observed,cause=evidence(SOURCE,json.loads(a.failed_owner_ref),json.loads(a.parent_audit_ref));br=json.loads(a.prior_builder_ref);need(br['sha256']==COLLECTOR_SHA,'unchanged canonical source-owned readset collector');H=module('_g2_v9_original_collector',checked(br));mr=json.loads(a.manifest_ref);manifest=obj(mr);need(mr==ref(P/'MANIFEST.json'),'exact externally reviewed current manifest')
    for n,w in manifest['overlay_files'].items():
        actual=ref(P/n);need((actual['bytes'],actual['sha256'])==(w['bytes'],w['sha256'])and Path(w['path']).name==n,'portable ordinary exact overlay bytes/SHA; advisory paths remain historical '+n)
    old=Path(parent['root']);need(not any(p.exists()for p in(ROOT,OUT,Path(str(OUT)+'-CPU'))),'fresh immutable v9 source/model/CPU roots, retain all prior failures')
    for n in CHANGED:need(inverse(n,(P/n).read_text())==checked(parent['files'][n]).read_text(),'precise whole v8 inverse '+n)
    K=module('_g2_v9_exact_clock',P/'g2_cold_clock.py');K.validate((P/'host_service.py').read_text())
    need((parent['files']['service_entry.py']['bytes'],parent['files']['service_entry.py']['sha256'])==(2549,'d038ec92a38487b10a9a02b5d13538873aa074b5626739befbf80ecdff23fd7a'),'exact original279 entry freshly rerun, no historical control mutation')
    baseline=H.collect(SOURCE);g1=parent['g2_predecessor'];g1m=obj(g1['source']);historical=H.collect(g1['source'])
    shutil.copytree(old,ROOT,ignore=shutil.ignore_patterns('__pycache__'));(ROOT/'SOURCE_BOUND.json').rename(ROOT/'PARENT_G2_V8_SOURCE_BOUND.json')
    for n in('COMMANDS.json',parent['command_scope']['compatibility_file']):(ROOT/n).rename(ROOT/('PARENT_G2_V8_'+n))
    for n in manifest['overlay_files']:shutil.copyfile(P/n,ROOT/n)
    (ROOT/'contract090.py').write_text(H.outputs((old/'contract090.py').read_text(),str(OUT)));shutil.copyfile(P/'MANIFEST.json',ROOT/'G2_COLD_V9_MANIFEST.json')
    changed={*CHANGED,'contract090.py','G2_STREAM_EDITS_V1.json'}
    for n,r in parent['files'].items():
        if n not in changed:need((ROOT/n).read_bytes()==checked(r).read_bytes(),'all original279 controls/math/128transactions/argv/atomic/channel/consumer/resource sources unchanged '+n)
    delta={}
    for n,r in g1m['files'].items():
        if(ROOT/n).is_file()and Path(r['path']).is_relative_to(Path(g1m['root'])):
            before=checked(r).read_text();after=(ROOT/n).read_text()
            if before!=after:delta[n]=dict(before=r,after=ref(ROOT/n),edits=[dict(before=before,after=after)])
    replace(ROOT/'G2_STREAM_EDITS_V1.json',dict(schema='bole.exact-G2-stream-inverse-to-G1v2/v1',baseline=g1['source'],files=delta,original_math_unchanged=True,original_G1v2_full_controls_rerun_separately=True))
    ledger=replace(ROOT/'G2_COLD_EDITS_V9.json',dict(schema='bole.exact-main-cold-clock-and-allowed-leaf-inverse/v9',baseline=SOURCE,files={n:dict(before=parent['files'][n],after=ref(ROOT/n),edits=[dict(before=checked(parent['files'][n]).read_text(),after=(ROOT/n).read_text())])for n in(*CHANGED,'contract090.py')},original279_test_files_byteexact=True,all_original279_fresh_separate_exact_parent_process=True,original_math_argv_metadata_atomic_caps_unchanged=True))
    m=json.loads(json.dumps(parent));m.pop('prepared_template',None);m.update(root=str(ROOT),output_root=str(OUT),model_receipt_root=str(OUT/'dense/receipts'),prepared_only=True,default_enabled=False)
    def remap(r):return ref(ROOT/Path(r['path']).relative_to(old))if Path(r['path']).is_relative_to(old)else r
    m['files']={n:remap(r)for n,r in m['files'].items()}
    for n in(*manifest['overlay_files'],'G2_COLD_V9_MANIFEST.json','G2_COLD_EDITS_V9.json'):m['files'][n]=ref(ROOT/n)
    for key in('service_runtime_source_snapshots','g1_overlay','g1_repair_v2_overlay','g2_overlay'):m[key]={n:remap(r)for n,r in m.get(key,{}).items()}
    for row in m['g2_builder_portability_v2']['inventory'].values():row['actual_bound']=m['files'][Path(row['actual_bound']['path']).name]
    m['stream_channel_root']=str(OUT/'dense/receipts/STREAM');m['stream_channel_contract_path']=str(OUT/'dense/receipts/STREAM/CHANNEL.json');m['stream_consumer_source']=m['files']['g2_consumer.py']
    added=sum(tests(ROOT/n)for n in manifest['overlay_files']if n.startswith('test_g2_cold'))
    m['service_software_scope']=dict(schema='bole.G2-cold-clock-historical-plus-current-controls/v9',parent_source=SOURCE,parent_exact_cases=279,parent_suite_runs_in_separate_exact_source_process=True,current_pattern='test_g2_cold*.py',new_current_cases=added)
    m['service_required_sameimage_software_cases']=279+added
    m['g2_cold_clock_v9']=dict(cause,manifest=mr,actual_preparer=ref(__file__),whole_current_inverse=ledger,clock=K.validate((ROOT/'host_service.py').read_text()),original279_fresh_rerun_required=True,new_controls=added,original3600_and180_cutoff_unchanged=True,original_guest_B_CANN_environment_preserved=True,historical_v8_handoff_ledger_is_not_current_inverse=True,sameimage_cold_before_any_NPU_required=True)
    required=H.unique([*baseline['refs'],*historical['refs'],SOURCE,*observed,br,mr,*[ref(P/n)for n in manifest['overlay_files']]])
    m['dependencies']=H.unique([*parent['dependencies'],*required])
    for n in('SOURCE_TEMPLATE.json','SOURCE.json'):replace(ROOT/n,m)
    tr=ref(ROOT/'SOURCE_TEMPLATE.json');q=subprocess.run(['/usr/bin/python3','-I','-B',str(ROOT/'bind_model.py'),'--execute','--reviewed-template-ref',json.dumps(tr),'--component-refs-json',json.dumps(m['component_refs'])],capture_output=True,text=True,timeout=60);need(q.returncode==0,'new exact source binding failed '+q.stdout+q.stderr)
    sr=ref(ROOT/'SOURCE_BOUND.json');bound=obj(sr);sys.path.insert(0,str(ROOT));cc=module('_g2_v9_source_owned_commands',ROOT/'command_contract.py');history=obj(m['command_scope']['historical_ref'])
    commands=dict(schema='bole.G1-actual-bound-commands/v2',source=tr,bound_source=sr,**cc.expected(str(ROOT),str(OUT),sr,tr,m['component_refs']),required_sameimage_software_cases=m['service_required_sameimage_software_cases'],historical_required_sameimage_software_cases=history['required_sameimage_software_cases'],legacy_entrypoints_retained_for_inverse_tests_only=True,actual_G1_execution_claimed=False,G2_stream_protocol=True,actual_G2_execution_claimed=False)
    replace(ROOT/'COMMANDS.json',commands);replace(ROOT/m['command_scope']['compatibility_file'],dict(source=sr,template=tr,commands=ref(ROOT/'COMMANDS.json'),model=commands['model'],CPU=commands['CPU'],required_sameimage_software_cases=m['service_required_sameimage_software_cases']))
    cc.validate(cc.C,sr,bound);current=H.collect(sr);present={r['path']:r for r in current['refs']};need(all(present.get(r['path'])==r for r in required),'complete source/actualfailure279/parser/cleanup/audit/command/inverse readset closure')
    for f in ROOT.rglob('*.py'):compile(f.read_bytes(),str(f),'exec')
    print(json.dumps(dict(source=sr,commands=ref(ROOT/'COMMANDS.json'),prospective_sameimage_cases=279+added,original279_fresh_separate_exact_parent_process=True,new_controls=added,cold_main_entry_before_source=True,original_candidate_leaf_policy=True,cold_complete_original_channel_reader_before_NPU=True,actual_sameimage_executed=False,actual_model_executed=False,model_ready=False,NPU=False)));return 0


if __name__=='__main__':raise SystemExit(main())
