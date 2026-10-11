"""DEFAULT OFF single MAIN-owned Devices[] replay of already released014.
Exact original Control AST; CPU-only scoped adapter, no accelerator idle gate.
CPU_QUEUE: no peer/joint admission. Never edits, resumes or recaptures014.
"""
import argparse,ast,hashlib,json,os,re,shutil,stat,subprocess,sys,time,traceback,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import offline_contract as D
TOTAL=3600;CLEANUP=180;GIB=2**30;OUTCAP=64*2**20
OWNER='skvq-capture014-offline-consumer-v1-001'
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
PY='/usr/local/python3.12.13/bin/python3';DOCKER='/usr/bin/docker';PRLIMIT='/usr/bin/prlimit'
def binding(file):
    old=D.obj(D.CAPTURE);return next(r for r in old['files']if Path(r['path']).name==file)
def newroot(path):
    p=Path(path);D.need(p.is_absolute()and'..'not in p.parts and p.parent==D.ROOT.parent and
      p.parent.resolve()==p.parent and re.fullmatch('run-skvq-capture014-offline-001-[a-zA-Z0-9-]+',p.name)and
      not p.exists()and not p.is_symlink(),'exact absent new CPU replay leaf')
    p.mkdir(mode=0o700);return p
def environment():
    return dict(TORCH_DEVICE_BACKEND_AUTOLOAD='0',ASCEND_RT_VISIBLE_DEVICES='',
      PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',
      NUMEXPR_NUM_THREADS='1')
def guest_args(source,root):
    return [str(D.ROOT/'consume_raw.py'),'--execute','--source-manifest-sha256',source['sha256'],
      '--output',str(root/'work')]
def mount_set(out,source):
    from previous_failure import HOST_REF
    host=D.obj(HOST_REF);manifest=D.obj(source)
    # Exact original consumer source/TRAIN/package/checkpoint mounts, all now RO.
    # Old experiment is immutable; only the NEW leaf is writable.
    mounts={dst:(src,False)for dst,(src,rw)in host['owned'][2]['mounts'].items()}
    mounts[str(D.RAW_ROOT)]=(str(D.RAW_ROOT),False)
    train='/cache/cch/qwen36-damp-20261006/calibration-inputs/source-v2'
    mounts[train]=(train,False) # old mount-preflight also reads real host source path
    mounts[str(D.ROOT)]=(str(D.ROOT),False)
    for r in [source,*manifest['dependencies']]:
        p=Path(r['path'])
        if not any(p==Path(dst)or Path(dst)in p.parents for dst in mounts):mounts[str(p)]=(str(p),False)
    mounts[str(out)]=(str(out),True)
    D.need([d for d,(_,rw)in mounts.items()if rw]==[str(out)],'one new writable output, no raw014/source overwrite')
    for dst,(src,rw)in mounts.items():
        D.need(Path(src).is_absolute()and Path(dst).is_absolute()and','not in src+dst and
          '..'not in Path(src).parts and '..'not in Path(dst).parts,'exact comma-free absolute mounts')
        if not rw:D.need(not(Path(dst)==out or Path(dst)in out.parents or out in Path(dst).parents),
          'immutable source/evidence cannot overlap new write tree')
    return mounts
def mount_adapter():
    module=D.load('_skvq014_offline_mount_primitives',binding('mount_preflight.py'))
    def observe(mounts,phase,source):
        rows,errors=module.inspect_mounts(mounts)
        return dict(schema='skvq.capture014.offline.mount-preflight/v1',phase=phase,source_ref=source,
          mounts=rows,errors=errors,passed=not errors,Devices_empty=True,no_NPU_access=True)
    return types.SimpleNamespace(observe=observe)
def control_class(source,resources,mounts,preflight):
    row=binding('MAIN_HOST.py');D.checked(row)
    tree=ast.parse(Path(row['path']).read_bytes(),filename=row['path'])
    nodes=[n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Control']
    D.need(len(nodes)==1,'one original reviewed Control AST')
    scope=dict(__name__='_skvq014_offline_exact_control',Path=Path,os=os,json=json,re=re,
      subprocess=subprocess,time=time,traceback=traceback,shutil=shutil,
      TOTAL=TOTAL,CLEANUP=CLEANUP,DEADLINE=D.CUT,OWNER=OWNER,HERE=D.ROOT,IMAGE=IMAGE,
      PY=PY,DOCKER=DOCKER,PRLIMIT=PRLIMIT,SMI='/usr/local/sbin/npu-smi',GIB=GIB,
      R=resources,M=preflight,closure=lambda:source,reference=D.ref,publish_json=D.publish,require=D.need)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),row['path'],'exec'),scope)
    original=scope['Control']
    class CPUControl(original):
        def __init__(self,out,limit=TOTAL):
            D.need(limit==TOTAL,'one3600 total includes original180 cleanup');super().__init__(out,limit)
        def observe(self,*a,**kw):raise ValueError('CPU-only no accelerator observer/idle/reservation')
        def devices(self,npu):D.need(npu is False,'sole Devices[] stage');return {}
        def env(self,npu):D.need(npu is False,'sole CPU environment');return environment()
        def mounts(self,npu,inputs=None):
            D.need(npu is False and inputs is None,'prebound immutable original raw inputs');return mounts
        def create(self,phase,npu,mem,inputs=None):
            D.need(phase=='offline-consumer'and npu is False and mem==2*GIB and inputs is None,
              'one fresh CPU2GiB consumer, no NPU create path')
            return super().create(phase,npu,mem,inputs)
        def exec(self,label,args,npu=False,cap=3420,env=None):
            D.need(label=='consume-released014'and npu is False and env is None,
              'sole new actual child, no hidden retry/environment mutation')
            return super().exec(label,args,False,min(cap,3420),None)
    CPUControl.donor_source_ref=row
    CPUControl.donor_class_ast_sha256=hashlib.sha256(ast.dump(nodes[0],include_attributes=False).encode()).hexdigest()
    return CPUControl
