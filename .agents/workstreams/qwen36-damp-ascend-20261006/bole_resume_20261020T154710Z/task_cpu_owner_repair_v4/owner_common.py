"""Small owner IO/readset helpers. No model/runner/device imports."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

P=Path(__file__).resolve().parent
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
PACKET_SHA='f687ad69fa0226fe72565e8ed356b65244a475c570259c865e6b3cf68fcda851'
G1_SOURCE=(109479,'010914ebe1bf5d3e6b516103e1a376e24e0a0d965ac0a3a42d7aeb19fca57677')
G1_OWNER=(131517,'52030a932da1f3cd2392389a2d9246925e40c2d93186b5f67d41fba8cfa1e4fc')
G1_INDEPENDENT=(12221,'8caf55b28f4a3c4108b8b932e9c664e08b3c28ea18f0bf4fc3bdf62de3538d53')
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


def packet(root):
    root=Path(root);mr=ref(root/'PROPOSAL_MANIFEST.json');need(mr['sha256']==PACKET_SHA,'whole unchanged frozen decoder/scorer packet')
    m=obj(mr)
    for name,row in m['files'].items():
        p=root/name;actual=ref(p);need((actual['bytes'],actual['sha256'])==(row['bytes'],row['sha256']),'every frozen task packet file unchanged')
    return mr


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


def task_readset(source_ref,*,host):
    """Explicit complete inputs/source readset. Large row arrays are streamed only.
    Runtime library files are checked inside the actual image, not guessed on host.
    No checkpoint weight file is added or hashed.
    """
    m=obj(source_ref);base=obj(m['rendered_inputs_ref']);original=obj(m['original_inputs_ref']);refs={}
    def add(r):
        path=Path(r['path'])
        need(path.suffix not in{'.safetensors','.bin','.pth'}and path.stat().st_size<=256*2**20,
             'bounded source/input/tokenizer only; never stream checkpoint weights')
        actual=ref(checked(r));refs[actual['path']]=actual;return actual
    add(source_ref)
    for r in m['files'].values():add(r)
    for key in('authority_ref','rendered_inputs_ref','original_inputs_ref','renderer_ref','official_source_ref','human_eval_package_ref'):add(m[key])
    add(base['official_audit_ref'])
    for header in(base,original):
        for value in header['tasks'].values():add(value['rows_ref'])
    oldsource=obj(m['official_source_ref']);add(oldsource['official_index_ref'])
    for r in original['original_sources']+original['gsm_sources']:add(r)
    he=obj(m['human_eval_package_ref'])
    for r in he['files']+[he['dataset_ref']]:add(r)
    # Exact pinned official GSM dataset implementation/license, not guessed names.
    sys.path.insert(0,m['root'])
    try:
        frozen=load(m['files']['frozen/gsm_scorer.py'],'_task_cpu_readset_gsm_'+str(len(sys.modules)))
        for key in('source','license'):add(frozen.BINDING['official_provenance'][key])
    finally:sys.path.pop(0)
    tokenizer=[]
    for r in base['tokenizer_assets']:
        p=Path(r['path']);need(p.parent==Path('/models/Qwen3.6-27B'),'exact tokenizer namespace')
        actual=dict(r,path=str(Path('/cache/efim/Qwen3.6-27B')/p.name))if host else r
        add(actual);tokenizer.append(dict(host=actual,guest=r))
    if not host:
        for r in original['library_refs']:add(r)
    return list(refs.values()),tokenizer


def inputs(reference,*,host=True,clock=True):
    x=obj(reference)
    need(x['schema']=='bole.task-finite-CPU-owner-inputs/v2'and x['default_enabled']is False
         and x['phase_seconds']==PHASE and x['cleanup_seconds']==CLEANUP and x['image_id']==IMAGE
         and x['CPU']==CPU and x['host_CPU']==HOST_CPU and x['guest_memory_bytes']==8*GIB
         and x['reserve_CPU_budget']==2 and x['summed_ancestor_CPU_budget']==7,'exact finite CPU-only owner profile')
    need(set(x['files'])=={'owner_common.py','owner_namespace.py','prepare_owner.py','cpu_steps.py','cpu_host.py','he_owned.py','test_owner_pure.py','main_quiescence.py','test_quiescence_pure.py'},'complete exact executable owner closure')
    for name,r in x['files'].items():need(checked(r)==P/name,'current exact owner code')
    packet(x['task_packet_root'])
    T=load(ref(Path(x['task_packet_root'])/'task_contract.py'),'_task_owner_exact_packet_contract')
    tm=T.source(x['task_source_unbound_ref'],allow_unbound_inputs=True)
    need(tm['root']==x['task_packet_root']and tm['authority_ref']==x['authority_ref']
         and tm['rendered_inputs_ref']==x['rendered_inputs_ref']and tm['effective_inputs_ref']is None
         and tm['input_preparation_source_ref']is None,'same unchanged packet and new exact unbound task source/authority')
    import main_quiescence as Q
    Q.policy(x['main_quiescence_ref'],authority_ref=x['authority_ref'])
    if clock:authority(x['authority_ref'])
    if host:basis(x['G1_source_ref'],x['G1_owner_ref'],x['G1_bundle_ref'],x['G1_independent_ref'])
    return x
