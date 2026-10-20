"""Prepare exact prompt-only requests; no HTTP/model execution."""
import argparse
import json
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import task_contract as C
import score_tokens as S


def run(source_ref,phase,arm,model,output):
    m=C.source(source_ref,seconds=300);C.cpu_runtime();effective=C.verify_inputs(m)
    C.need(arm in('OFF','ON')and output.is_absolute()and not output.exists(),'explicit new arm/request-plan leaf')
    output.mkdir(mode=0o700);count=0
    path=output/'requests.jsonl'
    with path.open('xb')as stream:
        for task,row in C.select(effective,phase):
            value=dict(task=task,id=row['id'],frozen_row_sha256=C.digest(row),body=S.request_body(row,model))
            C.need(set(value['body'])=={'model','prompt','max_tokens','ignore_eos','temperature','top_p','seed','n','stream','return_token_ids'},
                   'wire contains prompt IDs and generation policy only; no gold/test/prompt text')
            stream.write(C.canonical(value)+b'\n');count+=1
    C.current_authority(m['authority_ref'])
    return C.write(output/'REQUEST_PLAN.json',dict(schema='bole.three-task-prompt-only-request-plan/v1',source_ref=source_ref,
        effective_inputs_ref=m['effective_inputs_ref'],phase=phase,arm=arm,model=model,count=count,requests_ref=C.ref(path),
        minimum_model_context_tokens=5199,concurrency=1,HTTP_executed=False,model_ready=False,task_ready=False))


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--phase',choices=('smoke','full'));p.add_argument('--arm',choices=('OFF','ON'))
    p.add_argument('--model');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.prepare:print('{"enabled":false,"HTTP_executed":false}');return 0
    C.need(a.source_ref and a.phase and a.arm and a.model and a.output,'explicit source/phase/arm/model/output')
    print(json.dumps(run(json.loads(a.source_ref),a.phase,a.arm,a.model,a.output)));return 0


if __name__=='__main__':raise SystemExit(main())
