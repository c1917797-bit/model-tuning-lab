"""Devices[] same-image startup only: actual Torch/dill, no HAL/FA operator."""
import argparse
import json
import os
from pathlib import Path
import sys
import traceback
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import common116 as C

def run(m,sr,output,stage_root):
    C.need(sys.platform=='linux' and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0' and
           not list(Path('/dev').glob('davinci*')),'actual Linux Devices[] startup smoke only')
    S=C.load(m['files']['scratch_environment.py'],'_factor_r2_exact_scratch')
    proof=S.validate(stage_root)
    # Kernel mount evidence is observed, not inferred from a source boolean.
    mounts=Path('/proc/self/mountinfo').read_text().splitlines()
    roots=[line.split() for line in mounts if len(line.split())>5 and line.split()[4]=='/']
    C.need(len(roots)==1 and 'ro' in roots[0][5].split(','),'actual image root is read-only')
    import torch
    import dill
    C.need(torch.tensor([1,2],dtype=torch.int32).sum().item()==3,'actual installed CPU Torch import/use')
    C.need(dill.loads(dill.dumps(dict(actual='dill-import-roundtrip')))==dict(actual='dill-import-roundtrip'),'actual dill serialization import path')
    C.need(not any(Path('/dev').glob('davinci*')),'startup test did not create/expose device nodes')
    value=dict(schema='bole.factor-repair2-actual-CPU-startup/v1',source=sr,
        scratch=proof,torch_python=C.ref(torch.__file__),dill_python=C.ref(dill.__file__),
        torch_version=torch.__version__,image_root_readonly=True,Devices=[],NPU=False,
        operator_executed=False,qualification=False)
    C.write(output,value);return C.ref(output)

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--stage-root',type=Path);p.add_argument('--output',type=Path);p.add_argument('--controlled-failure',action='store_true');a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    sr=json.loads(a.source_ref);m=C.source(sr);C.window(m)
    print(json.dumps(run(m,sr,a.output,a.stage_root)),flush=True)
    if a.controlled_failure:raise RuntimeError('BOLE_FACTOR_R2_CONTROLLED_FAILURE_AFTER_REAL_TORCH_DILL_STARTUP_NO_NPU')
    return 0

if __name__=='__main__':raise SystemExit(main())
