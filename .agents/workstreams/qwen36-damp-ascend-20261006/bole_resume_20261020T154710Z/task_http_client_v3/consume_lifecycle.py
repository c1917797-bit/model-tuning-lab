"""Independent CPU reader for bounded actual normal-EOS smoke/native retirement.
Does not import or call the native inference runtime, issue HTTP, or execute code.
Actual token decoding uses the unchanged frozen CPU task decoder on execute only.
"""
import argparse
import json
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import http_common as C
ROLES=('scheduler','frontend','worker0','worker1','worker2','worker3')


def journal(reference,source_ref,role):
    p=C.checked(reference);C.need(p.stat().st_size<=16*2**20,'bounded complete role journal');raw=p.read_bytes()
    C.need(raw.endswith(b'\n'),'complete last durable journal line');rows=[C.parse(s)for s in raw.splitlines()]
    C.need(3<=len(rows)<=128 and all(v['schema']=='bole.actual-native-finish-event/v1'and v['ordinal']==n for n,v in enumerate(rows)),'complete ordered native event journal')
    C.need(rows[0]['event']=='header'and rows[-1]['event']=='closed'and sum(r['event']=='header'for r in rows)==sum(r['event']=='closed'for r in rows)==1,'one header and complete explicit freeze')
    h=rows[0]['payload'];C.need(h['source_ref']==source_ref and h['role']==role
        and rows[-1]['payload']==dict(native_source_unchanged=True,process=h['process']),'same exact source/role/process across completed freeze')
    C.need(all(rows[n]['monotonic_ns']<=rows[n+1]['monotonic_ns']for n in range(len(rows)-1)),'actual per-process event order')
    return h,rows


def inventory(source_ref,root,out):
    C.source(source_ref,native_runtime=False);mapping={}
    for role in ROLES:
        found=list(root.glob(role+'-*.REF.json'));C.need(len(found)==1,'one explicit frozen '+role+' journal')
        r=C.obj(C.ref(found[0]));journal(r,source_ref,role);mapping[role]=r
    return C.write(out,dict(schema='bole.actual-task-smoke-journal-inventory/v1',source_ref=source_ref,journals=mapping))


def stop_replay(before,after,max_model_len,body,generation):
    p=after['parameters'];C.need(before['parameters']==p and before['num_output_tokens']==after['num_output_tokens']
        and before['num_tokens']==after['num_tokens']and before['last_token_id']==after['last_token_id']
        and before['request_id']==after['request_id']and before['object_id']==after['object_id']and before['status']=='RUNNING'
        and before['stop_reason']is None,'actual same native request after token append, before stop status mutation')
    C.need(not after['pooling']and not after['resumable']and not after['prompt_embeds']and after['prompt_token_ids']==body['prompt']
        and after['all_token_ids']==body['prompt']+after['output_token_ids']
        and after['num_tokens']==len(after['all_token_ids'])and after['num_output_tokens']==len(after['output_token_ids'])
        and after['output_token_ids']and after['last_token_id']==after['output_token_ids'][-1],'actual full native prompt/output/current counters')
    extra=generation.get('eos_token_id',[]);extra={extra}if type(extra)is int else set(extra);extra.discard(248046)
    C.need(p['ignore_eos']is body['ignore_eos']and p['eos_token_id']==(None if body['ignore_eos']else 248046)
        and p['stop_token_ids']==([]if body['ignore_eos']else sorted(extra))and p['all_stop_token_ids']==sorted(extra|{248046})
        and p['stop']==[]and p['repetition_detection']is None and p['min_tokens']==0 and p['max_tokens']==body['max_tokens']
        and after['request_max_tokens']==body['max_tokens']and p['temperature']==0 and p['top_p']==1 and p['seed']==0 and p['n']==1
        and p['presence_penalty']==p['frequency_penalty']==0 and p['repetition_penalty']==1
        and p['output_kind']in{'RequestOutputKind.FINAL_ONLY','RequestOutputKind.CUMULATIVE'},'actual neutral native EOS/greedy policy matches exact wire and checkpoint defaults')
    C.need(max_model_len>=5199 and 0<after['num_output_tokens']<=body['max_tokens'],'actual admitted full context/output geometry')
    last=after['last_token_id'];stop_reason=None
    if last==p['eos_token_id']:cause='primary-EOS';status='FINISHED_STOPPED';reason='stop'
    elif last in p['stop_token_ids']:cause='checkpoint-secondary-EOS';status='FINISHED_STOPPED';reason='stop';stop_reason=last
    elif after['num_tokens']>=max_model_len or after['num_output_tokens']>=body['max_tokens']:
        cause='output-budget'if after['num_output_tokens']>=body['max_tokens']else'model-context';status='FINISHED_LENGTH_CAPPED';reason='length'
    else:raise ValueError('native stop not independently justified by exact pinned check_stop order')
    C.need(cause!='model-context'and after['status']==status and after['stop_reason']==stop_reason,'EOS priority before exact2048 cap; no prompt/context truncation')
    # Every earlier output token must remain eligible for continuation.
    terminal_tokens=set(p['stop_token_ids'])|({p['eos_token_id']}if p['eos_token_id']is not None else set())
    C.need(not terminal_tokens.intersection(after['output_token_ids'][:-1]),'no native emitted token after an earlier EOS')
    return dict(cause=cause,finish_reason=reason,stop_reason=stop_reason,output_token_count=after['num_output_tokens'])


