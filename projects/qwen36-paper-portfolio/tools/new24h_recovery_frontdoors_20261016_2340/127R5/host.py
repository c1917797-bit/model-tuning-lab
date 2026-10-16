"""MAIN-owned paired CPU ABI -> physical5 numerical -> independent CPU.

Reuse exact v7 Lane's subprocess/RSS/lease/polling/stop-retain implementation.
Overrides child/mount/inspection/CPU assignment/ARM interface. Numeric admission
is physical5 only; unrelated external4/6/7 activity is recorded, not blocked.
"""
import argparse,ast,concurrent.futures as cf,hashlib,importlib.util,json,os,shutil,sys,time,types,uuid
try:import resource
except ImportError:resource=None
from datetime import datetime,timezone
from pathlib import Path
import clock127r4 as CLOCK
_WHOLE_DEADLINE=None
HERE=Path(__file__).resolve().parent
START,CUT=1792134133,1792220533
OWNER='deltalog-anchor-consumer-recovery-new24h-MAIN-127-repair5'
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
DOCKER='/usr/bin/docker';PY='/usr/local/python3.12.13/bin/python3';HOST_RESERVE=512*1024**2
RESERVE=8*1024**3;PRLIMIT='/usr/bin/prlimit';SMI='/usr/local/sbin/npu-smi'
PIPE={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/_draft_damp_operator_reuse/NEW48H/deltalog-v7-20261014-001/pipeline.py','bytes':40280,'sha256':'1df9ce6cac75b68e0f8781c40a2445887a00494941c9cde9488abafe735ab07c'}
CPU={'path':PIPE['path'].replace('pipeline.py','cpu_capacity.py'),'bytes':5043,'sha256':'992cfcb419eabbf69902f9358c703815c268d3f99b00ae9e410a291d374d456d'}
HOST=Path('/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py')
HOST_SHA='ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86'
OLD=Path('/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/saved_step_native_order_v2/host_run.py')
OLD_SHA='86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc'
AUTH_SHA='e8c373b6664a4bdd80012428b686227a6f15c0535b3c57a7654fb7996c02cf28'
def need(v,m):
    if not v:raise ValueError(m)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):
            if _WHOLE_DEADLINE is not None:CLOCK.remaining(_WHOLE_DEADLINE)
            h.update(b)
    return h.hexdigest()
def ref(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def validate_ref_streamed(r):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'},'strict actual Ref3')
    p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary stable input');before=p.stat()
    need(before.st_size==r['bytes']and sha(p)==r['sha256'],'whole streamed actual source/input')
    after=p.stat();need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'input changed during streamed verification')
    return p
def checked(r):
    return validate_ref_streamed(r).read_bytes()
def obj(r):return json.loads(checked(r))
def write(p,x):
    with Path(p).open('x',encoding='utf8')as f:json.dump(x,f,sort_keys=True,allow_nan=False);f.write('\n')
def load(r,name):
    checked(r);s=importlib.util.spec_from_file_location(name,r['path']);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def require_digest(p,h):need(sha(p)==h,'exact frozen dependency '+str(p));return h
def load_host():
    require_digest(HOST,HOST_SHA);require_digest(OLD,OLD_SHA)
    v=load(ref(HOST),'_dldeadbridge024_existing_host_helper');v.legacy();return v