def output_bytes(root):
    total=0
    for parent,dirs,files in os.walk(root,followlinks=False):
        D.need(all(not Path(parent,n).is_symlink()for n in dirs+files),'no output symlink')
        for name in files:
            p=Path(parent,name);s=p.stat();D.need(stat.S_ISREG(s.st_mode),'ordinary new CPU output')
            total+=s.st_size;D.need(total<=OUTCAP,'64MiB receipts/host observations cap; no raw copy')
    return total
def execute(a):
    D.need(os.environ.get('MAIN_SKVQ_OFFLINE_CPU_ENABLE')=='1','explicit MAIN-only CPU admission')
    D.need(time.time()+TOTAL<=D.CUT,'3600incl180 fits original fixed cutoff')
    source=D.source(a.source_manifest_sha256);D.original_modules(source)
    import previous_failure as F
    F.inspect() # original failure/capture0/consumer1 checked before any create
    R=D.load('_skvq014_offline_cpu_resources',binding('resources.py'));R.helper()
    view=R.helper().cpu_view(os.getpid());os.sched_setaffinity(0,{min(view['effective_cpus'])})
    import resource
    soft,hard=resource.getrlimit(resource.RLIMIT_AS)
    D.need(hard==resource.RLIM_INFINITY,'Docker-only child original unlimited hardAS')
    resource.setrlimit(resource.RLIMIT_AS,(R.HOST,hard))
    out=newroot(a.output);(out/'work').mkdir(mode=0o700)
    mounts=mount_set(out,source);Controller=control_class(source,R,mounts,mount_adapter());ctl=Controller(out)
    result=None
    try:
        ctl.create('offline-consumer',False,2*GIB)
        cli=ctl.exec('consume-released014',guest_args(source,out))
        rr=D.ref(out/'work/CPU_WORKLOAD_RESULT.json');value=D.obj(rr)
        D.need(value['schema']=='skvq.capture014.offline.workload/v1'and
          value['status']=='ALL256_ORIGINAL_RAW_WITH_ORDERED_IDENTITY_CONSUMED_PENDING_CPU_WHOLE'and
          value['source_ref']==source and value['producer_source_ref']==D.CAPTURE,
          'actual fresh full raw child terminal, not metadata-only/fixture receipt')
        result=dict(workload_ref=rr,actual_child_cli_ref=cli)
    except BaseException as e:ctl.primary=e
    finally:
        try:ctl.cleanup()
        except BaseException as e:ctl.secondary.append('cleanup persistence: '+repr(e))
        cap=None
        try:cap=output_bytes(out)
        except BaseException as e:ctl.secondary.append('output cap: '+repr(e))
        value=dict(schema='skvq.capture014.offline.owned-host/v1',
          status='RELEASED014_CPU_RAW_REPLAY_COMPLETE_PENDING_WHOLE'if result and not ctl.primary and not ctl.secondary else'FAILED',
          source_ref=source,producer_source_ref=D.CAPTURE,original_failed_whole_ref=D.FAILED_ORIGINAL,
          result=result,owned=ctl.owned,capspent=ctl.spend,primary=repr(ctl.primary)if ctl.primary else None,
          secondary=ctl.secondary,elapsed_seconds=time.monotonic()-ctl.start,total_seconds=TOTAL,
          cleanup_included_seconds=CLEANUP,actual_cleanup_seconds=ctl.cleanup_spent,portfolio_cutoff_epoch=D.CUT,
          donor_control_source_ref=Controller.donor_source_ref,exact_original_control_class_ast_sha256=Controller.donor_class_ast_sha256,
          CPU_QUEUE_no_peer_admission=True,Devices_empty=True,no_NPU_observation=True,
          output_bytes_snapshot=cap,output_peak_not_measured=True,
          native_ready=False,model_ready=False,performance_ready=False,task_ready=False)
        rr=D.publish(out/'HOST_RESULT.json',value);print(json.dumps(rr,sort_keys=True),flush=True)
    if ctl.primary:raise ctl.primary
    D.need(not ctl.secondary,'failed cleanup/output cannot pass')
def main():
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true')
    p.add_argument('--source-manifest-sha256');p.add_argument('--output');a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,Devices_empty=True,no_NPU=True,model_ready=False)));return
    D.need(a.output and a.source_manifest_sha256,'explicit source/new output');execute(a)
if __name__=='__main__':main()
