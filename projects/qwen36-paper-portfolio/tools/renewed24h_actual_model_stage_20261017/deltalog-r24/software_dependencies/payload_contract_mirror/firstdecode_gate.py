"""Source/evidence/owned mount entry. Serialized facts never grant geometry."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path,PurePosixPath
import sys
import time
from contextlib import contextmanager

GIB=1024**3
START,CUT=1792226600,1792313000
TINY_SOURCE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-byteabi-tiny-new24h-20261017-001/SOURCE_MANIFEST.json',bytes=2268,sha256='8bcf90c0489ce5ba5c74826f5033ad6392496634e763f2ac2cab8e1647ac5592')
TINY_INDEPENDENT=dict(path='/opt/host/vnf/austinov/run-dl-byteabi-MAIN-20261017-001/INDEPENDENT_BYTE_ABI_MAIN.json',bytes=1284,sha256='a69d397acc1d8bde7404de41e4939f95a9a564be6c713c89417cd58f175a8b10')

def need(v,s):
    if not v:raise ValueError(s)
def ref(p):
    p=Path(p);h=hashlib.sha256();n=0
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
    need(type(r) is dict and set(r)=={'path','bytes','sha256'},'exact Ref3')
    p=Path(r['path']);need(p.is_absolute() and p.is_file() and all(not x.is_symlink() for x in(p,*p.parents)),'ordinary stable source/data path')
    a=p.stat();need(ref(p)==r,'whole streamed source/data bytes')
    b=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns,b.st_ctime_ns),'stable streamed source/data')
    return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,name):
    p=checked(r);need(name not in sys.modules,'one cold source-private namespace')
    s=importlib.util.spec_from_file_location(name,p);v=importlib.util.module_from_spec(s);sys.modules[name]=v
    try:s.loader.exec_module(v)
    except BaseException:del sys.modules[name];raise
    return v
def source(sr):
    m=obj(sr);need(m['schema']=='deltalog.selected-firstdecode-source/v1' and m['default_enabled'] is False,'new source/defaultOFF')
    need(m['scope']==dict(prefill_tokens=2048,decode_query_tokens=1,C=1,TP=4,all_GDN_layers=48,all_layers=64),'frozen firstdecode-only scope')
    for r in m['files'].values():checked(r)
    need(set(m['native_torch_sources'])=={'contextlib','grad_mode'},'complete actual Torch wrapper sources')
    for r in m['native_torch_sources'].values():
        need(type(r) is dict and set(r)=={'path','bytes','sha256'} and PurePosixPath(r['path']).is_absolute(),'exact installed native Torch source Ref')
    need(m['workspace_cap_bytes']==32*GIB and m['total_cap_bytes']==80*GIB and m['per_worker_cap_bytes']==8*GIB,'new exact32/80/8 declaration, not old4GiB')
    need(m['allocated_worker_cap_bytes']==15*GIB//2 and m['opt_total_cap_bytes']==2*GIB and m['payload_total_cap_bytes']==30*GIB,'separate absolute8/allocated7.5, exact2+30=32 split')
    return m

def numerical_readset(m):
    """Actual original loaders use these physical neighboring files, not fixtures."""
    refs=tuple(m[k] for k in('original_tensor_consumer','original_numeric_oracle','original_integer_round','original_precast','original_direct_round'))
    t=Path(refs[0]['path']).parent
    need(Path(refs[1]['path'])==t/'dependencies/numeric_oracle.py'
        and Path(refs[2]['path'])==t/'dependencies/direct_round013.py'
        and Path(refs[3]['path'])==t/'precast.py'
        and Path(refs[4]['path'])==t/'direct_round.py','original exact relative numerical-loader closure')
    return refs

def module_ref(module,r):
    need(module is not None and Path(module.__file__).resolve()==checked(r),'exact source-owned public module '+r['path'])

@contextmanager
def tiny_namespace(tiny,payload):
    """Only two explicitly source-checked aliases; no framework-module purge."""
    saved_path=list(sys.path);saved={n:sys.modules.get(n)for n in('io_api','byteaudit')}
    try:
        if saved['io_api'] is not None:module_ref(saved['io_api'],tiny['files']['io_api.py'])
        if saved['byteaudit'] is not None:module_ref(saved['byteaudit'],payload['files']['byteaudit.py'])
        p=checked(tiny['files']['io_api.py'])
        spec=importlib.util.spec_from_file_location('_firstdecode_exact_tiny_io',p)
        exact=importlib.util.module_from_spec(spec);spec.loader.exec_module(exact)
        sys.modules['io_api']=exact
        sys.path.insert(0,str(p.parent))
        yield
    finally:
        # Even a source check/import/consume failure restores the exact path.
        sys.path[:]=saved_path
        for name,prior in saved.items():
            current=sys.modules.get(name)
            if current is prior:continue
            allowed=(tiny['files']['io_api.py'],)if name=='io_api'else(tiny['files']['byteaudit.py'],payload['files']['byteaudit.py'])
            need(current is not None and any(Path(current.__file__).resolve()==checked(r)for r in allowed),'refuse unknown namespace mutation; never delete arbitrary framework module')
            if prior is None:del sys.modules[name]
            else:sys.modules[name]=prior

def payload_byteaudit(m):
    r=m['files']['byteaudit.py'];module=sys.modules.get('byteaudit')
    if module is None:module=load(r,'byteaudit')
    module_ref(module,r)
    need(module.Store.__module__=='byteaudit' and module.Store.__init__.__globals__ is module.__dict__
        and Path(module.Store.__init__.__code__.co_filename).resolve()==checked(r),'actual payload Store defining module/code/globals binding')
    return module
def verify_tiny(m):
    need(m['tiny_source']==TINY_SOURCE and m['tiny_independent']==TINY_INDEPENDENT,'actual completed tiny evidence, not a template')
    tiny=obj(TINY_SOURCE);ind=obj(TINY_INDEPENDENT)
    need(ind['source']==TINY_SOURCE and ind['actual_NPU_byte_ABI'] is True and ind['actual_native_pool_geometry'] is False
         and ind['model_qualified'] is False and ind['performance_qualified'] is False and ind['task_qualified'] is False,'ABI only, no model promotion')
    with tiny_namespace(tiny,m):
        reader=load(tiny['files']['reader.py'],'_firstdecode_tiny_actual_reader')
        actual=reader.consume(TINY_SOURCE,ind['owner'],ind['final_inspect'])
    need(actual==ind,'repeat exact frozen independent tiny receipt/release/evidence')
    payload_byteaudit(m)
    # Verify the shared alias/streaming implementations, not merely a similar
    # helper name. Tiny-only appended test code is deliberately excluded.
    import ast
    actual_source=checked(tiny['files']['byteaudit.py']).read_bytes()
    proposed_source=checked(m['files']['byteaudit.py']).read_bytes()
    for name in('whole_storage_bytes','chunk_bytes','ranges','first_inactive_difference','Store'):
        a=[n for n in ast.parse(actual_source).body if getattr(n,'name',None)==name]
        b=[n for n in ast.parse(proposed_source).body if getattr(n,'name',None)==name]
        need(len(a)==len(b)==1 and ast.dump(a[0],include_attributes=False)==ast.dump(b[0],include_attributes=False),'actual tiny-tested byte backend exact body '+name)
    return ind

def validate_budget(b,model_sr,payload_sr,cid):
    need(b['schema']=='deltalog.first-decode-owned-budget/v1' and b['source']==model_sr and b['payload_source']==payload_sr and b['cid']==cid,'current owned model/source/CID budget join')
    need(b['workspace_cap_bytes']==32*GIB and b['per_worker_cap_bytes']==8*GIB and b['total_cap_bytes']==80*GIB
         and b['disk_reserve_bytes']==int(8.5*GIB) and b['ledger_advanced'] is False,'new exact workspace/total/resource contract')
    need(b['allocated_worker_cap_bytes']==15*GIB//2 and b['opt_total_cap_bytes']==2*GIB and b['payload_total_cap_bytes']==30*GIB
         and 4*b['allocated_worker_cap_bytes']==b['payload_total_cap_bytes'] and b['opt_total_cap_bytes']+b['payload_total_cap_bytes']==b['workspace_cap_bytes'],'actual2GiB opt plus four7.5GiB allocation; never four8 plus extra opt')
    need(b['guest_stage_root']=='/adakv-results' and b['guest_payload_root']=='/adakv-results/model/capture','exact native owner guest aliases')
    for n in('host_stage_root','host_payload_root'):
        p=PurePosixPath(b[n]);need(p.is_absolute() and '..' not in p.parts,'exact source-owned host paths')
    need(b['host_stage_root']!=b['host_payload_root'] and not PurePosixPath(b['host_stage_root']).is_relative_to(PurePosixPath(b['host_payload_root'])),'distinct exact control/payload roots')
    # Do not reinterpret policy-specific storage_proof keys here. The NEW
    # source-bound owner validates its complete current sealed ledger. Retain
    # that entire proof rather than replacing it with a guest boolean.
    need(type(b['storage_proof']) is dict and b['storage_proof'],'actual complete retained storage policy proof')
    return b

class Gate:
    def __init__(self,model_sr,payload_sr):
        renewal_source=source(payload_sr)
        renewal_path=checked(renewal_source['files']['renewal_authority.py'])
        renewal_spec=importlib.util.spec_from_file_location('_firstdecode_exact_renewal_authority',renewal_path)
        renewal=importlib.util.module_from_spec(renewal_spec);renewal_spec.loader.exec_module(renewal)
        renewal.check()
        need(START<=time.time()<CUT,'explicit renewed clock; old evidence unchanged')
        self.model_sr,self.payload_sr=model_sr,payload_sr
        self.payload=source(payload_sr);self.model=obj(model_sr)
        contract=self.model['firstdecode_contract']
        need(contract['schema']=='deltalog.firstdecode-model-contract/v1' and contract['payload_source']==payload_sr
             and contract['scope']=='C1-native2048-firstdecode' and contract['tiny_independent']==TINY_INDEPENDENT,'actual new model exact payload/tiny linkage')
        self.tiny=verify_tiny(self.payload)
        self.checked_budget=None;self.loaded=None;self.worker=None
    def actual_worker(self,F,runner):
        from firstdecode import domain_from_actual_loaded
        from vllm.distributed import parallel_state as ps
        cid=os.environ['DL026_ACTUAL_OWNER_CID'];rank=ps.get_tensor_model_parallel_rank()
        budget_path=Path(os.environ['DL_FIRST_DECODE_BUDGET_PATH'])
        need(str(budget_path)=='/adakv-results/FIRST-DECODE-BUDGET.json','exact owned budget receipt path')
        b=validate_budget(obj(ref(budget_path)),self.model_sr,self.payload_sr,cid)
        loaded_path=Path(os.environ['DL_FIRST_DECODE_ALL4_LOADED']);need(str(loaded_path)=='/adakv-results/ALL4-LOADED.json','exact original all4 loaded path')
        loaded=obj(ref(loaded_path));stat=Path('/proc/self/stat').read_text();cg=Path('/proc/self/cgroup').read_text()
        d,row=domain_from_actual_loaded(F,loaded,self.model_sr,cid,rank,os.getpid(),stat,cg)
        # Map original loaded native receipt through the precise control RW.
        original=row['loaded_receipt'];h=Path(original['path']);host=Path(b['host_stage_root']);need(host in h.parents,'loaded receipt inside actual control root')
        guest=Path(b['guest_stage_root'])/h.relative_to(host);proof=obj(dict(original,path=str(guest)))
        need(proof['pid']==os.getpid(),'actual native loaded receipt namespace PID')
        self.checked_budget,self.loaded,self.worker=b,loaded,d
        return d
    def root_factory(self,epoch):
        need(self.worker is epoch.binding.domain and self.checked_budget is not None,'actual same source/CID/worker budget capability')
        b=self.checked_budget;root=Path(b['guest_payload_root'])
        need(root.is_dir() and all(not q.is_symlink() for q in(root,*root.parents)),'actual exact private payload mount')
        s=os.statvfs(root);need(s.f_bavail*s.f_frsize>=100*GIB,'actual authorized filesystem free100GiB remains hard')
        return root/('FIRST-DECODE-'+str(os.getpid())),b['allocated_worker_cap_bytes']
