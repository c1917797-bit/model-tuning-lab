"""Plug-in run function for the existing 118 owned guest, after actual ARM.

No device initialization here. The existing controller must validate its same-source
ticket and predecessor results before calling this function. CLI never launches NPU.
"""
import dataclasses
import hashlib
import json
import time
import traceback
from pathlib import Path
import adapter as A


def ref(p):
    p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def checked(r):
    A.need(type(r)is dict and set(r)=={'path','bytes','sha256'},'Ref3')
    p=Path(r['path']);A.need(p.is_absolute()and p.is_file()and
        not any(x.is_symlink()for x in(p,*p.parents))and ref(p)==r,'exact ordinary source')
    return p


def write(p,value):
    with Path(p).open('x',encoding='utf8',newline='\n')as f:
        json.dump(value,f,allow_nan=False,sort_keys=True);f.write('\n')


def run(t,torch_npu,m,out,deadline,*,actual_arm_verified):
    A.need(actual_arm_verified is True,'existing MAIN owned ARM required')
    for r in m['files'].values():checked(r)
    abi=json.loads(checked(m['actual_abi_ref']).read_bytes())
    checked(abi['header_ref']);checked(abi['torch_npu_python_ref'])
    A.need(ref(torch_npu.__file__)==abi['torch_npu_python_ref'],'actual loaded TorchNPU')
    A.need(out.is_dir()and not any(out.iterdir()),'fresh owned leaf')
    rows=[]
    for case,length in enumerate((0,127,128,131)):
        g=t.Generator(device='cpu').manual_seed(261016701+case)
        cpu=dict(q=(t.randn((3,6,256),generator=g)*.1).bfloat16(),
                 k=(t.randn((3,1,256),generator=g)*.1).bfloat16(),
                 v=(t.randn((3,1,256),generator=g)*.1).bfloat16(),
                 kc=(t.randn((5,128,1,256),generator=g)*.1).bfloat16(),
                 vc=(t.randn((5,128,1,256),generator=g)*.1).bfloat16())
        owner=A.Owner('component-request',1,7,length,0);table=(3,1,4)
        child=(None,1,-1,2)[case]
        for mode in(0,1):
            A.need(time.time()<deadline,'existing whole deadline')
            raw=dict(schema='bole.paged-tree-raw/v1',source=m['_actual_source'],case=case,
                     mode=mode,owner=dataclasses.asdict(owner),table=table,inputs=cpu,
                     accepted_child=child,output=None,primary=None)
            before=out/('BEFORE-%d-%d.pt'%(case,mode));t.save(raw,before)
            try:
                device={k:v.to('npu:0')for k,v in cpu.items()}
                trial=A.prepare(t,owner,device['q'],device['k'],device['v'],device['kc'],device['vc'],table)
                output,_=A.native(t,torch_npu,trial,abi,sparse_mode=mode)
                t.npu.synchronize()
                raw['output']=output.cpu();raw['scratch_k']=trial['scratch_k'].cpu();raw['scratch_v']=trial['scratch_v'].cpu()
                raw['actual_mask']=trial['mask'].cpu()
                new=A.commit(t,trial,owner,child);t.npu.synchronize()
                raw['committed_owner']=dataclasses.asdict(new)
                raw['after_k']=device['kc'].cpu();raw['after_v']=device['vc'].cpu()
            except BaseException as e:
                raw['primary']=dict(error=repr(e),traceback=traceback.format_exc())
            path=out/('RAW-%d-%d.pt'%(case,mode));t.save(raw,path)
            row=dict(case=case,mode=mode,raw=ref(path),before=ref(before),primary=raw['primary']);rows.append(row)
            write(out/('ROW-%d-%d.json'%(case,mode)),row)
            A.need(sum(p.stat().st_size for p in out.iterdir()if p.is_file())<=64*2**20,'raw64MiB bound')
    value=dict(schema='bole.paged-tree-stage/v1',source=m['_actual_source'],actual_abi_ref=m['actual_abi_ref'],
               rows=rows,NPU=True,qualified=False,model_ready=False)
    write(out/'STAGE_RESULT.json',value);return value
