"""Immutable v10: correct actual025 callee boundary + exact CPU-source snapshot."""
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
SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v9/SOURCE_BOUND.json',bytes=682545,sha256='7dafb83330946b4690824d188f688db8f445270e3c1f86d119c0728e269fef1f')
FAILED_OWNER=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v9-CPU/RESULT.json',bytes=849855,sha256='d4429c7642c40fa8e28b671e3e6d92bb2383cbd29baf110bdd7d37b142896e3c')
FAULT=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v9-CPU/HOST-FIRST-FAULT.json',bytes=2688,sha256='f6ceb2cd4cbda009a3bd5c1387216e4e4028df4238db4293a08a919950df07ba')
ROOT=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v10');OUT=ROOT.with_name('run-'+ROOT.name)
COLLECTOR_SHA='ce4f5c41be679f0f969b7178e02667461a7f2f601d7c5c8f19c04dabb8f23dd3'
PRESERVED=('host_service.py','owned_create.py','g2_cold_clock.py','g2_handoff.py','g2_handoff_cold.py','service_entry.py','test_g2_cold_clock.py','test_g2_cold_builder.py','prepare_g2_cold_v9.py','audit_source_v9.py','sourceio.py','g1_contract.py','g2_contract.py')


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


def proof_module(root,sourceio_ref):
    root=Path(root);need(checked(sourceio_ref)==root/'sourceio.py','exact declared proof IO source in reviewed root')
    existing=sys.modules.get('sourceio')
    need(existing is None or ref(existing.__file__)==sourceio_ref,'no foreign preloaded source IO namespace')
    sys.path.insert(0,str(root))
    proof=module('_g2_v10_bound_callee_snapshot_proof',root/'g2_callee_proof.py')
    need(ref(proof.C.__file__)==sourceio_ref,'actual proof IO imported from exact reviewed source')
    return proof


def inverse(text):
    after="def parent_alias(c,sr,leaf,readset,source_root):\n    m=c.obj(sr);parent=c.obj(m['g2_cold_clock_v9']['parent_source']);alias=Path(parent['output_root'])/'cpu-preflight'"
    before="def parent_alias(C,sr,leaf,readset,source_root):\n    m=C.obj(sr);parent=C.obj(m['g2_cold_clock_v9']['parent_source']);alias=Path(parent['output_root'])/'cpu-preflight'"
    need(text.count(after)==1,'one exact callee-parameter shadowing repair; same complete alias guard')
    return text.replace(after,before,1)


def evidence(sr,owner_ref):
    need(sr==SOURCE and owner_ref==FAILED_OWNER,'only retained actual cold-clock v9 precreate CPU failure')
    m=obj(sr);o=obj(owner_ref);f=obj(FAULT)
    need(m['service_required_sameimage_software_cases']==297 and m['service_software_scope']['parent_exact_cases']==279 and m['service_software_scope']['new_current_cases']==18 and m['g2_cold_clock_v9']['original3600_and180_cutoff_unchanged']is True,'actual immutable v9 clock/candidate/source scope, no software/model pass inferred')
    need(o['source']==sr and o['cpu_only']is True and o['primary']==f['error_repr']=="AttributeError(\"module 'model_contract' has no attribute 'need'\")"and o['secondary']==[]and o['source_before']and o['source_before']==o['source_after']and o['source_before'].get(sr['path'])==sr['sha256']and o['cleanup_spent']==0 and set(o['summary'])=={'first_host_fault'},'actual source-stable no-CID precreate failure; no cached297/parser/cold/NPU pass')
    need(o['summary']['first_host_fault']=={k:FAULT[k]for k in('path','bytes')}and f['source']==sr and f['error_type']=='builtins.AttributeError'and f['cleanup_not_started']is True and f['fail_closed']is True and f['recovery_attempted']is False and f['phase']['step']=='create-start-inspect'and'parent_alias(c,sr,leaf,readset,source_root)'in f['traceback']and'C.need(alias.is_absolute()'in f['traceback'],'actual original025 helper callee/parameter shadowing first fault')
    need('safety_host.py'not in m['files'],'actual old18 CPU source-read fallback lacks its declared snapshot')
    return m,[sr,owner_ref,FAULT],dict(parent_source=sr,failed_cpu_owner=owner_ref,first_fault=FAULT,actual_parent_297_executed=False,actual_parent_parser_executed=False,actual_parent_cold_executed=False,actual_parent_model_executed=False,actual_parent_CID_created=False,cold_clock_and_candidate_retained=True,original297_test_file_bytes_preserved=True,callee_repair='original025 c.obj remains real; unshadowed sourceio C.need owns alias assertion',source_snapshot_fix='exact original declared safety_host source only; original owner still loads original025 Ref')


