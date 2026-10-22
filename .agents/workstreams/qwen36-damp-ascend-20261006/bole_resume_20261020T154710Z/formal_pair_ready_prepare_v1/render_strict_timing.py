"""Reversible source-only timing transplant into existing two-arm owner. No dispatch."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
W=P.parent
ORIGINAL=W/'fixed1024_sse_timing_client_v1'
def need(v,m):
 if not v:raise ValueError(m)
def once(t,a,b):
 need(t.count(a)==1,'one original source fragment '+a);return t.replace(a,b,1)
def original(name,sha):
 raw=(ORIGINAL/name).read_bytes();need(hashlib.sha256(raw).hexdigest()==sha,'exact prior observer source');return raw.decode()
def ref(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def render(base=P,permit_materialized=False):
    prior=W/'performance_followup_prepare_20261022T203100Z'
    sys.path.insert(0,str(prior))
    spec=importlib.util.spec_from_file_location('_actual_paired_prepare',prior/'paired_prepare.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    bundle=module.render_pair(base_root=base,permit_materialized=permit_materialized)
    observer=original('fixed1024_client.py','0639cbe6e00a4c54eab3f9afe4886b47fbcc10737756b4fcbe46e57ae389dbf8')
    reader=original('independent_reader.py','9ffba3df8c2417e2249f368ebe7573f093e6a45f62e5bcefc1186259f08f273c')
    evidence=original('evidence.py','9fc7ec4a4737c1edd386b6e7926367d1a12b2b35ed237faad1005a972caa7ab4')
    observer=once(observer,'from evidence import','from formal_token_evidence import')
    reader=once(reader,'from evidence import','from formal_token_evidence import')
    for name,t in [('observer',observer),('reader',reader)]:
        t=once(t,'temperature=0,top_p=1,n=1,stream=True','temperature=0,top_p=1,seed=0,n=1,stream=True')
        if name=='observer':observer=t
        else:reader=t
    additions={'formal_token_client.py':observer.encode(),'formal_token_reader.py':reader.encode(),
        'formal_token_evidence.py':evidence.encode(),'strict_token_timing.py':(P/'strict_token_timing.py').read_bytes()}
    for arm,part in bundle['arms'].items():
        m=part['manifest'];files=part['files'];before=copy.deepcopy(files)
        t=files['performance_service_client.py'].decode()
        t=once(t,'def request(donor, args, ids, index, count, label, transport=None, records=None):',
         'def request(donor, args, ids, index, count, label, transport=None, records=None, capture_root=None, manifest=None, source_ref=None):')
        t=once(t,'    from urllib.request import Request, urlopen',
         "    import strict_token_timing as T\n    C.need(capture_root is not None and manifest is not None and source_ref is not None, 'source-bound strict timing inputs')\n    if count == 1024:\n        return T.request(C,manifest,donor,args,ids,index,label,capture_root,source_ref,transport,records)\n    from urllib.request import Request, urlopen")
        t=once(t,"    header = 'bole-perf-131-' + label","    header, request_identity = T.request_identity(C,manifest,source_ref,capture_root,label)")
        t=once(t,"record = dict(label=label, header=header, token_ids=[]","record = dict(label=label, header=header, request_identity=request_identity, token_ids=[]")
        for call in ["'warmup',transport,rows)","'measured',transport,rows)","'retirement-barrier',transport,rows)"]:
            t=once(t,call,call[:-1]+',capture_root=root,manifest=m,source_ref=sr)')
        t=once(t,"ttft_scope='donor first nonempty text chunk'","ttft_scope='actual first generated-ID receive minus pre-POST'")
        t=once(t,"tpot_scope='donor request-final duration minus TTFT divided by output_tokens-1'","tpot_scope='actual last minus first generated-ID receive divided by1023'")
        files['performance_service_client.py']=t.encode()
        t=files['performance_client_consumer.py'].decode()
        # Insert into final public consume, before legacy metadata return.
        marker="    result['all_observers_disabled']=False"
        t=once(t,marker,"    import strict_token_timing as T\n    wire=C.obj(C.ref(client_output/'HTTP_RESULT.json'))\n    for row in wire['rows']:T.validate_identity(C,manifest,row,source,client_output)\n    result['actual_token_receive_metrics']=[T.consume(C,manifest,row,source_ref=source,client_output=client_output) for row in wire['rows'][:2]]\n"+marker)
        files['performance_client_consumer.py']=t.encode()
        files.update(additions)
        m['common_collective_configuration']=dict(schema='bole.common-collective-configuration/v1',hccl_deterministic='true',applies_to=['native_ar','bole'])
        m['strict_token_timing_profile']=dict(schema='bole.actual-token-receive-timing/v1',enabled=True,
            output_tokens=1024,first_token_can_have_empty_text=True,tail_usage_DONE_excluded=True)
        m['request_identity_protocol']='actual-source-arm-client-output-nonce-label/v1'
        m['files']={n:ref(Path(m['root'])/n,raw)for n,raw in sorted(files.items())}
        oldrefs={json.dumps(ref(Path(m['root'])/n,raw),sort_keys=True):n for n,raw in before.items()}
        def rebind(value):
            if type(value)is dict and set(value)=={'path','bytes','sha256'}:
                name=oldrefs.get(json.dumps(value,sort_keys=True))
                if name is not None:return m['files'][name]
            if type(value)is dict:return {k:rebind(v)for k,v in value.items()}
            if type(value)is list:return [rebind(v)for v in value]
            return value
        m=rebind(m);part['manifest']=m
        need(m['performance_streaming_client']==m['files']['performance_service_client.py']
             and m['performance_streaming_client']in m['dependencies'],'exact rebased actual client alias/dependency')
        m['pending_runtime_validator']=True
        m['workload_acceptance_ref']=None
        m['workload_acceptance_pending']=True
        m['performance_input_scope']='current131-token prototype only; not2k/16k or general workload acceptance'
        m['performance_ready']=False;m['numerical_qualified']=False
        part['strict_timing_inverse']={n:dict(before=ref(Path(m['root'])/n,before[n])if n in before else None,after=m['files'][n])for n in files if n not in before or files[n]!=before[n]}
        restored=dict(files)
        for n in part['strict_timing_inverse']:
            if n in before:restored[n]=before[n]
            else:restored.pop(n)
        need(restored==before,'whole exact timing-only inverse to prior paired owner')
        for n,raw in files.items():
            if n.endswith('.py'):compile(raw,n,'exec')
    bundle.update(source_bound=False,performance_ready=False,formal_performance=False,
        pending=['current FAST numerical gate','source validator/admission transplant','current explicit authority','actual worker loaded closure','raw-SSE owner/cleanup binding'])
    return bundle
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--review',action='store_true');p.add_argument('--prepare',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
 if a.prepare:
  need(a.output and a.output.is_absolute()and a.output.parent==P and not a.output.exists(),'new source-only direct child; never overwrite')
  b=render(a.output);a.output.mkdir(mode=0o700);manifests={}
  for arm,part in b['arms'].items():
   root=Path(part['manifest']['root']);root.mkdir(mode=0o700)
   for n,raw in part['files'].items():
    path=root/n;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb')as f:f.write(raw)
   manifests[arm]=dict(manifest=part['manifest'],strict_timing_inverse=part['strict_timing_inverse'])
  value=dict(schema='bole.strict-token-timing-source-preparation/v1',arms=manifests,
   source_bound=False,performance_ready=False,numerical_qualified=False,authority_ref=None,
   HTTP=False,NPU=False,pending=b['pending'])
  path=a.output/'PREPARED_PAIR.json'
  with path.open('xb')as f:f.write(json.dumps(value,sort_keys=True,allow_nan=False).encode()+b'\n')
  print(json.dumps(ref(path,path.read_bytes())))
 elif not a.review:print('{"enabled":false,"HTTP":false,"NPU":false,"formal_performance":false}')
 else:
  b=render();print(json.dumps({arm:dict(root=x['manifest']['root'],inverse=x['strict_timing_inverse'],performance_ready=False)for arm,x in b['arms'].items()}))
