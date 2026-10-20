"""Fresh immutable G2-v7 owning-commandline repair; no host/device launch."""
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
SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v6/SOURCE_BOUND.json',bytes=475051,sha256='41a3ffb818e9163515f4bc2e15ab46f2ffbd301ae8a28c7c14e2f209ef92cfd1')
ROOT=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v7');OUT=ROOT.with_name('run-'+ROOT.name)
FAILED_OWNER=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v6/RESULT.json',bytes=528356,sha256='b45284f06ef12fd7fbbbc91d65fd13469d57402c5dd6c66ffc706999b6b41e24')
FAULT=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v6/HOST-FIRST-FAULT.json',bytes=1261,sha256='f51a820774dd2167313bee58fca022d52ff0b2170e1b220154707948ce02dd44')
OWNER_BYTES=5638;OWNER_SHA='de21742536cd9a5bc70dc324aed2ccc8ffcddabe0a7f983b217134caa52a134b'
COLLECTOR_SHA='ce4f5c41be679f0f969b7178e02667461a7f2f601d7c5c8f19c04dabb8f23dd3'
OLD="""    argv=boot['argv']
    C.need(argv[1:3]==['-I','-B']and argv[3]==str(Path(m['root'])/'g2_consumer.py')and
        set(argv[4:])>= {'--execute','--bootstrap','--source-ref'}and
        json.loads(argv[argv.index('--source-ref')+1])==source_ref,
        'actual exact-source independent consumer commandline')
"""
NEW="""    argv=boot['argv']
    consumer_commandline(C,c,argv,source_ref=source_ref,root=m['root'])
"""
HELPER="""def consumer_commandline(C,c,argv,*,source_ref,root):
    actual=C.ref(C.checked(source_ref))
    C.need(Path(actual['path'])==Path(root)/'SOURCE_BOUND.json',
        'same exact source-owned consumer root before argv qualification')
    expected=[c.PY,'-B',str(Path(root)/'g2_consumer.py'),
        '--execute','--bootstrap','--source-ref',json.dumps(actual)]
    C.need(type(argv)is list and argv==expected,
        'actual exact-source independent consumer commandline')
    return expected


"""


def need(value,message):
    if not value:raise ValueError(message)


def ref(path):
    p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary exact absolute Ref3')
    before=p.stat();h=hashlib.sha256();size=0
    with p.open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):size+=len(b);h.update(b)
    after=p.stat();need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)and size==after.st_size,'stable exact source');return dict(path=str(p),bytes=size,sha256=h.hexdigest())


def checked(r):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'complete supplied exact Ref3');return Path(r['path'])


def obj(r):return json.loads(checked(r).read_bytes())


def legacy(r):
    a=ref(r['path']);need(a['sha256']==r['sha256']and('bytes'not in r or r['bytes']==a['bytes']),'whole actual original Ref2/3 evidence');return a


def write(path,value):
    with Path(path).open('x')as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n')
    return ref(path)


def replace(path,value):
    if Path(path).exists():Path(path).unlink()
    return write(path,value)


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def patch(text):
    need(len(text.encode())==OWNER_BYTES and hashlib.sha256(text.encode()).hexdigest()==OWNER_SHA,'exact retained v6 owning-boundary source before any transformation')
    marker='def bind(C,c,S,*,';need(text.count(OLD)==text.count(marker)==1 and 'def consumer_commandline('not in text,'one exact old commandline guard/owner function')
    after=text.replace(OLD,NEW,1).replace(marker,HELPER+marker,1)
    need(inverse(after)==text,'whole-file inverse, no numerical/resource/namespace/source guard omitted');return after


def inverse(text):
    need(text.count(HELPER)==text.count(NEW)==1 and OLD not in text,'one declared helper/call inverse');return text.replace(HELPER,'',1).replace(NEW,OLD,1)


def tests(path):return sum(isinstance(n,ast.FunctionDef)and n.name.startswith('test_')for n in ast.walk(ast.parse(path.read_bytes())))


