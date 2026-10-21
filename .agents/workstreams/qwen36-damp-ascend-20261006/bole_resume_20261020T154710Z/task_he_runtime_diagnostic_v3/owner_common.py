"""Small owner IO/readset helpers. No model/runner/device imports."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

P=Path(__file__).resolve().parent
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
PACKET_SHA='33761994f0fcd18ec39f21ad0fa93a3fdfb11649d18a0a53f37667bc02abb37d'
LEGACY_PACKET_SHA='f687ad69fa0226fe72565e8ed356b65244a475c570259c865e6b3cf68fcda851'
DIAGNOSTIC_EXPECTED_SHA='840997a1e04f485a74d8ae19a40b61593631c3dba459d26c22a6e714d9308a3c'
G1_SOURCE=(109479,'010914ebe1bf5d3e6b516103e1a376e24e0a0d965ac0a3a42d7aeb19fca57677')
G1_OWNER=(131517,'52030a932da1f3cd2392389a2d9246925e40c2d93186b5f67d41fba8cfa1e4fc')
G1_INDEPENDENT=(12221,'8caf55b28f4a3c4108b8b932e9c664e08b3c28ea18f0bf4fc3bdf62de3538d53')
TOKENIZER_EXPECTED_SHA='28a71ff1b869462007b18db85f6ecde8227c5d46b89a1c9a89b7702b32ec1063'
PREVIOUS_EXPECTED_SHA='c29908e4f662fa532c7adea54a6a6ee2bda6169c5ccc5168deb2e62e2678fbc0'
PREVIOUS_DIAGNOSTIC_EXPECTED_SHA='56d2964926c23936afe3cf8ec77ca9fbd2edf32cca51ab4006bd65640ed6fd3a'
PHASE=3600;CLEANUP=180;CPU=145;HOST_CPU=166;GIB=2**30

def need(value,message):
    if not value:raise ValueError(message)

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def ref(path):
    p=Path(path);need(p.is_absolute()and p.is_file()and not any(v.is_symlink()for v in(p,*p.parents)),'ordinary exact Ref')
    before=p.stat();h=hashlib.sha256();size=0
    with p.open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b);size+=len(b)
    after=p.stat();need((before.st_ino,before.st_mtime_ns,before.st_size)==(after.st_ino,after.st_mtime_ns,after.st_size)and size==after.st_size,'stable complete Ref')
    return dict(path=str(p),bytes=size,sha256=h.hexdigest())

def checked(reference):
    need(type(reference)is dict and set(reference)in({'path','sha256'},{'path','bytes','sha256'}),'original Ref2 or strict Ref3')
    actual=ref(reference['path']);need(actual['sha256']==reference['sha256']and('bytes'not in reference or actual['bytes']==reference['bytes']),'whole exact source/evidence bytes')
    return Path(reference['path'])

def obj(reference):return json.loads(checked(reference).read_bytes())

def write(path,value):
    p=Path(path);need(p.is_absolute()and p.parent.is_dir()and not p.exists(),'new exact output')
    with p.open('xb')as f:f.write(canonical(value)+b'\n');f.flush();__import__('os').fsync(f.fileno())
    return ref(p)

def load(reference,name):
    need(name not in sys.modules,'fresh exact private module '+name)
    spec=importlib.util.spec_from_file_location(name,checked(reference));m=importlib.util.module_from_spec(spec);sys.modules[name]=m
    try:spec.loader.exec_module(m);checked(reference)
    except BaseException:sys.modules.pop(name,None);raise
    return m

def authority(reference,seconds=0):
    v=obj(reference);need(v['start_epoch']<=time.time()and time.time()+seconds<v['cutoff_epoch'],'current separately supplied authority includes full finite budget')
    return v

def basis(source_ref,owner_ref,bundle_ref,independent_ref):
    for r,expected in((source_ref,G1_SOURCE),(owner_ref,G1_OWNER),(independent_ref,G1_INDEPENDENT)):
        need((ref(checked(r))['bytes'],r['sha256'])==expected,'exact actual successful G1 v2 basis')
    on=obj(source_ref);own=obj(owner_ref);bundle=obj(bundle_ref);ind=obj(independent_ref)
    need(own['source']==source_ref and own['primary']is None and own['secondary']==[]
         and ind['source']==source_ref and ind['inputs']==bundle_ref and ind['service_complete']is True
         and ind['completed_request_count']==2 and ind['model_ready']is False,'actual bounded G1 software/owner basis, no model promotion')
    for key in('CPU_release','model_release','independent_release'):
        release=obj(own['summary'][key]);need(release['stopped']is True and release['retained']is True and release['errors']==[],'actual preceding owned stages stopped retained')
    need(bundle['source']==source_ref,'same actual G1 input bundle')
    return on


FILES=('owner_common.py','owner_namespace.py','main_quiescence.py','he_owned.py','he_policy.py','task_contract.py',
       'prepare_diagnostic.py','prepare_registry.py','diagnostic_host.py','he_runtime_probe.py','lock_evidence.py','network_evidence.py','probe_evidence.py','test_diagnostic_pure.py','test_quiescence_pure.py')


def inputs(reference):
    x=obj(reference)
    need(x['schema']=='bole.HE-runtime-isolation-diagnostic-inputs/v1'and x['diagnostic_revision']==3 and x['default_enabled']is False
         and x['diagnostic_only']is True and x['image_id']==IMAGE
         and x['phase_seconds']==3600 and x['cleanup_seconds']==180
         and x['host_CPU']==166 and x['CPU']==145 and x['HE_memory_bytes']==2*GIB
         and x['reserve_CPU_budget']==2 and x['summed_ancestor_CPU_budget']==7
         and x['HE_seconds']==90 and x['identity_hold_seconds']==5
         and x['generated_code_executed']is False and x['task_score_produced']is False,
         'exact finite nonprivileged HE runtime-only diagnostic source')
    need(set(x['files'])==set(FILES),'whole exact diagnostic executable closure')
    for n,r in x['files'].items():need(checked(r)==P/n,'current whole source-bound diagnostic code')
    authority(x['authority_ref'])
    import main_quiescence as Q
    Q.policy(x['main_quiescence_ref'],authority_ref=x['authority_ref'])
    stage=obj(x['stage_ref']);need(stage['schema']=='bole.he-runtime-isolation-diagnostic-stage/v1'
        and stage['source_root']==str(P/'public-source')and stage['image_id']==IMAGE,
        'explicit new probe public source stage; old evaluator untouched')
    cap=obj(stage['capsule_ref']);expected=obj(ref(P/'PREVIOUS_CPU_EXPECTED.json'))
    need(ref(P/'PREVIOUS_CPU_EXPECTED.json')['sha256']==PREVIOUS_EXPECTED_SHA
         and cap['schema']=='bole.HE-runtime-isolation-diagnostic-capsule/v1'
         and cap['identity_hold_seconds']==5 and cap['original_runtime_guard_unchanged']is True,
         'whole exact runtime-only diagnostic source capsule')
    rows=cap['files'];need(type(rows)is list and {r['relative']for r in rows}=={'he_worker.py','task_contract.py','he_runtime_probe.py','AUTHORITY.json'}and len(rows)==4,
         'only four exact public diagnostic sources')
    for row in rows:
        a=ref(Path(stage['source_root'])/row['relative'])
        need((a['bytes'],a['sha256'])==(row['bytes'],row['sha256']),'complete public capsule bytes')
        key={'he_worker.py':'original_he_worker','task_contract.py':'original_task_contract'}.get(row['relative'])
        if key is not None:need((a['bytes'],a['sha256'])==(expected[key]['bytes'],expected[key]['sha256']),'whole original guard/source remains unchanged')
        if row['relative']=='he_runtime_probe.py':need(a['sha256']==x['files']['he_runtime_probe.py']['sha256'],'actual declared diagnostic probe')
        if row['relative']=='AUTHORITY.json':need(a['sha256']==x['authority_ref']['sha256'],'same current diagnostic authority')
    return x
