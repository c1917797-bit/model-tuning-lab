"""Small owner IO/readset helpers. No model/runner/device imports."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

P=Path(__file__).resolve().parent
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
PACKET_SHA='a2bb6bc9459ff4b9ca0540a296f22ad6f4b62e2541cc4ef00e53b1446e03ad22'
LEGACY_PACKET_SHA='f687ad69fa0226fe72565e8ed356b65244a475c570259c865e6b3cf68fcda851'
DIAGNOSTIC_EXPECTED_SHA='840997a1e04f485a74d8ae19a40b61593631c3dba459d26c22a6e714d9308a3c'
G1_SOURCE=(109479,'010914ebe1bf5d3e6b516103e1a376e24e0a0d965ac0a3a42d7aeb19fca57677')
G1_OWNER=(131517,'52030a932da1f3cd2392389a2d9246925e40c2d93186b5f67d41fba8cfa1e4fc')
G1_INDEPENDENT=(12221,'8caf55b28f4a3c4108b8b932e9c664e08b3c28ea18f0bf4fc3bdf62de3538d53')
HE_DIAGNOSTIC_EXPECTED_SHA='4ec737f3bca7e5901a0c4a9af7f0be4872037f08ac29626e438710fd8e1159bc'
TOKENIZER_EXPECTED_SHA='28a71ff1b869462007b18db85f6ecde8227c5d46b89a1c9a89b7702b32ec1063'
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


