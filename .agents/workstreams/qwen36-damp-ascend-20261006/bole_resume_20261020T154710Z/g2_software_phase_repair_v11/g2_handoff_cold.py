"""Actual Devices[] cold read of four complete saved metadata copies.

This calls the exact original v7 contract/finalizer functions on saved live
snapshots. It proves transport/readability, never present model/live identity.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    parser=argparse.ArgumentParser(allow_abbrev=False);parser.add_argument('--execute',action='store_true')
    for key in('source-ref','stage-ref','output'):parser.add_argument('--'+key)
    a=parser.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    import sourceio as C,g2_handoff as H
    sr=json.loads(a.source_ref);stage=json.loads(a.stage_ref);m=H.source_guard(C,sr)
    C.need(m['root']==str(P)and sr==C.ref(P/'SOURCE_BOUND.json')and m['prepared_only']is False and C.ref(__file__)==m['files']['g2_handoff_cold.py']and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not list(Path('/dev').glob('davinci[0-9]*')),'exact actual bound Devices[] cold source, before any ML/backend import')
    v=H.verify_saved_probe(C,sr,stage,guest=True);old=C.obj(v['evidence_source'])
    originals={n:old['files'][n]for n in('g2_channel.py','g2_finalize.py','sourceio.py','g1_contract.py','g2_contract.py')}
    for n in('sourceio.py','g1_contract.py','g2_contract.py'):C.need((m['files'][n]['bytes'],m['files'][n]['sha256'])==(originals[n]['bytes'],originals[n]['sha256']),'original source/contract support implementation byteexact '+n)
    for r in originals.values():C.checked(r)
    original_channel=load(C.checked(originals['g2_channel.py']),'_g2_v8_exact_saved_v7_channel')
    prior=sys.modules.get('g2_channel');sys.modules['g2_channel']=original_channel
    try:original_finalizer=load(C.checked(originals['g2_finalize.py']),'_g2_v8_exact_saved_v7_finalizer')
    finally:
        if prior is None:sys.modules.pop('g2_channel',None)
        else:sys.modules['g2_channel']=prior
    first=original_channel.contract(C,v['evidence_source'],v['channel'])
    second=original_finalizer.owned_channel(old,v['evidence_source'],v['channel'])
    C.need(first==second==C.obj(v['channel']),'original complete channel and independent owner/inspect assertions really execute')
    H.verify_saved_probe(C,sr,stage,guest=True)
    C.need(not any(n=='torch'or n.startswith(('torch.','torch_npu','acl'))for n in sys.modules),'no ML/NPU imports in complete metadata-read cold gate')
    for r in originals.values():C.checked(r)
    output=Path(a.output);C.need(output==Path(v['actual_probe_root'])/'HANDOFF-COLD.json','sole actual owned CPU probe output')
    result=dict(schema='bole.actual-Devices0-full-channel-handoff-cold/v1',source=sr,stage=stage,evidence_source=v['evidence_source'],original_function_sources=originals,original_functions=['g2_channel.contract','g2_finalize.owned_channel'],all_four_original_files_guest_absent=True,complete_saved_metadata_handoff=True,original_owner_inspection_source_resource_and_mount_assertions_preserved=True,Ref2_inspect_actual_bytes_normalized=True,original_source_and_copies_unchanged=True,Devices=[],Torch_imported=False,actual_live_identity_qualified=False,saved_stopped_capture_only=True,model_ready=False,formal_success=False,NPU=False)
    rr=C.write(output,result);print(json.dumps(dict(result=rr,model_ready=False,NPU=False)));return 0


if __name__=='__main__':raise SystemExit(main())
