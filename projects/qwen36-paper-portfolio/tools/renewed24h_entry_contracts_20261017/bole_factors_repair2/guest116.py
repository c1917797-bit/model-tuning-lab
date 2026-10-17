import argparse,importlib.machinery,importlib.util,json,os,sys,time,traceback
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common116 as C


def execute(t,m,out,deadline):
 import pipeline118t as K
 ticket=C.obj(m['_plan']['abi_ticket_ref']);C.need(ticket['source']==m['_actual_source']and ticket['cpu_stage']==m['_plan']['cpu_stage'],'same-source actual bootstrap CPU ticket')
 m['actual_abi_ref']=ticket['actual_abi_ref'];leaf=out/'factors';leaf.mkdir()
 import factor
 factor.validate_abi(t,__import__('torch_npu'),C,C.obj(ticket['actual_abi_ref']))
 original=C.obj(m['original_fia_abi_ref']);C.need(original['schema_family']==C.obj(ticket['actual_abi_ref'])['schema_family'],'same original model dispatcher family, new actual CPU proof required')
 K.run(t,C,m,leaf,deadline);return C.ref(leaf/'STAGE_RESULT.json')


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--plan-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    sr=json.loads(a.source_ref);m=C.source(sr);C.window(m);m['_actual_source']=sr;pr=json.loads(a.plan_ref);plan=C.obj(pr);m['_plan']=plan;m['_plan_ref']=pr
    C.need(plan['schema']=='bole.tree-plan/vFAfactor'and plan['source']==sr and plan['physical']==4 and plan['logical']==0 and plan['qualification']is False,'source-bound actual single4 plan')
    cpu=C.obj(plan['cpu_stage']);C.need(cpu['schema']=='bole.tree-CPU-stage/vFAfactor'and cpu['source']==sr and cpu['actual_meta']['pass_gate']is True,'sameimage actual CPU Meta required')
    C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0'and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','actual singleton visibility')
    C.need(not a.output.exists()and a.output.parent.is_dir(),'fresh output');a.output.mkdir();out=a.output;attempted=False;result=None;primary=None;start=time.monotonic()
    try:
        scratch=C.load(m['files']['scratch_environment.py'],'_factor_repair2_native_scratch');C.write(out/'PRIVATE_SCRATCH.json',scratch.validate(out.parent))
        helper=C.load(m['cann_helper_ref'],'_116actualcann');root='/usr/local/Ascend/cann-9.1.0/python/site-packages'
        C.need(helper.ROOT==root,'actual CANN Python source');helper.file_identity('/usr/local/Ascend/cann-9.1.0/set_env.sh',5112,'de50f1bf5b960f8305792ef407e3bfc3fc1b6d82931d0feae39ac4c965690aaf')
        direct=helper.spec_identity(importlib.machinery.PathFinder.find_spec('acl',[root]));sys.path.insert(0,root);C.need(helper.spec_identity(importlib.util.find_spec('acl'))==direct,'real ACL extension')
        C.write(out/'CANN.json',dict(helper=m['cann_helper_ref'],actual=direct))
        import torch as t,torch_npu
        t.set_num_threads(1);torch_npu.npu.set_compile_mode(jit_compile=False);attempted=True;t.npu.set_device(0)
        C.need(t.npu.device_count()==1,'actual singleton');t.npu.matmul.allow_hf32=False
        C.need(t.npu.matmul.allow_hf32 is False,'explicit common FP32 matmul HF32OFF')
        C.write(out/'ACTUAL_TORCH.json',dict(torch_version=t.__version__,torch_python=C.ref(t.__file__),torch_npu_python=C.ref(torch_npu.__file__),HF32=False,operator='actual saved-input FIA factors; no GDN import/conv',custom_DSO=None,NPU=True))
        canary=(t.tensor([1.,2.],device='npu:0')+3).cpu().tolist();C.need(canary==[4.,5.],'actual canary')
        C.write(out/'DEVICE.json',dict(pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),logical=0,physical_declared_by_plan=4,plan=pr,canary=canary,physical_proof_must_be_host_owned=True))
        until=time.monotonic()+30
        while not(out/'MAIN_ARM.json').exists():C.need(time.monotonic()<until,'actual host ARM30');time.sleep(.1)
        C.need(C.obj(C.ref(out/'MAIN_ARM.json'))==dict(schema='bole.tree-arm/vFAfactor',pid=os.getpid(),plan_sha256=pr['sha256'],physical=4),'exact host ARM')
        remaining=560-(time.monotonic()-start);C.need(remaining>0,'startup charged to guest600')
        result=execute(t,m,out,min(1792313000,time.time()+remaining))
    except BaseException as e:primary=repr(e);C.write(out/'FAILURE.json',dict(primary=primary,traceback=traceback.format_exc()))
    C.write(out/'STAGE_RESULT.json',dict(schema='bole.tree-stage/vFAfactor',source=sr,authority=m['authority_ref'],plan=pr,abi_ticket_ref=plan['abi_ticket_ref'],actual_abi_ref=m.get('actual_abi_ref'),result=result,primary=primary,NPU=attempted,qualified=False));return 0 if primary is None else 3

if __name__=='__main__':raise SystemExit(main())
