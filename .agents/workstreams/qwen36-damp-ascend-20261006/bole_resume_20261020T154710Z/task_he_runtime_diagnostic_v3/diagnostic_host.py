"""Finite exact-owned HE runtime probe. No evaluator/tokenizer/model execution."""
import argparse
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import owner_namespace as N
import main_quiescence as Q
import he_owned
import he_policy
import probe_evidence as E
import lock_evidence as L
import network_evidence as V

def memory_view(H,pid,expected):
    version,group,mount,chain=H.hierarchy(pid,'memory');rows=[];finite=[]
    for path in chain:
        name='memory.max'if version==2 else'memory.limit_in_bytes';file=path/name
        if not file.is_file():C.need(path==Path(mount),'actual ancestor memory control missing');continue
        text=file.read_text().strip();limit=None if text=='max'else int(text)
        if limit is not None:finite.append(limit)
        usage_file=path/('memory.current'if version==2 else'memory.usage_in_bytes')
        swap=path/('memory.swap.max'if version==2 else'memory.memsw.limit_in_bytes')
        rows.append(dict(path=str(path),limit=text,usage_bytes=int(usage_file.read_text())if usage_file.is_file()else None,
            swap_limit=swap.read_text().strip()if swap.is_file()else None))
    C.need(finite and min(finite)==expected,'actual guest plus all ancestors admit exact finite memory cap')
    return dict(version=version,cgroup=group,ancestors=rows,effective_bytes=min(finite))

def host_binding(S,ctl,pid,uid,namespace_module,*,guest=None,HE=False):
    proc=Path('/proc')/str(pid);status=(proc/'status').read_text();stat=(proc/'stat').read_text();fields=stat[stat.rfind(')')+2:].split()
    cg=(proc/'cgroup').read_text();nspid=[int(v)for line in status.splitlines()if line.startswith('NSpid:')for v in line.split()[1:]]
    uids=[int(v)for line in status.splitlines()if line.startswith('Uid:')for v in line.split()[1:]]
    C.need(ctl.cid in cg and nspid and uids==[uid]*4 and fields[0]!='Z','actual exact live owned cgroup/namespace/uid')
    if guest is not None:C.need(nspid[-1]==guest['pid']and int(fields[19])==guest['start_ticks'],'actual child strong lifetime namespace mapping')
    argv=[v.decode()for v in(proc/'cmdline').read_bytes().split(b'\0')if v]
    if HE:
        # env-i resolves python3 using the frozen PATH. Compare the actual loaded
        # binary with the first executable in that PATH inside the same pinned root.
        F=namespace_module;namespaces=F.namespace_id(proc)
        rootfd=os.open(proc/'root',os.O_RDONLY|os.O_DIRECTORY);expected_fd=actual_fd=None
        C.need(F.identity(os.fstat(rootfd))==namespaces['root'],'pinned actual HE namespace root FD')
        expected=None
        try:
            for directory in('/usr/local/sbin','/usr/local/bin','/usr/sbin','/usr/bin','/sbin','/bin'):
                try:fd,canonical=F.root_open(rootfd,directory+'/python3')
                except FileNotFoundError:continue
                try:proof=F.file_proof(fd)
                except ValueError:os.close(fd);continue
                expected_fd=fd;expected=canonical;break
            C.need(expected_fd is not None,'actual frozen PATH resolves a real Python executable')
            actual_fd=os.open(proc/'exe',os.O_RDONLY)
            actual=F.file_proof(actual_fd);C.need(actual==F.file_proof(expected_fd),'actual HE loaded executable matches whole namespace PATH binary')
            C.need(F.namespace_id(proc)==namespaces,'same actual HE namespaces/root throughout binary probe')
            program=dict(expected_namespace_executable=expected,actual_namespace_executable=os.readlink(proc/'exe'),executable=actual,namespaces=namespaces)
        finally:
            for fd in(actual_fd,expected_fd,rootfd):
                if fd is not None:os.close(fd)
        C.need(argv==['python3','-I','-B','/source/he_runtime_probe.py','--controls','--capsule-sha256',ctl.stage['capsule_ref']['sha256']],
               'actual fixed HE runtime probe process; evaluator never called')
    else:
        program=namespace_module.verify(proc,Path('/proc')/str(ctl.inspect()[0]['State']['Pid']),'/usr/local/python3.12.13/bin/python3')
        C.need(len(argv)>4 and argv[1:3]==['-I','-B']and argv[3]==str(P/'cpu_steps.py'),'actual private owned CPU child executable/entry')
    cpu=S.H.cpu_view(pid);C.need(cpu['effective_cpus']==[145]and cpu['effective_capacity']==1,'actual CPU145/oneCPU guest and ancestor quotas')
    memory=memory_view(S.H,pid,2*C.GIB if HE else 8*C.GIB)
    C.need((proc/'stat').read_text().split(')')[-1].split()[19]==fields[19]and(proc/'cgroup').read_text()==cg,'same live owned process across full host probe')
    return C.write(ctl.out/'PROCESS-BINDING.json',dict(container_id=ctl.cid,host_pid=pid,guest_pid=nspid[-1],
        nspid=nspid,start_ticks=int(fields[19]),uid=uid,status=status,cgroup=cg,argv=argv,
        program=program,cpu=cpu,memory=memory,guest_start=guest,Devices=[]))

