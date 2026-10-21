"""Finite sequential loopback smoke recorder. No retries, model imports or scoring."""
import argparse
import json
import os
import signal
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import http_common as C


def endpoint(url):
    x=urllib.parse.urlsplit(url)
    C.need(x.scheme=='http'and x.hostname in{'127.0.0.1','::1'}and x.port is not None and 1<=x.port<=65535
           and x.path=='/v1/completions'and not x.query and not x.fragment and not x.username and not x.password,
           'explicit literal loopback completions endpoint only')
    return url


def wire(body,request_id,url,seconds):
    data=C.canonical(body);req=urllib.request.Request(endpoint(url),data=data,method='POST',
        headers={'Content-Type':'application/json','X-Request-Id':request_id})
    # Explicitly disable proxies and redirects; no alternate service/destination.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    start=time.monotonic();old_handler=signal.getsignal(signal.SIGALRM)
    C.need(signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0),'fresh finite client owns no preexisting alarm')
    def expired(signum,frame):raise TimeoutError('whole HTTP operation deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,seconds)
    try:
        try:r=opener.open(req,timeout=seconds)
        except urllib.error.HTTPError as e:r=e
        with r:
            raw=r.read(8*2**20+1);C.need(len(raw)<=8*2**20,'bounded complete raw HTTP body')
            status=r.status;headers=list(r.headers.items())
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old_handler)
    return dict(status=status,headers=headers,raw_body=raw,elapsed_seconds=time.monotonic()-start)


def validate_response(body,response):
    C.need(response['status']==200,'actual HTTP200 without retry')
    b=C.parse(response['raw_body']);choices=b['choices']
    C.need(b['model']==body['model']and type(b['id'])is str and b['id']and len(choices)==1 and choices[0]['index']==0,'one actual same-model completion')
    c=choices[0];ids=c['token_ids'];u=b['usage']
    C.need(type(ids)is list and 0<len(ids)<=body['max_tokens']and all(type(t)is int and 0<=t<248320 for t in ids)
           and type(c['text'])is str and c['finish_reason']in{'stop','length'},'complete actual token IDs/text/terminal reason')
    C.need(u['prompt_tokens']==len(body['prompt'])and u['completion_tokens']==len(ids)and u['total_tokens']==len(body['prompt'])+len(ids)
           and all(type(u[k])is int for k in('prompt_tokens','completion_tokens','total_tokens')),'exact full prompt/output usage')
    C.need(c['finish_reason']!='length'or len(ids)==body['max_tokens'],'length only at full output budget')
    return b


def execute(source_ref,url,out):
    m=C.source(source_ref,seconds=1800);plan,rows=C.plan(m['plan_ref']);C.CPU_proof(m['CPU_owner_ref'],plan['source_ref'])
    C.need(os.environ.get('BOLE_TASK_HTTP_MAIN_ENABLE')=='1','MAIN explicit actual-model smoke opt-in')
    endpoint(url);C.need(out.is_absolute()and out.parent.is_dir()and not out.exists(),'new retained raw output leaf');out.mkdir(mode=0o700)
    start=time.monotonic();records=[];barrier=None;fault=None;raw_bytes=0;nonce=uuid.uuid4().hex
    catalog=[]
    bodies=[(r['task'],r['id'],r['body'],r['frozen_row_sha256'])for r in rows]
    b=dict(rows[0]['body'],max_tokens=1,ignore_eos=True)
    bodies.append(('retirement-barrier','native-1-token',b,None))
    for n,(task,id,body,rowsha)in enumerate(bodies):
        rid='bole-task-smoke-'+nonce+'-'+str(n);leaf=out/('%02d'%n);leaf.mkdir(mode=0o700)
        request=C.write(leaf/'REQUEST.json',dict(request_id=rid,body=body))
        catalog.append(dict(task=task,id=id,request_ref=request,frozen_row_sha256=rowsha))
    catalog_ref=C.write(out/'CATALOG.json',dict(schema='bole.task-normalEOS-smoke-catalog/v1',source_ref=source_ref,plan_ref=m['plan_ref'],entries=catalog))
    # Catalog is durable before the first request. Failed/incomplete output is retained.
    try:
        for n,entry in enumerate(catalog):
            remaining=1800-(time.monotonic()-start);C.need(remaining>0,'finite whole smoke budget')
            request=C.obj(entry['request_ref']);leaf=out/('%02d'%n)
            r=wire(request['body'],request['request_id'],url,min(300,remaining));raw_bytes+=len(r['raw_body'])
            C.need(raw_bytes<=m['raw_limit_bytes'],'whole retained raw HTTP cap')
            raw=leaf/'HTTP_BODY.raw'
            with raw.open('xb')as f:f.write(r['raw_body']);f.flush();os.fsync(f.fileno())
            receipt=C.write(leaf/'HTTP_WIRE.json',dict(request_ref=entry['request_ref'],status=r['status'],headers=r['headers'],raw_body_ref=C.ref(raw),
                elapsed_seconds=r['elapsed_seconds'],client_request_id=request['request_id']))
            body=validate_response(request['body'],r)
            response=C.write(leaf/'RESPONSE.json',dict(request_id=request['request_id'],status=r['status'],body=body))
            row=dict(task=entry['task'],id=entry['id'],request_ref=entry['request_ref'],response_ref=response)
            if n<6:records.append(row)
            else:barrier=dict(record=row,wire_ref=receipt)
        raw_ref=C.write(out/'RAW_TASK_COMPLETIONS.json',dict(schema='bole.actual-three-task-HTTP-completions/v1',source_ref=plan['source_ref'],
            effective_inputs_ref=plan['effective_inputs_ref'],phase='smoke',arm=plan['arm'],model=plan['model'],records=records))
    except BaseException as e:
        fault=dict(error=repr(e));C.write(out/'FIRST-FAULT.json',fault);raw_ref=None
    C.authority(m['authority_ref'])
    result=C.write(out/'CLIENT-TERMINAL.json',dict(schema='bole.actual-task-normalEOS-smoke-client/v1',source_ref=source_ref,catalog_ref=catalog_ref,
        raw_ref=raw_ref,barrier=barrier,primary=fault,completed_task_requests=len(records),raw_body_bytes=raw_bytes,
        elapsed_seconds=time.monotonic()-start,HTTP_executed=True,task_score_produced=False,normal_EOS_cause_proven=False,
        worker_lifecycle_proven=False,BOLE_activation_proven=False,model_ready=False,formal_accuracy_accepted=False,performance_ready=False))
    C.need(fault is None,'actual finite client failed; retained '+str(result));return result


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--url');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"HTTP_executed":false}');return 0
    C.need(a.source_ref and a.url and a.output,'explicit actual source/loopback/output')
    print(json.dumps(dict(result_ref=execute(C.parse(a.source_ref),a.url,a.output),model_ready=False)));return 0


if __name__=='__main__':raise SystemExit(main())
