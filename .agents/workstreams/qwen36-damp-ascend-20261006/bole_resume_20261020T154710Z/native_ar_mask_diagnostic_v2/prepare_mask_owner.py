"""Default-OFF source-only new saved-mask diagnostic owner assembly."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--prepare',action='store_true')
    p.add_argument('--new-control-root',type=Path);p.add_argument('--new-output-root',type=Path)
    p.add_argument('--mask-source-evidence-ref');a=p.parse_args()
    if not a.prepare:print('{"enabled":false,"NPU":false,"mask_semantics_qualified":false}');return 0
    if not(a.new_control_root and a.new_output_root):p.error('two new ordinary source/output roots required')
    sys.dont_write_bytecode=True;root=Path(__file__).parent
    s=importlib.util.spec_from_file_location('_mask_prepare',root/'diag_common.py');D=importlib.util.module_from_spec(s);s.loader.exec_module(D);C=D.common()
    failure=C.obj(C.ref(root/'ACTUAL_V3_FAILURE_REFS.json'))
    owner,oldy,_,x,_,_=D.prior(C,dict(actual_v3_failure_refs=failure))
    new,out=a.new_control_root,a.new_output_root
    C.need(new.is_absolute()and new.parent.is_dir()and not new.exists()and not out.exists()and new!=out and
        not any(p.is_symlink()for p in(new,*new.parents,out,*out.parents)),'new ordinary control and output leaves')
    new.mkdir(mode=0o700)
    for name in D.FILES:shutil.copyfile(root/name,new/name)
    y=dict(schema='bole.native-ar-mask-diagnostic-inputs/v1',actual_v3_failure_refs=failure,
        actual_original_CPU_profile_refs=C.obj(C.ref(new/'ACTUAL_CPU_PROFILE_REFS.json')),
        original_saved_inputs=owner['inputs'],AR_source=x['AR_source'],authority=x['authority'],
        mask_source_evidence_ref=json.loads(a.mask_source_evidence_ref)if a.mask_source_evidence_ref else C.ref(new/'MASK_SOURCE_EVIDENCE.json'),
        output_root=str(out),consumer_output_root=str(out/'cpu-consumer'),MAIN_lock=D.LOCK,
        files={name:C.ref(new/name)for name in D.FILES},default_enabled=False,prepared_only=True,
        model_reexecution_permitted=False,mathematical_reader_execution_permitted=False,NPU=False,formal_success=False)
    ir=C.write(new/'INPUTS.json',y);D.source(C,ir);_,_,_,refs,_=D.readset(C,y)
    print(json.dumps(dict(inputs=ir,readset_count=len(refs),NPU=False,resources_admitted=False,
        diagnostic_only=True,mask_semantics_qualified=False,formal_success=False)),flush=True);return 0

if __name__=='__main__':raise SystemExit(main())
