"""MAIN finite original025 Devices[]CPU0 saved native-FA numerical diagnostic."""
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
    C.need(0<=elapsed and remaining>=1380,'cold source replay leaves source300+diagnostic900+cleanup180 within original3600')
    C.need(time.time()+remaining<=cutoff,'remaining original cold phase fits unchanged cutoff; no renewal')
    return remaining


def main():
    entry_start=time.monotonic()  # Before source/evidence/predecessor hashing.
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    g=p.add_mutually_exclusive_group();g.add_argument('--execute',action='store_true');g.add_argument('--source-audit',action='store_true')
    p.add_argument('--inputs-ref');a=p.parse_args()
    if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false,"mask_semantics_qualified":false}');return 0
    if not a.inputs_ref:p.error('exact new diagnostic input Ref3 required')
    sys.dont_write_bytecode=True;s=importlib.util.spec_from_file_location('_numeric_host_common',Path(__file__).parent/'numeric_common.py')
    D=importlib.util.module_from_spec(s);s.loader.exec_module(D);C=D.common();ir=json.loads(a.inputs_ref);y=D.source(C,ir)
    C.need(C.ref(__file__)==y['files']['numeric_cpu_owner.py'],'exact new finite owner source')
    lock=D.held_main_lock(C)if a.execute else None
    x,m,on,refs,mapping=D.readset(C,y);C.checked(ir);refs.append(ir)
    if a.source_audit:
        print(json.dumps(dict(inputs=ir,readset_count=len(refs),NPU=False,resources_admitted=False,
            diagnostic_only=True,mask_semantics_qualified=False,original_G1_math_rerun=False)));return 0
    C.need(os.environ.get('BOLE_NATIVE_NUMERIC_DIAGNOSTIC_MAIN_ENABLE')=='1','MAIN explicit saved numerical diagnostic opt-in')
    argv=[v.decode()for v in Path('/proc/self/cmdline').read_bytes().split(b'\0')if v]
    C.need(argv[1:3]==['-I','-B']and Path(argv[3]).resolve()==Path(__file__).resolve(),'actual private -I/-B host command')
    NS=C.load(y['files']['ar_saved_namespace.py'],'_numeric_private_original_namespace')
    with NS.open_namespace(C,dict(x,output_root=y['output_root']),on)as(c,S,H,namespace):
        import owned_create
        remaining=remaining_phase(C,entry_start,C.obj(y['authority'])['cutoff_epoch']);start=entry_start
        C.need(166 in os.sched_getaffinity(0),'original actual host CPU166 available');os.sched_setaffinity(0,{166})
        _,hard=resource.getrlimit(resource.RLIMIT_AS);C.need(hard==resource.RLIM_INFINITY,'original Go-child AS wrapper')
        resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
        root=Path(y['output_root']);root.mkdir(mode=0o700);joint=H.Joint(start)
        before={r['path']:r['sha256']for r in refs};after={};ctl=None;primary=None;summary={};math_recomputed=False
        C.write(root/'MAIN-LOCK.json',lock);C.write(root/'PRIVATE_NAMESPACE.json',namespace);C.write(root/'SOURCE-MAPPING.json',mapping)
        try:
            leaf=H.fresh_leaf(Path(y['consumer_output_root']));H.outputs(leaf);(leaf/'receipts').mkdir()
            ctl=H.controller(S,joint)(argparse.Namespace(output_dir=leaf),start)
            C.need(ctl.name.islower()and len(ctl.name)<80,'bounded lowercase owner name')
            ctl.observe('saved-native-numeric-CPU-admission',initial=True)
            C.need(ctl.cpu['guest_cpus'][:1]==[0],'original actual one CPU0 profile')
            owned_create.create(c,S,ctl,ir,refs,'cpu-preflight',Path(__file__).parent)
            inspected,inspection=ctl.inspect();C.need(inspected['State']['Running']is True and
                not(inspected['HostConfig'].get('Devices')or[])and inspected['HostConfig']['Memory']==8*2**30,
                'actual same-image Devices[]8GiB original CPU helper')
            summary['actual_CPU_inspect']=inspection
            oldy=C.obj(y['original_numeric_inputs'])
            summary['source_preflight_child']=H.child(ctl,'SAVED-SOURCE-PREFLIGHT',[
                oldy['files']['saved_preflight.py']['path'],'--execute','--inputs-ref',json.dumps(y['original_numeric_inputs']),
                '--output',str(leaf/'SAVED-SOURCE-PREFLIGHT.json')],300,observe=False)
            summary['source_preflight']=C.ref(leaf/'SAVED-SOURCE-PREFLIGHT.json');v=C.obj(summary['source_preflight'])
            C.need(v['inputs']==y['original_numeric_inputs']and v['source_preflight_pass']is True and
                v['installed_sources_reopened']is True and v['Devices']==[],'exact original saved numerical-v4 source preflight retained')
            summary['diagnostic_child']=H.child(ctl,'NUMERIC-DIAGNOSTIC',[
                y['files']['numeric_diagnostic.py']['path'],'--execute','--inputs-ref',json.dumps(ir),
                '--output',str(leaf/'NUMERIC-DIAGNOSTIC.json')],900,observe=False)
            summary['diagnostic']=C.ref(leaf/'NUMERIC-DIAGNOSTIC.json');v=C.obj(summary['diagnostic'])
            C.need(v['inputs']==ir and v['rank_count']==4 and v['frame_count']==128 and v['weights_only_load']is True and v['current_failure_frame_count']==16 and v['mathematics_recomputed']is True and
                all(v[k]is False for k in('NPU','original_G1_math_rerun','mask_semantics_qualified',
                    'native_FA_math_qualified','native_AR_numeric_pass','common_effects_pass','model_ready','formal_success')),
                'complete all128 numerical failure diagnostic; no mathematical qualification fabricated')
            math_recomputed=True
            summary['release']=ctl.cleanup();ctl._numeric_closed=True;v=C.obj(summary['release'])
            C.need(v['stopped']is True and v['retained']is True and v['errors']==[],'actual exact owned helper stopped-retained')
        except BaseException as error:
            primary=dict(error=repr(error),traceback=traceback.format_exc());C.write(root/'FIRST-FAULT.json',primary)
        finally:
            if ctl is not None:
                if ctl.cid and not getattr(ctl,'_numeric_closed',False):
                    ctl.primary=primary
                    try:summary['failure_release']=ctl.cleanup()
                    except BaseException as error:joint.secondary.append(repr(error))
                joint.secondary.extend(ctl.secondary)
            try:
                for r in refs:C.checked(r);after[r['path']]=r['sha256']
            except BaseException as error:joint.secondary.append('immutable-input-after '+repr(error))
            joint.secondary.extend(S.formal_time_failures(joint.deadline))
            if joint.cleanup_used>180:joint.secondary.append('original cleanup180 exceeded')
            completed=primary is None and not joint.secondary and before==after and 'release'in summary
            result=C.write(root/'RESULT.json',dict(schema='bole.native-ar-numeric-diagnostic-finite-owner/v1',inputs=ir,
                source=y['AR_source'],actual_failed_numeric_v4=y['actual_numeric_v4_refs']['RESULT.json'],summary=summary,
                primary=primary,secondary=joint.secondary,source_before=before,source_after=after,
                MAIN_lock=lock,actual_host_argv=argv,private_namespace=namespace,entry_clock_before_source_replay=True,
                phase_remaining_at_admission=remaining,elapsed=time.monotonic()-start,phase_seconds=3600,
                cleanup_seconds=180,cleanup_spent=joint.cleanup_used,diagnostic_completed=completed,Devices=[],NPU=False,
                host_memory_limit_bytes=512*2**20,guest_memory_limit_bytes=8*2**30,guest_CPU=0,
                original_CPU_profile_basis=mapping['actual_CPU_profile'],
                original_G1_math_rerun=False,mathematics_recomputed=math_recomputed,model_reexecuted=False,
                mask_semantics_qualified=False,native_FA_math_qualified=False,native_AR_numeric_pass=False,
                common_effects_pass=False,model_ready=False,performance_ready=False,formal_success=False))
            print(json.dumps(dict(result=result,diagnostic_completed=completed,NPU=False,
                mask_semantics_qualified=False,formal_success=False)),flush=True)
        return 0 if completed else 3

if __name__=='__main__':raise SystemExit(main())
