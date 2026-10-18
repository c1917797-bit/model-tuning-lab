"""Independent Devices[] consumer; original R36 model/payload identities stay.

Only geometry control accounting changes. This file imports no owner or native
runtime and obtains source-bound modules only after verifying their manifests.
The owner entry remains responsible for admission, read-only mounts and leases.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys

REPAIR_SCOPE = 'geometry-control-accounting-only'
ORIGINAL_CONSUME_SHA = '6725eca40dc08cef07b6e1c7255f9d72abc30ab889d8463667f798a95bb7d6c7'
ORIGINAL_CLI_SHA = '6d7f232c3bb386fe6ec9ca9283c484720d5d2fbccf08856e38df33817151c4fc'
Q = None


def _need(value, reason):
    if not value:
        raise ValueError(reason)


def _bootstrap_checked(ref):
    """Verify full ordinary immutable source bytes before importing helpers."""
    _need(type(ref) is dict and set(ref) == {'path', 'bytes', 'sha256'}, 'consumer exact Ref3')
    path = Path(ref['path'])
    _need(path.is_absolute() and '..' not in path.parts
          and str(path) == ref['path'] and type(ref['bytes']) is int
          and 0 < ref['bytes'] <= 16 * 1024**2
          and all(not p.is_symlink() for p in (path, *path.parents)),
          'consumer bounded ordinary source path')
    before = path.stat()
    _need(stat.S_ISREG(before.st_mode), 'consumer regular source file')
    with path.open('rb') as stream:
        raw = stream.read(ref['bytes'] + 1)
        opened = os.fstat(stream.fileno())
    after = path.stat()
    key = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    _need(key(before) == key(opened) == key(after)
          and len(raw) == ref['bytes']
          and hashlib.sha256(raw).hexdigest() == ref['sha256'],
          'consumer whole stable source Ref')
    return path, raw


def _json(raw):
    def pairs(items):
        value = {}
        for k, v in items:
            _need(k not in value, 'consumer no duplicate JSON keys')
            value[k] = v
        return value
    def constant(value):
        raise ValueError('consumer no nonfinite JSON constant ' + value)
    return json.loads(raw.decode('utf8'), object_pairs_hook=pairs, parse_constant=constant)


def _load_source(ref, name):
    path, _ = _bootstrap_checked(ref)
    old = sys.modules.get(name)
    if old is not None:
        _need(Path(old.__file__).resolve() == path,
              'consumer no ambient module for ' + name)
        return old
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[name]
        raise
    return module


def consumer_modules(consumer_sr, model_sr, payload_sr):
    global Q
    source_path, raw = _bootstrap_checked(consumer_sr)
    consumer = _json(raw)
    _need(consumer['schema'] == 'deltalog.geometry-consumer-source/v1'
          and consumer['default_enabled'] is False and consumer['prepared_only'] is False
          and consumer['model_source'] == model_sr and consumer['payload_source'] == payload_sr,
          'consumer separate immutable source with unchanged actual model and payload')
    root = Path(consumer['root'])
    _need(root.is_absolute() and '..' not in root.parts and source_path.parent == root,
          'consumer immutable source root')
    files = consumer['files']
    _need({'consumer_cli.py', 'consume_rank_new.py', 'geometry_witness.py'} <= set(files),
          'consumer complete repair source closure')
    for name, ref in files.items():
        path, _ = _bootstrap_checked(ref)
        _need(path == root / name and '..' not in Path(name).parts,
              'consumer exact source-owned file')
    _need(Path(files['consumer_cli.py']['path']) == Path(__file__).resolve(),
          'consumer executing exact source-owned CLI')
    geometry = _load_source(files['geometry_witness.py'], 'geometry_witness')
    _, payload_bytes = _bootstrap_checked(payload_sr)
    payload = _json(payload_bytes)
    _need(payload['files']['firstdecode_consume.py']['sha256'] == ORIGINAL_CONSUME_SHA
          and payload['files']['firstdecode_cli.py']['sha256'] == ORIGINAL_CLI_SHA,
          'consumer exact frozen predecessor numerical and CLI source lineage')
    Q = _load_source(payload['files']['firstdecode_gate.py'], '_geometry_consumer_original_gate')
    consume_module = _load_source(files['consume_rank_new.py'], '_geometry_consumer_rank')
    return consumer, geometry, consume_module.consume_rank


class AliasIO:
    """Preserve original Ref and authenticate actual longest exact RW alias."""
    def __init__(self,inspect,budget,torch):
        self.t=torch
        Q.need(len(inspect['Mounts'])==len({x['Destination']for x in inspect['Mounts']})
            and sum(x['RW']is True for x in inspect['Mounts'])==3,'distinct actual mount destinations/exact three RW aliases')
        self.mounts={Path(x['Destination']):Path(x['Source']) for x in inspect['Mounts'] if x['RW']}
        stage=Path(budget['host_stage_root'])
        expected={stage:stage,Path(budget['guest_stage_root']):stage,Path(budget['guest_payload_root']):Path(budget['host_payload_root'])}
        Q.need(len(expected)==3 and self.mounts==expected,'exact original008 identity+alias control and sole nested payload RW; only two host write roots')
        self.joins=[]
    def actual_ref(self,r):
        p=Path(r['path']);Q.need('..'not in p.parts,'no parent traversal through an authenticated mount alias')
        choices=[(dst,src) for dst,src in self.mounts.items() if p==dst or dst in p.parents]
        if not choices:return r
        dst,src=max(choices,key=lambda x:len(x[0].parts));host=src/p.relative_to(dst)
        h=dict(r,path=str(host));self.joins.append(dict(original_guest_ref=r,actual_host_ref=h,exact_mount=dict(source=str(src),destination=str(dst))))
        return h
    def __call__(self,r,*,kind):
        guest=Path(r['path']);payload=Path('/adakv-results/model/capture')
        Q.need(payload in guest.parents,'owned model payload raw/baseline/comparison refs only')
        h=self.actual_ref(r);p=Q.checked(h)
        if kind=='streamed-bytes':return h
        if kind=='json':return json.loads(p.read_bytes())
        Q.need(kind=='torch','explicit closed raw kind');return self.t.load(p,map_location='cpu',weights_only=False)


def numerical_modules(payload):
    # Exact unchanged predecessor numerical-loader implementation.
    for r in Q.numerical_readset(payload):Q.checked(r)
    T=Q.load(payload['original_tensor_consumer'],'_firstdecode_original_tensor_consumer')
    R=T.module();Q.need(R.STATE_LIMIT==7.92e-7 and R.OUTPUT_LIMIT==.00303,'original unchanged numerical limits')
    for key in('direct_round','precast'):
        r=payload['original_'+key];old=sys.modules.get(key)
        Q.need(old is None or Path(old.__file__).resolve()==Q.checked(r),'no ambient numerical namespace')
        if old is None:Q.load(r,key)
    return T,R


def consume(consumer_sr,model_sr,payload_sr,owner_ref,inspect_ref,loaded_ref,reports_ref,geometry_refs_ref):
    consumer,G,consume_rank=consumer_modules(consumer_sr,model_sr,payload_sr)
    payload=Q.source(payload_sr);m=Q.obj(model_sr)
    # Preserve the old CLI's source-directory import path, after its full Ref
    # closure is authenticated; no unrelated or fixture directory is admitted.
    sys.path.insert(0,str(Q.checked(payload['files']['firstdecode_cli.py']).parent))
    Q.verify_tiny(payload)
    for r in m['files'].values():Q.checked(r)
    contract=m['firstdecode_contract'];Q.need(contract['payload_source']==payload_sr and contract['scope']=='C1-native2048-firstdecode','actual new model input/source linkage')
    parent=Q.obj(owner_ref);Q.need(parent['schema']=='deltalog.actual-owned-dispatch-smoke/v025' and parent['source']==model_sr
        and parent['status']=='failed' and parent['primary'] is not None and parent['secondary']==[]
        and parent['all_created_containers_release_verified'] is True,'original deliberate-stop parent failure retained, complete actual cleanup/source-after')
    root=Path(owner_ref['path']).parent;Q.need(root==Path(m['output_root']),'actual nonoverwritten original model owner root')
    x=Q.obj(inspect_ref)
    if type(x) is list:Q.need(len(x)==1,'one exact candidate inspect');x=x[0]
    Q.need(x['Image']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
        and x['State']['Running'] is False and x['State']['Pid']==0 and not x['State']['OOMKilled'] and not x.get('ExecIDs'),'fresh actual model CID released/noOOM/noExec')
    # DiagnosticStop normally makes the engine process nonzero. Do not rewrite
    # it to exit0 or borrow a successful unrelated process as the owner.
    Q.need(any(v['cid']==x['Id'] and v['exact_owned_release_verified'] is True for v in parent['owned_containers']),'same actual candidate CID original cleanup join')
    Q.need({(d['PathOnHost'],d['PathInContainer']) for d in x['HostConfig']['Devices']}=={*(('/dev/davinci'+str(i+4),'/dev/davinci'+str(i)) for i in range(4)),*((p,p) for p in('/dev/davinci_manager','/dev/devmm_svm','/dev/hisi_hdc'))},'actual only admitted4-7 to logical0-3')
    budget_ref=Q.ref(root/'candidate/FIRST-DECODE-BUDGET.json');budget=Q.validate_budget(Q.obj(budget_ref),model_sr,payload_sr,x['Id'])
    Q.need(budget['host_stage_root']==str(root/'candidate'),'actual control root source')
    loaded=Q.obj(loaded_ref);Q.need(Path(loaded_ref['path'])==root/'candidate/ALL4-LOADED.json' and loaded['source']==model_sr,'actual all4 worker binding before first HTTP')
    reports=Q.obj(reports_ref);Q.need(reports['schema']=='deltalog.firstdecode-all4-report-refs/v1' and reports['source']==model_sr and reports['payload_source']==payload_sr and len(reports['reports'])==4,'four actual report references, not a future plan')
    sidecar=G.strict_json(G.read_ordinary_ref(geometry_refs_ref,max_bytes=1024*1024))
    geometry=G.validate_geometry_sidecar(sidecar,consumer_sr,model_sr,payload_sr,reports_ref,reports['reports'],budget['host_payload_root'])
    import torch
    torch.set_num_threads(1)
    aio=AliasIO(x,budget,torch)
    # Original module's numerical AST and reference loaders remain source-bound.
    T,R=numerical_modules(payload)
    rank_results=[];seen=set();failures=[]
    for rr in reports['reports']:
        try:
            Q.need(Path(rr['path']).parent.parent==Path(budget['host_payload_root']) and Path(rr['path']).name=='FIRST-DECODE-REPORT.json','exact new payload worker report leaf')
            report=Q.obj(rr);rank=report['domain']['rank'];Q.need(rank not in seen and rank in range(4),'distinct actual report rank');seen.add(rank)
            row=next(b for b in loaded['rows'] if b['rank']==rank);p=row['actual_host_process']
            Q.need(report['domain']==dict(cid=x['Id'],host_pid=p['pid'],start_ticks=p['start_ticks'],physical=row['physical'],rank=rank)
                and report['namespace_pid']==row['namespace_pid'] and Path(rr['path']).parent.name=='FIRST-DECODE-'+str(row['namespace_pid']),'actual namespace/host PID/start/card/source binding')
            witness=geometry[rank]
            Q.need(witness['report_ref']==rr and witness['namespace_pid']==report['namespace_pid'],'geometry same exact immutable report and loaded worker')
            rank_results.append(consume_rank(torch,T,R,report,aio,model_sr,payload_sr,m['library_ref'],m['debug_library'],geometry_ref=witness['geometry_ref']))
        except BaseException as e:failures.append(dict(report=rr,primary=repr(e)))
    logs=reports['expected_stop_logs'];Q.need(logs,'actual retained stop logs are required, not a string field')
    stop_join=False
    for r in logs:
        h=aio.actual_ref(r);p=Q.checked(h);Q.need(p.stat().st_size<=64*1024**2,'bounded actual diagnostic log')
        text=p.read_text(encoding='utf8',errors='replace')
        stop_join |= 'DL_FIRST_DECODE_COMPLETE_OBSERVATION_NOT_MODEL_QUALIFICATION' in text and 'DiagnosticStop' in text and payload['files']['firstdecode.py']['path'] in text
    passed=seen=={0,1,2,3} and len(rank_results)==4 and not failures and all(r['all48_firstdecode_pass'] for r in rank_results)
    return dict(schema='deltalog.independent-all4-firstdecode/v1',consumer_source=consumer_sr,geometry_refs_ref=geometry_refs_ref,repair_scope=REPAIR_SCOPE,source=payload_sr,model_source=model_sr,parent_failed_owner=owner_ref,original_primary=parent['primary'],original_status_retained='failed',owner_success=False,final_inspect=inspect_ref,actual_budget=budget_ref,loaded=loaded_ref,reports=reports_ref,rank_results=rank_results,failures=failures,actual_single_decode_data_gates_pass=passed,expected_stop_causally_joined=bool(stop_join),diagnostic_complete=passed and stop_join,alias_joins=aio.joins,full_model_qualified=False,normalEOS_qualified=False,lifecycle_reuse_qualified=False,long160_qualified=False,performance_qualified=False,task_qualified=False)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    names=('consumer-source-ref','model-source-ref','payload-source-ref','owner-ref','inspect-ref','loaded-ref','reports-ref','geometry-refs-ref')
    for name in names:p.add_argument('--'+name)
    p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    _need(all(getattr(a,n.replace('-','_')) for n in names) and a.output is not None,'consumer complete explicit Ref arguments')
    args=[json.loads(getattr(a,n.replace('-','_'))) for n in names]
    value=consume(*args)
    # Normal admitted execution uses the source-owned guarded host entry.
    # Standalone CLI has no authority to open an arbitrary output file.
    _need(a.output==Path('/adakv-results/FIRST-DECODE-INDEPENDENT.json'),'consumer one exact owned CPU result')
    with a.output.open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n')
    print(json.dumps(Q.ref(a.output)));return 0 if value['diagnostic_complete'] else 3


if __name__=='__main__':raise SystemExit(main())