def evidence(sr,owner_ref):
    m=obj(sr);o=obj(owner_ref);out=Path(owner_ref['path']).parent
    need(owner_ref==FAILED_OWNER and sr==SOURCE and out==Path(str(ROOT).replace('bole-g2','run-bole-g2').replace('-v7','-v6'))and owner_ref['path']==str(out/'RESULT.json'),'only actual retained failed G2-v6 source/output')
    need(o['source']==sr and o['primary']=="ValueError('actual exact-source independent consumer commandline')"and o['secondary']==[]and o['cpu_only']is False and o['source_before']and o['source_before']==o['source_after'],'actual commandline failure, source equal, no cleanup debt; never a parent model PASS')
    need(m['service_required_sameimage_software_cases']==258 and m['service_software_scope']['parent_exact_cases']==214 and m['service_software_scope']['new_current_cases']==44,'actual inherited258 software scope')
    need(m['service_experiment']==dict(schema='bole.c1-two-request-stream-service/v2',profile='smoke4',prefix=131,request_count=2,max_steps_per_request=3,max_output_tokens=4,capture_protocol='every-frame-independent-CPU-ACK/v1'),'unchanged actual bounded stream scope')
    owned=checked(m['files']['g2_stream_owner.py']);text=owned.read_text();patch(text)
    host=checked(m['files']['host_service.py']).read_text();need("argv[index+1:index+2]=['-I','-B'];"not in host and "C.need(argv[index+1]=='-B','exact original guest Python argv');"in host,'actual v6 original-B/CANN-aware launcher already repaired and must stay byteexact')
    boot_ref=ref(out/'dense/receipts/STREAM/STREAM_CONSUMER_BOOT.json');boot=obj(boot_ref)
    need(boot['schema']=='bole.actual-stream-consumer-BOOT/v2'and boot['source']==sr and boot['source_before']==m['files']and boot['Devices']==[]and boot['Torch_imported']is False,'actual exact-source pre-Torch Devices[] consumer BOOT')
    # The exact original025 runtime value is reopened, rather than guessed from
    # a partial executable basename or accepted from the BOOT itself.
    substrate=checked(m['files']['owned_substrate.py']).read_text();tree=ast.parse(substrate)
    base=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='BASE'for t in n.targets)))
    contract_path=Path(base)/'model_contract.py';original_contract_ref=m['dependencies'];matches=[r for r in original_contract_ref if r['path']==str(contract_path)];need(matches and all(checked(r)==contract_path for r in matches),'actual exact original025 contract in declared source readset')
    contract=contract_path.read_text();cn=ast.parse(contract);py=ast.literal_eval(next(n.value for n in cn.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PY'for t in n.targets)))
    expected=[py,'-B',str(Path(m['root'])/'g2_consumer.py'),'--execute','--bootstrap','--source-ref',json.dumps(ref(sr['path']))]
    need(boot['argv']==expected and boot['argv'][1:3]!=['-I','-B'],'actual same-source original-B argv conclusively contradicts stale -I/-B guard')
    fault_ref=FAULT;fault=obj(fault_ref);need(o['summary']['first_host_fault']==dict(path=FAULT['path'],bytes=FAULT['bytes'])and fault['source']==SOURCE and fault['error_repr']==o['primary']and'g2_stream_owner.py'in fault['traceback'],'actual owning-boundary failure trace with newly pinned full observed SHA; original partial Ref preserved')
    release_refs=[]
    for role in('cpu-preflight','dense','cpu-consumer'):
        r=ref(out/role/'cleanup.json');v=obj(r);need(v['stopped']is True and v['retained']is True and v['errors']==[],'every actual previous owned stage stopped retained');release_refs.append(r)
    workers=[]
    for rank in range(4):
        r=ref(out/'dense/receipts/STREAM'/('STREAM_WORKER_BOOT-RANK-%d.json'%rank));w=obj(r);need(w['source']==sr and w['rank']==rank and w['TP_world_size']==4,'all4 actual TP4 source-bound worker BOOT');workers.append(r)
    child_ref=legacy(o['summary']['actual_software_child']);child=obj(child_ref);need(child['exit_code']==0 and child['child_termination_observed']is True,'actual inherited software child passed, all rerun again in v7')
    stdout_ref=legacy(child['stdout_ref']);stderr_ref=legacy(child['stderr_ref']);summaries=[]
    for line in checked(stdout_ref).read_text().splitlines():
        try:v=json.loads(line)
        except ValueError:continue
        if type(v)is dict and v.get('schema')=='bole.G2-explicit-combined-software-gate/v1':summaries.append(v)
    need(len(summaries)==1 and summaries[0]['source']==sr and summaries[0]['tests']==258 and summaries[0]['historical_cases']==214 and summaries[0]['current_cases']==44 and summaries[0]['all_tests_passed']is True,'actual258 software scope only; not model qualification')
    mtp=[legacy(r)for r in o['summary']['MTP_load_receipts']];need(len(mtp)==4,'actual all4 native MTP load receipts retained')
    return m,[owner_ref,boot_ref,fault_ref,*release_refs,*workers,child_ref,stdout_ref,stderr_ref,*mtp],dict(actual_BOOT=boot_ref,actual_argv=expected,old_guard_rejected_only_guest_option_layout=True,first_host_fault=fault_ref,releases=release_refs,actual258_software_pass_only=True,actual_model_pass=False)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    for n in('failed-owner-ref','prior-builder-ref','manifest-ref'):p.add_argument('--'+n)
    a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    need(all(vars(a).values()),'retained actual failure, frozen collector and current reviewed manifest required')
    fo=json.loads(a.failed_owner_ref);failed,observed,cause=evidence(SOURCE,fo);br=json.loads(a.prior_builder_ref);need(br['sha256']==COLLECTOR_SHA,'unchanged corrected original source-owned collector');H=module('_g2_exact_v5_collector',checked(br))
    mr=json.loads(a.manifest_ref);manifest=obj(mr);need(mr==ref(P/'MANIFEST.json'),'reviewed current exact packet manifest')
    for name,w in manifest['files'].items():
        actual=ref(P/name);need((actual['bytes'],actual['sha256'])==(w['bytes'],w['sha256'])and Path(w['path']).name==name,'portable exact reviewed bytes/SHA, advisory paths only lineage '+name)
    need(ref(__file__)==ref(P/'prepare_g2_consumer_v7.py'),'exact executing reviewed builder')
    old=Path(failed['root']);need((P/'g2_stream_owner.py').read_text()==patch((old/'g2_stream_owner.py').read_text()),'reviewed current owner matches the only exact generated patch');need(not any(p.exists()for p in(ROOT,OUT,Path(str(OUT)+'-CPU'))),'fresh immutable v7 source/model/CPU leaves; actual failed v6 remains retained')
    baseline=H.collect(SOURCE);g1=failed['g2_predecessor'];parent=obj(g1['source']);historical=H.collect(g1['source'])
    shutil.copytree(old,ROOT,ignore=shutil.ignore_patterns('__pycache__'));(ROOT/'SOURCE_BOUND.json').rename(ROOT/'FAILED_G2_V6_SOURCE_BOUND.json')
    for n in('COMMANDS.json',failed['command_scope']['compatibility_file']):(ROOT/n).rename(ROOT/('FAILED_G2_V6_'+n))
    for n in manifest['files']:shutil.copyfile(P/n,ROOT/n)
    (ROOT/'g2_stream_owner.py').write_text(patch((old/'g2_stream_owner.py').read_text()));(ROOT/'contract090.py').write_text(H.outputs((old/'contract090.py').read_text(),str(OUT)));shutil.copyfile(P/'MANIFEST.json',ROOT/'G2_EXACT_CONSUMER_V7_MANIFEST.json')
    changed={'g2_stream_owner.py','contract090.py','G2_STREAM_EDITS_V1.json'}
    for n,r in failed['files'].items():
        checked(r)
        if n not in changed:need((ROOT/n).read_bytes()==checked(r).read_bytes(),'all original numerical/runtime/consumer/oracle/resource/258 controls byteexact '+n)
    delta={}
    for n,r in parent['files'].items():
        if(ROOT/n).is_file()and Path(r['path']).is_relative_to(Path(parent['root'])):
            before=checked(r).read_text();after=(ROOT/n).read_text()
            if before!=after:delta[n]=dict(before=r,after=ref(ROOT/n),edits=[dict(before=before,after=after)])
    replace(ROOT/'G2_STREAM_EDITS_V1.json',dict(schema='bole.exact-G2-stream-inverse-to-G1v2/v1',baseline=g1['source'],files=delta,original_math_unchanged=True,original_G1v2_full_controls_rerun_separately=True))
    replace(ROOT/'G2_EXACT_CONSUMER_EDITS_V7.json',dict(schema='bole.exact-consumer-commandline-repair/v7',baseline=SOURCE,files={n:dict(before=failed['files'][n],after=ref(ROOT/n),edits=[dict(before=(old/n).read_text(),after=(ROOT/n).read_text())])for n in('g2_stream_owner.py','contract090.py')},guest_original_B_and_host_I_B_retained=True,consumer_oracle_math_resources_unchanged=True))
    m=json.loads(json.dumps(failed));m.pop('prepared_template',None);m.update(root=str(ROOT),output_root=str(OUT),model_receipt_root=str(OUT/'dense/receipts'),prepared_only=True,default_enabled=False)
    def remap(r):return ref(ROOT/Path(r['path']).relative_to(old))if Path(r['path']).is_relative_to(old)else r
    m['files']={n:remap(r)for n,r in m['files'].items()}
    for n in(*manifest['files'],'G2_EXACT_CONSUMER_V7_MANIFEST.json','G2_EXACT_CONSUMER_EDITS_V7.json'):m['files'][n]=ref(ROOT/n)
    for key in('service_runtime_source_snapshots','g1_overlay','g1_repair_v2_overlay','g2_overlay'):m[key]={n:remap(r)for n,r in m.get(key,{}).items()}
    for row in m['g2_builder_portability_v2']['inventory'].values():row['actual_bound']=m['files'][Path(row['actual_bound']['path']).name]
    m['stream_channel_root']=str(OUT/'dense/receipts/STREAM');m['stream_channel_contract_path']=str(OUT/'dense/receipts/STREAM/CHANNEL.json');m['stream_consumer_source']=m['files']['g2_consumer.py']
    added=tests(ROOT/'test_g2_consumer_argv.py');need(added==8,'eight real new source/argv/inverse/defaultOFF controls');m['service_software_scope']=dict(m['service_software_scope'],new_current_cases=44+added);m['service_required_sameimage_software_cases']=258+added
    m['g2_exact_consumer_v7']=dict(failed_source=SOURCE,failed_model_owner=fo,manifest=mr,actual_preparer=ref(__file__),cause=cause,original258_controls_fresh_rerun_required=True,added_argv_controls=added,full_actual_executable_script_flags_canonical_source_argv_required=True,native_math_consumer_resource_protocol_unchanged=True,previous_failed_model_is_not_qualification=True)
    required=H.unique([*baseline['refs'],*historical['refs'],SOURCE,*observed,br,mr,*[ref(P/n)for n in manifest['files']]]);m['dependencies']=H.unique([*failed['dependencies'],*required])
    for n in('SOURCE_TEMPLATE.json','SOURCE.json'):replace(ROOT/n,m)
    tr=ref(ROOT/'SOURCE_TEMPLATE.json');q=subprocess.run(['/usr/bin/python3','-I','-B',str(ROOT/'bind_model.py'),'--execute','--reviewed-template-ref',json.dumps(tr),'--component-refs-json',json.dumps(m['component_refs'])],capture_output=True,text=True,timeout=60);need(q.returncode==0,'new exact binding failed '+q.stdout+q.stderr)
    sr=ref(ROOT/'SOURCE_BOUND.json');bound=obj(sr);sys.path.insert(0,str(ROOT));cc=module('_g2_v7_exact_commands',ROOT/'command_contract.py');history=obj(m['command_scope']['historical_ref'])
    commands=dict(schema='bole.G1-actual-bound-commands/v2',source=tr,bound_source=sr,**cc.expected(str(ROOT),str(OUT),sr,tr,m['component_refs']),required_sameimage_software_cases=m['service_required_sameimage_software_cases'],historical_required_sameimage_software_cases=history['required_sameimage_software_cases'],legacy_entrypoints_retained_for_inverse_tests_only=True,actual_G1_execution_claimed=False,G2_stream_protocol=True,actual_G2_execution_claimed=False)
    replace(ROOT/'COMMANDS.json',commands);replace(ROOT/m['command_scope']['compatibility_file'],dict(source=sr,template=tr,commands=ref(ROOT/'COMMANDS.json'),model=commands['model'],CPU=commands['CPU'],required_sameimage_software_cases=m['service_required_sameimage_software_cases']))
    cc.validate(cc.C,sr,bound);current=H.collect(sr);present={r['path']:r for r in current['refs']};need(all(present.get(r['path'])==r for r in required),'full actual failed-v6/qualifiedG1/source/evidence readset closure')
    need(inverse((ROOT/'g2_stream_owner.py').read_text())==(old/'g2_stream_owner.py').read_text(),'whole owning-boundary inverse after exact source assembly')
    for f in ROOT.rglob('*.py'):compile(f.read_bytes(),str(f),'exec')
    print(json.dumps(dict(source=sr,commands=ref(ROOT/'COMMANDS.json'),prospective_sameimage_cases=m['service_required_sameimage_software_cases'],original258_fresh_rerun=True,new_controls=added,full_readset_missing=[],consumer_oracle_runtime_math_resources_unchanged=True,guest_original_B_retained=True,actual_model_executed=False,model_ready=False,NPU=False)));return 0


if __name__=='__main__':raise SystemExit(main())
