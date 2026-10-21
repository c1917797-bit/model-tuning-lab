"""DefaultOFF finite saved-native-FA diagnostic source assembly; no admission."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--prepare',action='store_true')
    p.add_argument('--new-control-root',type=Path);p.add_argument('--new-output-root',type=Path);a=p.parse_args()
    if not a.prepare:print('{"enabled":false,"NPU":false,"formal_success":false}');return 0
    if not(a.new_control_root and a.new_output_root):p.error('two new independent source/output leaves required')
    sys.dont_write_bytecode=True;root=Path(__file__).parent
    s=importlib.util.spec_from_file_location('_numeric_packet_prepare',root/'numeric_common.py');D=importlib.util.module_from_spec(s);s.loader.exec_module(D);C=D.common()
    refs=C.obj(C.ref(root/'ACTUAL_NUMERIC_V4_REFS.json'));old=C.obj(refs['INPUTS.json'])
    new,out=a.new_control_root,a.new_output_root
    C.need(new.is_absolute()and new.parent.is_dir()and not new.exists()and not out.exists()and new!=out and
        not any(v.is_symlink()for v in(new,*new.parents,out,*out.parents)),'fresh ordinary control/output leaves')
    new.mkdir(mode=0o700)
    for name in D.FILES:shutil.copyfile(root/name,new/name)
    original=C.ref(root/'numeric_common.py');prepared=C.ref(new/'numeric_common.py')
    C.need(prepared['path']!=original['path']and(prepared['bytes'],prepared['sha256'])==(original['bytes'],original['sha256']),
        'complete exact helper at prepared module path')
    E=C.load(prepared,'_numeric_prepared_control')
    y=dict(schema='bole.native-ar-numeric-diagnostic-inputs/v1',actual_numeric_v4_refs=refs,
        original_numeric_inputs=refs['INPUTS.json'],AR_source=old['AR_source'],authority=old['authority'],
        output_root=str(out),consumer_output_root=str(out/'cpu-consumer'),MAIN_lock=D.LOCK,
        files={n:C.ref(new/n)for n in D.FILES},default_enabled=False,prepared_only=True,
        NPU=False,formal_success=False)
    ir=C.write(new/'INPUTS.json',y);E.source(C,ir);_,_,_,rs,_=E.readset(C,y)
    print(json.dumps(dict(inputs=ir,readset_count=len(rs),resources_admitted=False,NPU=False,formal_success=False)));return 0

if __name__=='__main__':raise SystemExit(main())
