"""Default-OFF local assembly after exact actual stopped v5; never admits work."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--new-control-root',type=Path);p.add_argument('--new-output-root',type=Path)
    a=p.parse_args()
    if not a.execute:print('{"enabled":false,"prepared_only":true,"NPU":false}');return 0
    if not(a.new_control_root and a.new_output_root):p.error('new control and new independent nativeAR CPU output roots required')
    sys.dont_write_bytecode=True;root=Path(__file__).resolve().parent
    spec=importlib.util.spec_from_file_location('_saved_prepare_common',root/'saved_common.py')
    B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B);C=B.common()
    actual=C.obj(C.ref(root/'ACTUAL_SAVED_REFS.json'));objects,x,m=B.prior(C,actual)
    C.need(a.new_control_root.is_absolute()and not a.new_control_root.exists()and a.new_control_root.parent.is_dir()and
           not any(p.is_symlink()for p in(a.new_control_root,*a.new_control_root.parents)), 'new ordinary source leaf')
    C.need(a.new_output_root.is_absolute()and a.new_output_root.parent==Path('/opt/host/vnf/austinov')and
           a.new_output_root.name.startswith('run-bole-native-ar-')and not a.new_output_root.exists()and
           not any(p.is_symlink()for p in(a.new_output_root,*a.new_output_root.parents))and
           a.new_output_root!=a.new_control_root,'fresh independent source-bound output, no reuse of failed CPU leaf')
    record=a.new_output_root
    a.new_control_root.mkdir(mode=0o700)
    for name in B.FILES:shutil.copyfile(root/name,a.new_control_root/name)
    y=dict(schema='bole.native-ar-saved-requalification-inputs/v3',actual_saved_refs=actual,
        actual_prior_cpu_failure_refs=C.obj(C.ref(root/'ACTUAL_FAILURE_REFS.json')),
        actual_second_cpu_failure_refs=C.obj(C.ref(root/'ACTUAL_V2_FAILURE_REFS.json')),
        original_owner_inputs=actual['OWNER_INPUTS.json'],saved_producer_result=actual['RESULT.json'],
        AR_source=x['AR_source'],authority=x['authority'],output_root=str(a.new_output_root),
        consumer_output_root=str(a.new_output_root/'cpu-consumer'),host_record_root=str(record),MAIN_lock=B.LOCK,
        files={n:C.ref(a.new_control_root/n)for n in B.FILES},default_enabled=False,prepared_only=True,
        model_reexecution_permitted=False,NPU=False,formal_success=False)
    _,_,_,refs,mapping=B.readset(C,y,installed=False)
    result=C.write(a.new_control_root/'INPUTS.json',y)
    print(json.dumps(dict(inputs=result,readset_count=len(refs),mapping=mapping,prepared_only=True,NPU=False,
        original_producer_failed=True,independent_numeric_qualification=False)));return 0


if __name__=='__main__':raise SystemExit(main())