def observe_cpu(ctl,label,initial=False):
    # Original025 actual NPU/HBM/FD/protected/resource guards always run first.
    r=ctl.observe(label,initial=initial)
    return Q.observe(ctl,r,ctl._main_quiescence_ref)


def diagnostic_class(c,S,H,joint):
    Base=he_owned.create_class(C,c,S,H,joint,he_policy)
    class Diagnostic(Base):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            C.need(self.command.count('/source/he_worker.py')==1,'one original fixed worker entry')
            self.command[self.command.index('/source/he_worker.py')]='/source/he_runtime_probe.py'
            self.expected['create_argv']=self.command
    return Diagnostic


def main():
    entry_start=time.monotonic()  # Original finite window includes every source/readset replay.
    p=argparse.ArgumentParser(allow_abbrev=False);g=p.add_mutually_exclusive_group()
    g.add_argument('--execute',action='store_true');g.add_argument('--source-audit',action='store_true');p.add_argument('--inputs-ref');a=p.parse_args()
    if not(a.execute or a.source_audit):print('{"enabled":false,"full_software_qualification_accepted":false,"NPU":false}');return 0
    C.need(a.inputs_ref,'explicit new source-bound diagnostic inputs');ir=json.loads(a.inputs_ref);x=C.inputs(ir)
    prior=E.predecessor(x['previous_CPU_owner_ref'],x['previous_HE_owned_ref'],x['previous_HE_release_ref'])
    previous_diagnostic=E.prior_diagnostic(x['previous_diagnostic_owner_ref'],x['previous_diagnostic_independent_ref'])
    on=C.basis(x['G1_source_ref'],x['G1_owner_ref'],x['G1_bundle_ref'],x['G1_independent_ref'])
    C.need(x['helper_refs']==N.helper_refs(C,on),'whole original resource/namespace helper closure')
    stage=C.obj(x['stage_ref']);cap=C.obj(stage['capsule_ref'])
    readset=[ir,*x['files'].values(),*x['helper_refs'],*prior['refs'],*previous_diagnostic['refs'],x['authority_ref'],x['stage_ref'],stage['capsule_ref'],
        *Q.readset(x['main_quiescence_ref'],authority_ref=x['authority_ref']),x['G1_source_ref'],x['G1_owner_ref'],x['G1_bundle_ref'],x['G1_independent_ref']]
    for row in cap['files']:readset.append(dict(path=str(Path(stage['source_root'])/row['relative']),bytes=row['bytes'],sha256=row['sha256']))
    for r in readset:C.checked(r)
    if a.source_audit:print(json.dumps(dict(inputs_ref=ir,readset_files=len(readset),full_input_decode_repeated=False,resources_admitted=False,NPU=False)));return 0
    C.need(os.environ.get('BOLE_TASK_CPU_MAIN_ENABLE')=='1','MAIN explicit CPU-only diagnostic opt-in')
    argv=[v.decode()for v in Path('/proc/self/cmdline').read_bytes().split(b'\0')if v]
    C.need(argv[1:3]==['-I','-B']and Path(argv[3]).resolve()==Path(__file__).resolve(),'fresh actual source-bound -I/-B diagnostic owner')
    C.need(166 in os.sched_getaffinity(0),'original hostCPU166 available');os.sched_setaffinity(0,{166})
    _,hard=resource.getrlimit(resource.RLIMIT_AS);C.need(hard==resource.RLIM_INFINITY,'original Go-child AS contract');resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
    C.authority(x['authority_ref'],3600)
    C.need(time.monotonic()+90+180<entry_start+3600,'source/readset replay plus probe90 and originalcleanup180 fit single cold-entry window')
    start=entry_start;out=Path(x['output_root']);ctl=None;primary=None;summary={};after={}
    before={r['path']:r['sha256']for r in readset}
    with N.open_namespace(C,x,on)as(c,S,H,proof):
        out.mkdir(mode=0o700);C.write(out/'PRIVATE_NAMESPACE.json',proof);joint=H.Joint(start)
        F=C.load(on['files']['frontend_namespace131r18.py'],'_HE_probe_actual_namespace_program')
        try:
            leaf=out/'he-runtime-diagnostic';leaf.mkdir(mode=0o700)
            ctl=diagnostic_class(c,S,H,joint)(argparse.Namespace(output_dir=leaf),start,x['stage_ref'],ir)
            ctl._main_quiescence_ref=x['main_quiescence_ref'];observe_cpu(ctl,'HE-probe-admission',initial=True)
            policy=Q.policy(x['main_quiescence_ref'],authority_ref=x['authority_ref'])
            summary['inherited_lock_ref']=C.write(leaf/'INHERITED_MAIN_LOCK.json',L.capture(x['main_quiescence_ref'],policy['serial_schedule']['external_lock_path']))
            live,_=ctl.create_start();summary['binding_ref']=host_binding(S,ctl,live['State']['Pid'],65534,F,HE=True)
            summary['net_namespace_ref']=C.write(leaf/'HOST_GUEST_NET_NAMESPACE.json',V.capture_namespaces(C.obj(summary['binding_ref'])))
            until=time.monotonic()+min(90,ctl.remaining(cap=90));next_observe=time.monotonic()+5
            while True:
                actual,inspect_ref=ctl.inspect()
                if not actual['State']['Running']:break
                C.need(time.monotonic()<until,'finite90second HE runtime-only probe; no retry')
                if time.monotonic()>=next_observe:observe_cpu(ctl,'HE-probe-running');next_observe=time.monotonic()+5
                ctl.remaining(cap=90);time.sleep(.2)
            C.need(actual['State']['ExitCode']==0 and not actual['State']['OOMKilled'],'runtime diagnostic operational exit0 without OOM')
            he_policy.inspect_actual([actual],expected_id=ctl.cid,expected_image=C.IMAGE,expected_argv=ctl.command,
                source_root=stage['source_root'],suite_root=stage['suite_root'],input_root=stage['input_root'])
            summary['inspect_ref']=C.write(leaf/'DIAGNOSTIC_INSPECT.json',[actual])
            wait,wr=ctl.call('HE-probe-wait',[S.DOCKER,'wait',ctl.cid],cap=10);C.need(wait['stdout'].strip()=='0','actual diagnostic wait0')
            logs,lr=ctl.call('HE-probe-logs',[S.DOCKER,'logs',ctl.cid],cap=10);text=logs['stdout']+logs['stderr']
            C.need(len(text.encode())<=2**20,'bounded1MiB diagnostic logs')
            logpath=leaf/'DIAGNOSTIC_LOG.stdout';logpath.write_text(text)
            observation=E.parse_probe(text,stage['capsule_ref']['sha256'])
            summary.update(observation_ref=C.write(leaf/'OBSERVATION.json',observation),logs_ref=C.ref(logpath),wait_receipt=wr,logs_receipt=lr,
                owned_ref=C.ref(leaf/'OWNED.json'),create_argv_ref=C.ref(leaf/'CREATE_ARGV.json'),CPU145_prestart_update=ctl.update_ref)
            summary['release_ref']=ctl.cleanup();ctl._diagnostic_closed=True;release=C.obj(summary['release_ref'])
            C.need(release['stopped']is True and release['retained']is True and release['errors']==[],'actual diagnostic stopped retained before inverse')
        except BaseException as e:
            primary=dict(phase='he-runtime-diagnostic',error=repr(e),traceback=traceback.format_exc());C.write(out/'FIRST-FAULT.json',primary)
        finally:
            if ctl is not None:
                if ctl.cid and not getattr(ctl,'_diagnostic_closed',False):
                    ctl.primary=primary
                    try:ctl.cleanup()
                    except BaseException as e:joint.secondary.append(repr(e))
                joint.secondary.extend(ctl.secondary)
            try:
                for r in readset:after[r['path']]=C.ref(C.checked(r))['sha256']
            except BaseException as e:joint.secondary.append('source/input-after '+repr(e))
            joint.secondary.extend(S.formal_time_failures(joint.deadline))
            if joint.cleanup_used>180:joint.secondary.append('joint diagnostic cleanup180 exceeded')
            passed=primary is None and not joint.secondary and before==after
            value=dict(schema='bole.actual-HE-runtime-diagnostic-owner/v3',inputs_ref=ir,summary=summary,primary=primary,secondary=joint.secondary,
                actual_host_pid=os.getpid(),actual_host_start_ticks=L.start_ticks(Path('/proc/self/stat').read_text()),
                source_input_before=before,source_input_after=after,diagnostic_observation_complete=passed,
                quiescence_observations=[]if ctl is None else getattr(ctl,'_main_quiescence_observations',[]),
                phase_seconds=3600,cleanup_seconds=180,cleanup_spent=joint.cleanup_used,elapsed_seconds=time.monotonic()-start,
                actual_host_argv=argv,full_input_decode_repeated=False,evaluator_executed=False,generated_code_executed=False,
                full_software_qualification_accepted=False,network_safety_accepted=False,model_ready=False,task_score_produced=False,NPU=False)
    value['private_namespace_restored_by_identity']=True;result=C.write(out/'RESULT.json',value)
    print(json.dumps(dict(result_ref=result,diagnostic_observation_complete=passed,full_software_qualification_accepted=False,NPU=False)),flush=True)
    return 0 if passed else 3


if __name__=='__main__':raise SystemExit(main())
