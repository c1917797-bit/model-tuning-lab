"""Default-OFF Devices[] exact source/evidence preflight; stdlib only."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--inputs-ref')
    parser.add_argument('--output',type=Path);args=parser.parse_args()
    if not args.execute:print('{"enabled":false,"NPU":false}');return 0
    if not(args.inputs_ref and args.output):parser.error('exact new inputs and new output required')
    sys.dont_write_bytecode=True
    spec=importlib.util.spec_from_file_location('_saved_preflight_common',Path(__file__).parent/'saved_common.py')
    B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B);C=B.common()
    ir=json.loads(args.inputs_ref);y=B.source(C,ir)
    C.need(C.ref(__file__)==y['files']['saved_preflight.py']and
           os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and
           not list(Path('/dev').glob('davinci[0-9]*')),'actual exact Devices[] source preflight')
    x,m,on,readset,mapping=B.readset(C,y,installed=True)
    for r in y['files'].values():
        if r['path'].endswith('.py'):compile(C.checked(r).read_bytes(),r['path'],'exec')
    result=C.write(args.output,dict(schema='bole.native-ar-saved-source-preflight/v1',inputs=ir,source=x['AR_source'],
        source_preflight_pass=True,Devices=[],NPU=False,model_reexecuted=False,checkpoint_rehashed=False,
        installed_sources_reopened=True,readset_count=len(readset),mapping=mapping,model_ready=False,formal_success=False))
    print(json.dumps(dict(result=result,NPU=False)));return 0


if __name__=='__main__':raise SystemExit(main())
