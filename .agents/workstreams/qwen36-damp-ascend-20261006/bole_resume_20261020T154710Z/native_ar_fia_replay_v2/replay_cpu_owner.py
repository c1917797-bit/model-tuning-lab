"""MAIN finite original025 CPU→physical4 singleton→CPU diagnostic, defaultOFF."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback


def remaining_phase(C,start,cutoff):
    elapsed=time.monotonic()-start;remaining=3600-elapsed
    C.need(elapsed>=0 and remaining>=2580,'cold source/predecessor hashing leaves metadata600+replay900+consumer900+cleanup180')
    C.need(time.time()+remaining<=cutoff,'same original phase3600 fits fixed cutoff; never renew clock')
    return remaining


def main():
    entry_start=time.monotonic()  # FIRST entry, before parser/import/source replay.
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    g=p.add_mutually_exclusive_group();g.add_argument('--execute',action='store_true');g.add_argument('--source-audit',action='store_true')
    p.add_argument('--inputs-ref');a=p.parse_args()
    if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false,"formal_success":false}');return 0
    if not a.inputs_ref:p.error('new exact source-bound INPUTS Ref3 required')
    sys.dont_write_bytecode=True;s=importlib.util.spec_from_file_location('_fia_owner_common',Path(__file__).parent/'replay_common.py')
    R=importlib.util.module_from_spec(s);s.loader.exec_module(R);C=R.common();ir=json.loads(a.inputs_ref);y=R.source(C,ir)
    C.need(C.ref(__file__)==y['files']['replay_cpu_owner.py'],'exact new finite singleton owner source')
    lock=R.held_main_lock(C)if a.execute else None
    x,m,on,refs,mapping=R.readset(C,y);C.checked(ir);refs.append(ir)
    if a.source_audit:
        print(json.dumps(dict(inputs=ir,readset_count=len(refs),NPU=False,resources_admitted=False,
            diagnostic_only=True,original_native_numerical_pass=False,formal_success=False)));return 0
    C.need(os.environ.get('BOLE_NATIVE_FIA_REPLAY_MAIN_ENABLE')=='1','MAIN explicit finite singleton diagnostic opt-in')
    argv=[v.decode()for v in Path('/proc/self/cmdline').read_bytes().split(b'\0')if v]
    C.need(argv[1:3]==['-I','-B']and Path(argv[3]).resolve()==Path(__file__).resolve(),'actual inherited-flock private host -I/-B argv')
    remaining=remaining_phase(C,entry_start,C.obj(y['authority'])['cutoff_epoch'])
    NS=C.load(y['files']['ar_saved_namespace.py'],'_fia_private_original_namespace')
    SP=C.load(y['files']['singleton_profile.py'],'_fia_private_singleton_profile')
    root=Path(y['output_root']);joint=None;primary=None;summary={};namespace_restored=False;profile_restored=False
    before={r['path']:r['sha256']for r in refs};after={};all_refs={r['path']:r for r in refs};ctl=None
    def add(values):
        for r in values:
            C.checked(r);C.need(r['path']not in all_refs or all_refs[r['path']]==r,'one immutable stage input identity')
            all_refs[r['path']]=r;before[r['path']]=r['sha256']
    try:
        with NS.open_namespace(C,dict(x,output_root=y['output_root']),on)as(c,S,H,namespace):
            import owned_create
            C.need(166 in os.sched_getaffinity(0),'original host CPU166 available');os.sched_setaffinity(0,{166})
            _,hard=resource.getrlimit(resource.RLIMIT_AS);C.need(hard==resource.RLIM_INFINITY,'original Go-child AS wrapper')
            resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard));root.mkdir(mode=0o700);joint=H.Joint(entry_start)
            C.write(root/'MAIN-LOCK.json',lock);C.write(root/'PRIVATE_NAMESPACE.json',namespace);C.write(root/'SOURCE-MAPPING.json',mapping)
            with SP.install(C,c,S,H,on)as profile:
                profile_ref=C.write(root/'SINGLETON-PROFILE.json',profile);add([profile_ref])
                def open_owner(leaf,role,readset):
                    nonlocal ctl
                    leaf=H.fresh_leaf(root/leaf);H.outputs(leaf);(leaf/'receipts').mkdir()
                    ctl=H.controller(S,joint)(argparse.Namespace(output_dir=leaf),entry_start)
                    C.need(ctl.name.islower()and len(ctl.name)<80,'bounded lowercase actual owner name')
                    ctl.observe('native-fia-'+role+'-admission',initial=True)
                    C.need(ctl.cpu is not None and ctl.cpu['guest_cpus'][:1]==[0],'actual original CPU0 allocation AFTER observe before create')
                    ctl.remaining(cap=60)  # Original remaining budget and create guards remain intact.
                    live_ref=owned_create.create(c,S,ctl,ir,readset,role,Path(__file__).parent)
                    live,inspection=ctl.inspect()
                    C.need(live['State']['Running']is True and live['State']['Pid']>0,'actual source-bound live init')
                    if role=='cpu-preflight':
                        C.need(not(live['HostConfig'].get('Devices')or[])and live['HostConfig']['Memory']==8*2**30,
                            'actual original Devices[]CPU0/8GiB helper')
                    else:C.need(len(live['HostConfig'].get('Devices')or[])==4,'only singleton4→0 plus3aux')
                    return leaf,inspection
                def release(label):
                    nonlocal ctl
                    release_ref=ctl.cleanup();ctl._fia_closed=True;v=C.obj(release_ref)
                    C.need(v['stopped']is True and v['retained']is True and v['deleted']is False and v['errors']==[],
                        'actual exact owned '+label+' stopped-retained clean')
                    joint.secondary.extend(ctl.secondary);ctl=None;return release_ref
                try:
                    leaf,inspection=open_owner('cpu-preflight','cpu-preflight',list(all_refs.values()))
                    summary['metadata_live_inspect']=inspection
                    summary['metadata_child']=H.child(ctl,'FIA-METADATA',[
                        y['files']['metadata_cpu.py']['path'],'--execute','--inputs-ref',json.dumps(ir),
                        '--output',str(leaf/'METADATA.json')],600,observe=False)
                    summary['metadata_report']=C.ref(leaf/'METADATA.json');owned=C.ref(leaf/'OWNED.json');release_ref=release('metadata')
                    hr=C.write(root/'CPU-HANDOFF.json',dict(schema='bole.native-AR-FIA-actual-CPU-handoff/v1',inputs=ir,
                        report=summary['metadata_report'],child=summary['metadata_child'],owned=owned,release=release_ref))
                    summary['metadata_handoff']=hr;extra,projection=R.metadata_readset(C,y,ir,hr);add(extra)
                    C.write(root/'CPU-HANDOFF-PROJECTION.json',projection)
                    leaf,inspection=open_owner('dense','dense',list(all_refs.values()))
                    owned=C.ref(leaf/'OWNED.json')
                    ar=C.write(leaf/'ADMISSION.json',dict(schema='bole.native-AR-FIA-actual-singleton-admission/v1',inputs=ir,
                        metadata_handoff=hr,owned=owned,live_inspect=inspection,owned_CID=ctl.cid,singleton_profile=profile_ref,
                        phase_clock_not_renewed=True,entry_clock=entry_start))
                    R.admission_gate(C,y,ir,hr,ar);summary['admission']=ar
                    summary['replay_child']=H.child(ctl,'FIA-REPLAY',[
                        y['files']['replay_fia.py']['path'],'--execute','--inputs-ref',json.dumps(ir),
                        '--metadata-handoff-ref',json.dumps(hr),'--admission-ref',json.dumps(ar),
                        '--output',str(leaf/'REPLAY.json')],900,observe=True)
                    summary['replay_report']=C.ref(leaf/'REPLAY.json');actual=C.obj(summary['replay_report']);process=actual['process']
                    matches=[v for v in ctl.process_proofs if v['physical']==4 and v['chip']==0 and ctl.cid in v['cgroup']and
                        v['namespace_pids'][-1]==process['pid']and v['start_ticks']==process['start_ticks']and
                        v['argv'].count(y['files']['replay_fia.py']['path'])==1]
                    C.need(matches and len({(v['pid'],v['start_ticks'])for v in matches})==1,
                        'original real host compute observations join exact guest PID/start/cgroup/script on physical4')
                    process_join=C.write(leaf/'PROCESS-JOIN.json',dict(schema='bole.native-AR-FIA-live-process-join/v1',inputs=ir,
                        owned_CID=ctl.cid,guest=process,actual_compute=matches,observations=ctl.observations,
                        original_controller_observe_unmodified=True,private_cgroup_text_not_CID_authority=True))
                    release_ref=release('singleton replay')
                    rr=C.write(root/'REPLAY-HANDOFF.json',dict(schema='bole.native-AR-FIA-actual-replay-handoff/v1',inputs=ir,
                        metadata_handoff=hr,report=summary['replay_report'],child=summary['replay_child'],owned=owned,
                        release=release_ref,admission=ar,process_join=process_join))
                    summary['replay_handoff']=rr;extra,projection=R.replay_readset(C,y,ir,hr,rr);add(extra)
                    C.write(root/'REPLAY-HANDOFF-PROJECTION.json',projection)
                    leaf,inspection=open_owner('cpu-consumer','cpu-preflight',list(all_refs.values()))
                    summary['consumer_live_inspect']=inspection
                    summary['consumer_child']=H.child(ctl,'FIA-INDEPENDENT',[
                        y['files']['consume_replay.py']['path'],'--execute','--inputs-ref',json.dumps(ir),
                        '--metadata-handoff-ref',json.dumps(hr),'--replay-handoff-ref',json.dumps(rr),
                        '--output',str(leaf/'INDEPENDENT.json')],900,observe=False)
                    summary['independent']=C.ref(leaf/'INDEPENDENT.json');v=C.obj(summary['independent'])
                    C.need(v['inputs']==ir and v['independent_diagnostic_completed']is True and v['frame_count']==128 and
                        v['actual_operator_outputs_consumed']==256 and v['independent_installed_fullSHA_buildID_join']is True and v['original_failure_frame_count']==16 and v['original_violation_count']==32 and
                        v['native_FA_math_qualified']is False and v['formal_success']is False,'complete independent all128×two diagnostic, no promotion')
                    summary['consumer_release']=release('independent Devices[] consume')
                except BaseException as error:
                    primary=dict(error=repr(error),traceback=traceback.format_exc());C.write(root/'FIRST-FAULT.json',primary)
                finally:
                    if ctl is not None:
                        if ctl.cid and not getattr(ctl,'_fia_closed',False):
                            ctl.primary=primary
                            try:summary['failure_release']=ctl.cleanup()
                            except BaseException as error:joint.secondary.append(repr(error))
                        joint.secondary.extend(ctl.secondary)
            profile_restored=True
        namespace_restored=True
    except BaseException as error:
        failure=dict(error=repr(error),traceback=traceback.format_exc())
        if primary is None:primary=failure
        elif joint is not None:joint.secondary.append('namespace/profile-finally '+repr(error))
        if root.is_dir()and not(root/'FIRST-FAULT.json').exists():C.write(root/'FIRST-FAULT.json',failure)
    if joint is None:raise ValueError('pre-admission failure; no owned controller/result authority: '+repr(primary))
    # RESULT is after both actual context inverses; never report finally success early.
    try:
        for r in all_refs.values():C.checked(r);after[r['path']]=r['sha256']
    except BaseException as error:joint.secondary.append('immutable-input-after '+repr(error))
    if time.monotonic()>joint.deadline or time.time()>=C.obj(y['authority'])['cutoff_epoch']:joint.secondary.append('original whole3600/fixed cutoff expired')
    if joint.cleanup_used>180:joint.secondary.append('original joint cleanup180 exceeded')
    completed=primary is None and not joint.secondary and before==after and profile_restored and namespace_restored and 'consumer_release'in summary
    result=C.write(root/'RESULT.json',dict(schema='bole.native-AR-FIA-finite-diagnostic-owner/v1',inputs=ir,source=y['AR_source'],summary=summary,
        primary=primary,secondary=joint.secondary,source_before=before,source_after=after,MAIN_lock=lock,actual_host_argv=argv,
        entry_clock_before_source_replay=True,phase_remaining_at_admission=remaining,phase_seconds=3600,cleanup_seconds=180,
        elapsed=time.monotonic()-entry_start,cleanup_spent=joint.cleanup_used,private_namespace_restored_by_identity=namespace_restored,
        singleton_profile_restored_by_identity=profile_restored,original025_resource_methods_preserved=True,
        diagnostic_completed=completed,all128_two_filler_control_pending=not completed,NPU_stage_requested=True,physical=[4],logical=[0],
        original_G1_math_rerun=False,model_reexecuted=False,original_native_numerical_pass=False,native_FA_math_qualified=False,
        common_effects_pass=False,performance_ready=False,formal_success=False))
    print(json.dumps(dict(result=result,diagnostic_completed=completed,formal_success=False)),flush=True)
    return 0 if completed else 3

if __name__=='__main__':raise SystemExit(main())
