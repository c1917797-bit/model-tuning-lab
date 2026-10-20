"""Owned Devices[] child: fixed pure controls, actual full tokenizer replay or reader."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C


def snapshot():
    stat=Path('/proc/self/stat').read_text();fields=stat[stat.rfind(')')+2:].split()
    return dict(pid=os.getpid(),uid=os.getuid(),euid=os.geteuid(),start_ticks=int(fields[19]),
        affinity=sorted(os.sched_getaffinity(0)),cgroup=Path('/proc/self/cgroup').read_text(),
        status=Path('/proc/self/status').read_text(),executable=os.readlink('/proc/self/exe'),
        actual_python_argv=[v.decode()for v in Path('/proc/self/cmdline').read_bytes().split(b'\0')if v])


def run(inputs_ref,mode,out,owner_ref=None,bound_ref=None,decoder_ref=None,stage_ref=None):
    x=C.inputs(inputs_ref,host=False);task=Path(x['task_packet_root']);sys.path.insert(0,str(task))
    import task_contract as T
    T.cpu_runtime();C.need(os.sched_getaffinity(0)=={145}and out.is_dir(),'actual oneCPU145 Devices[] child')
    before=snapshot();initial=C.write(out/('CHILD-START-'+mode+'.json'),before)
    readset,_=C.task_readset(x['task_source_unbound_ref'],host=False)
    hashes_before={r['path']:r['sha256']for r in readset}
    if mode=='prepare-decode':
        C.need(owner_ref is bound_ref is decoder_ref is stage_ref is None,'predeclared software-only entry')
        # Exactly the frozen38 local controls; their own9 entrypoint help/OFF checks execute here.
        command=[sys.executable,'-I','-B',str(task/'test_software.py')]
        value=subprocess.run(command,capture_output=True,text=True,timeout=120)
        C.write(out/'SOFTWARE-CONTROLS.json',dict(argv=command,returncode=value.returncode,
            stdout=value.stdout,stderr=value.stderr,pure_tests=38,generated_code_executed=False,task_score_produced=False))
        C.need(value.returncode==0 and 'Ran 38 tests'in value.stderr and value.stderr.rstrip().endswith('OK'),'actual frozen38 software controls')
        import restore_GSM_inputs as G
        import prepare_packet as B
        import decoder as D
        import provenance as V
        effective_ref=G.run(x['task_source_unbound_ref'],out/'effective-v012')
        bound=B.bind(x['task_source_unbound_ref'],effective_ref,out/'TASK_SOURCE_BOUND.json');m=T.source(bound,seconds=300)
        effective=T.verify_inputs(m);tok,identity=D.create(m,effective)
        report=dict(source=bound,rendered_inputs_ref=m['rendered_inputs_ref'],effective_inputs_ref=m['effective_inputs_ref'],
            decoder=identity,result=D.controls(tok),coverage=V.run(m,effective,tok),
            actual_frozen_tokenizer_executed=True,same_image_owner_verified=False,
            model_ready=False,task_ready=False,performance_ready=False)
        decoder_ref=T.write(out/'DECODER.json',report)
        import stage_he as H
        stage_ref=H.run(bound,out/'he-public-controls','controls')
        payload=dict(bound_task_source_ref=bound,effective_inputs_ref=effective_ref,decoder_ref=decoder_ref,
            HE_stage_ref=stage_ref,counts=report['coverage']['counts'],pure_controls_pass=True,
            all_input_source_gold_template_verified=report['coverage']['complete_official_source_gold_and_template_coverage'])
    else:
        C.need(mode=='independent-reader'and all(v is not None for v in(owner_ref,bound_ref,decoder_ref,stage_ref)),
               'actual existing frozen source/decoder/stage/HE owner refs required')
        import consume_results as R
        result=R.run(bound_ref,stage_ref,owner_ref,decoder_ref)
        C.need(result['software_controls_only']is True and result['independent_component_checks_pass']is True
               and result['HumanEval']['official_executor_controls_pass']is True
               and result['formal_task_accuracy_accepted']is False,'actual independent software controls only')
        attribution=C.write(out/'ATTRIBUTION.json',result)
        payload=dict(independent_ref=attribution,software_controls_pass=True,task_score_produced=False)
    after={r['path']:C.ref(C.checked(r))['sha256']for r in readset}
    T.cpu_runtime();C.authority(x['authority_ref']);C.need(after==hashes_before,'unchanged complete input/source readset across CPU child')
    return C.write(out/('CHILD-'+mode+'.json'),dict(schema='bole.actual-task-CPU-child/v1',inputs_ref=inputs_ref,
        mode=mode,start_ref=initial,process_before=before,process_after=snapshot(),readset_before=hashes_before,
        readset_after=after,payload=payload,model_executed=False,HTTP_executed=False,
        generated_code_executed=False,task_score_produced=False,NPU=False,model_ready=False))


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--mode',choices=('prepare-decode','independent-reader'));p.add_argument('--inputs-ref');p.add_argument('--output',type=Path)
    for name in('owner-ref','bound-ref','decoder-ref','stage-ref'):p.add_argument('--'+name)
    a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"HTTP_executed":false}');return 0
    C.need(a.mode and a.inputs_ref and a.output,'explicit finite owned CPU entry')
    optional={name:None if getattr(a,name)is None else json.loads(getattr(a,name))for name in('owner_ref','bound_ref','decoder_ref','stage_ref')}
    print(json.dumps(run(json.loads(a.inputs_ref),a.mode,a.output,**optional)));return 0


if __name__=='__main__':raise SystemExit(main())
