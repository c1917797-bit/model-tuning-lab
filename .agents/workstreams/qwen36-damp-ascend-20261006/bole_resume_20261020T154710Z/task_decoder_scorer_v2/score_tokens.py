"""Actual CPU decoding/component grades. Never executes generated code or a model."""
import argparse
import json
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import task_contract as C
import postprocess as S
import decoder as D


def request_body(row,model):
    C.need(type(model)is str and model,'explicit observed served model name')
    return dict(model=model,prompt=row['prompt_token_ids'],max_tokens=2048,ignore_eos=False,
        temperature=0,top_p=1,seed=0,n=1,stream=False,return_token_ids=True)


def completion(record,task,row,model):
    """Independent raw wire validation. Normal-EOS policy != worker EOS proof."""
    request=C.obj(record['request_ref']);response=C.obj(record['response_ref'])
    C.need(set(request)=={'request_id','body'}and C.canonical(request['body'])==C.canonical(request_body(row,model))
           and type(request['request_id'])is str and request['request_id']
           and type(response['status'])is int and response['status']==200,'exact normal-EOS frozen-ID request and actual HTTP200')
    C.need(response['request_id']==request['request_id'],'same actual client response request identity')
    body=response['body'];choices=body['choices']
    C.need(type(choices)is list and len(choices)==1 and type(choices[0]['index'])is int and choices[0]['index']==0
           and body['model']==model and type(body['id'])is str and body['id'],
           'one actual completion identity from same declared model')
    choice=choices[0];ids=choice['token_ids'];usage=body['usage']
    C.need(type(ids)is list and len(ids)<=2048 and all(type(x)is int and 0<=x<248320 for x in ids)
           and type(choice['text'])is str,'actual full returned token IDs and raw completion text')
    C.need(all(type(usage[k])is int for k in('prompt_tokens','completion_tokens','total_tokens'))
           and usage['prompt_tokens']==len(row['prompt_token_ids'])
           and usage['completion_tokens']==len(ids)
           and usage['total_tokens']==len(row['prompt_token_ids'])+len(ids),'actual complete usage, no truncated/re-tokenized output')
    reason=choice['finish_reason']
    C.need(reason in('stop','length')and(reason!='length'or len(ids)==2048),'normal EOS/stop or actual full2048 cap')
    C.need(248046 not in ids[:-1]and(248046 not in ids or reason=='stop'),'EOS, when returned, is last; no tokens after EOS')
    C.need(set(record)=={'task','id','request_ref','response_ref'}and record['task']==task and record['id']==row['id'],
           'raw record joins exact task and ID')
    return ids,choice['text'],dict(finish_reason=reason,completion_tokens=len(ids),
        returned_EOS_observed=bool(ids and ids[-1]==248046),EOS_policy_requested=True,
        actual_worker_normal_EOS_cause_proven=False,request_id=request['request_id'],
        frontend_completion_id=body['id'],actual_frontend_worker_identity_join_accepted=False,
        prompt_token_ids_sha256=C.digest(row['prompt_token_ids']),raw_request_ref=record['request_ref'],
        raw_response_ref=record['response_ref'])


def replay(source_ref,raw_ref,*,full_provenance=True):
    m=C.source(source_ref,seconds=300);C.cpu_runtime();effective=C.verify_inputs(m)
    raw=C.obj(raw_ref)
    C.need(raw['schema']=='bole.actual-three-task-HTTP-completions/v1'and raw['source_ref']==source_ref
           and raw['effective_inputs_ref']==m['effective_inputs_ref']and raw['arm']in('OFF','ON')
           and type(raw['model'])is str and raw['model'],'actual source/input/arm-bound raw record set')
    cases=list(C.select(effective,raw['phase']));records=raw['records'];C.exact_order(records,cases)
    C.need(len({C.obj(r['request_ref'])['request_id']for r in records})==len(records),'actual request IDs unique across tasks')
    tok,identity=D.create(m,effective);coverage=None
    if full_provenance:
        import provenance
        coverage=provenance.run(m,effective,tok)
    finish_counts={task:{'stop':0,'length':0}for task in C.COUNTS}
    grades=[];samples=[];problems=[];counts={task:0 for task in C.COUNTS};correct={task:0 for task in('GSM8K','MMLU')}
    for record,(task,row)in zip(records,cases):
        ids,wire_text,identity_row=completion(record,task,row,raw['model']);text=D.decode(tok,ids)
        C.need(text==wire_text,'actual independent returned-ID decoding equals actual server completion text')
        if task=='GSM8K':grade=S.gsm_grade(text,row['gold_row'],m['files']['frozen/gsm_scorer.py'])
        elif task=='MMLU':grade=S.mmlu_grade(text,row['gold'])
        else:
            grade=S.human_eval_completion(text,row['official_problem']['prompt'])
            samples.append(dict(task_id=row['id'],completion=grade['completion']))
            problems.append(row['official_problem'])
        counts[task]+=1;finish_counts[task][identity_row['finish_reason']]+=1
        if task!='HumanEval':correct[task]+=int(grade['correct'])
        grades.append(dict(task=task,id=row['id'],raw_decoded_text=text,raw_token_ids_sha256=C.digest(ids),
            frozen_row_sha256=C.digest(row),actual_output=identity_row,grade=grade))
    C.need(counts==({k:2 for k in C.COUNTS}if raw['phase']=='smoke'else C.COUNTS),'measured complete selected counts')
    C.cpu_runtime();C.current_authority(m['authority_ref'])
    return dict(schema='bole.actual-three-task-component-grades/v1',source_ref=source_ref,raw_ref=raw_ref,
        effective_inputs_ref=m['effective_inputs_ref'],phase=raw['phase'],arm=raw['arm'],model=raw['model'],
        postprocess_protocol=S.PROTOCOL,counts=counts,correct=correct,finish_reason_counts=finish_counts,
        component_scores={task:correct[task]/counts[task]for task in correct},rows=grades,
        human_eval_samples=samples,human_eval_problems=problems,decoder=identity,coverage=coverage,
        actual_task_output_decoded=True,human_eval_code_executed=False,
        normal_EOS_native_worker_proof_accepted=False,worker_lifecycle_accepted=False,
        BOLE_activation_accepted=False,task_accuracy_accepted=False,model_ready=False,
        performance_ready=False,NPU=False)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--raw-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"generated_code_executed":false,"task_ready":false}');return 0
    C.need(a.source_ref and a.raw_ref and a.output,'explicit actual source/raw/output')
    sr=json.loads(a.source_ref);m=C.source(sr)
    C.need(C.ref(__file__)==m['files']['score_tokens.py'],'whole exact score source')
    print(json.dumps(C.write(a.output,replay(sr,json.loads(a.raw_ref)))));return 0


if __name__=='__main__':raise SystemExit(main())