def inspect_owned(x,cid,stage,output,root,a,allow_oom=False):
    need(x['Id']==cid and len(cid)==64 and x['Image']==IMAGE,'exact original CID/image')
    hc=x['HostConfig'];labels=x['Config'].get('Labels',{})
    need(labels.get('qwen36.owner')==OWNER and labels.get('qwen36.stage')==stage and labels.get('deltalog-fresh-bridge.owner-source-sha256')==a.owner_ref['sha256'],'actual frozen owner labels')
    need(not x.get('ExecIDs')and not hc['Privileged']and 'ALL'in hc.get('CapDrop',[])and any('no-new-privileges'in s for s in hc.get('SecurityOpt',[])),'no foreign exec/privileges')
    need(hc['Memory']==hc['MemorySwap']==8*1024**3 and hc['NanoCpus']==10**9 and hc['IpcMode']=='private'and hc['ShmSize']==2*1024**3 and hc['PidsLimit']==512,'bounded real CPU/RAM/swap/IPC/PID')
    need(hc['CpusetCpus']==str(a.guest_cpu)and hc['NetworkMode']=='none'and not hc.get('PortBindings'),'explicit actual guest CPU/networknone')
    mounts={m['Destination']:(m['Source'],m['RW'])for m in x['Mounts']};need(mounts==a.current_mounts,'exact RO closure and sole new RW')
    expected=set()if stage=='native'else{(f'/dev/davinci{a.physical_device}','/dev/davinci0'),*((p,p)for p in('/dev/davinci_manager','/dev/devmm_svm','/dev/hisi_hdc'))}
    need({(d['PathOnHost'],d['PathInContainer'])for d in hc.get('Devices')or[]}==expected and not hc.get('DeviceRequests')and not hc.get('DeviceCgroupRules'),'only scoped actual singleton devices or Devices[]')
    need(x['Config']['Cmd']==a.current_cmd,'exact actual image Python child')
    env=dict(t.split('=',1)for t in x['Config']['Env']);need(all(env.get(k)==v for k,v in a.current_env.items()),'actual frozen child environment')
    if not allow_oom:need(not x['State'].get('OOMKilled',False),'OOM invalidates stage')
    return x
def base_lane():
    # The selected original definitions are compiled WITHOUT changing their AST
    # bodies. New subclass methods have this new actual host.py provenance.
    import clock_profile131
    raw=checked(PIPE);tree=ast.parse(clock_profile131.transform(raw));names={'Lane'}
    nodes=[n for n in tree.body if isinstance(n,ast.ClassDef)and n.name in names]
    need(len(nodes)==1,'exact original Lane class')
    cpu=load(CPU,'_dldeadbridge024_actual_cpu_capacity')
    ns=dict(cf=cf,hashlib=hashlib,importlib=__import__('importlib'),json=json,os=os,resource=resource,shutil=shutil,subprocess=__import__('subprocess'),time=time,uuid=uuid,
        datetime=datetime,timezone=timezone,Path=Path,OWNER=OWNER,DOCKER=DOCKER,SMI=SMI,PY=PY,PRLIMIT=PRLIMIT,
        HOST_RESERVE=HOST_RESERVE,RESERVE=RESERVE,CUTOFF=datetime.fromtimestamp(CUT,timezone.utc),HOST=HOST,OLD=OLD,cpu=cpu,
        require=need,save=write,load_host=load_host,check_inspect=inspect_owned)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),PIPE['path'],'exec'),ns)
    return ns['Lane'],cpu
def target_closure(sr):
 import runtime127
 return runtime127.target_closure(sr)

