"""Default-OFF local assembly after exact actual stopped v5; never admits work."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--new-control-root',type=Path);p.add_argument('--host-record-name')
    a=p.parse_args()
    if not a.execute:print('{"enabled":false,"prepared_only":true,"NPU":false}');return 0
    if not(a.new_control_root and a.host_record_name):p.error('new control root and unique CPU-REQUALIFICATION-* host record name required')
    sys.dont_write_bytecode=True;root=Path(__file__).resolve().parent
    spec=importlib.util.spec_from_file_location('_saved_prepare_common',root/'saved_common.py')
    B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B);C=B.common()
    actual=C.obj(C.ref(root/'ACTUAL_SAVED_REFS.json'));objects,x,m=B.prior(C,actual)
    C.need(a.new_control_root.is_absolute()and not a.new_control_root.exists()and a.new_control_root.parent.is_dir()and
           not any(p.is_symlink()for p in(a.new_control_root,*a.new_control_root.parents)), 'new ordinary source leaf')
    C.need(a.host_record_name.startswith('CPU-REQUALIFICATION-')and '/'not in a.host_record_name and
           '\\'not in a.host_record_name and len(a.host_record_name)<=80,'unique bounded host record basename')
    record=Path(x['output_root'])/a.host_record_name
    C.need(not record.exists()and not Path(m['pair_consumer_output_root']).exists(),'fresh exact declared CPU/host record leaves')
    a.new_control_root.mkdir(mode=0o700)
    for name in B.FILES:shutil.copyfile(root/name,a.new_control_root/name)
    y=dict(schema='bole.native-ar-saved-requalification-inputs/v1',actual_saved_refs=actual,
        original_owner_inputs=actual['OWNER_INPUTS.json'],saved_producer_result=actual['RESULT.json'],
        AR_source=x['AR_source'],authority=x['authority'],output_root=x['output_root'],
        consumer_output_root=m['pair_consumer_output_root'],host_record_root=str(record),MAIN_lock=B.LOCK,
        files={n:C.ref(a.new_control_root/n)for n in B.FILES},default_enabled=False,prepared_only=True,
        model_reexecution_permitted=False,NPU=False,formal_success=False)
    _,_,_,refs,mapping=B.readset(C,y,installed=False)
    result=C.write(a.new_control_root/'INPUTS.json',y)
    print(json.dumps(dict(inputs=result,readset_count=len(refs),mapping=mapping,prepared_only=True,NPU=False,
        original_producer_failed=True,independent_numeric_qualification=False)));return 0


if __name__=='__main__':raise SystemExit(main())