def main():
    parser=argparse.ArgumentParser(allow_abbrev=False);parser.add_argument('--execute',action='store_true')
    for n in('failed-owner-ref','prior-builder-ref','manifest-ref'):parser.add_argument('--'+n)
    a=parser.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    need(all(vars(a).values()),'actual failed CPU/correct collector/reviewed new manifest Refs required')
    parent,observed,cause=evidence(SOURCE,json.loads(a.failed_owner_ref));br=json.loads(a.prior_builder_ref);need(br['sha256']==COLLECTOR_SHA,'unchanged original exact source-owned canonical command/readset collector');H=module('_g2_v10_original_collector',checked(br));mr=json.loads(a.manifest_ref);manifest=obj(mr);need(mr==ref(P/'MANIFEST.json'),'exact externally reviewed current packet manifest')
    for n,w in manifest['overlay_files'].items():
        actual=ref(P/n);need((actual['bytes'],actual['sha256'])==(w['bytes'],w['sha256'])and Path(w['path']).name==n,'ordinary portable current overlay; advisory paths remain lineage only '+n)
    io=ref(P/'sourceio.py');need((io['bytes'],io['sha256'])==(parent['files']['sourceio.py']['bytes'],parent['files']['sourceio.py']['sha256']),'original source IO proof support byteexact');Q=proof_module(P,io);declared=Q.declarations(checked(parent['files']['owned_substrate.py']))
    for r in declared.values():checked(r)
    old=Path(parent['root']);need(not any(p.exists()for p in(ROOT,OUT,Path(str(OUT)+'-CPU'))),'new immutable v10 source/model/CPU leaves; v9 failure retained')
    need(inverse((P/'g2_cold_parent_output.py').read_text())==checked(parent['files']['g2_cold_parent_output.py']).read_text(),'exact complete actual v9 helper inverse, no guard or argv/resource change')
    for n in PRESERVED:need((P/n).read_bytes()==checked(parent['files'][n]).read_bytes(),'original18 tests and runtime clock/candidate/source/wrapper preserved byteexact '+n)
    baseline=H.collect(SOURCE);g1=parent['g2_predecessor'];g1m=obj(g1['source']);historical=H.collect(g1['source'])
    shutil.copytree(old,ROOT,ignore=shutil.ignore_patterns('__pycache__'));(ROOT/'SOURCE_BOUND.json').rename(ROOT/'FAILED_G2_V9_SOURCE_BOUND.json')
    for n in('COMMANDS.json',parent['command_scope']['compatibility_file']):(ROOT/n).rename(ROOT/('FAILED_G2_V9_'+n))
    for n in manifest['overlay_files']:shutil.copyfile(P/n,ROOT/n)
    (ROOT/'contract090.py').write_text(H.outputs((old/'contract090.py').read_text(),str(OUT)));shutil.copyfile(P/'MANIFEST.json',ROOT/'G2_CALLEE_V10_MANIFEST.json')
    shutil.copyfile(checked(declared['safety_host']),ROOT/'safety_host.py');snapshot=ref(ROOT/'safety_host.py');need((snapshot['bytes'],snapshot['sha256'])==(declared['safety_host']['bytes'],declared['safety_host']['sha256']),'byteequal source-test snapshot only, never change genuine025 imports')
    changed={'g2_cold_parent_output.py','contract090.py','G2_STREAM_EDITS_V1.json'}
    for n,r in parent['files'].items():
        if n not in changed:need((ROOT/n).read_bytes()==checked(r).read_bytes(),'all original297 tests/math/128/argv/atomic/metadata/CPU/RAM/disk/HBM sources byteexact '+n)
    delta={}
    for n,r in g1m['files'].items():
        if(ROOT/n).is_file()and Path(r['path']).is_relative_to(Path(g1m['root'])):
            before=checked(r).read_text();after=(ROOT/n).read_text()
            if before!=after:delta[n]=dict(before=r,after=ref(ROOT/n),edits=[dict(before=before,after=after)])
    replace(ROOT/'G2_STREAM_EDITS_V1.json',dict(schema='bole.exact-G2-stream-inverse-to-G1v2/v1',baseline=g1['source'],files=delta,original_math_unchanged=True,original_G1v2_full_controls_rerun_separately=True))
    ledger=replace(ROOT/'G2_CALLEE_EDITS_V10.json',dict(schema='bole.exact-actual025-callee-boundary-inverse/v10',baseline=SOURCE,files={n:dict(before=parent['files'][n],after=ref(ROOT/n),edits=[dict(before=checked(parent['files'][n]).read_text(),after=(ROOT/n).read_text())])for n in('g2_cold_parent_output.py','contract090.py')},added_CPU_source_snapshot=dict(original_ref=declared['safety_host'],snapshot_ref=snapshot,byteequal=True,CPU_test_source_only=True,actual_owner_original025_Ref_unchanged=True,snapshot_imported_as_controller=False),original297_test_files_byteexact=True))
    m=json.loads(json.dumps(parent));m.pop('prepared_template',None);m.update(root=str(ROOT),output_root=str(OUT),model_receipt_root=str(OUT/'dense/receipts'),prepared_only=True,default_enabled=False)
    def remap(r):return ref(ROOT/Path(r['path']).relative_to(old))if Path(r['path']).is_relative_to(old)else r
    m['files']={n:remap(r)for n,r in m['files'].items()}
    for n in(*manifest['overlay_files'],'safety_host.py','G2_CALLEE_V10_MANIFEST.json','G2_CALLEE_EDITS_V10.json'):m['files'][n]=ref(ROOT/n)
    for key in('service_runtime_source_snapshots','g1_overlay','g1_repair_v2_overlay','g2_overlay'):m[key]={n:remap(r)for n,r in m.get(key,{}).items()}
    for row in m['g2_builder_portability_v2']['inventory'].values():row['actual_bound']=m['files'][Path(row['actual_bound']['path']).name]
    m['stream_channel_root']=str(OUT/'dense/receipts/STREAM');m['stream_channel_contract_path']=str(OUT/'dense/receipts/STREAM/CHANNEL.json');m['stream_consumer_source']=m['files']['g2_consumer.py']
    added=sum(tests(ROOT/n)for n in manifest['overlay_files']if n.startswith('test_g2_cold'))
    m['service_software_scope']=dict(m['service_software_scope'],new_current_cases=18+added);m['service_required_sameimage_software_cases']=297+added
    snapshot_proof=Q.verify_snapshot(m)
    m['g2_callee_contract_v10']=dict(cause,manifest=mr,actual_preparer=ref(__file__),whole_current_inverse=ledger,original025_sources=declared,CPU_source_test_snapshot=snapshot_proof,historical_source_v8_fresh_cases=279,current_source_v10_original_v9_byteequal_cases=18,current_source_v10_new_real_callee_controls=added,old_v9_inverse_and_manifest_are_historical=True,original_phase3600_cleanup180_cutoff_unchanged=True,sameimage_actual_parser_and_cold_before_NPU_required=True)
    required=H.unique([*baseline['refs'],*historical['refs'],SOURCE,*observed,*declared.values(),br,mr,*[ref(P/n)for n in manifest['overlay_files']]])
    m['dependencies']=H.unique([*parent['dependencies'],*required])
    for n in('SOURCE_TEMPLATE.json','SOURCE.json'):replace(ROOT/n,m)
    tr=ref(ROOT/'SOURCE_TEMPLATE.json');q=subprocess.run(['/usr/bin/python3','-I','-B',str(ROOT/'bind_model.py'),'--execute','--reviewed-template-ref',json.dumps(tr),'--component-refs-json',json.dumps(m['component_refs'])],capture_output=True,text=True,timeout=60);need(q.returncode==0,'new exact source binding failed '+q.stdout+q.stderr)
    sr=ref(ROOT/'SOURCE_BOUND.json');bound=obj(sr);need(ref(sys.modules['sourceio'].__file__)==io,'only reviewed proof IO namespace may be replaced by current source-owned IO');sys.modules.pop('sourceio');sys.path.insert(0,str(ROOT));cc=module('_g2_v10_current_source_owned_commands',ROOT/'command_contract.py');history=obj(m['command_scope']['historical_ref']);need(ref(cc.C.__file__)==bound['files']['sourceio.py'],'command contract uses actual current source-owned IO and canonical Ref order')
    commands=dict(schema='bole.G1-actual-bound-commands/v2',source=tr,bound_source=sr,**cc.expected(str(ROOT),str(OUT),sr,tr,m['component_refs']),required_sameimage_software_cases=m['service_required_sameimage_software_cases'],historical_required_sameimage_software_cases=history['required_sameimage_software_cases'],legacy_entrypoints_retained_for_inverse_tests_only=True,actual_G1_execution_claimed=False,G2_stream_protocol=True,actual_G2_execution_claimed=False)
    replace(ROOT/'COMMANDS.json',commands);replace(ROOT/m['command_scope']['compatibility_file'],dict(source=sr,template=tr,commands=ref(ROOT/'COMMANDS.json'),model=commands['model'],CPU=commands['CPU'],required_sameimage_software_cases=m['service_required_sameimage_software_cases']))
    cc.validate(cc.C,sr,bound);current=H.collect(sr);present={r['path']:r for r in current['refs']};need(all(present.get(r['path'])==r for r in required)and present[snapshot['path']]==snapshot,'complete actual failure/original025/new snapshot/whole inverse/current command readset closure')
    Q.verify_snapshot(bound)
    for f in ROOT.rglob('*.py'):compile(f.read_bytes(),str(f),'exec')
    print(json.dumps(dict(source=sr,commands=ref(ROOT/'COMMANDS.json'),prospective_sameimage_cases=297+added,historical_source_v8_fresh_cases=279,current_source_v10_original_v9_test_cases=18,current_source_v10_new_real_callee_cases=added,source_snapshot=snapshot_proof,actual_sameimage_executed=False,actual_cold_handoff_executed=False,actual_model_executed=False,model_ready=False,NPU=False)));return 0


if __name__=='__main__':raise SystemExit(main())
