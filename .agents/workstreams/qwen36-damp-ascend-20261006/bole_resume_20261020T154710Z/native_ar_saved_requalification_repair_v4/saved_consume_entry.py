"""Devices[] reversible metadata and exact full-mask ABI adapter; arithmetic unchanged."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    p.add_argument('--execute',action='store_true');p.add_argument('--inputs-ref');p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    if not(a.inputs_ref and a.output):p.error('exact metadata ticket and fresh consumer output required')
    sys.dont_write_bytecode=True
    spec=importlib.util.spec_from_file_location('_saved_pair_v2_common',Path(__file__).parent/'saved_common.py')
    B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B);C=B.common()
    ir=json.loads(a.inputs_ref);y=B.source(C,ir)
    C.need(C.ref(__file__)==y['files']['saved_consume_entry.py']and str(a.output)==y['consumer_output_root']and
           os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and
           not list(Path('/dev').glob('davinci[0-9]*')),'actual source-bound Devices[] private reader')
    x,m,on,readset,mapping=B.readset(C,y,installed=True)
    B.verify_derivative(C,y,m)
    sys.path.insert(0,m['root']);C.load(m['files']['pair_contract.py'],'pair_contract')
    old=C.load(x['files']['consume_pair_entry.py'],'_saved_pair_original_metadata_join')
    D=C.load(y['files']['derived_math_consumer.py'],'_saved_pair_exact_metadata_derivative')
    H=C.load(y['files']['http_provenance.py'],'_saved_pair_actual_HTTP_provenance')
    original=D.image_and_common
    C.need(D.run.__globals__ is vars(D)and D.http_tokens.__globals__ is vars(D)and
           not hasattr(D,'_SAVED_METADATA')and not hasattr(D,'_http_provenance'),'fresh owned derivative namespace')
    def common(pair,ar,on,model):return old.metadata_join(C,x,pair,ar,on,model)
    def provenance(PC,source,bundle,value,schema,header,frozen,ticket):
        C.need(ticket is y and C.ref(PC.__file__)==m['files']['pair_contract.py'],'same exact original pair contract')
        return H.validate(C,x,m,y,source,bundle,value,schema,header,frozen)
    D.image_and_common=common;D._SAVED_METADATA=y;D._http_provenance=provenance
    try:
        import torch
        controls=C.load(y['files']['mask_controls.py'],'_saved_v4_actual_CPU_mask_controls')
        control=controls.run(torch,C,y['files']['derived_math_consumer.py'])
        C.write(a.output/'NATIVE-MASK-CONTROLS.json',control)
        result=D.run(torch,x['AR_source'],y['actual_saved_refs']['PAIR-INPUTS.json'],a.output)
        C.need(result['bounded_pair_pass']is False and result['matched_common_plugin_effects_gate_pending']is True,
               'metadata-only repair cannot promote pending common effects')
    finally:
        C.need(D.image_and_common is common and D._SAVED_METADATA is y and D._http_provenance is provenance,
               'no foreign namespace mutation during independent reader')
        D.image_and_common=original;del D._SAVED_METADATA;del D._http_provenance
        C.need(D.image_and_common is original,'exact original function object inverse')
    C.write(a.output/'METADATA_ADAPTATION.json',dict(schema='bole.saved-pair-mask-ABI-adaptation/v4',inputs=ir,
        source=x['AR_source'],original_consumer=m['files']['consume_pair.py'],
        derivative=y['files']['derived_math_consumer.py'],delta=y['files']['CONSUMER_METADATA_DELTA.json'],
        full_byte_inverse_verified=True,HTTP_receipts_unmodified=True,missing_inputs_ref_synthesized=False,
        original_math_and_thresholds_unchanged=True,original_full_G1_consumer_retained=True,
        mask_ABI_full2048_guard_changed=True,actual_completed_mask_metadata=y['actual_mask_metadata_refs']['RESULT.json'],
        CPU_guard_controls=C.ref(a.output/'NATIVE-MASK-CONTROLS.json'),all128_actual_frames_required=True,
        attribution=C.ref(a.output/'ATTRIBUTION.json'),common_effects_pending=True,formal_success=False))
    return 0


if __name__=='__main__':raise SystemExit(main())
