"""Strict HE control-only owner over original025 calls, resources and cleanup."""
import json
import re
import time
from pathlib import Path


def create_class(C,c,S,H,joint,policy):
    Base=H.controller(S,joint)
    class HE(Base):
        def __init__(self,args,start,stage_ref,source):
            super().__init__(args,start);self.stage_ref=stage_ref;self.stage=C.obj(stage_ref)
            self.name='bole-he-'+self.out.parent.name.removeprefix('run-bole-')+'-controls'
            self.command=policy.argv(self.name,C.IMAGE,self.stage['source_root'],self.stage['suite_root'],
                self.stage['input_root'],self.stage['capsule_ref']['sha256'],'controls')
            self.expected=dict(cid=None,name=self.name,image=C.IMAGE,arm='cpu-preflight',source=source,
                host_sha256=c.sha(S.__file__),guest_cpus=[145],create_argv=self.command,
                mounts={dst:(self.stage[key],False)for dst,key in(('/source','source_root'),('/suite','suite_root'),('/inputs','input_root'))})
            self.affinity_updated=False
        def inspect(self,cleanup=False):
            raw,r=self.call('inspect',[S.DOCKER,'inspect',self.cid],cleanup=cleanup);v=json.loads(raw['stdout'])
            C.need(type(v)is list and len(v)==1,'exact single HE inspect')
            x=v[0];h=x['HostConfig'];cfg=x['Config'];state=x['State']
            C.need(x['Id']==self.cid and re.fullmatch('[0-9a-f]{64}',self.cid or'')and x['Image']==C.IMAGE
                   and x['Name']=='/'+self.name and cfg['Image']==C.IMAGE,'complete exact self-owned HE identity')
            args=self.command[self.command.index(C.IMAGE)+1:]
            C.need(cfg['Entrypoint']==['/usr/bin/env']and cfg['Cmd']==args and x['Path']=='/usr/bin/env'
                   and x['Args']==args and cfg['User']=='65534:65534'and cfg['WorkingDir']=='/tmp','exact immutable env-i control entrypoint and uid')
            C.need(h['Runtime']=='runc'and h['NetworkMode']=='none'and h['IpcMode']=='private'and h['PidMode']==''
                   and h['UTSMode']==''and h['Privileged']is False and h['ReadonlyRootfs']is True
                   and h['Memory']==h['MemorySwap']==2*C.GIB and h['NanoCpus']==10**9 and h['PidsLimit']==64
                   and h['Tmpfs']=={'/tmp':policy.TMPFS},'unchanged strict isolated HE control resource profile')
            C.need(not h.get('Devices')and not h.get('DeviceRequests')and not h.get('DeviceCgroupRules')
                   and not h.get('VolumesFrom')and not h.get('Links')and not h.get('PortBindings')and not h.get('ExtraHosts')
                   and not h.get('CapAdd')and h['CapDrop']==['ALL']and h['SecurityOpt']==['no-new-privileges'],
                   'no HE device/network/privilege injection')
            C.need({u['Name']:(u['Soft'],u['Hard'])for u in h['Ulimits']}=={'nofile':(128,128),'fsize':(8388608,8388608)},'exact HE limits')
            C.need(h['CpusetCpus']in({'145'}if self.affinity_updated else {'','145'}),'actual prestart CPU update, no invented original argv')
            mounts=x['Mounts'];C.need(len(mounts)==3 and {m['Destination']:(m['Source'],m['RW'])for m in mounts}==self.expected['mounts']
                and all(m['Type']=='bind'and m.get('Propagation')=='rprivate'for m in mounts),'exact public-only read-only HE mounts')
            C.need(type(state['Running'])is bool and type(state['Pid'])is int and type(state['OOMKilled'])is bool,
                   'actual HE state; outcome failure never removes exact stop authority')
            if cleanup:
                self._cleanup_owned_identity=(self.cid,c.canonical(self.expected))
                self._cleanup_stopped=not state['Running']and state['Pid']==0 and not x.get('ExecIDs')
            return x,r
        def create_start(self):
            C.need(self.cid is None and self.cpu['host_cpu']==166 and self.cpu['guest_cpus'][0]==145,'one source-bound HE CPU creation')
            raw,_=self.call('unique-name',[S.DOCKER,'ps','-a','--filter','name=^/'+self.name+'$','--format','{{.ID}}'])
            C.need(not raw['stdout'].strip(),'never reuse an existing HE name')
            # Preserve successful CID before persistence/RSS checks, exactly as025.
            try:created=self.h.run(self.wrapper(self.command),self.remaining(cap=60))
            except BaseException as error:
                c.write(self.out/'CREATE-ERROR.json',dict(requested_argv=self.command,error=repr(error)));raise
            candidate=created.get('stdout','').strip()
            if created.get('exit_code')==0 and re.fullmatch('[0-9a-f]{64}',candidate):
                self.cid=candidate;self.expected['cid']=candidate
            cr=c.write(self.out/'CREATE.json',dict(created,requested_argv=self.command))
            C.need(self.cid is not None and created['exit_code']==0,'actual complete HE create CID; no retry')
            C.write(self.out/'CREATE_ARGV.json',self.command)
            with(self.out/'CREATE.stdout').open('x')as f:f.write(created['stdout'])
            c.write(self.out/'OWNED.json',dict(self.expected,create_receipt=cr))
            self.rss();self.remaining(cap=60);x,_=self.inspect()
            C.need(not x['State']['Running']and x['State']['Pid']==0,'fresh stopped HE container before CPU-affinity update')
            update=[S.DOCKER,'update','--cpuset-cpus','145',self.cid]
            _,ur=self.call('HE-prestart-CPU145',update,cap=30);self.affinity_updated=True
            x,ir=self.inspect();C.need(not x['State']['Running'],'no HE code executes before CPU-affinity gate')
            self.update_ref=C.write(self.out/'PRESTART_CPU_UPDATE.json',dict(actual_argv=update,receipt=ur,inspect_ref=ir))
            self.call('start',[S.DOCKER,'start',self.cid],cap=30)
            x,ir=self.inspect();C.need(x['State']['Running']and x['State']['Pid']>0,'actual live HE init for immediate cgroup/uid capture')
            return x,ir
    return HE
