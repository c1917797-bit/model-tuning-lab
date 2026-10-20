"""Freeze a fresh G1-v2 metadata/test repair; never edits failed v1 or V6."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys


def need(v,s):
    if not v:raise ValueError(s)
def ref(p):
    p=Path(p);b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):
    need(ref(r['path'])==r,'exact input Ref3');return json.loads(Path(r['path']).read_bytes())
def write(p,v):
    with p.open('x',encoding='utf8',newline='\n')as f:
        json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
def replace_json(p,v):
    if p.exists():p.unlink()
    write(p,v)
def count_tests(p):
    if not p.exists():return 0
    return sum(isinstance(n,ast.FunctionDef)and n.name.startswith('test_')for n in ast.walk(ast.parse(p.read_bytes())))
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def registry_plan(old_plan,before,after):
    need(hashlib.sha256(before).hexdigest()==old_plan['after_sha256'],'exact passed V6 R10 registry postimage')
    v=json.loads(json.dumps(old_plan))
    if before!=after:
        v['edits'].append(dict(new_start=0,new_end=len(after),new=after.decode(),old=before.decode()))
    v['after_sha256']=hashlib.sha256(after).hexdigest()
    v['G1_generation_layer']='exact current G1 source to passed V6 before original R10 inverse'
    raw=after
    for e in reversed(v['edits']):
        a,b=e['new_start'],e['new_end'];need(raw[a:b].decode()==e['new'],'exact registry inverse operand')
        raw=raw[:a]+e['old'].encode()+raw[b:]
    need(hashlib.sha256(raw).hexdigest()==v['before_sha256'],'complete registry inverse recovers original R3')
    return v


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--failed-source-ref');p.add_argument('--failed-owner-result-ref')
    p.add_argument('--overlay',type=Path);p.add_argument('--new-root',type=Path);p.add_argument('--output-root',type=Path)
    a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    need(all((a.failed_source_ref,a.failed_owner_result_ref,a.overlay,a.new_root,a.output_root)),'exact failed source/owner and new operands')
    parent_ref=json.loads(a.failed_source_ref);parent=obj(parent_ref);old=Path(parent['root'])
    failed_ref=json.loads(a.failed_owner_result_ref);failed=obj(failed_ref)
    need(failed['source']==parent_ref and failed['primary']is not None and failed['secondary']==[] and
         failed['source_before']==failed['source_after'] and failed['cpu_only']is True,
         'retained actual failed-v1 same-image owner with clean cleanup/unchanged source')
    need(parent['service_experiment']==dict(schema='bole.c1-two-request-service/v1',prefix=131,
        request_count=2,max_steps_per_request=1,max_output_tokens=2),'same bounded G1 runtime scope')
    for r in parent['files'].values():obj(r)if r['path'].endswith('/SOURCE_BOUND.json')else need(ref(r['path'])==r,'frozen failed-v1 file')
    lineage=parent['g1_predecessor'];v6_ref=lineage['source'];v6=obj(v6_ref);v6root=Path(v6['root'])
    original_ref=lineage['inverse_original'];original=obj(original_ref);original_root=Path(original['root'])
    preparer=module('_exact_original_G1_preparer',Path(parent['files']['prepare_g1.py']['path']))
    preparer.validate_parent_qualification(v6_ref,v6,lineage['owner_result'],lineage['independent_qualification'])
    new,out=a.new_root,a.output_root
    need(new.parent==out.parent==Path('/opt/host/vnf/austinov')and
         new.name.startswith('bole-g1-two-request-')and new.name.endswith('-v2')and
         out.name=='run-'+new.name and not new.exists()and not out.exists()and
         not Path(str(out)+'-CPU').exists(),'fresh explicit NEW-v2 source/model/CPU leaves')
    names=('host_service.py','command_contract.py','g1_inverse.py','test_model_calibration131r12.py',
        'test_repair14_delta.py','test_root_repeat_witness.py','test_output_contract_repair4.py',
        'test_g1_repair_v2.py','prepare_g1_repair_v2.py')
    overlays={name:a.overlay/name for name in names}
    need(all(f.is_file()for f in overlays.values()),'complete minimal v2 repair overlay')
    for f in overlays.values():compile(f.read_bytes(),str(f),'exec')
    shutil.copytree(old,new,ignore=shutil.ignore_patterns('__pycache__'))
    (new/'SOURCE_BOUND.json').rename(new/'PARENT_G1_V1_SOURCE_BOUND.json')
    for name,f in overlays.items():shutil.copyfile(f,new/name)
    path=new/'contract090.py';text=path.read_text();need(text.count(parent['output_root'])==2,'exact current output operands')
    path.write_text(text.replace(parent['output_root'],str(out)))
    # No runtime math/kernel/calibrator changes are admitted by this repair.
    for name in ('model_entry.py','worker_entry.py','cache_registry.py','service_runner.py','service_bridge.py',
        'model_process_calibration.py','model_calibration131r12.py','calibrate_conv118.py','core112.py',
        'adapter.py','oracle112.py','native_seams.py','treeconv118.py','independent_model.py'):
        need((new/name).read_bytes()==(old/name).read_bytes(),'v2 leaves actual runtime/math/calibration byteexact '+name)
    for name in ('model_calibration131r12.py','calibrate_conv118.py','core112.py','adapter.py',
                 'oracle112.py','native_seams.py','treeconv118.py','independent_model.py'):
        need((new/name).read_bytes()==(v6root/name).read_bytes(),'exact passed V6 numerical reference '+name)
    def methods(path):
        tree=ast.parse(path.read_bytes());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Bridge')
        return{n.name:ast.dump(n,include_attributes=False)for n in cls.body if isinstance(n,ast.FunctionDef)}
    a_math,b_math=methods(v6root/'model_entry.py'),methods(new/'model_entry.py')
    for name in ('_gdn','_fa','_anchors','_unchanged','_native_gdn_ar','_native_fa_ar',
                 'sequential_native_paths','stage_selected_path','greedy_proposal'):
        need(a_math[name]==b_math[name],'exact numerical model method before G1 historical inverse '+name)
    plan=obj(parent['files']['REGISTRY_EDITS131R10.json'])
    replace_json(new/'REGISTRY_EDITS131R10.json',registry_plan(plan,(v6root/'cache_registry.py').read_bytes(),(new/'cache_registry.py').read_bytes()))
    # The existing R14 full-source inverse is regenerated from its exact original
    # template, including new declared test/host metadata edits, never guessed.
    ledger={}
    for name,r in original['files'].items():
        if Path(r['path']).is_relative_to(original_root)and(new/name).is_file():
            need(ref(r['path'])==r,'exact original inverse source '+name)
            before,after=Path(r['path']).read_text(),(new/name).read_text()
            if before!=after:ledger[name]=dict(before=r,after=ref(new/name),edits=[dict(before=before,after=after)])
    replace_json(new/'FA_BOUNDARY_EDITS_R14.json',ledger)
    inverse={}
    for name,r in v6['files'].items():
        if Path(r['path']).is_relative_to(v6root)and(new/name).is_file():
            need(ref(r['path'])==r,'exact passed V6 source '+name)
            before,after=Path(r['path']).read_text(),(new/name).read_text()
            if before!=after:inverse[name]=dict(before=r,after=ref(new/name),edits=[dict(before=before,after=after)])
    proof=new/'G1_LIFECYCLE_EDITS_V1.json'
    write(proof,dict(schema='bole.exact-G1-lifecycle-inverse-to-passed-V6/v1',baseline_v6=v6_ref,
        failed_g1_v1=parent_ref,files=inverse,original_math_unchanged=True))
    m=json.loads(json.dumps(parent));m.update(root=str(new),output_root=str(out),
        model_receipt_root=str(out/'dense/receipts'),prepared_only=True,default_enabled=False)
    m.pop('prepared_template',None)
    for name,r in list(m['files'].items()):
        if Path(r['path']).is_relative_to(old):m['files'][name]=ref(new/Path(r['path']).relative_to(old))
    for name in (*overlays,'G1_LIFECYCLE_EDITS_V1.json'):m['files'][name]=ref(new/name)
    for key,r in list(m.get('service_runtime_source_snapshots',{}).items()):
        if Path(r['path']).is_relative_to(old):
            m['service_runtime_source_snapshots'][key]=ref(new/Path(r['path']).relative_to(old))
    # This field names the current copied G1 implementation, not its history.
    # Historical V6/failed-v1 refs remain explicit in their lineage fields.
    for name,r in list(m.get('g1_overlay',{}).items()):
        if Path(r['path']).is_relative_to(old):
            m['g1_overlay'][name]=ref(new/Path(r['path']).relative_to(old))
    m['dependencies']=[ref(new/Path(r['path']).relative_to(old))if Path(r['path']).is_relative_to(old)else r for r in m['dependencies']]
    historical=ref(v6root/'COMMANDS.json');obj(historical)
    m['dependencies'] += [parent_ref,failed_ref,historical,ref(__file__)]
    m['g1_inverse']=dict(baseline_v6=v6_ref,failed_g1_v1=parent_ref)
    m['command_scope']=dict(schema='bole.post-binding-command-readset/v2',file='COMMANDS.json',
        generated_after_binding=True,included_in_actual_host_readset=True,historical_ref=historical,
        compatibility_file='COMMANDS_G1.json',manifest_hash_cycle=False)
    delta=sum(count_tests(new/name)-count_tests(old/name)for name in overlays if name.startswith('test'))
    m['service_required_sameimage_software_cases']=parent['service_required_sameimage_software_cases']+delta
    m['g1_repair_v2']=dict(failed_source=parent_ref,failed_owner=failed_ref,
        actual_runtime_and_math_byteexact=True,commands_in_dynamic_host_readset=True,
        historical_inverse_layer_explicit=True,actual_G1_execution_claimed=False)
    m['g1_repair_v2_overlay']={name:ref(new/name)for name in overlays}
    for f in new.rglob('*.py'):compile(f.read_bytes(),str(f),'exec')
    for name in ('SOURCE_TEMPLATE.json','SOURCE.json'):replace_json(new/name,m)
    template=ref(new/'SOURCE_TEMPLATE.json')
    q=subprocess.run(['/usr/bin/python3','-I','-B',str(new/'bind_model.py'),'--execute',
        '--reviewed-template-ref',json.dumps(template),'--component-refs-json',json.dumps(parent['component_refs'])],
        cwd=new,capture_output=True,text=True,timeout=25)
    need(q.returncode==0,'actual v2 source binding '+q.stdout+q.stderr)
    sr=ref(new/'SOURCE_BOUND.json');bound=obj(sr)
    sys.path.insert(0,str(new));cc=module('_actual_v2_command_contract',new/'command_contract.py')
    historical_value=obj(historical)
    commands=dict(schema='bole.G1-actual-bound-commands/v2',source=template,bound_source=sr,
        **cc.expected(str(new),str(out),sr,template,parent['component_refs']),
        required_sameimage_software_cases=m['service_required_sameimage_software_cases'],
        historical_required_sameimage_software_cases=historical_value['required_sameimage_software_cases'],
        legacy_entrypoints_retained_for_inverse_tests_only=True,actual_G1_execution_claimed=False)
    replace_json(new/'COMMANDS.json',commands)
    replace_json(new/'COMMANDS_G1.json',dict(source=sr,template=template,commands=ref(new/'COMMANDS.json'),
        model=commands['model'],CPU=commands['CPU'],
        required_sameimage_software_cases=m['service_required_sameimage_software_cases']))
    cc.validate(cc.C,sr,bound)
    print(json.dumps(dict(source=sr,commands=ref(new/'COMMANDS.json'),
        compatibility_commands=ref(new/'COMMANDS_G1.json'),output=str(out),
        required_sameimage_cases=m['service_required_sameimage_software_cases'],
        actual_sameimage_executed=False,actual_scheduler_executed=False,model_ready=False)))
    return 0


if __name__=='__main__':raise SystemExit(main())
