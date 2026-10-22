"""Source-bound adapter for existing fixed1024 token-receive observer and reader."""
from dataclasses import asdict
import hashlib
import json
import time
import uuid
from pathlib import Path
from urllib.request import Request,urlopen
IDENTITY_PROTOCOL='actual-source-arm-client-output-nonce-label/v1'
def identity_header(C,m,source_ref,root,label,nonce):
    C.need(C.ref(__file__)==m['files']['strict_token_timing.py'] and C.obj(source_ref)==m,
        'actual own timing source and manifest, not guessed trial metadata')
    C.need(m['request_identity_protocol']==IDENTITY_PROTOCOL and m['performance_arm']in ('native_ar','bole')
        and label in ('warmup','measured','retirement-barrier') and root.is_absolute(),
        'explicit source/arm/owned-output/role identity')
    C.need(type(nonce)is str and len(nonce)==32 and all(x in '0123456789abcdef'for x in nonce),'actual per-request nonce')
    value=dict(source_ref=source_ref,arm=m['performance_arm'],client_output=str(root),label=label,nonce=nonce)
    scope=hashlib.sha256(C.canonical({k:v for k,v in value.items()if k not in ('nonce','label')})).hexdigest()[:16]
    return 'bole-perf-131-'+m['performance_arm']+'-'+scope+'-'+nonce+'-'+label,value
def request_identity(C,m,source_ref,root,label):
    return identity_header(C,m,source_ref,root,label,uuid.uuid4().hex)
def validate_identity(C,m,row,source_ref,root):
    identity=row['request_identity']
    expected,value=identity_header(C,m,source_ref,root,row['label'],identity['nonce'])
    C.need(identity==value and row['header']==expected and row['id']=='cmpl-'+expected,
        'source/actual owned-output/arm/role/nonce and HTTP completion identity join')
    return value
def modules(C,m):
    for n in ('strict_token_timing.py','formal_token_client.py','formal_token_reader.py','formal_token_evidence.py'):
        C.checked(m['files'][n])
    C.need(C.ref(__file__)==m['files']['strict_token_timing.py'],'exact current timing adapter source')
    C.load(m['files']['formal_token_evidence.py'],'formal_token_evidence')
    obs=C.load(m['files']['formal_token_client.py'],'_formal_token_client')
    reader=C.load(m['files']['formal_token_reader.py'],'_formal_token_reader')
    return obs,reader
def request(C,m,donor,args,ids,index,label,root,source_ref,transport=None,records=None,clock=time.monotonic_ns):
    obs,reader=modules(C,m)
    C.need(m['performance_arm']in ('native_ar','bole') and m['performance_profile']['scope']['output_tokens']==1024,'exact unqualified fixed1024 arm')
    C.need(label in ('warmup','measured') and root.is_absolute() and root.is_dir(),'same owned existing client output')
    leaf=root/('TOKEN-WIRE-'+label);C.need(not leaf.exists(),'new exclusive timing leaf');leaf.mkdir(mode=0o700)
    header,identity=request_identity(C,m,source_ref,root,label);body=obs.fixed_request(ids)
    C.need(body['seed']==0 and body['ignore_eos']is True and body['max_tokens']==1024,'common exact original deterministic generation')
    record=dict(label=label,header=header,request_identity=identity,request=body,token_ids=[],done=False,wire_bytes=0)
    if records is not None:records.append(record)
    wire=Request(args.base_url+'/v1/completions',data=json.dumps(body).encode(),
        headers={'Content-Type':'application/json','X-Request-Id':header},method='POST')
    transport=urlopen if transport is None else transport
    start=clock() # Immediately before actual owner-provided transport/POST.
    with transport(wire,timeout=args.timeout)as response:
        trace_ref=obs.observe_response(response,leaf,request_start_ns=start,
            request_id='cmpl-'+header,input_ids=ids,clock=clock)
    actual=reader.read_observation(trace_ref)
    C.need(actual['request']==body and actual['request_id']=='cmpl-'+header and len(actual['ordered_token_ids'])==1024,'full raw independent token replay and request join')
    tokens=actual['ordered_token_ids']
    # Legacy hash is explicitly token-ID scoped, not a claim about decoded text.
    result=donor.RequestResult(index=index,ok=True,ttft_ms=actual['TTFT_ns']/1e6,
        duration_s=actual['T_total_ns']/1e9,output_tokens=1024,
        output_sha256=hashlib.sha256(C.canonical(tokens)).hexdigest(),
        requested_output_tokens=1024,finish_reason='length')
    record.update(status=200,id=actual['request_id'],done=True,token_ids=tokens,
        usage=dict(prompt_tokens=131,completion_tokens=1024,total_tokens=1155),
        wire_bytes=actual['raw']['bytes'],timing=asdict(result),fixed1024_trace_ref=trace_ref,
        output_sha256_scope='ordered-token-IDs',timing_scope='pre-POST to actual first/last generated-ID receipt',
        timing_qualification=False,formal_performance=False)
    return result,record
def consume(C,m,row,*,source_ref,client_output):
    validate_identity(C,m,row,source_ref,client_output)
    _,reader=modules(C,m);actual=reader.read_observation(row['fixed1024_trace_ref'])
    C.need(actual['ordered_token_ids']==row['token_ids'] and actual['request']==row['request']
        and actual['request_id']==row['id'] and len(row['token_ids'])==1024,'independent whole raw/token/request equality')
    C.need(row['timing']['ttft_ms']==actual['TTFT_ns']/1e6
        and row['timing']['duration_s']==actual['T_total_ns']/1e9
        and row['timing']['output_tokens']==1024,'legacy reporting fields exactly use actual receive metrics')
    return dict(trace_ref=row['fixed1024_trace_ref'],TTFT_ns=actual['TTFT_ns'],
        TPOT_numerator_ns=actual['TPOT_numerator_ns'],TPOT_denominator=1023,
        T_total_ns=actual['T_total_ns'],output_tokens=1024,
        throughput_tokens_per_second=1024*1e9/actual['T_total_ns'],formal_performance=False)
