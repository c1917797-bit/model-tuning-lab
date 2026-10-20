"""Exact-count full-cohort numerical comparison; no formal/model promotion."""
import argparse
import json
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import task_contract as C
import consume_results as R


def loss_gate(off_correct,on_correct,count):
    C.need(type(count)is int and count>0 and type(off_correct)is type(on_correct)is int
           and 0<=off_correct<=count and 0<=on_correct<=count,'actual complete integer correct counts')
    drop=max(0,off_correct-on_correct)
    defined=off_correct>0
    return dict(count=count,OFF_correct=off_correct,ON_correct=on_correct,
        OFF_score=off_correct/count,ON_score=on_correct/count,drop_correct_count=drop,
        drop_percentage_points=100*drop/count,
        drop_relative=None if not defined else drop/off_correct,
        relative_comparison_defined=defined,absolute_drop_at_most_one_pp=100*drop<=count,
        relative_drop_at_most_one_percent=defined and 100*drop<=off_correct,
        component_loss_gate_pass=defined and 100*drop<=count and 100*drop<=off_correct)


def reopen(source_ref,reference):
    value=C.obj(reference)
    expected=R.run(source_ref,value['HE_stage_ref'],value['HE_owner_ref'],value['decoder_smoke_ref'],value['grades_ref'])
    C.need(value==expected,'independently replayed whole actual component result')
    return value


def run(source_ref,off_ref,on_ref):
    m=C.source(source_ref,seconds=900);C.cpu_runtime()
    off=reopen(source_ref,off_ref);on=reopen(source_ref,on_ref)
    C.need(off['phase']==on['phase']=='full'and off['arm']=='OFF'and on['arm']=='ON'
           and off['counts']==on['counts']==C.COUNTS and not off['software_controls_only']and not on['software_controls_only'],
           'same source/input generation protocol and complete full OFF/ON task cohorts')
    gates={task:loss_gate(off['component_correct'][task],on['component_correct'][task],count)
           for task,count in C.COUNTS.items()}
    C.current_authority(m['authority_ref'])
    return dict(schema='bole.independent-three-task-count-comparison/v1',source_ref=source_ref,
        OFF_ref=off_ref,ON_ref=on_ref,effective_inputs_ref=m['effective_inputs_ref'],tasks=gates,
        all_component_loss_gates_pass=all(x['component_loss_gate_pass']for x in gates.values()),
        same_model_stack_concurrency_and_common_effects_verified=False,
        all_request_BOLE_activation_verified=False,normal_EOS_native_worker_proof_accepted=False,
        formal_task_accuracy_accepted=False,model_ready=False,performance_ready=False,NPU=False)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    for name in('source-ref','off-ref','on-ref'):p.add_argument('--'+name)
    p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"formal_task_accuracy_accepted":false}');return 0
    C.need(a.source_ref and a.off_ref and a.on_ref and a.output,'explicit actual full paired evidence/output')
    result=run(json.loads(a.source_ref),json.loads(a.off_ref),json.loads(a.on_ref))
    print(json.dumps(C.write(a.output,result)));return 0


if __name__=='__main__':raise SystemExit(main())
