"""Runs only inside a separately MAIN-owned strict Devices[] CPU sandbox."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import sys
import time
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import task_contract as C

MARKER='BOLE_HE_OFFICIAL_V1 '
EVAL_SHA='e926d5e9b8f1ec040096cd5952e8cf79f8dc0b7fb80ba6667ce604ffea0397bc'
EXEC_SHA='79901c6f5b59701c465b164aed290fa53abc35abc80a5378fc10f4dac1f9a84c'


def local_hash(root,row):
    p=Path(row['relative']);C.need(not p.is_absolute()and '..'not in p.parts,'bounded public capsule relative path')
    actual=C.ref(root/p);C.need((actual['bytes'],actual['sha256'])==(row['bytes'],row['sha256']),'whole public capsule/source/input bytes')


def runtime():
    C.cpu_runtime();C.need(P==Path('/source')and os.getuid()==os.geteuid()==65534,'actual nonprivileged dedicated sandbox')
    C.need(os.environ.get('ASCEND_VISIBLE_DEVICES')==''and os.environ.get('HOME')=='/tmp'
           and {p.name for p in Path('/sys/class/net').iterdir()}<={'lo'},'actual no-network namespace')
    status=Path('/proc/self/status').read_text()
    C.need('NoNewPrivs:\t1'in status and 'CapEff:\t0000000000000000'in status,'no privileges/capabilities')
    allowed={'PATH','HOME','LANG','LC_CTYPE','ASCEND_RT_VISIBLE_DEVICES','ASCEND_VISIBLE_DEVICES',
        'TORCH_DEVICE_BACKEND_AUTOLOAD','PYTHONDONTWRITEBYTECODE','HF_HUB_OFFLINE','OPENBLAS_NUM_THREADS',
        'OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'}
    C.need(set(os.environ)<=allowed,'minimal env-i, no inherited credentials/secrets')
    C.need(resource.getrlimit(resource.RLIMIT_NOFILE)==(128,128)
           and resource.getrlimit(resource.RLIMIT_FSIZE)==(8388608,8388608),'actual per-process limits')
    C.need(Path.cwd()==Path('/tmp'),'only private temporary working directory')


def rows(path):return [json.loads(line)for line in Path(path).read_text().splitlines()if line.strip()]


def run(mode,capsule_sha):
    runtime();capsule_path=P/'HE_CAPSULE.json';raw=capsule_path.read_bytes()
    C.need(hashlib.sha256(raw).hexdigest()==capsule_sha,'exact new dedicated capsule source')
    cap=json.loads(raw);C.need(cap['schema']=='bole.he-public-source-capsule/v1','new explicit evaluator capsule')
    for row in cap['files']:local_hash(P,row)
    ar=P/'AUTHORITY.json';C.need(C.ref(ar)['sha256']==cap['authority_sha256'],'exact new authority bytes')
    authority=json.loads(ar.read_bytes())
    C.need(authority['start_epoch']<=time.time()and time.time()+30<authority['cutoff_epoch'],'new current sandbox admission, original cutoffs untouched')
    for row in cap['official_package_files']:local_hash(Path('/suite'),row)
    C.need(C.ref('/suite/human_eval/evaluation.py')['sha256']==EVAL_SHA
           and C.ref('/suite/human_eval/execution.py')['sha256']==EXEC_SHA,'unchanged official original executor/evaluator')
    input_path=Path('/inputs/INPUTS.json');inp=json.loads(input_path.read_bytes())
    C.need(inp['schema']=='bole.he-official-staged-inputs/v1'and inp['root_source_sha256']==cap['root_source_sha256']
           and inp['capsule_sha256']==capsule_sha and inp['authority_sha256']==cap['authority_sha256'],'same exact root source/input/capsule/authority')
    for row in inp['files']:local_hash(Path('/inputs'),row)
    sys.path.insert(0,'/suite')
    import human_eval.evaluation as E
    import human_eval.execution as X
    import numpy,tqdm
    C.need(C.ref(E.__file__)['sha256']==EVAL_SHA and C.ref(X.__file__)['sha256']==EXEC_SHA,'actual original imported functions')
    base=dict(schema='bole.actual-HE-official-sandbox-result/v1',mode=mode,
        root_source_sha256=cap['root_source_sha256'],capsule_sha256=capsule_sha,
        input_sha256=hashlib.sha256(input_path.read_bytes()).hexdigest(),authority_sha256=cap['authority_sha256'],
        official_evaluation_sha256=EVAL_SHA,official_execution_sha256=EXEC_SHA,
        runtime_identity=dict(python_executable=sys.executable,python_version=sys.version,
            numpy_version=numpy.__version__,tqdm_version=tqdm.__version__,
            numpy_source=C.ref(Path(numpy.__file__).resolve()),tqdm_source=C.ref(Path(tqdm.__file__).resolve())),
        task_accuracy_accepted=False,model_ready=False,NPU=False)
    if mode=='preflight':
        runtime();return dict(base,generated_code_executed=False,task_score_produced=False)
    samples=rows('/inputs/samples.jsonl');problems=rows('/inputs/problems.jsonl')
    C.need(mode==inp['kind']and all(set(s)=={'task_id','completion'}and type(s['completion'])is str for s in samples),
           'exact immutable completion strings and explicit controls/tasks mode')
    C.need(time.time()+4*len(samples)+30<authority['cutoff_epoch'],
           'whole bounded official evaluator timeout budget fits new authority')
    work=Path('/tmp/official-he-work');work.mkdir(mode=0o700)
    shutil.copyfile('/inputs/samples.jsonl',work/'samples.jsonl');shutil.copyfile('/inputs/problems.jsonl',work/'problems.jsonl')
    before=time.monotonic()
    metrics=E.evaluate_functional_correctness(str(work/'samples.jsonl'),k=[1],n_workers=1,timeout=3.0,problem_file=str(work/'problems.jsonl'))
    actual=rows(work/'samples.jsonl_results.jsonl')
    C.need(time.time()<authority['cutoff_epoch'],'completed inside unchanged new authority window')
    C.need(len(actual)==len(samples)and all(a['task_id']==s['task_id']and a['completion']==s['completion']
           and type(a['passed'])is bool and type(a['result'])is str for a,s in zip(actual,samples)),
           'original evaluator output joins complete exact immutable samples')
    if mode=='controls':
        C.need(inp['case_labels']==['correct','wrong','timeout']and len(samples)==3 and len(problems)==1
               and [r['passed']for r in actual]==[True,False,False]
               and actual[2]['result']=='timed out','correct/wrong/timeout controls must discriminate')
        return dict(base,rows=actual,case_labels=inp['case_labels'],control_discrimination_pass=True,
            generated_code_executed=True,task_score_produced=False,elapsed_seconds=time.monotonic()-before)
    expected=C.SMOKE['HumanEval']if inp['phase']=='smoke'else['HumanEval/'+str(i)for i in range(164)]
    C.need([s['task_id']for s in samples]==[p['task_id']for p in problems]==expected,'exact whole selected HE cohort')
    score=sum(r['passed']for r in actual)/len(actual)
    C.need(set(metrics)=={'pass@1'}and abs(metrics['pass@1']-score)<1e-12,'actual original complete-count pass@1')
    return dict(base,rows=actual,count=len(actual),component_score=score,
        generated_code_executed=True,task_score_produced=True,elapsed_seconds=time.monotonic()-before)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);g=p.add_mutually_exclusive_group()
    for mode in('preflight','controls','tasks'):g.add_argument('--'+mode,action='store_true')
    p.add_argument('--capsule-sha256');a=p.parse_args();mode=next((x for x in('preflight','controls','tasks')if getattr(a,x)),None)
    if mode is None:print('{"enabled":false,"generated_code_executed":false}');return 0
    C.need(a.capsule_sha256,'explicit capsule identity')
    print(MARKER+C.canonical(run(mode,a.capsule_sha256)).decode(),flush=True);return 0


if __name__=='__main__':raise SystemExit(main())
