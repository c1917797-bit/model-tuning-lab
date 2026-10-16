import argparse,json,os,sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common112 as C


def meta(t):
    import core112 as K,recipe112 as R
    rows=[]
    for b,kind,d in R.cases('full'):
        n=len(R.parents(kind,d));dev='meta'
        q=t.empty((b,12,n,128),device=dev);v=t.empty_like(q);g=t.empty((b,12,n),device=dev);s=t.empty((b,12,128,128),device=dev);mask=t.empty((n,n),device=dev)
        output,factors=K.verify(t,q,q,v,g,g,s,mask,d);after=K.commit(t,s,q,factors,mask,n-1)
        C.need(output.shape==(b,12,n,128)and after.shape==s.shape and output.dtype==t.float32,'actual Meta shape/dtype')
        rows.append(dict(batch=b,kind=kind,depth=d,nodes=n,output_shape=list(output.shape),state_shape=list(after.shape)))
    return dict(schema='bole.actual-Torch-Meta/v112',pass_gate=True,rows=rows,NPU=False,custom_DSO=None,operator='torch.matmul/exp/log/cat',registrations_not_custom_kernel=True)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    sr=json.loads(a.source_ref);m=C.source(sr);C.window(m)
    C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not list(Path('/dev').glob('davinci*')),'Devices[] preflight')
    C.need(not a.output.exists()and a.output.parent.is_dir(),'fresh CPU output');a.output.mkdir()
    result=subprocess.run([sys.executable,'-I','-B',str(C.checked(m['files']['test112.py']))],capture_output=True,text=True,timeout=180)
    C.write(a.output/'SOFTWARE_CONTROLS.json',dict(source=sr,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,NPU=False))
    C.need(result.returncode==0,'actual cold source/Meta/oracle/create/inspect controls')
    mapping=subprocess.run([sys.executable,'-I','-B',str(C.checked(m['files']['test_mapping112r2.py']))],capture_output=True,text=True,timeout=60)
    C.write(a.output/'MAPPING_CONTROLS.json',dict(source=sr,exit_code=mapping.returncode,stdout=mapping.stdout,stderr=mapping.stderr,NPU=False))
    C.need(mapping.returncode==0,'actual physical4 scope/inspect/protected/cold controls')
    controller=subprocess.run([sys.executable,'-I','-B',str(C.checked(m['files']['test_controller112r4.py']))],capture_output=True,text=True,timeout=60)
    C.write(a.output/'CONTROLLER_CONTROLS.json',dict(source=sr,exit_code=controller.returncode,stdout=controller.stdout,stderr=controller.stderr,NPU=False))
    C.need(controller.returncode==0,'actual private controller and original base_lane construction before backend')
    import torch as t
    t.set_num_threads(1);v=meta(t);C.need('torch_npu'not in sys.modules,'no NPU backend import')
    C.write(a.output/'STAGE_RESULT.json',dict(schema='bole.tree-CPU-stage/v112',source=sr,actual_meta=v,NPU=False,qualified=False));return 0

if __name__=='__main__':raise SystemExit(main())
