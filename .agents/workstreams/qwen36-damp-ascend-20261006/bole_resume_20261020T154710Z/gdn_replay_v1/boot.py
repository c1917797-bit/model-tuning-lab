"""Bounded post-inspection handoff; imports no tensor runtime."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--root',type=Path);ap.add_argument('--source',type=Path)
    a=ap.parse_args()
    if not a.execute:
        print(json.dumps(dict(enabled=False,NPU=False,tensor_runtime_imported=False)));return
    if a.root is None or a.source is None or os.environ.get('BOLE_GDN3_REPLAY_ENABLE')!='1':ap.error('explicit bounded owner handoff required')
    until=time.monotonic()+60;pointer=a.root/'MANIFEST-REF.json'
    while not pointer.exists():
        if time.monotonic()>=until:raise TimeoutError('MAIN inspection/admission handoff absent')
        time.sleep(.1)
    reference=json.loads(pointer.read_bytes());p=Path(reference['path']);b=p.read_bytes()
    if len(b)!=reference['bytes']or hashlib.sha256(b).hexdigest()!=reference['sha256']:raise ValueError('exact completed MAIN manifest')
    m=json.loads(b);r=m['files']['replay_gdn.py'];driver=a.source/'replay_gdn.py';d=driver.read_bytes()
    if str(driver)!=r['path']or len(d)!=r['bytes']or hashlib.sha256(d).hexdigest()!=r['sha256']:raise ValueError('exact replay driver before exec')
    os.execv('/usr/local/python3.12.13/bin/python3',['/usr/local/python3.12.13/bin/python3','-I','-B',str(driver),'--execute','--manifest-ref',json.dumps(reference),'--output',str(a.root/'data')])
if __name__=='__main__':main()
