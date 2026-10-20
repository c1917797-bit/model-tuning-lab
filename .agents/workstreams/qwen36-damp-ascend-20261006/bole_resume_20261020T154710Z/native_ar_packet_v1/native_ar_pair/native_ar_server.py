"""Owned-runner entry only; MAIN owns all process/container/resource admission."""
import argparse
import json
import os
from pathlib import Path
import runpy
import sys
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0,str(_Path(__file__).resolve().parent))
import pair_contract as C


def environment(base,sr):
    m=C.source(sr);e=dict(base)
    C.need(not any(k.startswith(('VLLM_PROFILER','TORCH_PROFILER'))for k in e),'no profiling')
    for key in list(e):
        if key.startswith(('BOLE_','BOLE111_','DENSE_OPPORTUNITY090_','MXR_','MST_MXR_','QWEN36_DELTALOG','DLOG_')):
            e.pop(key)
    e.update(VLLM_PLUGINS='ascend,bole_native_ar_pair',BOLE_NATIVE_AR_PAIR_ENABLE='1',
        BOLE_NATIVE_AR_PAIR_SOURCE_REF=json.dumps(sr),BOLE_MODEL_OBJECT_AUDIT_ENABLE='1',
        BOLE_MODEL_RAW_ROOT=m['model_receipt_root'],
        PYTHONPATH=m['root']+os.pathsep+e.get('PYTHONPATH',''))
    return e


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--source-ref');a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    C.need(a.source_ref is not None,'explicit current source and owned runtime')
    sr=json.loads(a.source_ref);m=C.source(sr)
    C.need(C.ref(__file__)==m['files']['native_ar_server.py']
           and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0,1,2,3',
           'actual owned TP4 runtime only')
    root=Path(m['model_receipt_root']);C.need(root.is_dir(),'precreated owned AR leaf')
    args=m['native_server_argv']
    C.write(root/'SERVER_COMMAND.json',dict(source=sr,argv=args,native_AR=True,
        speculative_config=None,BOLE=False,common_argv_derived_from=m['BOLE_server_command_ref'],
        actual_kernel_route_not_assumed=True,model_ready=False))
    os.environ.update(environment(os.environ,sr))
    import identity_journal
    identity_journal.install_frontend(sr)
    C.need(len(args)>3 and args[1]=='-m','source-bound original module command')
    sys.argv=[args[2],*args[3:]]
    runpy.run_module(args[2],run_name='__main__');return 0


if __name__=='__main__':raise SystemExit(main())
