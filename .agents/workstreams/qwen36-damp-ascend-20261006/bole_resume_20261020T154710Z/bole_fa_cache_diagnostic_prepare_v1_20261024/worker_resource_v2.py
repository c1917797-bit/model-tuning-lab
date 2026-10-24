"""Source-owned same-worker diagnostic RAM reservation; no authority/controller."""
import fa_cache_advisory as CACHE
import contextlib
import fcntl
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

GIB=2**30
LIMIT=48*GIB
PER_RANK=8455716864
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
SCHEMA='bole.worker-diagnostic-RAM-reservation/v2'


def need(x,s):
    if not x:raise ValueError(s)


def read(path):
    return Path(path).read_text()


def identity(c):
    C,m,t=c['C'],c['m'],c['t']
    import resource32k_runtime as R32
    R32.require_actual(c)
    need(C.ref(__file__)==m['files']['worker_resource_v2.py'],'actual source-owned worker resource guard')
    need(t.distributed.is_initialized()and t.distributed.get_world_size()==4 and
         type(c['rank'])is int and t.distributed.get_rank()==c['rank']in range(4),
         'actual initialized TP4 worker rank, not a caller label')
    base=Path(m['model_receipt_root']).parent
    owned_ref=C.ref(base/'OWNED.json');owned=C.obj(owned_ref)
    cid=owned['cid']
    need(type(cid)is str and re.fullmatch('[0-9a-f]{64}',cid)and
         owned['source']==c['source']and owned['image']==IMAGE and owned['arm']==base.name=='dense'and
         owned['mounts'].get(str(base))==[str(base),True],
         'exact source/current model CID/image and same-path owned RW output')
    memberships=[l.split(':',2)[2]for l in read('/proc/self/cgroup').splitlines()
                 if len(l.split(':',2))==3 and 'memory'in l.split(':',2)[1].split(',')]
    need(len(memberships)==1,'one actual cgroup-v1 memory controller')
    member=PurePosixPath(memberships[0])
    need(member.is_absolute()and member.parts[-1]==cid,'current worker belongs to exact OWNED CID')
    choices=[]
    for line in read('/proc/self/mountinfo').splitlines():
        left,sep,right=line.partition(' - ')
        if not sep:continue
        fields=left.split();post=right.split()
        if len(fields)<6 or len(post)<3 or post[0]!='cgroup'or'memory'not in post[2].split(','):continue
        root,mount=PurePosixPath(fields[3]),PurePosixPath(fields[4])
        need('\\'not in str(root)+str(mount),'unambiguous mountinfo paths')
        try:relative=member.relative_to(root)
        except ValueError:continue
        choices.append(Path(str(mount))/str(relative))
    need(len(choices)==1,'one memory mount covers actual membership, no guessed cgroup root')
    cg=choices[0]
    need(cg.is_absolute()and not any(p.is_symlink()for p in(cg,*cg.parents)),
         'ordinary actual cgroup-v1 path')
    pid=os.getpid();status={}
    for line in read('/proc/self/status').splitlines():
        k,_,v=line.partition(':')
        if k in('VmRSS','VmHWM'):
            words=v.split();need(len(words)==2 and words[1]=='kB','real kernel RSS/HWM units')
            status[k]=int(words[0])*1024
    text=read('/proc/self/stat');actual=int(text.split(' ',1)[0])
    start=int(text.rsplit(')',1)[1].split()[19])
    need(actual==pid and pid in [int(x)for x in read(cg/'cgroup.procs').split()],
         'current worker PID/start belongs to actual cgroup')
    limit=int(read(cg/'memory.limit_in_bytes').strip())
    usage=int(read(cg/'memory.usage_in_bytes').strip())
    need(limit==LIMIT and 0<=usage<=limit and set(status)=={'VmRSS','VmHWM'}and
         0<=status['VmRSS']<=status['VmHWM'],'actual32GiB current model cgroup, finite kernel counters')
    return dict(source=c['source'],rank=c['rank'],pid=pid,start_ticks=start,cid=cid,
                owned=owned_ref,cgroup=str(cg),cgroup_membership=str(member),limit=limit,usage=usage,
                memory_stat=CACHE.sample_memory_stat(cg),**status)


