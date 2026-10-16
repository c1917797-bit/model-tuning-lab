"""Independent sequential CPUdouble recurrence; no candidate closedform call."""
import argparse,json,os,sys,time,traceback
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common112 as C


def metric(t,actual,expected):
    C.need(actual.shape==expected.shape and actual.dtype==t.float32,'exact FP32 observed ABI')
    C.need(bool(t.isfinite(actual).all())and bool(t.isfinite(expected).all()),'finite observed/reference')
    delta=actual.double()-expected
    # Preregistered empirical FP32 arithmetic comparison; no epsilon fitting.
    peak=float(delta.abs().max());scale=float(expected.abs().max());relative=float(t.linalg.vector_norm(delta)/t.linalg.vector_norm(expected).clamp_min(1e-30))
    return dict(peak_abs=peak,relative_l2=relative,passed=peak<=2e-5+2e-4*scale and relative<=2e-4)


def consume(t,m,stage,out):
    import oracle112 as K,recipe112 as R
    C.need(stage['schema']=='bole.tree-stage/v112'and stage['source']==m['_actual_source']and stage['primary']is None and stage['NPU']is True,'actual source-bound NPU producer')
    result=stage['result'];expected_cases=R.cases(m['profile']);C.need(len(result['anchors'])==len(expected_cases)and len(result['rows'])==len(expected_cases)*3,'all cases/three rounds')
    reports=[];previous={};trajectory={};failures=[]
    for index,anchor in enumerate(result['anchors']):
        raw=t.load(C.checked(anchor),map_location='cpu',weights_only=True);batch,kind,depth=expected_cases[index]
        parents,planned,steps=R.recipe(t,batch,kind,depth,index)
        C.need(raw['case']==index and raw['parents']==parents and t.equal(raw['state'],planned),'independent preregistered nonzero initial anchor')
        previous[index]=raw['state'];trajectory[index]=raw['state'].double()
    for number,row in enumerate(result['rows']):
        index,step=divmod(number,3);C.need(row['case']==index and row['step']==step,'ordered complete rounds')
        raw=t.load(C.checked(row['raw']),map_location='cpu',weights_only=True);batch,kind,depth=expected_cases[index];parents,initial,events=R.recipe(t,batch,kind,depth,index);event=events[step]
        C.need((raw['case'],raw['batch'],raw['kind'],raw['depth'],raw['step'],raw['parents'],raw['terminal'])==(index,batch,kind,depth,step,parents,event['terminal']),'exact case metadata')
        C.need(all(t.equal(raw['inputs'][n],event[n])for n in('q','k','v','beta','gamma')),'actual operands equal independent recipe')
        inputs=raw['inputs'];q=inputs['q'].double().repeat_interleave(3,dim=1);k=inputs['k'].double().repeat_interleave(3,dim=1)
        args=(q,k,inputs['v'].double(),inputs['beta'].double(),inputs['gamma'].double())
        expected,states,updates=K.sequential(t,*args,previous[index].double(),parents,return_updates=True)
        accumulated,acc_states=K.sequential(t,*args,trajectory[index],parents)
        after=previous[index].double()if event['terminal']is None else states[event['terminal']]
        acc_after=trajectory[index]if event['terminal']is None else acc_states[event['terminal']]
        local_output=metric(t,raw['output'],expected);local_state=metric(t,raw['after'],after)
        products=[]
        for i,parent in enumerate(parents):products.append(inputs['gamma'][...,i].double()*(1 if parent==-1 else products[parent]))
        factor_update=metric(t,raw['U'],updates);factor_decay=metric(t,raw['P'],t.stack(products,dim=-1))
        cumulative_output=metric(t,raw['output'],accumulated);cumulative_state=metric(t,raw['after'],acc_after)
        noaccept=event['terminal']is not None or t.equal(raw['after'].view(t.int32),previous[index].view(t.int32))
        ok=all(x['passed']for x in(local_output,local_state,cumulative_output,cumulative_state,factor_update,factor_decay))and raw['canonical_immutable']is True and noaccept
        reports.append(dict(case=index,step=step,raw=row['raw'],output=local_output,state=local_state,cumulative_output=cumulative_output,cumulative_state=cumulative_state,U=factor_update,P=factor_decay,canonical_immutable=raw['canonical_immutable'],noaccept_bitwise=noaccept,passed=ok))
        if not ok:failures.append(dict(case=index,step=step))
        # Always advance independent trajectory; a failed row must not create
        # synthetic continuity failures or suppress later diagnostics.
        previous[index]=raw['after'];trajectory[index]=acc_after
    return dict(schema='bole.tree-independent/v112',source=m['_actual_source'],rows=reports,failures=failures,pass_gate=not failures,qualified=False,model_ready=False,performance_ready=False)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--stage-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    sr=json.loads(a.source_ref);m=C.source(sr);C.window(m);m['_actual_source']=sr
    C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not list(Path('/dev').glob('davinci*')),'Devices[] CPU environment')
    C.need(not a.output.exists()and a.output.parent.is_dir(),'new independent output')
    import torch as t
    t.set_num_threads(1)
    try:v=consume(t,m,C.obj(json.loads(a.stage_ref)),a.output.parent)
    except BaseException as e:
        C.write(a.output.with_name(a.output.name+'.failure.json'),dict(source=sr,primary=repr(e),traceback=traceback.format_exc(),raw_unchanged=True,qualified=False));raise
    C.write(a.output,v);return 0 if v['pass_gate']else 3

if __name__=='__main__':raise SystemExit(main())
