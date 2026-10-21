"""Metadata-only new diagnostic leaf; never starts a process/container/device."""
import argparse
import json
from pathlib import Path
import shutil
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import owner_namespace as N
import main_quiescence as Q
import probe_evidence as E


def prepare(a):
    names=('G1_source_ref','G1_owner_ref','G1_bundle_ref','G1_independent_ref','authority_ref','main_quiescence_ref',
           'previous_CPU_owner_ref','previous_HE_owned_ref','previous_HE_release_ref')
    refs={n:json.loads(getattr(a,n))for n in names};C.authority(refs['authority_ref'],3600)
    Q.policy(refs['main_quiescence_ref'],authority_ref=refs['authority_ref'])
    previous=E.predecessor(refs['previous_CPU_owner_ref'],refs['previous_HE_owned_ref'],refs['previous_HE_release_ref'])
    on=C.basis(refs['G1_source_ref'],refs['G1_owner_ref'],refs['G1_bundle_ref'],refs['G1_independent_ref']);helpers=N.helper_refs(C,on)
    root=a.new_root;out=a.output_root
    C.need(root.is_absolute()and root.parent.is_dir()and not root.exists()and out.is_absolute()and not out.exists()
        and out.parent==Path('/opt/host/vnf/austinov')and out.name.startswith('run-bole-task-cpu-')
        and not root.is_relative_to(out)and not out.is_relative_to(root)and not any(p.is_symlink()for p in(*root.parents,*out.parents)),
        'new distinct source/output leaves; retained predecessor never changed')
    root.mkdir(mode=0o700)
    for n in(*C.FILES,'PREVIOUS_CPU_EXPECTED.json','CPU3_ACTUAL_ENTRIES.json'):shutil.copyfile(P/n,root/n)
    public=root/'public-source';public.mkdir(mode=0o755);public.chmod(0o755);closure=[]
    def copy(name,data):
        p=public/name;p.write_bytes(data);p.chmod(0o644);r=C.ref(p);closure.append(dict(relative=name,bytes=r['bytes'],sha256=r['sha256']))
    for name in('he_worker.py','task_contract.py'):
        copy(name,(Path(previous['stage']['source_root'])/name).read_bytes())
    copy('he_runtime_probe.py',(P/'he_runtime_probe.py').read_bytes());copy('AUTHORITY.json',C.checked(refs['authority_ref']).read_bytes())
    cap=C.write(public/'HE_CAPSULE.json',dict(schema='bole.HE-runtime-isolation-diagnostic-capsule/v1',files=closure,
        original_control_stage_ref=previous['stage_ref'],identity_hold_seconds=5,original_runtime_guard_unchanged=True,
        evaluator_executed=False,generated_code_executed=False,full_software_qualification_accepted=False));(public/'HE_CAPSULE.json').chmod(0o644)
    stage=C.write(root/'DIAGNOSTIC_STAGE.json',dict(schema='bole.he-runtime-isolation-diagnostic-stage/v1',source_root=str(public),
        suite_root=previous['stage']['suite_root'],input_root=previous['stage']['input_root'],capsule_ref=cap,image_id=C.IMAGE,
        original_control_stage_ref=previous['stage_ref'],evaluator_executed=False))
    value=dict(schema='bole.HE-runtime-isolation-diagnostic-inputs/v1',default_enabled=False,diagnostic_only=True,
        files={n:C.ref(root/n)for n in C.FILES},image_id=C.IMAGE,stage_ref=stage,helper_refs=helpers,
        phase_seconds=3600,cleanup_seconds=180,host_CPU=166,CPU=145,HE_memory_bytes=2*C.GIB,
        reserve_CPU_budget=2,summed_ancestor_CPU_budget=7,HE_seconds=90,identity_hold_seconds=5,
        output_root=str(out),generated_code_executed=False,task_score_produced=False,full_software_qualification_accepted=False,
        model_ready=False,network_safety_accepted=False,**refs)
    return C.write(root/'DIAGNOSTIC_INPUTS.json',value)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true')
    for n in('G1-source-ref','G1-owner-ref','G1-bundle-ref','G1-independent-ref','authority-ref','main-quiescence-ref',
              'previous-CPU-owner-ref','previous-HE-owned-ref','previous-HE-release-ref'):p.add_argument('--'+n)
    for n in('new-root','output-root'):p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    if not a.prepare:print('{"enabled":false,"container_created":false,"NPU":false}');return 0
    C.need(all(v is not None for v in vars(a).values()),'all actual source/prior-stage/retirement/current authority refs required')
    print(json.dumps(dict(inputs_ref=prepare(a),resources_admitted=False,full_software_qualification_accepted=False,NPU=False)));return 0


if __name__=='__main__':raise SystemExit(main())
