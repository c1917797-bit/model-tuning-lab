"""Stages public-only official evaluator inputs; prints argv, never executes it."""
import argparse
import gzip
import json
import shutil
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import task_contract as C
import he_policy as H


def bytes_write(path,data):
    with Path(path).open('xb')as stream:stream.write(data)
    Path(path).chmod(0o644);return C.ref(path)


def slim(reference,relative):return dict(relative=relative,bytes=reference['bytes'],sha256=reference['sha256'])


def jsonl(path,rows):return bytes_write(path,b''.join(C.canonical(row)+b'\n'for row in rows))


def run(source_ref,output,kind,grades_ref=None):
    m=C.source(source_ref,seconds=300);C.cpu_runtime();effective=C.verify_inputs(m)
    C.need(kind in('controls','tasks')and output.is_absolute()and not output.exists()and output.parent.is_dir(),'new separate public-only HE stage')
    package=C.obj(m['human_eval_package_ref']);dataset=C.checked(package['dataset_ref']);original_suite=dataset.parent.parent
    package_rows=[]
    for reference in package['files']+[package['dataset_ref']]:
        relative=str(C.checked(reference).relative_to(original_suite));package_rows.append(slim(reference,relative))
    with gzip.open(dataset,'rt',encoding='utf8')as stream:official=[json.loads(line)for line in stream if line.strip()]
    C.need([r['task_id']for r in official]==['HumanEval/'+str(i)for i in range(164)],'full original official HE dataset')
    if kind=='controls':
        C.need(grades_ref is None,'software controls never consume model task outputs')
        problem=official[0];problems=[problem];phase='software-controls'
        samples=[dict(task_id=problem['task_id'],completion=value)for value in(
            problem['canonical_solution'],"    raise AssertionError('deliberately wrong software control')\n",
            '    while True:\n        pass\n')]
    else:
        import score_tokens as S
        grade=C.obj(grades_ref);independent=S.replay(source_ref,grade['raw_ref'])
        C.need(grade==independent,'independently redecoded/graded actual task rows before HE staging')
        samples=grade['human_eval_samples'];problems=grade['human_eval_problems'];phase=grade['phase']
        lookup={r['task_id']:r for r in official}
        C.need(all(p==lookup[p['task_id']]for p in problems),'all staged actual HE tests/gold remain official')
    output.mkdir(mode=0o755);output.chmod(0o755)
    source_root=output/'source';input_root=output/'inputs';suite=output/'suite'
    for directory in(source_root,input_root,suite):directory.mkdir(mode=0o755);directory.chmod(0o755)
    for reference in package['files']+[package['dataset_ref']]:
        relative=C.checked(reference).relative_to(original_suite);destination=suite/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        for parent in(destination.parent,*destination.parent.parents):
            if parent==suite.parent:break
            parent.chmod(0o755)
        bytes_write(destination,C.checked(reference).read_bytes())
    closure=[]
    for name in('he_worker.py','task_contract.py'):
        reference=m['files'][name];actual=bytes_write(source_root/name,C.checked(reference).read_bytes());closure.append(slim(actual,name))
    authority=bytes_write(source_root/'AUTHORITY.json',C.checked(m['authority_ref']).read_bytes());closure.append(slim(authority,'AUTHORITY.json'))
    capsule=C.write(source_root/'HE_CAPSULE.json',dict(schema='bole.he-public-source-capsule/v1',
        root_source_sha256=source_ref['sha256'],authority_sha256=authority['sha256'],files=closure,
        official_package_files=package_rows,official_repository=package['repository'],official_commit=package['commit']))
    (source_root/'HE_CAPSULE.json').chmod(0o644)
    staged_files=[slim(jsonl(input_root/'samples.jsonl',samples),'samples.jsonl'),
                  slim(jsonl(input_root/'problems.jsonl',problems),'problems.jsonl')]
    inputs=C.write(input_root/'INPUTS.json',dict(schema='bole.he-official-staged-inputs/v1',kind=kind,phase=phase,
        root_source_sha256=source_ref['sha256'],capsule_sha256=capsule['sha256'],authority_sha256=authority['sha256'],
        files=staged_files,case_labels=['correct','wrong','timeout']if kind=='controls'else None))
    (input_root/'INPUTS.json').chmod(0o644)
    result=dict(schema='bole.he-sandbox-stage/v1',source_ref=source_ref,effective_inputs_ref=m['effective_inputs_ref'],
        kind=kind,phase=phase,grades_ref=grades_ref,source_root=str(source_root),suite_root=str(suite),input_root=str(input_root),
        capsule_ref=capsule,inputs_ref=inputs,original_suite_root=str(original_suite),official_package_ref=m['human_eval_package_ref'],image_id=m['image_id'],
        container_not_created=True,generated_code_executed=False,task_ready=False)
    C.current_authority(m['authority_ref']);return C.write(output/'STAGE.json',result)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--output',type=Path);p.add_argument('--kind',choices=('controls','tasks'))
    p.add_argument('--grades-ref');p.add_argument('--container-name');a=p.parse_args()
    if not a.prepare:print('{"enabled":false,"container_created":false,"generated_code_executed":false}');return 0
    C.need(a.source_ref and a.output and a.kind and a.container_name,'explicit source/new stage/mode/name')
    sr=json.loads(a.source_ref);gr=None if a.grades_ref is None else json.loads(a.grades_ref)
    reference=run(sr,a.output,a.kind,gr);stage=C.obj(reference)
    command=H.argv(a.container_name,stage['image_id'],stage['source_root'],stage['suite_root'],stage['input_root'],
        stage['capsule_ref']['sha256'],stage['kind'])
    print(json.dumps(dict(stage_ref=reference,create_argv=command,MAIN_actual_owner_launch_and_inspect_required=True)));return 0


if __name__=='__main__':raise SystemExit(main())
