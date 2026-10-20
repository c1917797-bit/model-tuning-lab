"""Stdlib source/readset checks; no Torch, host mutation or device admission."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
MODEL_SHA='11ac18fa31878609b6b56a9c9213d12729cdb466d14c587efcf6d261566a706c'
MODEL_ROOT=Path('/cache/efim/Qwen3.6-27B')
GUEST_MODEL=Path('/models/Qwen3.6-27B')
SCOPE=dict(schema='bole.c1-two-request-service/v1',prefix=131,request_count=2,
           max_steps_per_request=1,max_output_tokens=2)


def need(v,m):
    if not v:raise ValueError(m)


def ref(p):
    p=Path(p);need(p.is_absolute() and p.is_file() and not any(v.is_symlink()for v in(p,*p.parents)), 'ordinary absolute Ref')
    before=p.stat();h=hashlib.sha256();count=0
    with p.open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b);count+=len(b)
    after=p.stat();need((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns), 'stable bytes')
    return dict(path=str(p),bytes=count,sha256=h.hexdigest())


def checked(r):
    need(type(r)is dict and set(r)in({'path','bytes','sha256'},{'path','sha256'}),'exact Ref3 or original025 Ref2')
    actual=ref(r['path'])
    need(actual['sha256']==r['sha256'] and ('bytes'not in r or actual['bytes']==r['bytes']),'exact referenced whole bytes')
    return Path(r['path'])


def obj(r):
    p=checked(r);need(p.stat().st_size<=16*2**20,'bounded JSON')
    def pairs(rows):
        d={}
        for k,v in rows:need(k not in d,'duplicate JSON key');d[k]=v
        return d
    return json.loads(p.read_bytes(),object_pairs_hook=pairs,
        parse_constant=lambda v:(_ for _ in()).throw(ValueError('nonfinite JSON')))


def write(p,v):
    p=Path(p)
    with p.open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
    return ref(p)


def load(r,name):
    p=checked(r)
    if name in sys.modules:
        m=sys.modules[name];need(ref(m.__file__)==r,'fresh exact source namespace');return m
    s=importlib.util.spec_from_file_location(name,str(p));m=importlib.util.module_from_spec(s);sys.modules[name]=m
    try:s.loader.exec_module(m);need(ref(p)==r,'unchanged helper across import')
    except BaseException:sys.modules.pop(name,None);raise
    return m


def host_source(sr):
    """AR installed runtime refs are checked only inside the same image."""
    m=obj(sr)
    need(m['schema']=='bole.native-ar-pair-observer-source/v1' and m['prepared_only']is False and
         m['default_enabled']is False and m['expected_image_id']==IMAGE and
         Path(m['root']).is_absolute(),'bound defaultOFF actual AR source')
    for r in m['files'].values():checked(r)
    for r in m['runtime_sources'].values():
        need(type(r)is dict and set(r)=={'path','bytes','sha256'} and Path(r['path']).is_absolute() and
             r['path'].startswith(('/vllm-workspace/','/usr/local/python3.12.13/'))and type(r['bytes'])is int and r['bytes']>0 and
             re.fullmatch('[0-9a-f]{64}',r['sha256']),'installed runtime Ref declaration, not host path check')
    on=obj(m['BOLE_source_ref']);command=obj(m['BOLE_server_command_ref'])
    pair=load(m['files']['pair_contract.py'],'_ar_host_pair_contract')
    need(on['service_experiment']==SCOPE and command['source']==m['BOLE_source_ref'] and
         Path(m['BOLE_server_command_ref']['path'])==Path(on['model_receipt_root'])/'SERVER_COMMAND.json' and
         m['native_server_argv']==pair.native_argv(command['argv']) and
         m['runtime_sources']==on['runtime_sources'],'actual G1 v2 receipt command and exact single MTP argv delta')
    return m,on


def g1_pass(source_ref,owner_ref,bundle_ref,independent_ref):
    on=obj(source_ref);own=obj(owner_ref);b=obj(bundle_ref);v=obj(independent_ref)
    need((source_ref.get('bytes'),source_ref['sha256'])==(109479,'010914ebe1bf5d3e6b516103e1a376e24e0a0d965ac0a3a42d7aeb19fca57677')and
         (owner_ref.get('bytes'),owner_ref['sha256'])==(131517,'52030a932da1f3cd2392389a2d9246925e40c2d93186b5f67d41fba8cfa1e4fc')and
         (independent_ref.get('bytes'),independent_ref['sha256'])==(12221,'8caf55b28f4a3c4108b8b932e9c664e08b3c28ea18f0bf4fc3bdf62de3538d53'),
         'exact actual G1 repair-v2 full pass bytes, not an arbitrary successful source')
    need(on['service_experiment']==SCOPE and on['prepared_only']is False and
         own['schema']=='bole.actual-three-node-model-owned/v131' and own['source']==source_ref and
         own['primary']is None and own['secondary']==[] and own['source_before']==own['source_after'] and
         own['cpu_only']is False and own['summary']['independent']==independent_ref and
         b['schema']=='bole.actual-four-rank-two-request-inputs/v1' and b['source']==source_ref and
         v['schema']=='bole.actual-c1-two-request-service-independent/v1' and v['source']==source_ref and
         v['inputs']==bundle_ref and v['service_complete']is True and v['completed_request_count']==2 and
         v['component_checks_pass']is True and v['scheduler_committed_independently']is True and
         v['model_ready']is False and v['formal_success']is False,
         'actual full bounded G1 pass required; pending/failure/assertion cannot admit AR')
    for k in('CPU_release','model_release','independent_release'):
        release=obj(own['summary'][k]);need(release['stopped']is True and release['retained']is True and
            release['errors']==[],'actual G1 all owned phases stopped retained')
    need(len(b['ranks'])==4 and len(b['snapshots'])==4 and len(b['host_bindings'])==4,
         'actual all4 BOLE bundle')
    return on,own,b,v


def model_manifest(actual_ref,*,host,rehash=True):
    m=obj(actual_ref)
    need(actual_ref['bytes']==5813 and actual_ref['sha256']==MODEL_SHA and
         m['schema']=='qwen36.actual-model-manifest/v1' and m['host_model_root']==str(MODEL_ROOT) and
         m['complete_file_count']==29 and m['weight_shard_count']==15 and m['total_bytes']==55586107940 and
         m['image_id']==IMAGE,'actual exact 29-file/15-shard full checkpoint')
    root=MODEL_ROOT if host else GUEST_MODEL;seen=set();refs=[]
    for row in m['files']:
        name=row['relative_path'];need(name not in seen and not Path(name).is_absolute() and '..'not in Path(name).parts,
                                      'unique ordinary checkpoint names');seen.add(name)
        r=dict(path=str(root/name),bytes=row['size_bytes'],sha256=row['sha256'])
        if rehash:checked(r)
        refs.append(r)
    need(len(refs)==29 and sum(r['bytes']for r in refs)==55586107940 and
         len([r for r in refs if r['path'].endswith('.safetensors')])==15,'complete checkpoint accounting')
    return dict(schema='bole.actual-model-tokenizer-file-manifest/v1',model_root=str(GUEST_MODEL),
                files=refs,actual_host_manifest=actual_ref,host_paths_used_for_this_check=host,
                model_ready=False)


def readset(inputs,*,installed):
    """Complete executable/actual G1 evidence closure; host/installed path split."""
    sr=inputs['AR_source'];m,on=host_source(sr)
    need(inputs['authority']==m['authority_ref']==on['authority_ref']and
         inputs['shared_model_manifest']==m['model_manifest_ref']and
         inputs['G1_server_command']==m['BOLE_server_command_ref'],
         'one unchanged authority/shared model/actual ON command across owner and AR source')
    g1_pass(m['BOLE_source_ref'],inputs['G1_owner'],inputs['G1_bundle'],inputs['G1_independent'])
    refs={}
    def walk(v):
        if type(v)is dict:
            if set(v)in({'path','bytes','sha256'},{'path','sha256'}):
                if v not in m['runtime_sources'].values() or installed:checked(v);refs[v['path']]=ref(v['path'])
            else:
                for z in v.values():walk(z)
        elif type(v)is list:
            for z in v:walk(z)
    walk(inputs);walk(m['files']);walk(on['files']);walk(on.get('dependencies',[]))
    for k in('G1_owner','G1_bundle','G1_independent'):walk(obj(inputs[k]))
    walk(obj(inputs['G1_initial_profile']))
    b=obj(inputs['G1_bundle'])
    for r in b['journal']:checked(r)
    for row in b['ranks']:
        walk(obj(row['receipt']))
    walk(obj(b['http']))
    need(set(inputs['runtime_host_evidence'])==set(m['runtime_sources']),'complete distinct runtime host evidence map')
    for k,r in inputs['runtime_host_evidence'].items():
        checked(r);actual=m['runtime_sources'][k]
        need(r['path']!=actual['path'] and (r['bytes'],r['sha256'])==(actual['bytes'],actual['sha256']),
             'host source copy is content-equal but not an installed Ref path')
    return m,on,list(refs.values())
