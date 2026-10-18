"""Original paged singleton canary/MAIN_ARM boundary for a new fixed-frame probe."""
import argparse
import importlib.machinery
import importlib.util
import json
import os
import sys
import time
import traceback
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import common as C


def main():
    p=argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument('--execute',action='store_true');p.add_argument('--source-ref')
    p.add_argument('--plan-ref');p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not a.execute:
        print('{"enabled":false,"NPU":false}');return 0
    sr=json.loads(a.source_ref);m=C.source(sr);C.window(m)
    C.need(m['files']['guest.py']==C.ref(__file__),'actual new guest identity')
    pr=json.loads(a.plan_ref);plan=C.obj(pr)
    C.need(plan['schema']=='bole.fia-replay-plan/v1'and plan['source']==sr and
           plan['physical']==4 and plan['logical']==0 and plan['qualification']is False,
           'source-bound original singleton mapping')
    C.need(type(plan['work_deadline'])in(int,float)and
           time.time()<plan['work_deadline']<=C.CUT-180,'owner-charged work/cleanup deadline')
    ticket=C.load(m['files']['ticket.py'],'_fia_guest_ticket')
    tv=C.obj(plan['abi_ticket_ref'])
    ticket.consume(plan['abi_ticket_ref'],sr,tv['cpu_owner'])
    C.need(tv['cpu_stage']==plan['cpu_stage']and tv['image']==C.IMAGE,'same-source released CPU plan')
    C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0'and
           os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and
           os.environ.get('BOLE_FIA_FIXED_FRAME_ENABLE')=='1','actual opt-in singleton visibility')
    C.need(not a.output.exists()and a.output.parent.is_dir(),'fresh original controlled guest output')
    a.output.mkdir();out=a.output;attempted=False;result=None;primary=None
    start=time.monotonic();actual_abi_ref=tv['actual_abi_ref'];probe_summary=None
    try:
        helper=C.load(m['cann_helper_ref'],'_fia_actual_cann')
        root='/usr/local/Ascend/cann-9.1.0/python/site-packages'
        C.need(helper.ROOT==root,'actual original CANN Python source')
        helper.file_identity('/usr/local/Ascend/cann-9.1.0/set_env.sh',5112,
                             'de50f1bf5b960f8305792ef407e3bfc3fc1b6d82931d0feae39ac4c965690aaf')
        direct=helper.spec_identity(importlib.machinery.PathFinder.find_spec('acl',[root]))
        sys.path.insert(0,root)
        C.need(helper.spec_identity(importlib.util.find_spec('acl'))==direct,'actual ACL extension')
        C.write(out/'CANN.json',dict(helper=m['cann_helper_ref'],actual=direct))
        import torch as t
        import torch_npu
        t.set_num_threads(1);torch_npu.npu.set_compile_mode(jit_compile=False)
        attempted=True;t.npu.set_device(0)
        C.need(t.npu.device_count()==1,'actual original singleton')
        t.npu.matmul.allow_hf32=False
        C.need(t.npu.matmul.allow_hf32 is False,'original common matmul HF32OFF')
        C.write(out/'ACTUAL_TORCH.json',dict(torch_version=t.__version__,
                 torch_python=C.ref(t.__file__),torch_npu_python=C.ref(torch_npu.__file__),
                 HF32=False,operator='original FIA boundary replay and parameter comparison',
                 custom_DSO=None,NPU=True,qualified=False))
        canary=(t.tensor([1.,2.],device='npu:0')+3).cpu().tolist()
        C.need(canary==[4.,5.],'actual original device canary')
        C.write(out/'DEVICE.json',dict(pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),
                 cgroup=Path('/proc/self/cgroup').read_text(),logical=0,
                 physical_declared_by_plan=4,plan=pr,canary=canary,
                 physical_proof_must_be_host_owned=True))
        until=min(time.monotonic()+30,start+560)
        while not(out/'MAIN_ARM.json').exists():
            C.need(time.monotonic()<until and time.time()<plan['work_deadline'],
                   'original bounded actual host ARM30')
            time.sleep(.1)
        C.need(C.obj(C.ref(out/'MAIN_ARM.json'))==dict(schema='bole.fia-replay-arm/v1',
                  pid=os.getpid(),plan_sha256=pr['sha256'],physical=4),'exact actual host ARM')
        remaining=560-(time.monotonic()-start)
        C.need(remaining>0,'all startup charged to original guest600')
        deadline=min(plan['work_deadline'],C.CUT-180,time.time()+remaining)
        probe=C.load(m['files']['probe.py'],'_fia_actual_fixed_probe')
        target=out/'probe';target.mkdir()
        probe_summary=probe.run(sr,pr,target,work_deadline=deadline,actual_arm_verified=True)
        C.write(out/'PROBE_RUN.json',probe_summary)
        C.need(probe_summary['source']==sr and probe_summary['plan']==pr and
               probe_summary['actual_abi_ref']==actual_abi_ref and
               probe_summary['qualified']is False,'actual source and sameimage ABI probe output')
        result=probe_summary['result']
        if probe_summary['primary']is not None:
            primary='FIA original or changed parameter call failed: '+repr(probe_summary['primary'])
        C.need(time.time()<=deadline,'all actual FIA work remained inside original charged bound')
    except BaseException as error:
        primary=repr(error)
        C.write(out/'FAILURE.json',dict(primary=primary,traceback=traceback.format_exc()))
    C.write(out/'STAGE_RESULT.json',dict(schema='bole.fia-replay-stage/v1',source=sr,
             authority=m['authority_ref'],plan=pr,abi_ticket_ref=plan['abi_ticket_ref'],
             actual_abi_ref=actual_abi_ref,result=result,primary=primary,
             NPU=attempted,qualified=False,old_failures_unchanged=True,
             diagnostic_complete=False if probe_summary is None else probe_summary['diagnostic_complete']))
    return 0 if primary is None else 3


if __name__=='__main__':raise SystemExit(main())
