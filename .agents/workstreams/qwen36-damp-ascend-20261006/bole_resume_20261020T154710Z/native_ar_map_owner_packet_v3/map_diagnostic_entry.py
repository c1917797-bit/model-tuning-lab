#!/usr/bin/env python3
import argparse,hashlib,json,os,runpy,sys,time
from pathlib import Path
def check(r):
    if not(type(r)is dict and set(r)=={'path','bytes','sha256'}):raise ValueError('exact Ref3')
    p=Path(r['path']);h=hashlib.sha256();n=0;s=p.stat()
    with p.open('rb')as f:
        a=os.fstat(f.fileno())
        if(a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)!=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns):raise ValueError('opened exact source')
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b);n+=len(b)
        z=os.fstat(f.fileno())
    q=p.stat()
    if(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)!=(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)or(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)!=(q.st_dev,q.st_ino,q.st_size,q.st_mtime_ns):raise ValueError('stable entry source')
    if n!=r['bytes']or h.hexdigest()!=r['sha256']:raise ValueError('whole source bytes/SHA')
def main():
    entry_start=time.monotonic();p=argparse.ArgumentParser(description='Default-OFF admitted CPU diagnostic entry',allow_abbrev=False)
    p.add_argument('--execute',action='store_true');p.add_argument('--inputs-ref');a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"formal_success":false}');return 0
    if not a.inputs_ref:p.error('exact diagnostic Ref3 required')
    ir=json.loads(a.inputs_ref);check(ir)
    if ir['bytes']>4*2**20:raise ValueError('bounded binding')
    b=Path(ir['path']).read_bytes()
    if len(b)!=ir['bytes']or hashlib.sha256(b).hexdigest()!=ir['sha256']:raise ValueError('exact binding reopen')
    d=json.loads(b)
    if d['schema']!='bole.native-ar-map-identity-diagnostic-inputs/v1'or d['default_enabled']is not False or d['diagnostic_seconds']!=600:raise ValueError('exact CPU diagnostic binding')
    own=[r for r in d['source_refs']if r['path']==str(Path(__file__).absolute())]
    if len(own)!=1:raise ValueError('actual entry full path Ref3 explicitly source bound')
    check(own[0]);check(d['files']['diagnostic'])
    if os.sched_getaffinity(0)!={0}or list(Path('/dev').glob('davinci[0-9]*')):raise ValueError('actual CPU0 and no numbered NPU')
    if time.monotonic()-entry_start>=600:raise ValueError('entry cold budget; no renewal')
    os.environ['ASCEND_RT_VISIBLE_DEVICES']='';os.environ['TORCH_DEVICE_BACKEND_AUTOLOAD']='0';os.environ['BOLE_NATIVE_AR_MAP_DIAGNOSTIC_ENABLE']='1'
    sys.argv=[d['files']['diagnostic']['path'],'--diagnose','--inputs-ref',json.dumps(ir)]
    runpy.run_path(d['files']['diagnostic']['path'],run_name='__main__');return 0
if __name__=='__main__':raise SystemExit(main())
