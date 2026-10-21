"""Finite MAIN-owned import-only HE preflight. Default OFF."""
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
import lock_evidence as L
import he_owned
import he_policy as HEP
import he_admission as HA
import binding as B
import preflight_contract as T
import preflight_evidence as E


def preflight_class(c,S,H,joint):
    Base=he_owned.create_class(C,c,S,H,joint,HEP)
    class Preflight(Base):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            C.need(self.command.count('--controls')==1 and '--tasks'not in self.command,'one fixed original known-control entry before preflight selection')
            self.command[self.command.index('--controls')]='--preflight'
            self.expected['create_argv']=self.command
    return Preflight


def main():
    entry_start=time.monotonic()  # Every input/source replay counts in the original finite window.
    p=argparse.ArgumentParser(allow_abbrev=False);g=p.add_mutually_exclusive_group()
    g.add_argument('--source-audit',action='store_true');g.add_argument('--execute',action='store_true');p.add_argument('--inputs-ref');a=p.parse_args()
    if not(a.source_audit or a.execute):print('{"enabled":false,"qualified":false,"NPU":false}');return 0
    C.need(a.inputs_ref,'exact newly prepared preflight source required');ir=json.loads(a.inputs_ref);x=T.inputs(ir)
    prior=T.predecessor(x['previous_CPU_owner_ref'],x['previous_HE_owned_ref'],x['previous_HE_release_ref'])
    on=C.basis(x['G1_source_ref'],x['G1_owner_ref'],x['G1_bundle_ref'],x['G1_independent_ref'])
    C.need(x['helper_refs']==N.helper_refs(C,on),'whole exact original025 helper closure')
    readset=E.readset(ir,x,prior);stage=C.obj(x['stage_ref'])
    if a.source_audit:print(json.dumps(dict(inputs_ref=ir,readset_files=len(readset),resources_admitted=False,qualified=False,NPU=False)));return 0
    C.need(os.environ.get('BOLE_TASK_CPU_MAIN_ENABLE')=='1','MAIN explicit import-only preflight opt-in')
    argv=[v.decode()for v in Path('/proc/self/cmdline').read_bytes().split(b'\0')if v]
    C.need(argv[1:3]==['-I','-B']and Path(argv[3]).resolve()==Path(__file__).resolve(),'fresh actual source-bound -I/-B owner')
    C.need(166 in os.sched_getaffinity(0),'original hostCPU166 available');os.sched_setaffinity(0,{166})
    _,hard=resource.getrlimit(resource.RLIMIT_AS);C.need(hard==resource.RLIM_INFINITY,'unchanged Go-child AS contract');resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
    C.authority(x['authority_ref'],3600);C.need(time.monotonic()+90+180<entry_start+3600,'source replay plus HE90 and cleanup180 fit one cold-entry3600')
    start=entry_start;out=Path(x['output_root']);ctl=None;primary=None;summary={};after={};before={r['path']:r['sha256']for r in readset}
    with N.open_namespace(C,x,on)as(c,S,H,proof):
        out.mkdir(mode=0o700);C.write(out/'PRIVATE_NAMESPACE.json',proof);joint=H.Joint(start)
        F=C.load(on['files']['frontend_namespace131r18.py'],'_HE_dependency_actual_namespace_program')
        G=C.load(C.ref(P/'he_network_guard.py'),'_HE_dependency_actual_network_guard')
        try:
            leaf=out/'he-dependency-preflight';leaf.mkdir(mode=0o700)
            ctl=preflight_class(c,S,H,joint)(argparse.Namespace(output_dir=leaf),start,x['stage_ref'],ir)
            ctl._main_quiescence_ref=x['main_quiescence_ref'];B.observe_cpu(ctl,'HE-dependency-admission',initial=True)
            policy=Q.policy(x['main_quiescence_ref'],authority_ref=x['authority_ref'])
            summary['inherited_lock_ref']=C.write(leaf/'INHERITED_MAIN_LOCK.json',L.capture(x['main_quiescence_ref'],policy['serial_schedule']['external_lock_path']))
            deadline=time.monotonic()+min(90,ctl.remaining(cap=90))
            live,_=ctl.create_start();summary['binding_ref']=B.host_binding(S,ctl,live['State']['Pid'],65534,F,HE=True)
            ctl._task_DOCKER=S.DOCKER
            summary['network_admission_ref']=HA.admit(ctl,summary['binding_ref'],F,G,stage['original_task_source_ref']['sha256'],stage['capsule_ref']['sha256'],deadline)
            next_observe=time.monotonic()+5
            while True:
                actual,ir_actual=ctl.inspect()
                if not actual['State']['Running']:break
                C.need(time.monotonic()<deadline,'finite90second real dependency/module import preflight; no retry')
                if time.monotonic()>=next_observe:B.observe_cpu(ctl,'HE-dependency-running');next_observe=time.monotonic()+5
                ctl.remaining(cap=90);time.sleep(.2)
            C.need(actual['State']['ExitCode']==0 and not actual['State']['OOMKilled'],'actual import-only preflight exit0 without OOM')
            HEP.inspect_actual([actual],expected_id=ctl.cid,expected_image=C.IMAGE,expected_argv=ctl.command,
                source_root=stage['source_root'],suite_root=stage['suite_root'],input_root=stage['input_root'])
            summary['inspect_ref']=C.write(leaf/'DOCKER-INSPECT.json',[actual])
            wait,wr=ctl.call('HE-dependency-wait',[S.DOCKER,'wait',ctl.cid],cap=10);C.need(wait['stdout'].strip()=='0','actual wait0')
            logs,lr=ctl.call('HE-dependency-logs',[S.DOCKER,'logs',ctl.cid],cap=10);text=logs['stdout']+logs['stderr']
            C.need(len(text.encode())<=2**20,'bounded1MiB import-only logs');logfile=leaf/'LOG.stdout';logfile.write_text(text)
            value=E.parse(text,stage);summary.update(preflight_ref=C.write(leaf/'PREFLIGHT.json',value),logs_ref=C.ref(logfile),
                wait_receipt=wr,logs_receipt=lr,owned_ref=C.ref(leaf/'OWNED.json'),create_argv_ref=C.ref(leaf/'CREATE_ARGV.json'),
                CPU145_prestart_update=ctl.update_ref)
            E.admission(value,C.obj(summary['binding_ref']),C.obj(summary['network_admission_ref']),G)
            summary['release_ref']=ctl.cleanup();ctl._preflight_closed=True;release=C.obj(summary['release_ref'])
            C.need(release['stopped']is True and release['retained']is True and release['errors']==[],'actual import preflight stopped retained before inverse')
        except BaseException as error:
            primary=dict(phase='he-dependency-preflight',error=repr(error),traceback=traceback.format_exc());C.write(out/'FIRST-FAULT.json',primary)
        finally:
            if ctl is not None:
                if ctl.cid and not getattr(ctl,'_preflight_closed',False):
                    ctl.primary=primary
                    try:ctl.cleanup()
                    except BaseException as error:joint.secondary.append(repr(error))
                joint.secondary.extend(ctl.secondary)
            try:
                for r in readset:after[r['path']]=C.ref(C.checked(r))['sha256']
            except BaseException as error:joint.secondary.append('source/input-after '+repr(error))
            joint.secondary.extend(S.formal_time_failures(joint.deadline))
            if joint.cleanup_used>180:joint.secondary.append('joint preflight cleanup180 exceeded')
            passed=primary is None and not joint.secondary and before==after
            value=dict(schema='bole.actual-HE-dependency-preflight-owner/v1',inputs_ref=ir,summary=summary,primary=primary,secondary=joint.secondary,
                actual_host_pid=os.getpid(),actual_host_start_ticks=L.start_ticks(Path('/proc/self/stat').read_text()),actual_host_argv=argv,
                source_input_before=before,source_input_after=after,dependency_preflight_complete=passed,
                quiescence_observations=[]if ctl is None else getattr(ctl,'_main_quiescence_observations',[]),
                phase_seconds=3600,cleanup_seconds=180,cleanup_spent=joint.cleanup_used,elapsed_seconds=time.monotonic()-start,
                full_input_decode_repeated=False,evaluator_called=False,generated_code_executed=False,task_score_produced=False,
                full_software_qualification_accepted=False,model_ready=False,performance_ready=False,NPU=False)
    value['private_namespace_restored_by_identity']=True;result=C.write(out/'RESULT.json',value)
    print(json.dumps(dict(result_ref=result,dependency_preflight_complete=passed,qualified=False,NPU=False)),flush=True)
    return 0 if passed else 3


if __name__=='__main__':raise SystemExit(main())