class Guard:
    def __init__(self,c):
        self.c=c;self.failed=False;self.active=False;self.acked=False
        self.initial=identity(c)
        self.root=Path(c['m']['model_receipt_root'])/'RUNTIME-JOINT-RAM-v2'
        need(self.root.parent.is_dir()and not any(p.is_symlink()for p in(self.root,*self.root.parents)),
             'only current actual common receipt RAM leaf')
        self.root.mkdir(mode=0o700,exist_ok=True)
        need(self.root.stat().st_uid==os.geteuid(),'same-owned shared reservation directory')

    @contextlib.contextmanager
    def locked(self):
        path=self.root/'RESERVATIONS.lock'
        fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            st=os.fstat(fd)
            need(stat.S_ISREG(st.st_mode)and st.st_nlink==1 and st.st_uid==os.geteuid(),
                 'ordinary same-owned reservation lock')
            fcntl.flock(fd,fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)

    def load(self):
        path=self.root/'RESERVATIONS.json'
        if not path.exists():return dict(schema=SCHEMA,source=self.c['source'],cid=self.initial['cid'],failed=None,slots={})
        need(not path.is_symlink()and path.stat().st_size<=65536,'bounded reservation state')
        value=json.loads(path.read_text())
        need(type(value)is dict and set(value)=={'schema','source','cid','failed','slots'}and
             value['schema']==SCHEMA and value['source']==self.c['source']and
             value['cid']==self.initial['cid']and type(value['slots'])is dict and len(value['slots'])<=4,
             'same actual source/CID reservation state')
        need(value['failed']is None or type(value['failed'])is str,'explicit sticky failure')
        for k,v in value['slots'].items():
            need(k in('0','1','2','3')and type(v)is dict and
                 set(v)=={'pid','start_ticks','baseline_RSS','baseline_HWM','generation','ordinal','bytes'}and
                 all(type(v[n])is int and v[n]>=0 for n in v)and v['bytes']==PER_RANK,
                 'only four strict2GiB worker reservations')
        return value

    def save(self,state):
        path=self.root/'RESERVATIONS.json';tmp=self.root/('STATE-%d.pending'%os.getpid())
        data=(json.dumps(state,sort_keys=True,allow_nan=False)+'\n').encode()
        need(len(data)<=65536,'bounded complete shared reservation')
        fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,path)
        fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(fd)
        finally:os.close(fd)

    def current(self):
        value=identity(self.c)
        for k in('source','rank','pid','start_ticks','cid','owned','cgroup','limit'):
            need(value[k]==self.initial[k],'same actual worker lifetime/source/cgroup '+k)
        return value

    def check(self,state,value):
        need(state['failed']is None,'shared RAM failure is sticky')
        total=sum(v['bytes']for v in state['slots'].values())
        if not (total<=4*PER_RANK and value['usage']+total<=value['limit']):
            # Preserve the original first exception; observation is best-effort and bounded.
            try:self.record('first_refusal',value,total)
            except Exception as diagnostic_error:self.first_refusal_record_error=type(diagnostic_error).__name__
        need(total<=4*PER_RANK and value['usage']+total<=value['limit'],
             'actual cgroup current plus all active conservative reservations within32GiB')
        slot=state['slots'].get(str(self.c['rank']))
        if slot is not None:
            need(slot['pid']==value['pid']and slot['start_ticks']==value['start_ticks']and
                 value['VmRSS']<=slot['baseline_RSS']+PER_RANK and
                 value['VmHWM']<=slot['baseline_HWM']+PER_RANK,
                 'current RSS/new lifecycle HWM increments within per-rank2GiB; not exact peak')
        return total

    def record(self,stage,value,reserved):
        C=self.c['C']
        report=dict(schema=SCHEMA,stage=stage,**value,reserved_total=reserved,
            generation=self.generation,ordinal=self.ordinal,
            per_rank_limit=PER_RANK,model_limit=LIMIT,CPU_copies_reserved=2,
            enter_RSS=self.enter_RSS,enter_HWM=self.enter_HWM,
            current_RSS_increment=max(0,value['VmRSS']-self.enter_RSS),
            new_HWM_increment=max(0,value['VmHWM']-self.enter_HWM),
            cgroup_usage_includes_reclaimable_filecache=True,
            admission_classification='conservative resource admission, not algorithm memory verdict',
            exact_instantaneous_peak_proven=False,numerical_qualified=False)
        data=(json.dumps(report,sort_keys=True,allow_nan=False)+'\n').encode()
        need(len(data)<=16384 and self.c['metadata_bytes']+len(data)<=64*2**20,
             'RAM observations charged to original per-rank64MiB metadata')
        path=self.c['root']/('G%d-O%d-RAM-%s.json'%(self.generation,self.ordinal,stage))
        r=C.write(path,report)
        fd=os.open(C.checked(r),os.O_RDONLY|os.O_NOFOLLOW)
        try:os.fsync(fd)
        finally:os.close(fd)
        fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(fd)
        finally:os.close(fd)
        self.c['metadata_bytes']+=r['bytes']
        return r

    def fail(self,error):
        self.failed=True
        try:
            with self.locked():
                state=self.load();state['failed']=repr(error)[:1024];self.save(state)
        except Exception as secondary:
            # Never replace the original source/resource error with a failure
            # journaling error. Local sticky failure still prevents retry.
            self.failure_record_error=repr(secondary)

    def enter(self,frame,logical):
        try:
            need(not self.failed and not self.active and
                 type(logical)is int and 2*logical+128*2**20+64*2**20<=PER_RANK,
                 'two CPU copies/checkpoint/metadata inside per-rank2GiB reservation')
            need(frame['source']==self.c['source']and frame['rank']==self.c['rank']and
                 type(frame['generation'])is int and frame['generation']in(1,2)and
                 type(frame['ordinal'])is int and frame['ordinal']>=0,'same actual frame')
            self.generation,self.ordinal=frame['generation'],frame['ordinal']
            with self.locked():
                state=self.load();value=self.current();key=str(self.c['rank'])
                need(key not in state['slots'],'no unfinished/restarted same-rank reservation')
                self.enter_RSS,self.enter_HWM=value['VmRSS'],value['VmHWM']
                state['slots'][key]=dict(pid=value['pid'],start_ticks=value['start_ticks'],
                    baseline_RSS=self.enter_RSS,baseline_HWM=self.enter_HWM,
                    generation=self.generation,ordinal=self.ordinal,bytes=PER_RANK)
                reserved=self.check(state,value);self.save(state)
            self.active=True;self.acked=False
            return self.record('pre_export',value,reserved)
        except Exception as error:
            self.fail(error);raise

    def stage(self,name):
        try:
            need(self.active and not self.failed and name in('pre_save','post_wire','pre_reload','post_consume','ACK'),
                 'only fixed actual diagnostic stages')
            with self.locked():
                state=self.load();value=self.current();reserved=self.check(state,value);self.save(state)
            return self.record(name,value,reserved)
        except Exception as error:
            self.fail(error);raise

    def mark_ack(self,proof):
        try:
            need(proof['source']==self.c['source']and proof['rank']==self.c['rank']and
                 proof['generation']==self.generation and proof['ordinal']==self.ordinal and
                 proof['frame_checks_passed']is True,'actual complete independent-consumer ACK')
            self.stage('ACK');self.acked=True
        except Exception as error:
            self.fail(error);raise

    def release_after_sink(self,proof):
        try:
            need(self.active and self.acked and not self.failed and
                 proof['source']==self.c['source']and proof['rank']==self.c['rank']and
                 proof['generation']==self.generation and proof['ordinal']==self.ordinal,
                 'only actual returned same-frame sink ACK releases RAM reservation')
            self.c['C'].checked(proof['report'])
            with self.locked():
                state=self.load();value=self.current();self.check(state,value)
                del state['slots'][str(self.c['rank'])]
                reserved=sum(v['bytes']for v in state['slots'].values());self.save(state)
            self.record('sink_returned',value,reserved)
            self.active=False
        except Exception as error:
            self.fail(error);raise


def get(c):
    if c.get('worker_resource_v2_failed')is not None:raise ValueError(c['worker_resource_v2_failed'])
    try:
        if 'worker_resource_v2'not in c:c['worker_resource_v2']=Guard(c)
        return c['worker_resource_v2']
    except Exception as error:
        c['worker_resource_v2_failed']=repr(error);raise