def main():
    if '--execute' not in sys.argv and '--source-audit-only' not in sys.argv:
        print('disabled: explicit --execute or --source-audit-only required');return 0
    need(resource is not None,'actual Linux owner required')
    global _WHOLE_DEADLINE
    started=time.monotonic();_WHOLE_DEADLINE=started+CLOCK.WHOLE;p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit-only',action='store_true')
    p.add_argument('--whole-start',type=float,required=True);p.add_argument('--owner-ref',required=True);p.add_argument('--target-source-ref',required=True);p.add_argument('--authority-ref',required=True)
    p.add_argument('--lifecycle-ref',required=True);p.add_argument('--smoke-ref');p.add_argument('--steps',type=int,choices=(16,),default=16);p.add_argument('--stage',choices=('cpu',),required=True);p.add_argument('--cpu-preflight-ref');p.add_argument('--output',required=True,type=Path)
    p.add_argument('--physical-device',type=int,choices=(5,),default=5);p.add_argument('--host-cpu',type=int,required=True);p.add_argument('--guest-cpu',type=int,required=True);a=p.parse_args()
    need(0<=time.monotonic()-a.whole_start<=CLOCK.PRE,'actual wrapper precheck clock within420/no future start');started=a.whole_start;_WHOLE_DEADLINE=started+CLOCK.WHOLE
    owner,sr,ar=[json.loads(v)for v in(a.owner_ref,a.target_source_ref,a.authority_ref)];om=obj(owner)
    need(om['schema']=='deltalog.deadpayload-native-bridge-source/v024'and om['root']==str(HERE)and om['window']==dict(start=START,cutoff=CUT)and om['default_enabled']is False,'exact new owner source/currentclock')
    for r in om['files'].values():checked(r)
    need(om['files']['host.py']==ref(__file__),'actual loaded owner identity')
    root,m,C,refs,historical_root=target_closure(sr);checked(PIPE);checked(CPU);require_digest(HOST,HOST_SHA);require_digest(OLD,OLD_SHA);C.window(ar)
    lr=json.loads(a.lifecycle_ref);need(lr==m['lifecycle_source_ref'],'same actual022 historical component only')
    # runtime.target_closure already completed this SAME full readset fence.
    CLOCK.remaining(_WHOLE_DEADLINE)
    need(ar['sha256']==AUTH_SHA,'same human authority')
    smoke=None
    if a.steps==160 and a.stage=='numeric':
        smoke=json.loads(a.smoke_ref);v=obj(smoke);need(v['schema']=='deltalog.fresh-bridge-owned-host/v5'and v['target_source']==sr and v['steps']==16 and v['bridge_primitive_gate_pass']is True and v['stopped_retained']is True and v['primary']is None and not v['secondary'],'actual same-source complete16 smoke/release before160');refs.extend([smoke,v['independent_consumer']]);need(obj(v['independent_consumer'])['pass_gate']is True,'independent16 smoke')
    if a.source_audit_only:
        need('torch'not in sys.modules and'torch_npu'not in sys.modules,'pure source audit');print(json.dumps(dict(readset=len(refs),source=owner,target=sr,NPU=False,resource_admitted=False)));return 0
    need(a.execute and a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists()and a.output.resolve().parent==Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061').resolve(),'explicit MAIN new result root')
    need(a.host_cpu in os.sched_getaffinity(0)and a.host_cpu!=a.guest_cpu,'host actual inherited CPU assignment and disjoint guest')
    a.owner_ref=owner;a.lease_seconds=CLOCK.WHOLE if a.stage=='cpu'else 2880;a.run_root=a.output;a.host_original_affinity=sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0,{a.host_cpu});rl=resource.getrlimit(resource.RLIMIT_AS);need(rl[1]==resource.RLIM_INFINITY,'hard AS supports safe Docker CLI');resource.setrlimit(resource.RLIMIT_AS,(HOST_RESERVE,rl[1]))
    Base,cpu=base_lane()
    budget=CLOCK.profile(m);checked(budget['measurement_ref'])
    a.stop_after_numerics=True
    adapter=load(m['files']['scope_adapter.py'],'_lifecycle003_scoped_original002')
    import inspect
    old_observe=inspect.getsource(Base.observe);registered=adapter.transform_observe(old_observe)
    ns=Base.observe.__globals__;module=types.SimpleNamespace(**dict(ns,c=types.SimpleNamespace(sha=sha),_adapter_ref=owner))
    adapter._MODULE=module
    ns.update(_adapter_scope=adapter.scoped_cards,_adapter_ref=owner,_adapter_checked=lambda r:checked(r),_adapter_protected=adapter.protected_observation,_adapter_nonselected=adapter.nonselected_identity)
    adapted={};exec(compile(registered,str(HERE/'host.py')+':registered-scope002','exec'),ns,adapted);Base.observe=adapted['observe']
    original_init=Base.__init__
    def init_private(self,*args):
        original_init(self,*args);self.lease_deadline=_WHOLE_DEADLINE-budget['final_fence_reserve_seconds'];self._adapter_module=module
        obs=load(m['observer_ref'],'_lifecycle003_actual_protected002')
        facade=types.SimpleNamespace(frozen=lambda:self.h)
        obs.install(facade,ref(HOST),a.output,write,lambda:([os.getpid()]+[p['pid']for p in self.pid_proofs.values()],[self.active]if self.active else[]))
    Base.__init__=init_private
    class GE(Base):
        def run(self,argv,timeout=60):
            timeout=min(timeout,CLOCK.remaining(_WHOLE_DEADLINE-budget['final_fence_reserve_seconds']))
            if getattr(self,'cleanup_until',None)is not None:
                left=self.cleanup_until-time.monotonic();need(left>0,'whole cleanup90 deadline')
                timeout=min(timeout,left)
            return super().run(argv,timeout)
        def call(self,argv,timeout=60,ok=True):
            if getattr(self,'cleanup_until',None)is not None:
                result=self.run(argv,timeout);need(not ok or result['exit_code']==0,'cleanup command failed: '+json.dumps(result));return result
            return super().call(argv,timeout,ok)
        def cleanup(self):
            self.cleanup_until=min(time.monotonic()+90,_WHOLE_DEADLINE-budget['final_fence_reserve_seconds'])
            try:return super().cleanup()
            finally:self.cleanup_until=None
        def cpu_observe(self,stage):
            memory={k:int(v.split()[0])*1024 for k,v in(line.split(':',1)for line in Path('/proc/meminfo').read_text().splitlines())}
            need(memory['SwapFree']==memory['SwapTotal'],'swap-active rejection');floor=RESERVE+HOST_RESERVE+(0 if self.active else 8*1024**3)
            need(memory['MemAvailable']>=floor and shutil.disk_usage(a.output.parent).free>=1024**3,'ordinaryRAM and 1GiB remaining disk reserve; HugeTLB not additive')
            er=self.call([DOCKER,'info','--format','{{json .}}']);info=json.loads(er['stdout']);dr=self.call(['/usr/bin/systemctl','show','docker.service','--property=MainPID','--value']);pid=int(dr['stdout'].strip())
            identity=self.h.process_identity(pid);engine=cpu.capacity(pid);host=cpu.capacity(os.getpid())
            need(a.guest_cpu in engine['effective_cpuset']and engine['effective_cpu_capacity']>=4 and host['effective_cpu_capacity']>=1 and a.host_cpu in host['effective_cpuset'],'fresh actual guest/host/reserve CPU pool')
            need(self.h.process_identity(pid)==identity,'engine PID reuse rejection')
            return dict(schema='good-enough.live-cpu-resource/v1',meminfo_bytes=memory,ordinary_floor_bytes=floor,disk_free_bytes=shutil.disk_usage(a.output.parent).free,host=host,engine=engine,engine_info=info,actual_engine_command=er,actual_engine_pid_command=dr,guest_cpu=a.guest_cpu,host_cpu=a.host_cpu)
        def create(self,stage):
            self.stage=stage;self.secondary=[];self.output=a.output/stage;self.output.mkdir();self.cards=[]if stage=='native'else[a.physical_device]
            if stage=='native':write(self.output/'cpu-resource-before.json',self.cpu_observe(stage))
            else:
                need(shutil.disk_usage(a.output.parent).free>=m['resources']['raw_cap_bytes']+1024**3,'fresh numeric32GiB raw plus1GiB reserve')
                self.observe('numeric',require_idle=True)
            parents={Path(r['path']).parent for r in refs};parents.add(root);parents.add(Path(historical_root));parents.add(Path(ar['path']).parent);parents={q for q in parents if not any(v!=q and v in q.parents for v in parents)}
            mounts={str(q):(str(q),False)for q in parents};mounts['/usr/local/Ascend/driver']=('/usr/local/Ascend/driver',False);mounts[str(self.output)]=(str(self.output),True)
            need(sum(rw for _,rw in mounts.values())==1,'sole owned output RW');a.current_mounts=mounts
            need(time.monotonic()-started<=CLOCK.PRE,'whole prechecks exceed registered420; no create')
            cap=CLOCK.child_cap(_WHOLE_DEADLINE,budget)
            env={'RECOVERY127R4_DEADLINE':str(_WHOLE_DEADLINE),'RECOVERY127R4_CHILD_CAP':str(cap),'OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1','TORCH_DEVICE_BACKEND_AUTOLOAD':'0','ASCEND_RT_VISIBLE_DEVICES':''if stage=='native'else'0'}
            childout=self.output/'result';args=[PY,'-I','-B',str(root/'entry.py'),'--execute','--stage','cpu-preflight'if stage=='native'else'numeric','--source-ref',json.dumps(sr,separators=(',',':')),'--authority-ref',json.dumps(ar,separators=(',',':')),'--lifecycle-ref',json.dumps(lr,separators=(',',':')),'--steps',str(a.steps),'--output',str(childout)]
            if getattr(self,'consumer_mode',False):
                childout=self.output/'INDEPENDENT.json'
                mounts[str((a.output/'numeric'))]=(str(a.output/'numeric'),False)
                args=[PY,'-I','-B',str(root/'consume.py'),'--execute','--source-ref',json.dumps(sr,separators=(',',':')),'--producer-ref',json.dumps(self.numeric_ref,separators=(',',':')),'--output',str(childout)]
            if stage!='native':
                cpur=json.loads(a.cpu_preflight_ref);checked(cpur);plan=self.output/'PLAN.json'
                write(plan,dict(schema='deltalog.fresh-bridge-plan/v2',source=sr,authority=ar,lifecycle=lr,steps=a.steps,smoke=smoke,cpu_preflight=cpur,output=str(childout),physical=a.physical_device,logical=0,graph=False,phase_seconds=1800,cleanup_seconds=90));self.plan_ref=ref(plan)
                mounts[str(Path(cpur['path']).parent)]=(str(Path(cpur['path']).parent),False)
                args+=['--plan-ref',json.dumps(self.plan_ref,separators=(',',':')),'--cpu-preflight-ref',json.dumps(cpur,separators=(',',':'))]
            cmd=[DOCKER,'create','--name','dldeadbridge024-'+stage+'-'+uuid.uuid4().hex[:12],'--label','qwen36.owner='+OWNER,'--label','qwen36.stage='+stage,'--label','deltalog-fresh-bridge.owner-source-sha256='+owner['sha256'],'--cpus=1','--cpuset-cpus='+str(a.guest_cpu),'--memory=8g','--memory-swap=8g','--ipc=private','--shm-size=2g','--pids-limit=512','--cap-drop=ALL','--security-opt=no-new-privileges','--network=none']
            for dst,(src,rw)in mounts.items():cmd+=['--mount','type=bind,src='+src+',dst='+dst+(''if rw else',readonly')]
            if stage!='native':
                cmd+=['--device=/dev/davinci'+str(a.physical_device)+':/dev/davinci0']
                for d in('/dev/davinci_manager','/dev/devmm_svm','/dev/hisi_hdc'):need(Path(d).exists(),'actual control device');cmd+=['--device='+d]
            for k,v in env.items():cmd+=['-e',k+'='+v]
            a.current_env=env;self.expected_child_argv=args;a.current_cmd=['/bin/bash','-c','source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"','dldeadbridge024']+args;cmd+=[IMAGE]+a.current_cmd
            write(self.output/'create-argv.json',dict(argv=cmd,source=owner,target=sr));receipt=self.call(cmd,60);write(self.output/'create-receipt.json',receipt);cid=receipt['stdout'].strip();need(len(cid)==64 and all(c in'0123456789abcdef'for c in cid),'actual created CID');self.active=cid
            r,x=self.inspect(cid);write(self.output/'inspect-created.json',r);need(not x['State']['Running']and x['State']['Pid']==0,'cold created state');write(self.output/'start-receipt.json',self.call([DOCKER,'start',cid],60))
            return childout
        def wait_ge(self,stage):
            childout=self.create(stage);end=min(time.monotonic()+CLOCK.CHILD,_WHOLE_DEADLINE-CLOCK.FINAL-CLOCK.CLEANUP-CLOCK.MARGIN);bound=None
            while True:
                storage.check(a.output.parent)
                r,x=self.inspect(self.active)
                if stage!='native':
                    record=self.observe('numeric');device=childout/'DEVICE.json'
                    if device.is_file()and bound is None:
                        dv=obj(ref(device));ticks=int(dv['stat'][dv['stat'].rfind(')')+2:].split()[19]);proof=[p for p in record['owned_process_proofs']if p['physical']==a.physical_device and p['namespace_pids'][-1]==dv['pid']and p['start_ticks']==ticks and self.active in p['cgroup']]
                        need(dv['logical']==0 and dv['physical']==a.physical_device and dv['visible']=='0'and dv['plan']==self.plan_ref and dv['canary']==[4.,5.] and self.active in dv['cgroup'],'source-bound actual child/card/plan/canary')
                        # Exact proven020repair2 visibility wait; never ARM from self-report.
                        if not proof:
                            need(not record['owned_process_proofs'],'nonempty actual ownership mismatch')
                            need(x['State']['Running'] and time.monotonic()<end,'bounded actual ownership visibility')
                            time.sleep(.2)
                            continue
                        need(len(proof)==1,'unique live source-bound actual ownership')
                        cmd=proof[0]['argv'];need(cmd==self.expected_child_argv,'actual GE008 complete Python command identity')
                        bound=proof[0];write(self.output/'ACTUAL_OWNER.json',bound);write(childout/'MAIN_ARM.json',dict(schema='deltalog.fresh-bridge-arm/v2',pid=dv['pid'],plan_sha256=self.plan_ref['sha256'],physical=a.physical_device))
                if not x['State']['Running']:
                    write(self.output/'inspect-exited.json',r);need(x['State']['ExitCode']==0,'actual GE child failed; preserved logs/raw')
                    rr=ref(childout if getattr(self,'consumer_mode',False)else childout/'STAGE_RESULT.json');v=obj(rr)
                    if stage=='numeric':rr=v['actual_result'];v=obj(rr);v['observation_complete']=bool(v['records'])
                    need(v['source']==sr and (v.get('observation_complete')is True if stage=='numeric'or getattr(self,'consumer_mode',False)else v.get('pass_gate')is True),'actual source complete gate')
                    if getattr(self,'consumer_mode',False):need(v['schema']=='deltalog.fresh-bridge-consumption/v5'and v['actual_result']==self.numeric_ref,'independent original FP64 consumption identity')
                    else:need(v['authority']==ar,'actual current authority gate')
                    if stage!='native':need(bound is not None,'real process handshake required')
                    return rr
                need(time.monotonic()<end,'bounded child deadline startup charged');time.sleep(.2 if stage!='native'and bound is None else 2)
    out=a.output;import runtime127;storage,seal=runtime127.storage(m);storage.reserve(out.parent,out,'cpu',obj,m['storage_authority_ref']);out.mkdir();lane=GE(a,root);primary=None;secondary=[];result_ref=None;consumed=None
    try:
        result_ref=lane.wait_ge('native'if a.stage=='cpu'else'numeric')
    except BaseException as exc:primary=repr(exc)
    finally:
        try:lane.cleanup()
        except BaseException as exc:secondary.append('cleanup '+repr(exc))
    if primary is None and not secondary and a.stage=='numeric':
        # Actual independent consumer in a SECOND owned sameimage Devices[]
        # container after singleton stop/retain/release. Same fixed owner lease.
        lane.consumer_mode=True;lane.numeric_ref=result_ref
        try:consumed=lane.wait_ge('native')
        except BaseException as exc:primary='independent consumer '+repr(exc)
        finally:
            try:lane.cleanup()
            except BaseException as exc:secondary.append('consumer cleanup '+repr(exc))
    complete_final_fence=False
    try:
        for r in refs:validate_ref_streamed(r)
        CLOCK.remaining(_WHOLE_DEADLINE);seal.final_verify(m['storage_seal_evidence_ref']);CLOCK.remaining(_WHOLE_DEADLINE);complete_final_fence=True
    except BaseException as exc:
        if primary is None:primary='final complete source/data/storage fence '+repr(exc)
        else:secondary.append('final complete source/data/storage fence '+repr(exc))
    v=dict(schema='deltalog.fresh-bridge-owned-host/v5',reader_contract='single-read-audit-reuse-budget/v127-repair5',reader_source=owner,producer_source=m['original_source_ref'],complete_final_fence=complete_final_fence,cpu_budget_profile_ref=m['cpu_budget_profile_ref'],whole_seconds=3600,cleanup_seconds=90,original_child_ceiling=585.6111058300012,registered_child_ceiling=2700,source=owner,target_source=sr,authority=ar,stage=a.stage,steps=a.steps,physical=[]if a.stage=='cpu'else[a.physical_device],result=result_ref,independent_consumer=consumed,primary=primary,secondary=secondary,elapsed_seconds=time.monotonic()-started,phase_seconds=a.lease_seconds,stopped_retained=lane.active is None,resource_admitted=True,bridge_primitive_gate_pass=a.stage=='numeric'and primary is None and not secondary and consumed is not None and obj(consumed)['pass_gate']is True,full_gdn_qualified=False,model_ready=False,NPU=a.stage=='numeric')
    if a.stage=='numeric'and consumed is not None and obj(consumed)['pass_gate']is False:v['primary']='independently confirmed lifecycle candidate failure';primary=v['primary']
    write(out/'RESULT.json',v);print('MAIN_DLLIFECYCLE002_OWNER '+json.dumps(ref(out/'RESULT.json')),flush=True);return 3 if primary or secondary else 0
if __name__=='__main__':raise SystemExit(main())
