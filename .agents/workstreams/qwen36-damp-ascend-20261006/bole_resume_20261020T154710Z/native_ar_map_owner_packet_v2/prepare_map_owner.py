#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,os
from pathlib import Path
NAMES=('map_cpu_owner.py','map_diagnostic_entry.py','map_identity_diagnostic.py','prepare_map_owner.py')
def ref(path):
    p=Path(path).absolute();h=hashlib.sha256();n=0;s=p.stat()
    with p.open('rb')as f:
        a=os.fstat(f.fileno())
        if(a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)!=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns):raise ValueError('opened source identity')
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b);n+=len(b)
        z=os.fstat(f.fileno())
    q=p.stat()
    if(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)!=(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)or(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)!=(q.st_dev,q.st_ino,q.st_size,q.st_mtime_ns):raise ValueError('stable complete source')
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def obj_arg(value):
    r=json.loads(value)
    if ref(r['path'])!=r or r['bytes']>4*2**20:raise ValueError('bounded exact metadata Ref3')
    b=Path(r['path']).read_bytes()
    if len(b)!=r['bytes']or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('exact metadata reopen')
    return r,json.loads(b)
def write(path,value):
    with Path(path).open('xb')as f:f.write((json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
    return ref(path)
def main():
    p=argparse.ArgumentParser(description='Default-OFF pure map-owner preparation',allow_abbrev=False);p.add_argument('--prepare',action='store_true')
    for name in('source-root','output-root','original-inputs-ref','diagnostic-template-ref','projection-ref','torch-host-copy-ref','torch-copy-receipt-ref','v2-result-ref','predecessors-ref'):p.add_argument('--'+name)
    a=p.parse_args()
    if not a.prepare:print('{"enabled":false,"resources_admitted":false}');return 0
    for name in('source_root','output_root','original_inputs_ref','diagnostic_template_ref','projection_ref','torch_host_copy_ref','torch_copy_receipt_ref','v2_result_ref','predecessors_ref'):
        if getattr(a,name)is None:p.error('required --'+name.replace('_','-'))
    ir,y=obj_arg(a.original_inputs_ref);dtr,d=obj_arg(a.diagnostic_template_ref);pjr,projection=obj_arg(a.projection_ref);psr,pred=obj_arg(a.predecessors_ref)
    vr,_=obj_arg(a.v2_result_ref);cr,_=obj_arg(a.torch_copy_receipt_ref);th=json.loads(a.torch_host_copy_ref)
    if ref(th['path'])!=th:raise ValueError('exact stopped-image Torch copy')
    root=Path(a.source_root).absolute();out=Path(a.output_root).absolute();packet=Path(__file__).absolute().parent
    if root.exists()or out.exists()or not root.parent.is_dir():raise ValueError('new source/output leaves only')
    if type(pred)is not list or not pred or type(projection)is not list:raise ValueError('actual predecessor/projection lists')
    root.mkdir(mode=0o700);files={}
    for name in NAMES:
        src=packet/name;before=ref(src)
        with src.open('rb')as f,(root/name).open('xb')as g:
            for b in iter(lambda:f.read(1024*1024),b''):g.write(b)
        after=ref(root/name)
        if(before['bytes'],before['sha256'])!=(after['bytes'],after['sha256'])or ref(src)!=before:raise ValueError('whole new-source copy')
        files[name]=after
    d['files']['diagnostic']=files['map_identity_diagnostic.py'];d['output_dir']=str(out/'cpu-preflight'/'map-identity')
    extra=list(d['source_refs'])+[files['map_diagnostic_entry.py'],ir];unique={}
    for r in extra:
        if r['path']in unique and unique[r['path']]!=r:raise ValueError('one diagnostic source Ref per path')
        unique[r['path']]=r
    d['source_refs']=list(unique.values());dr=write(root/'DIAGNOSTIC-INPUTS.json',d)
    t=dict(schema='bole.native-ar-map-diagnostic-owner-inputs/v1',default_enabled=False,source_root=str(root),output_root=str(out),
        original_fia_inputs_ref=ir,diagnostic_inputs_ref=dr,original_owner_ref=y['files']['replay_cpu_owner.py'],original_replay_common_ref=y['files']['replay_common.py'],files=files,
        installed_host_projection=projection,torch_host_copy_ref=th,torch_copy_receipt_ref=cr,v2_result_ref=vr,predecessor_refs=pred+[dtr,pjr,psr],preparer_execution_ref=ref(__file__))
    tr=write(root/'INPUTS.json',t);spec=importlib.util.spec_from_file_location('_prepared_map_owner_exact_path',files['map_cpu_owner.py']['path'])
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    C,R,tt,yy,x,m,on,refs,mapping,lock,projected=module.source_bundle(tr,execute=False)
    if lock is not None or out.exists():raise ValueError('source preparation must not admit/create')
    prep=write(root/'PREPARATION.json',dict(schema='bole.native-ar-map-diagnostic-preparation/v1',owner_inputs=tr,original_inputs=ir,diagnostic_inputs=dr,actual_preparer_execution_ref=ref(__file__),
        readset_count=len(refs),prepared_module_path_identity_verified=True,resources_admitted=False,NPU=False,formal_success=False))
    print(json.dumps(dict(owner_inputs=tr,diagnostic_inputs=dr,preparation=prep,resources_admitted=False),sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
