"""Metadata/public byte copies only; execution is a separate default-OFF CLI."""
import argparse
import json
from pathlib import Path
import shutil
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import owner_namespace as N
import main_quiescence as Q
import preflight_contract as T


def prepare(a):
    names=('G1_source_ref','G1_owner_ref','G1_bundle_ref','G1_independent_ref','authority_ref','main_quiescence_ref',
           'previous_CPU_owner_ref','previous_HE_owned_ref','previous_HE_release_ref','dependency_copy_ref')
    refs={n:json.loads(getattr(a,n))for n in names};C.authority(refs['authority_ref'],3600)
    Q.policy(refs['main_quiescence_ref'],authority_ref=refs['authority_ref'])
    prior=T.predecessor(refs['previous_CPU_owner_ref'],refs['previous_HE_owned_ref'],refs['previous_HE_release_ref'])
    old=prior['stage'];cap=C.obj(old['capsule_ref'])
    C.need(cap['authority_sha256']==refs['authority_ref']['sha256'],'same still-current finite authority; original cutoffs never extended')
    actual=C.obj(C.ref(P/'CPU12_ACTUAL_REFS.json'))
    C.need(C.ref(C.checked(refs['dependency_copy_ref']))==actual['COPY.json'],'exact actual primary whole COPY record, no reconstructed metadata substitute')
    copied=C.obj(refs['dependency_copy_ref']);expected=C.obj(C.ref(P/'DEPENDENCY_EXPECTED.json'))
    C.need(copied['schema']==expected['schema'].replace('bole.HE-python312-dependency-expected','bole.actual-stopped-same-image-Python312-dependency-source-copy')
        and copied['container']==expected['stopped_source_CID']and copied['no_guest_exec_or_import']is True
        and copied['files']==expected['files']and copied['actual_prior_binding']==expected['prior_binding'],
        'actual stopped same-image copied source/executable facts; existence is not import qualification')
    for row in copied['files'].values():C.checked(row['copied_ref'])
    on=C.basis(refs['G1_source_ref'],refs['G1_owner_ref'],refs['G1_bundle_ref'],refs['G1_independent_ref']);helpers=N.helper_refs(C,on)
    root=a.new_root;out=a.output_root
    C.need(root.is_absolute()and root.parent.is_dir()and not root.exists()and out.is_absolute()and not out.exists()
        and out.parent==Path('/opt/host/vnf/austinov')and out.name.startswith('run-bole-task-cpu-')
        and not root.is_relative_to(out)and not out.is_relative_to(root)
        and not any(p.is_symlink()for p in(*root.parents,*out.parents)),'new ordinary distinct source/output leaves')
    root.mkdir(mode=0o700)
    for name in(*T.FILES,*T.DATA,*T.PUBLIC):
        destination=root/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/name,destination)
    public=root/'public';public.mkdir(mode=0o755)
    source=public/'source';inputs=public/'inputs'
    for directory in(source,inputs):directory.mkdir(mode=0o755);directory.chmod(0o755)
    for name in(*T.PUBLIC,'AUTHORITY.json','HE_CAPSULE.json'):
        dst=source/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.parent.chmod(0o755)
        shutil.copyfile(Path(old['source_root'])/name,dst);dst.chmod(0o644)
    for name in('INPUTS.json','samples.jsonl','problems.jsonl'):
        dst=inputs/name;shutil.copyfile(Path(old['input_root'])/name,dst);dst.chmod(0o644)
    stage=C.write(root/'PREFLIGHT_STAGE.json',dict(schema='bole.HE-dependency-preflight-stage/v1',mode='preflight',image_id=C.IMAGE,
        source_root=str(source),suite_root=old['suite_root'],input_root=str(inputs),capsule_ref=C.ref(source/'HE_CAPSULE.json'),
        inputs_ref=C.ref(inputs/'INPUTS.json'),original_stage_ref=prior['stage_ref'],original_task_source_ref=prior['root_source_ref'],
        evaluator_called=False,generated_code_executed=False))
    value=dict(schema='bole.HE-dependency-preflight-inputs/v1',default_enabled=False,diagnostic_only=True,
        files={n:C.ref(root/n)for n in T.FILES},data_files={n:C.ref(root/n)for n in T.DATA},
        image_id=C.IMAGE,stage_ref=stage,helper_refs=helpers,output_root=str(out),
        phase_seconds=3600,cleanup_seconds=180,HE_seconds=90,CPU=145,host_CPU=166,HE_memory_bytes=2*C.GIB,
        reserve_CPU_budget=2,summed_ancestor_CPU_budget=7,generated_code_executed=False,
        task_score_produced=False,full_software_qualification_accepted=False,model_ready=False,NPU=False,**refs)
    return C.write(root/'PREFLIGHT_INPUTS.json',value)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true')
    for n in('G1-source-ref','G1-owner-ref','G1-bundle-ref','G1-independent-ref','authority-ref','main-quiescence-ref',
              'previous-CPU-owner-ref','previous-HE-owned-ref','previous-HE-release-ref','dependency-copy-ref'):p.add_argument('--'+n)
    for n in('new-root','output-root'):p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    if not a.prepare:print('{"enabled":false,"container_created":false,"NPU":false}');return 0
    C.need(all(v is not None for v in vars(a).values()),'all actual predecessor/source/authority refs and new roots required')
    print(json.dumps(dict(inputs_ref=prepare(a),resources_admitted=False,qualified=False,NPU=False)));return 0


if __name__=='__main__':raise SystemExit(main())
