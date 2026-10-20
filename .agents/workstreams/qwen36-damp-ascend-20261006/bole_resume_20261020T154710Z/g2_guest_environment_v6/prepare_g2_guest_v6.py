"""Prepare a fresh G2 leaf restoring the proven CANN-aware guest Python argv."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

SOURCE = dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v5/SOURCE_BOUND.json',
              bytes=414541, sha256='6dc571c598681f49b63a1c11b10f8be545b126fcfab12aa1cab7ea68cdae4006')
ROOT = Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v6')
OUT = ROOT.with_name('run-'+ROOT.name)
BUILDER = Path(__file__).resolve().parent


def need(v, s):
    if not v:
        raise ValueError(s)


def ref(p):
    p = Path(p)
    need(p.is_absolute() and p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)), 'ordinary absolute file')
    b = p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def obj(r):
    need(type(r) is dict and set(r)=={'path','bytes','sha256'} and ref(r['path'])==r, 'complete exact Ref3')
    return json.loads(Path(r['path']).read_bytes())


def replace(p,v):
    if p.exists():
        p.unlink()
    with p.open('x') as f:
        json.dump(v,f,sort_keys=True,allow_nan=False)
        f.write('\n')


def load(name,p):
    s=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def guest_argv_repair(text):
    old="argv[index+1:index+2]=['-I','-B'];"
    need(text.count(old)==1, 'one exact inherited guest isolated-mode insertion')
    repaired=text.replace(old,'',1)
    need(repaired.count("C.need(argv[index+1]=='-B','exact original guest Python argv');")==1,
         'original guest-B guard retained')
    need(repaired.replace("C.need(argv[index+1]=='-B','exact original guest Python argv');",
         "C.need(argv[index+1]=='-B','exact original guest Python argv');"+old,1)==text,
         'exact inverse; no other host body changed')
    return repaired


def main():
    p=argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument('--execute',action='store_true')
    for name in ('failed-owner-ref','prior-builder-ref','manifest-ref'):
        p.add_argument('--'+name)
    a=p.parse_args()
    if not a.execute:
        print('{"enabled":false,"NPU":false}')
        return 0
    need(all(vars(a).values()), 'exact failure, frozen prior collector and reviewed new manifest required')
    fs=SOURCE;failed=obj(fs);fo=json.loads(a.failed_owner_ref);owner=obj(fo)
    need(fo['path']=='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v5/RESULT.json' and
         owner['source']==fs and owner['cpu_only'] is False and owner['primary']=="ValueError('one bounded native server startup')" and
         owner['secondary']==[] and owner['source_before']==owner['source_after'], 'actual stopped failed-v5 producer retained')
    stderr=Path(fo['path']).parent/'dense/server.stderr'
    need("ModuleNotFoundError: No module named 'acl'" in stderr.read_text() and
         failed['service_required_sameimage_software_cases']==258, 'observed pyACL failure and exact258 suite')
    br=json.loads(a.prior_builder_ref);obj_source=Path(br['path']);need(ref(obj_source)==br and
         br['bytes']==16604 and br['sha256']=='ce4f5c41be679f0f969b7178e02667461a7f2f601d7c5c8f19c04dabb8f23dd3', 'frozen actual v5 preparation/readset helper')
    H=load('_g2_exact_v5_builder',obj_source)
    mr=json.loads(a.manifest_ref);manifest=obj(mr)
    need(mr==ref(BUILDER/'MANIFEST.json'), 'reviewed current manifest')
    for name,r in manifest['files'].items():
        actual=ref(BUILDER/name)
        need((actual['bytes'],actual['sha256'])==(r['bytes'],r['sha256']), 'reviewed flat source bytes '+name)
    old=Path(failed['root']);need(not ROOT.exists() and not OUT.exists() and not Path(str(OUT)+'-CPU').exists(), 'fresh immutable v6 source/output leaves')
    baseline=H.collect(fs);g1=failed['g2_predecessor'];parent=obj(g1['source']);historical=H.collect(g1['source'])
    shutil.copytree(old,ROOT,ignore=shutil.ignore_patterns('__pycache__'))
    (ROOT/'SOURCE_BOUND.json').rename(ROOT/'FAILED_G2_V5_SOURCE_BOUND.json')
    for name in ('COMMANDS.json',failed['command_scope']['compatibility_file']):
        (ROOT/name).rename(ROOT/('FAILED_G2_V5_'+name))
    (ROOT/'host_service.py').write_text(guest_argv_repair((old/'host_service.py').read_text()))
    (ROOT/'contract090.py').write_text(H.outputs((old/'contract090.py').read_text(),str(OUT)))
    shutil.copyfile(__file__,ROOT/'prepare_g2_guest_v6.py')
    shutil.copyfile(BUILDER/'MANIFEST.json',ROOT/'G2_GUEST_ENV_V6_MANIFEST.json')
    for name,r in failed['files'].items():
        need(ref(r['path'])==r, 'unchanged retained original source')
        if name not in ('host_service.py','contract090.py','G2_STREAM_EDITS_V1.json'):
            need((ROOT/name).read_bytes()==Path(r['path']).read_bytes(), 'all math/stream/tests/resources byteexact '+name)
    delta={}
    for name,r in parent['files'].items():
        target=ROOT/name
        if target.is_file() and Path(r['path']).is_relative_to(Path(parent['root'])):
            before=Path(r['path']).read_text();after=target.read_text()
            if before!=after:
                delta[name]=dict(before=r,after=ref(target),edits=[dict(before=before,after=after)])
    replace(ROOT/'G2_STREAM_EDITS_V1.json',dict(schema='bole.exact-G2-stream-inverse-to-G1v2/v1',baseline=g1['source'],files=delta,
        original_math_unchanged=True,original_G1v2_full_controls_rerun_separately=True))
    replace(ROOT/'G2_GUEST_ENV_EDITS_V6.json',dict(schema='bole.exact-guest-CANN-environment-repair/v6',baseline=fs,
        files={name:dict(before=failed['files'][name],after=ref(ROOT/name),edits=[dict(before=(old/name).read_text(),after=(ROOT/name).read_text())])
               for name in ('host_service.py','contract090.py')},guest_original_B_retained=True,host_I_B_retained=True,math_resources_unchanged=True))
    m=json.loads(json.dumps(failed));m.pop('prepared_template',None)
    m.update(root=str(ROOT),output_root=str(OUT),model_receipt_root=str(OUT/'dense/receipts'),prepared_only=True,default_enabled=False)
    def remap(r):
        return ref(ROOT/Path(r['path']).relative_to(old)) if Path(r['path']).is_relative_to(old) else r
    m['files']={name:remap(r) for name,r in m['files'].items()}
    for name in ('prepare_g2_guest_v6.py','G2_GUEST_ENV_V6_MANIFEST.json','G2_GUEST_ENV_EDITS_V6.json'):
        m['files'][name]=ref(ROOT/name)
    for key in ('service_runtime_source_snapshots','g1_overlay','g1_repair_v2_overlay','g2_overlay'):
        m[key]={name:remap(r) for name,r in m.get(key,{}).items()}
    for row in m['g2_builder_portability_v2']['inventory'].values():
        name=Path(row['actual_bound']['path']).name;row['actual_bound']=m['files'][name]
    m['stream_channel_root']=str(OUT/'dense/receipts/STREAM');m['stream_channel_contract_path']=str(OUT/'dense/receipts/STREAM/CHANNEL.json')
    m['stream_consumer_source']=m['files']['g2_consumer.py']
    m['g2_guest_environment_v6']=dict(failed_source=fs,failed_model_owner=fo,original_error=ref(stderr),
        manifest=mr,actual_preparer=ref(__file__),guest_original_B_retained=True,host_I_B_retained=True,
        original258_controls_fresh_rerun_required=True,original_mathematics_and_resource_profile_unchanged=True)
    required=H.unique([*baseline['refs'],*historical['refs'],fs,fo,ref(stderr),br,mr,*[ref(BUILDER/n) for n in manifest['files']]])
    m['dependencies']=H.unique([*failed['dependencies'],*required])
    for name in ('SOURCE_TEMPLATE.json','SOURCE.json'):
        replace(ROOT/name,m)
    tr=ref(ROOT/'SOURCE_TEMPLATE.json')
    r=subprocess.run(['/usr/bin/python3','-I','-B',str(ROOT/'bind_model.py'),'--execute','--reviewed-template-ref',json.dumps(tr),
                      '--component-refs-json',json.dumps(m['component_refs'])],capture_output=True,text=True,timeout=40)
    need(r.returncode==0,'new exact binding '+r.stdout+r.stderr)
    sr=ref(ROOT/'SOURCE_BOUND.json');bound=obj(sr);sys.path.insert(0,str(ROOT));cc=load('_g2_v6_commands',ROOT/'command_contract.py')
    history=obj(m['command_scope']['historical_ref'])
    commands=dict(schema='bole.G1-actual-bound-commands/v2',source=tr,bound_source=sr,
        **cc.expected(str(ROOT),str(OUT),sr,tr,m['component_refs']),required_sameimage_software_cases=258,
        historical_required_sameimage_software_cases=history['required_sameimage_software_cases'],
        legacy_entrypoints_retained_for_inverse_tests_only=True,actual_G1_execution_claimed=False,G2_stream_protocol=True,actual_G2_execution_claimed=False)
    replace(ROOT/'COMMANDS.json',commands)
    replace(ROOT/m['command_scope']['compatibility_file'],dict(source=sr,template=tr,commands=ref(ROOT/'COMMANDS.json'),model=commands['model'],CPU=commands['CPU'],required_sameimage_software_cases=258))
    cc.validate(cc.C,sr,bound);current=H.collect(sr);present={r['path']:r for r in current['refs']}
    need(not [r for r in required if present.get(r['path'])!=r], 'whole historical readset closure retained')
    for f in ROOT.rglob('*.py'):
        compile(ast.parse(f.read_bytes()),str(f),'exec')
    print(json.dumps(dict(source=sr,commands=ref(ROOT/'COMMANDS.json'),prospective_sameimage_cases=258,guest_original_B_retained=True,
        host_I_B_retained=True,mathematics_resources_unchanged=True,missing=[],actual_model_executed=False,NPU=False)))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