def events(rows,kind):return[(v['ordinal'],v['payload'])for v in rows if v['event']==kind]

def unique_request(rows,kind):
    out={}
    for ordinal,p in events(rows,kind):
        rid=p['after']['request_id']if kind=='check_stop'else p['request_id']
        C.need(rid not in out,'unique actual '+kind+' event');out[rid]=(ordinal,p)
    return out


def validate_one(request,response,front,step,update,kv,blocks,free,engine,worker_rows,generation,*,require_workers=True):
    body=request['body'];b=response['body'];choice=b['choices'][0];rid=step['after']['request_id']
    C.need(response['status']==200 and response['request_id']==request['request_id']and b['model']==body['model']and len(b['choices'])==1
        and choice['index']==0 and type(b['id'])is str and front['external_req_id']==b['id']+'-0'and front['request_id']==rid,'actual engine internal/frontend external/HTTP completion identity join')
    native=step['after'];replay=stop_replay(step['before'],native,step['max_model_len'],body,generation)
    C.need(step['returned']is True and front['prompt_token_ids']==body['prompt']and front['max_tokens_param']==body['max_tokens']
        and front['output_kind']in{'RequestOutputKind.CUMULATIVE','RequestOutputKind.FINAL_ONLY'}
        and front['output_token_ids']==choice['token_ids']==native['output_token_ids']and front['text']==choice['text']
        and front['finish_reason']==front['input_finish_reason']==choice['finish_reason']==engine['finish_reason']==replay['finish_reason']
        and front['stop_reason']==front['input_stop_reason']==choice.get('stop_reason')==engine['stop_reason']==replay['stop_reason'],
        'actual full native tokens/front text/HTTP finish, no frontend stop override or retokenization')
    accepted=update['returned_token_ids'];raw=update['proposed_token_ids'];n=update['before_output_count']
    C.need(update['stopped']is True and accepted and accepted==raw[:len(accepted)]==update['native_list_after']
        and n+len(accepted)==len(native['output_token_ids'])and native['output_token_ids'][n:]==accepted==engine['new_token_ids'],
        'original native append/check_stop trims actual speculative tail before EngineCoreOutput')
    oid=native['object_id']
    for e in(update,kv,blocks,free):C.need(e['request_id']==rid and e['object_id']==oid,'same actual strong native terminal request object')
    C.need(kv['original_returned_None']is True and blocks['present_before']is True and blocks['present_after']is False
        and free['finished_req_id_after']is True and free['request_present_after']is False,'actual original KV.free call, scheduler deletion and finished IDs')
    ranks=[]
    for w in worker_rows:
        C.need(w['request_id']==rid and rid in w['scheduler_finished_req_ids']and w['present_before']is True
            and type(w['object_id'])is int and w['prompt_token_ids']==body['prompt']and w['present_after']is False and w['batch_present_after']is False,
            'actual current native runner state observed then removed by original worker finished-ID update')
        ranks.append(w['rank'])
    C.need((sorted(ranks)==[0,1,2,3])if require_workers else(len(set(ranks))==len(ranks)and set(ranks)<={0,1,2,3}),'all required actual TP worker retirements')
    usage=b['usage'];expected=dict(prompt_tokens=len(body['prompt']),completion_tokens=len(native['output_token_ids']),total_tokens=len(body['prompt'])+len(native['output_token_ids']))
    C.need(all(type(usage[k])is int and usage[k]==v for k,v in expected.items()),'actual full prompt/output usage')
    return dict(request_id=rid,frontend_completion_id=b['id'],client_request_id=request['request_id'],**replay,
        full_token_ids_sha256=C.digest(native['output_token_ids']),all4_worker_retired=(sorted(ranks)==[0,1,2,3]),allocator_internal_reuse_proven=False)


