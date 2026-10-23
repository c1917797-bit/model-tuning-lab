"""Read-only actual validator-open/mount audit; MAIN supplies reviewed inputs."""
import argparse,hashlib,importlib,json,os,sys,time,traceback
from pathlib import Path
ROOTS=('/opt/host/vnf/austinov/','/cache/cch/','/cache/austinov/','/home/mtuser/')

def need(v,s):
    if not v:raise ValueError(s)

def checked(r):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact audit operand Ref3')
    p=Path(r['path']);need(p.is_absolute()and p.is_file()
        and not any(x.is_symlink()for x in(p,*p.parents)),
        'ordinary absolute audit operand without symlink components')
    b=p.read_bytes()
    need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'audit operand identity')
    return b

def audit(source_ref,mounts,validator_name='qualification_source_validate'):
    """One private-process use. The installed hook becomes inactive in finally."""
    need(validator_name=='qualification_source_validate','exact actual owning validator')
    m=json.loads(checked(source_ref));root=Path(m['root'])
    need(Path(source_ref['path']).parent==root,'actual source root')
    vr=m['files'][validator_name+'.py'];checked(vr)
    need(Path(vr['path'])==root/(validator_name+'.py'),'source-owned actual validator')
    need(type(mounts)is list,'actual or proposed Docker Mounts list')
    md={}
    for row in mounts:
        need(row['Destination']not in md,'unique actual mount destinations')
        md[row['Destination']]=row
    opened={};active=True;start=time.monotonic()
    def hook(event,args):
        if not active:return
        if event=='open':
            path,mode,flags=args
            need(not flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND),
                 'readonly audit rejects write')
            if isinstance(path,(str,bytes)):
                s=os.fsdecode(path)
                if s.startswith(ROOTS):opened[s]=opened.get(s,0)+1
        elif event in('subprocess.Popen','os.system','os.fork','os.exec',
                       'socket.connect','socket.bind','socket.__new__','ctypes.dlopen'):
            raise ValueError('readonly audit rejects process/network/native loading: '+event)
    saved=dict(sys.modules);paths=list(sys.path);error=None;tb=None;proof=None
    sys.addaudithook(hook)
    try:
        need(validator_name not in sys.modules,'fresh process, no warmed validator')
        sys.path.insert(0,str(root));V=importlib.import_module(validator_name)
        need(Path(V.__file__)==Path(vr['path']),'actual source-owned imported validator')
        proof=V.validate(source_ref)
    except BaseException as e:
        error=repr(e);tb=traceback.format_exc()
    finally:
        active=False;sys.modules.clear();sys.modules.update(saved);sys.path[:]=paths
    missing=[];wrong=[];attempts=[]
    for path,reads in sorted(opened.items()):
        p=Path(path)
        if not p.is_file():
            attempts.append(path);continue
        hit=next((md[str(x)]for x in(p,*p.parents)if str(x)in md),None)
        if hit is None:
            b=p.read_bytes()
            missing.append(dict(path=path,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),reads=reads))
        else:
            mapped=Path(hit['Source'])/p.relative_to(hit['Destination'])
            if hit['RW']or mapped!=p:wrong.append(dict(path=path,mount=hit,mapped=str(mapped)))
    return dict(schema='bole.actual-validator-readonly-open-coverage/v1',
        source=source_ref,validator=vr,validator_succeeded=error is None,
        first_error=error,traceback=tb,opened_unique=len(opened),opened_total=sum(opened.values()),
        missing=missing,wrong_mapping=wrong,failed_open_attempts=attempts,
        coverage_pass=error is None and not missing and not wrong,
        source_only=True,NPU=False,numerical_qualification=False,
        seconds=time.monotonic()-start,
        source_validated=bool(proof and proof.get('source_validated')is True))

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--audit',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--mounts-ref');a=p.parse_args()
    if not a.audit:
        need(a.source_ref is None and a.mounts_ref is None,'explicit readonly audit mode required')
        print('{"enabled":false,"NPU":false}');return
    need(a.source_ref and a.mounts_ref,'source and actual/proposed Mounts Ref required')
    mount=json.loads(checked(json.loads(a.mounts_ref)))
    if type(mount)is dict and 'stdout'in mount:mount=json.loads(mount['stdout'])
    if type(mount)is list and len(mount)==1 and type(mount[0])is dict and 'Mounts'in mount[0]:
        mount=mount[0]['Mounts']
    if type(mount)is dict and 'Mounts'in mount:mount=mount['Mounts']
    result=audit(json.loads(a.source_ref),mount)
    print(json.dumps(result,allow_nan=False),flush=True)
    if not result['coverage_pass']:raise SystemExit(2)

if __name__=='__main__':main()
