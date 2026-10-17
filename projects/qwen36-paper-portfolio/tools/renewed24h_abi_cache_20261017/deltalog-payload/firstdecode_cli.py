"""Devices[] postconsumer CLI. No owner/control/resource or native imports."""
import argparse
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import firstdecode_gate as Q
from firstdecode_consume import consume_rank

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
    # The original precast file imports public direct_round at module load.
    # Install its exact defining source first, never rely on the old parent
    # directory being ambient on sys.path (especially under -I).
    for r in Q.numerical_readset(payload):Q.checked(r)
    T=Q.load(payload['original_tensor_consumer'],'_firstdecode_original_tensor_consumer')
    R=T.module();Q.need(R.STATE_LIMIT==7.92e-7 and R.OUTPUT_LIMIT==.00303,'original unchanged numerical limits')
    for key in('direct_round','precast'):
        r=payload['original_'+key];old=sys.modules.get(key)
        Q.need(old is None or Path(old.__file__).resolve()==Q.checked(r),'no ambient numerical namespace')
        if old is None:Q.load(r,key)
    return T,R

def consume(model_sr,payload_sr,owner_ref,inspect_ref,loaded_ref,reports_ref):
    payload=Q.source(payload_sr);m=Q.obj(model_sr);Q.verify_tiny(payload)
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
            rank_results.append(consume_rank(torch,T,R,report,aio,model_sr,payload_sr,m['library_ref'],m['debug_library']))
        except BaseException as e:failures.append(dict(report=rr,primary=repr(e)))
    logs=reports['expected_stop_logs'];Q.need(logs,'actual retained stop logs are required, not a string field')
    stop_join=False
    for r in logs:
        h=aio.actual_ref(r);p=Q.checked(h);Q.need(p.stat().st_size<=64*1024**2,'bounded actual diagnostic log')
        text=p.read_text(encoding='utf8',errors='replace')
        stop_join |= 'DL_FIRST_DECODE_COMPLETE_OBSERVATION_NOT_MODEL_QUALIFICATION' in text and 'DiagnosticStop' in text and payload['files']['firstdecode.py']['path'] in text
    passed=seen=={0,1,2,3} and len(rank_results)==4 and not failures and all(r['all48_firstdecode_pass'] for r in rank_results)
    return dict(schema='deltalog.independent-all4-firstdecode/v1',source=payload_sr,model_source=model_sr,parent_failed_owner=owner_ref,original_primary=parent['primary'],original_status_retained='failed',owner_success=False,final_inspect=inspect_ref,actual_budget=budget_ref,loaded=loaded_ref,reports=reports_ref,rank_results=rank_results,failures=failures,actual_single_decode_data_gates_pass=passed,expected_stop_causally_joined=bool(stop_join),diagnostic_complete=passed and stop_join,alias_joins=aio.joins,full_model_qualified=False,normalEOS_qualified=False,lifecycle_reuse_qualified=False,long160_qualified=False,performance_qualified=False,task_qualified=False)

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    for n in('model-source-ref','payload-source-ref','owner-ref','inspect-ref','loaded-ref','reports-ref'):p.add_argument('--'+n)
    p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    args=[json.loads(getattr(a,n.replace('-','_'))) for n in('model-source-ref','payload-source-ref','owner-ref','inspect-ref','loaded-ref','reports-ref')]
    value=consume(*args)
    with a.output.open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n')
    print(json.dumps(Q.ref(a.output)));return 0 if value['diagnostic_complete'] else 3

if __name__=='__main__':raise SystemExit(main())
