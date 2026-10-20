"""Bind existing owned variant ledgers; never constructs ownership evidence."""
import argparse
import json
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import pair_contract as C


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--native-AR-bundle-ref');p.add_argument('--BOLE-bundle-ref')
    p.add_argument('--inputs-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    C.need(all(x is not None for x in(a.source_ref,a.native_AR_bundle_ref,a.BOLE_bundle_ref,a.inputs_ref,a.output)),
           'explicit existing actual owned ledgers')
    sr=json.loads(a.source_ref);m=C.source(sr)
    ar_ref,on_ref,inputs_ref=(json.loads(x)for x in(a.native_AR_bundle_ref,a.BOLE_bundle_ref,a.inputs_ref))
    ar,on,inputs=(C.obj(x)for x in(ar_ref,on_ref,inputs_ref))
    C.need(ar['schema']=='bole.actual-four-rank-native-ar-inputs/v1'and ar['source']==sr
           and on['schema']=='bole.actual-four-rank-two-request-inputs/v1'
           and on['source']==m['BOLE_source_ref']and inputs['source']==m['BOLE_source_ref'],
           'exact source-bound variant ledgers and shared tokenizer input')
    for bundle in(ar,on):
        for key in('docker_inspect_ref','server_command_ref','model_manifest_ref','launch_profile_ref'):
            C.checked(bundle[key])
    result=C.write(a.output,dict(schema='bole.actual-native-ar-bole-pair-inputs/v1',source=sr,
        scope=C.SCOPE,native_AR=ar_ref,BOLE=on_ref,inputs_ref=inputs_ref,model_ready=False))
    print(json.dumps(result));return 0


if __name__=='__main__':raise SystemExit(main())
