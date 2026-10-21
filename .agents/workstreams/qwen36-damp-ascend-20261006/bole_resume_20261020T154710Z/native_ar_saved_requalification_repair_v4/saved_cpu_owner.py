"""MAIN-only finite Devices[] saved nativeAR requalification; no model rerun.

The exact original consume_pair_entry, complete G1 numerical child and native
AR numerical/identity computation stays unchanged; only the exact observed mask
ABI guard changes. Original failed producer and CPU failures stay failed.
"""
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
    C.need(0<=elapsed and remaining>=1380,'cold replay leaves source300+reader900+cleanup180 within original3600')
    C.need(time.time()+remaining<=cutoff,'remaining cold phase fits original cutoff without renewal')
    return remaining


def main():
    entry_start=time.monotonic()
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--inputs-ref')
    a=p.parse_args()
    if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false,"formal_success":false}');return 0
    if not a.inputs_ref:p.error('exact new source-bound inputs required')
    sys.dont_write_bytecode=True
    spec=importlib.util.spec_from_file_location('_saved_host_common',Path(__file__).parent/'saved_common.py')
    B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B);C=B.common()
    ir=json.loads(a.inputs_ref);y=B.source(C,ir)
    C.need(C.ref(__file__)==y['files']['saved_cpu_owner.py'],'exact new CPU-only host owner source')
    x,m,on,readset,mapping=B.readset(C,y,installed=False);C.checked(ir);readset.append(ir)
    if a.source_audit:
        print(json.dumps(dict(inputs=ir,source=x['AR_source'],readset_count=len(readset),mapping=mapping,
                             NPU=False,resources_admitted=False,original_producer_failed=True)));return 0
    C.need(os.environ.get('BOLE_SAVED_AR_MAIN_ENABLE')=='1','MAIN explicit saved CPU requalification opt-in')
    argv=[v.decode('utf8','strict')for v in Path('/proc/self/cmdline').read_bytes().split(b'\0')if v]
    C.need(argv[1:3]==['-I','-B']and Path(argv[3]).resolve()==Path(__file__).resolve(),'actual private -I/-B host command')
    lock=B.held_main_lock(C)
    N=C.load(y['files']['ar_saved_namespace.py'],'_saved_ar_namespace')
    private=dict(x,output_root=y['output_root'])
    with N.open_namespace(C,private,on)as(c,S,H,namespace):
        import owned_create
        remaining=remaining_phase(C,entry_start,C.obj(y['authority'])['cutoff_epoch']);start=entry_start
        host=S.H.cpu_view(os.getpid());os.sched_setaffinity(0,{min(host['effective_cpus'])})
        _,hard=resource.getrlimit(resource.RLIMIT_AS);C.need(hard==resource.RLIM_INFINITY,'original restored Go-child AS contract')
        resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
        records=Path(y['host_record_root']);records.mkdir(mode=0o700)
        joint=H.Joint(start);ctl=None;primary=None;summary={};before={r['path']:r['sha256']for r in readset}
        C.write(records/'MAIN-LOCK.json',lock);C.write(records/'PRIVATE_NAMESPACE.json',namespace)
        C.write(records/'EXACT_INSTALLED_HOST_MAPPING.json',mapping)
        try:
            leaf=H.fresh_leaf(Path(y['consumer_output_root']));H.outputs(leaf);(leaf/'receipts').mkdir()
            ctl=H.controller(S,joint)(argparse.Namespace(output_dir=leaf),start)
            ctl.observe('saved-CPU-admission',initial=True)
            owned_create.create(c,S,ctl,x['AR_source'],readset,'cpu-preflight',Path(m['root']))
            inspected,inspection=ctl.inspect()
            C.need(not(inspected['HostConfig'].get('Devices')or[])and inspected['State']['Running']is True,
                   'actual same-image Devices[] owned CPU only')
            summary['actual_CPU_inspect']=inspection
            summary['source_preflight_child']=H.child(ctl,'SAVED-SOURCE-PREFLIGHT',[
                y['files']['saved_preflight.py']['path'],'--execute','--inputs-ref',json.dumps(ir),
                '--output',str(leaf/'SAVED-SOURCE-PREFLIGHT.json')],300,observe=False)
            summary['source_preflight']=C.ref(leaf/'SAVED-SOURCE-PREFLIGHT.json')
            proof=C.obj(summary['source_preflight'])
            C.need(proof['inputs']==ir and proof['source_preflight_pass']is True and proof['Devices']==[]and
                   proof['installed_sources_reopened']is True and proof['NPU']is False,'actual source-only preflight before original math')
            summary['independent_child']=H.child(ctl,'SAVED-PAIR-INDEPENDENT',[
                y['files']['saved_consume_entry.py']['path'],'--execute','--inputs-ref',json.dumps(ir),
                '--output',y['consumer_output_root']],900,observe=False)
            summary['independent']=C.ref(leaf/'ATTRIBUTION.json');v=C.obj(summary['independent'])
            C.need(v['source']==x['AR_source']and v['inputs']==y['actual_saved_refs']['PAIR-INPUTS.json']and
                   v['native_AR_reference_smoke_pass']is True and v['native_AR_full_TP_greedy_verified']is True and
                   v['all_actual_worker_retirements_verified']is True and v['native_AR_actual_PA_FIA_pointwise_pass']is True and
                   v['bounded_pair_pass']is False and v['matched_common_plugin_effects_gate_pending']is True and
                   v['model_ready']is False,'actual original full mathematics/lifecycle pass; common effects remain pending')
            summary['metadata_adaptation']=C.ref(leaf/'METADATA_ADAPTATION.json');adapt=C.obj(summary['metadata_adaptation'])
            C.need(adapt['inputs']==ir and adapt['full_byte_inverse_verified']is True and
                   adapt['missing_inputs_ref_synthesized']is False and adapt['original_math_and_thresholds_unchanged']is True,
                   'actual exact source/output/HTTP metadata adaptation receipt')
            summary['mask_guard_controls']=C.ref(leaf/'NATIVE-MASK-CONTROLS.json');control=C.obj(summary['mask_guard_controls'])
            C.need(control['positive_control_pass']is True and control['negative_count']==11 and
                all(row['rejected']is True for row in control['negative_controls'])and control['FIA_operator_executed']is False,
                'actual CPU guard counterexamples passed before original full mathematical run')
            summary['independent_release']=ctl.cleanup();ctl._saved_closed=True
            r=C.obj(summary['independent_release'])
            C.need(r['stopped']is True and r['retained']is True and r['errors']==[],'exact owned CPU stopped retained')
        except BaseException as error:
            primary=dict(error=repr(error),traceback=traceback.format_exc())
            C.write(records/'FIRST-FAULT.json',primary)
        finally:
            if ctl is not None:
                if ctl.cid and not getattr(ctl,'_saved_closed',False):
                    ctl.primary=primary
                    try:summary['failure_release']=ctl.cleanup()
                    except BaseException as error:joint.secondary.append(repr(error))
                joint.secondary.extend(ctl.secondary)
            after={}
            try:
                for r in readset:C.checked(r);after[r['path']]=r['sha256']
            except BaseException as error:joint.secondary.append('immutable-readset-after '+repr(error))
            joint.secondary.extend(S.formal_time_failures(joint.deadline))
            if joint.cleanup_used>180:joint.secondary.append('original joint cleanup180 exceeded')
            producer=C.obj(y['saved_producer_result'])
            passed=primary is None and not joint.secondary and before==after and 'independent_release'in summary
            result=C.write(records/'RESULT.json',dict(schema='bole.native-ar-saved-evidence-owner/v4',inputs=ir,
                source=x['AR_source'],original_owner_inputs=y['original_owner_inputs'],producer_result=y['saved_producer_result'],
                original_producer_primary=producer['primary'],original_producer_failed=True,producer_failure_rewritten=False,
                prior_CPU_qualification_failure=y['actual_prior_cpu_failure_refs']['saved_v1/RESULT.json'],
                prior_CPU_failure_rewritten=False,metadata_adaptation_ticket=ir,
                second_CPU_qualification_failure=y['actual_second_cpu_failure_refs']['RESULT.json'],
                second_CPU_failure_rewritten=False,successful_G1_source_closure=mapping['successful_G1_source_closure'],
                third_CPU_qualification_failure=mapping['mask_ABI_prerequisite']['actual_prior_v3_failure'],
                third_CPU_failure_rewritten=False,mask_ABI_prerequisite=mapping['mask_ABI_prerequisite'],
                primary=primary,secondary=joint.secondary,summary=summary,source_before=before,source_after=after,
                actual_host_argv=argv,MAIN_lock=lock,private_namespace=namespace,phase_seconds=3600,cleanup_seconds=180,
                cleanup_spent=joint.cleanup_used,elapsed=time.monotonic()-start,entry_clock_before_source_replay=True,
                phase_remaining_at_admission=remaining,NPU=False,Devices=[],model_reexecuted=False,
                original_consumer_checkpoint_validation_preserved=True,
                independent_numeric_requalification_pass=passed,native_AR_reference_smoke_pass=passed,
                bounded_pair_pass=False,matched_common_plugin_effects_gate_pending=True,model_ready=False,task_ready=False,
                performance_ready=False,E2E_measured=False,formal_success=False))
            print(json.dumps(dict(result=result,independent_numeric_requalification_pass=passed,
                                  original_producer_failed=True,NPU=False,formal_success=False)),flush=True)
        return 0 if passed else 3


if __name__=='__main__':raise SystemExit(main())