def owner_join(source_ref,m,client_ref,journals_ref,binding_ref,model_owner_ref):
    o=C.obj(model_owner_ref);b=C.obj(binding_ref)
    C.need(o['schema']=='bole.actual-task-runtime-owned/v1'and o['task_normalEOS_smoke_source_ref']==source_ref
        and o['primary']is None and o['secondary']==[]and o['source_input_before']==o['source_input_after']
        and o['private_namespace_restored_by_identity']is True,'actual finished source-stable model owner with completed inverse')
    summary=o['summary'];C.need(set(summary)=={'client_ref','journals_ref','process_binding_ref','model_owned_ref','model_release_ref'}
        and summary['client_ref']==client_ref and summary['journals_ref']==journals_ref and summary['process_binding_ref']==binding_ref
        and summary['model_owned_ref']==b['owned_ref'],'same actual model owner/client/journals/live collector/owned identity')
    e,x=C.owned_inspect(b['owned_ref'],b['owned_inspect_ref']);C.need(e['source']==o['source_ref']and x['State']['Running']is True
        and x['State']['Pid']==b['init_host_pid']and b['collector_ref']==m['files']['bind_processes.py'],'earlier actual live six-process binding under this exact model owner')
    model_source=C.obj(o['source_ref']);C.need(model_source['task_normalEOS_smoke_source_ref']==source_ref,'same actual model source smoke binding')
    release=C.obj(summary['model_release_ref']);C.need(release['stopped']is True and release['retained']is True and release['errors']==[],
        'complete exact-owned model stop-retain before separate Devices[] reader')
    G=C.ref(C.checked(b['G1_source_ref']));C.need((G['bytes'],G['sha256'])==(109479,'010914ebe1bf5d3e6b516103e1a376e24e0a0d965ac0a3a42d7aeb19fca57677'),'actual qualified original namespace helper basis')
    C.need(b['namespace_helper_ref']==C.obj(b['G1_source_ref'])['files']['frontend_namespace131r18.py'],'exact original full namespace loaded interpreter collector')
    C.checked(b['namespace_helper_ref']);return o


