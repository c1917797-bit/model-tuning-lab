import argparse,importlib.machinery,importlib.util,json,os,sys,time,traceback
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common112 as C


def execute(t,m,out,deadline,*,device='npu:0'):
    import core112 as K,recipe112 as R
    profile=m['profile'];rows=[];anchors=[]
    C.need(R.logical_raw_upper(profile)<768*2**20,'preregistered raw tensor bytes plus overhead')
    for index,(batch,kind,depth)in enumerate(R.cases(profile)):
        C.need(time.time()<deadline,'bounded kernel work deadline')
        parents,initial,steps=R.recipe(t,batch,kind,depth,index);mask,inc=R.masks(t,parents)
        C.need(device=='npu:0'or(device=='cpu'and m.get('software_control_only')is True),'device override only explicit local software control')
        state=initial.to(device);mask=mask.to(device);inc=inc.to(device)
        anchors.append(C.save(t,out/('initial-%02d.pt'%index),dict(case=index,parents=parents,state=state.cpu()),out))
        for step,inp in enumerate(steps):
            C.need(time.time()<deadline,'bounded tree iteration')
            actual={n:inp[n].to(device)for n in('q','k','v','beta','gamma')}
            q=actual['q'].float().repeat_interleave(3,dim=1);k=actual['k'].float().repeat_interleave(3,dim=1)
            before=state.clone()
            output,factors=K.verify(t,q,k,actual['v'].float(),actual['beta'],actual['gamma'],state,mask,depth)
            after=K.commit(t,state,k,factors,inc,inp['terminal'])
            if device=='npu:0':t.npu.synchronize()
            # Copies are diagnostic and occur outside any performance claim.
            immutable=t.equal(state,before)
            value=dict(schema='bole.tree-raw/v112',case=index,batch=batch,kind=kind,depth=depth,step=step,parents=parents,terminal=inp['terminal'],inputs={n:x.cpu()for n,x in actual.items()},output=output.cpu(),P=factors[0].cpu(),U=factors[1].cpu(),after=after.cpu(),canonical_immutable=bool(immutable),graph=False,GQA=[4,12],Dk=128,Dv=128)
            rr=C.save(t,out/('tree-%02d-%d.pt'%(index,step)),value,out)
            rows.append(dict(case=index,step=step,raw=rr))
            C.write(out/('ROW-%02d-%d.json'%(index,step)),dict(raw=rr,source=m['_actual_source'],canonical_immutable=bool(immutable)))
            C.need(immutable,'canonical state changed before accepted-path commit')
            state=after
    return dict(cases=len(anchors),rows=rows,anchors=anchors,profile=profile,raw_cap=768*2**20,logical_upper=R.logical_raw_upper(profile),qualified=False,full_mixed_graph_qualified=False)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--plan-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    sr=json.loads(a.source_ref);m=C.source(sr);C.window(m);m['_actual_source']=sr;pr=json.loads(a.plan_ref);plan=C.obj(pr)
    C.need(plan['schema']=='bole.tree-plan/v112'and plan['source']==sr and plan['physical']==4 and plan['logical']==0 and plan['qualification']is False,'source-bound actual single4 plan')
    cpu=C.obj(plan['cpu_stage']);C.need(cpu['schema']=='bole.tree-CPU-stage/v112'and cpu['source']==sr and cpu['actual_meta']['pass_gate']is True,'sameimage actual CPU Meta required')
    C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0'and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','actual singleton visibility')
    C.need(not a.output.exists()and a.output.parent.is_dir(),'fresh output');a.output.mkdir();out=a.output;attempted=False;result=None;primary=None;start=time.monotonic()
    try:
        helper=C.load(m['cann_helper_ref'],'_112actualcann');root='/usr/local/Ascend/cann-9.1.0/python/site-packages'
        C.need(helper.ROOT==root,'actual CANN Python source');helper.file_identity('/usr/local/Ascend/cann-9.1.0/set_env.sh',5112,'de50f1bf5b960f8305792ef407e3bfc3fc1b6d82931d0feae39ac4c965690aaf')
        direct=helper.spec_identity(importlib.machinery.PathFinder.find_spec('acl',[root]));sys.path.insert(0,root);C.need(helper.spec_identity(importlib.util.find_spec('acl'))==direct,'real ACL extension')
        C.write(out/'CANN.json',dict(helper=m['cann_helper_ref'],actual=direct))
        import torch as t,torch_npu
        t.set_num_threads(1);torch_npu.npu.set_compile_mode(jit_compile=False);attempted=True;t.npu.set_device(0)
        C.need(t.npu.device_count()==1,'actual singleton');t.npu.matmul.allow_hf32=False
        C.need(t.npu.matmul.allow_hf32 is False,'explicit common FP32 matmul HF32OFF')
        C.write(out/'ACTUAL_TORCH.json',dict(torch_version=t.__version__,torch_python=C.ref(t.__file__),torch_npu_python=C.ref(torch_npu.__file__),HF32=False,operator='registered Torch matmul/exp/log',custom_DSO=None,NPU=True))
        canary=(t.tensor([1.,2.],device='npu:0')+3).cpu().tolist();C.need(canary==[4.,5.],'actual canary')
        C.write(out/'DEVICE.json',dict(pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),logical=0,physical_declared_by_plan=4,plan=pr,canary=canary,physical_proof_must_be_host_owned=True))
        until=time.monotonic()+30
        while not(out/'MAIN_ARM.json').exists():C.need(time.monotonic()<until,'actual host ARM30');time.sleep(.1)
        C.need(C.obj(C.ref(out/'MAIN_ARM.json'))==dict(schema='bole.tree-arm/v112',pid=os.getpid(),plan_sha256=pr['sha256'],physical=4),'exact host ARM')
        remaining=560-(time.monotonic()-start);C.need(remaining>0,'startup charged to guest600')
        result=execute(t,m,out,min(1792220533,time.time()+remaining))
    except BaseException as e:primary=repr(e);C.write(out/'FAILURE.json',dict(primary=primary,traceback=traceback.format_exc()))
    C.write(out/'STAGE_RESULT.json',dict(schema='bole.tree-stage/v112',source=sr,authority=m['authority_ref'],plan=pr,result=result,primary=primary,NPU=attempted,qualified=False));return 0 if primary is None else 3

if __name__=='__main__':raise SystemExit(main())