def run(source_ref,client_ref,journals_ref,binding_ref,model_owner_ref):
    m=C.source(source_ref);plan,planned=C.plan(m['plan_ref']);C.CPU_proof(m['CPU_owner_ref'],plan['source_ref'])
    client=C.obj(client_ref);C.need(client['schema']=='bole.actual-task-normalEOS-smoke-client/v1'and client['source_ref']==source_ref
        and client['primary']is None and client['completed_task_requests']==6 and client['barrier']is not None,'all actual six HTTP requests plus final native retirement barrier complete')
    catalog=C.obj(client['catalog_ref']);C.need(catalog['source_ref']==source_ref and catalog['plan_ref']==m['plan_ref']and len(catalog['entries'])==7,'same pre-request durable complete catalog')
    inv=C.obj(journals_ref);C.need(inv['source_ref']==source_ref and set(inv['journals'])==set(ROLES),'complete six-role explicit evidence')
    decoded={role:journal(inv['journals'][role],source_ref,role)for role in ROLES}
    owner_join(source_ref,m,client_ref,journals_ref,binding_ref,model_owner_ref)
    binding=C.obj(binding_ref);C.need(binding['schema']=='bole.actual-task-normalEOS-process-bindings/v1'and binding['source_ref']==source_ref
        and binding['journals_ref']==journals_ref and binding['actual_live_six_roles_same_owned_container']is True,'actual live same-owned six-process host namespace collection')
    bound={v['role']:v for v in binding['processes']};C.need(set(bound)==set(ROLES),'all actual bound roles')
    actual=[]
    for role,(header,rows)in decoded.items():
        v=bound[role];C.need(v['journal_ref']==inv['journals'][role]and v['header']==header['process']and header['native_sources']==m['native_sources']
            and v['host_start_ticks']==header['process']['start_ticks']and v['NSpid'][-1]==header['process']['pid'],'source-bound actual process lifetime/namespace journal join')
        actual.append((v['host_pid'],v['host_start_ticks']))
    C.need(len(set(actual))==6,'six distinct actual source-bound processes')
    sched=decoded['scheduler'][1]
    sinstall=[p for _,p in events(sched,'installed')];C.need(len(sinstall)==1 and sinstall[0]['max_model_len']>=5199 and sinstall[0]['max_num_seqs']==1
        and sinstall[0]['async_scheduling']is False and sinstall[0]['TP']==4 and sinstall[0]['PP']==sinstall[0]['DP']==1,'actual bounded sync scheduler/config topology')
    front=unique_request(decoded['frontend'][1],'frontend_output')
    maps={k:unique_request(sched,k)for k in('check_stop','terminal_update','kv_free','free_blocks','free_request','engine_output')}
    C.need(all(len(v)==7 for v in maps.values())and len(front)==7,'all seven exact native terminals; no dropped/extra request')
    workers=[unique_request(decoded['worker'+str(n)][1],'worker_retired')for n in range(4)]
    generation=C.obj(m['generation_config_ref']);raw=C.obj(client['raw_ref']);records=raw['records'];C.need(len(records)==6 and raw['phase']=='smoke'and raw['arm']==plan['arm'],'six exact raw task records/same arm')
    result=[];nativeids=[]
    for n,(entry,record)in enumerate(zip(catalog['entries'],[*records,client['barrier']['record']])):
        request=C.obj(entry['request_ref']);response=C.obj(record['response_ref']);C.need(record['request_ref']==entry['request_ref']and record['task']==entry['task']and record['id']==entry['id'],'actual raw request catalog identity')
        if n<6:C.need((entry['task'],entry['id'])==C.SMOKE[n]and request['body']==planned[n]['body']and entry['frozen_row_sha256']==planned[n]['frozen_row_sha256'],'same full frozen task input/body')
        else:C.need(request['body']==dict(planned[0]['body'],max_tokens=1,ignore_eos=True),'separate same-input native one-token barrier')
        wire=C.obj(C.ref(C.checked(entry['request_ref']).parent/'HTTP_WIRE.json'));wirebody=C.parse(C.checked(wire['raw_body_ref']).read_bytes())
        C.need(wire['request_ref']==entry['request_ref']and wire['status']==response['status']==200 and wirebody==response['body'],'actual raw HTTP byte envelope exactly matches normalized response')
        matches=[rid for rid,(_,f)in front.items()if f['external_req_id']==response['body']['id']+'-0'];C.need(len(matches)==1,'unique actual frontend mapping for HTTP completion')
        rid=matches[0];nativeids.append(rid);order=[maps[k][rid][0]for k in maps]
        C.need(order==sorted(order)and len(set(order))==len(order),'actual native stop/trim/KVfree/requestdelete/engine output order')
        wrows=[]
        for rank,wm in enumerate(workers):
            if n==6 and rid not in wm:continue
            C.need(rid in wm,'actual last real task retired after barrier');wrows.append(wm[rid][1])
        checked=validate_one(request,response,front[rid][1],*(maps[k][rid][1]for k in maps),wrows,generation,require_workers=n<6)
        if n==6:checked['barrier_excluded_from_tasks']=True;checked['barrier_own_retirement_required']=False
        result.append(checked)
    C.need(len(set(nativeids))==7,'all native requests distinct')
    for role,w in enumerate(workers):
        C.need(set(nativeids[:6])<=set(w)<=set(nativeids),'worker evidence covers exactly all real tasks and optional final barrier')
        installed=[p for _,p in events(decoded['worker'+str(role)][1],'installed')];C.need(len(installed)==1 and installed[0]['rank']==role
            and installed[0]['TP']==4 and installed[0]['PP']==installed[0]['DP']==1,'actual native TP4 rank topology')
    # Actual independent CPU decoding from unchanged frozen scorer. No task code runs.
    tm=C.obj(plan['source_ref']);sys.path.insert(0,tm['root'])
    S=C.load(tm['files']['score_tokens.py'],'_task_http_exact_frozen_component_scorer')
    grades=S.replay(plan['source_ref'],client['raw_ref'],full_provenance=False)
    return dict(schema='bole.independent-task-normalEOS-smoke-lifecycle/v1',source_ref=source_ref,client_ref=client_ref,journals_ref=journals_ref,
        process_binding_ref=binding_ref,model_owner_ref=model_owner_ref,rows=result,task_count=6,native_normal_EOS_policy_and_finish_join_accepted=True,
        all4_native_worker_retirement_accepted=True,actual_independent_token_decoding_verified=True,component_grades=grades,
        finish_cause_counts={cause:sum(r['cause']==cause for r in result[:6])for cause in('primary-EOS','checkpoint-secondary-EOS','output-budget')},
        all_six_tasks_completed_by_EOS=all(r['cause']in{'primary-EOS','checkpoint-secondary-EOS'}for r in result[:6]),
        scope='six frozen smoke cases only; output-budget terminal means max2048 truncation',
        barrier_excluded_from_task_cohort=True,barrier_own_retirement_required=False,allocator_internal_reuse_proven=False,
        HumanEval_model_code_executed=False,BOLE_activation_accepted=False,all3_task_accuracy_accepted=False,
        formal_task_accuracy_accepted=False,model_ready=False,performance_ready=False)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);g=p.add_mutually_exclusive_group();g.add_argument('--execute',action='store_true');g.add_argument('--inventory',action='store_true')
    for n in('source-ref','client-ref','journals-ref','process-binding-ref','model-owner-ref'):p.add_argument('--'+n)
    p.add_argument('--journal-root',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    if not(a.execute or a.inventory):print('{"enabled":false,"HTTP_executed":false,"model_ready":false}');return 0
    C.need(a.source_ref and a.output,'exact source/output')
    sr=C.parse(a.source_ref)
    if a.inventory:C.need(a.journal_root,'explicit owned journal root');r=inventory(sr,a.journal_root,a.output)
    else:
        C.need(a.client_ref and a.journals_ref and a.process_binding_ref and a.model_owner_ref,'actual client/journal/live host-binding refs')
        r=C.write(a.output,run(sr,C.parse(a.client_ref),C.parse(a.journals_ref),C.parse(a.process_binding_ref),C.parse(a.model_owner_ref)))
    print(json.dumps(dict(result_ref=r,model_ready=False)));return 0


if __name__=='__main__':raise SystemExit(main())
