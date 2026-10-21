"""DefaultOFF source-only assembly of the finite all128×two-filler FIA replay."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--prepare',action='store_true')
    p.add_argument('--new-control-root',type=Path);p.add_argument('--new-output-root',type=Path)
    p.add_argument('--extra-copy-refs-json',default='[]');a=p.parse_args()
    if not a.prepare:print('{"enabled":false,"NPU":false,"formal_success":false}');return 0
    if not(a.new_control_root and a.new_output_root):p.error('two fresh source/output leaves required')
    sys.dont_write_bytecode=True;root=Path(__file__).parent
    s=importlib.util.spec_from_file_location('_fia_packet_prepare',root/'replay_common.py');R=importlib.util.module_from_spec(s);s.loader.exec_module(R);C=R.common()
    refs=C.obj(C.ref(root/'ACTUAL_FSUM_REFS.json'));old=C.obj(refs['INPUTS.json']);new,out=a.new_control_root,a.new_output_root
    C.need(new.is_absolute()and new.parent.is_dir()and not new.exists()and not out.exists()and new!=out and
        not any(p.is_symlink()for p in(new,*new.parents,out,*out.parents)),'new ordinary source/output paths')
    new.mkdir(mode=0o700)
    for name in R.FILES:shutil.copyfile(root/name,new/name)
    before=C.ref(root/'replay_common.py');after=C.ref(new/'replay_common.py')
    C.need(before['path']!=after['path']and(before['bytes'],before['sha256'])==(after['bytes'],after['sha256']),
        'whole copied helper at actual prepared full path')
    E=C.load(after,'_fia_prepared_control')
    y=dict(schema='bole.native-ar-FIA-replay-inputs/v1',actual_fsum_refs=refs,original_fsum_inputs=refs['INPUTS.json'],
        AR_source=old['AR_source'],authority=old['authority'],output_root=str(out),MAIN_lock=R.LOCK,
        files={n:C.ref(new/n)for n in R.FILES},extra_copy_refs=json.loads(a.extra_copy_refs_json),
        phase_seconds=3600,cleanup_seconds=180,metadata_cap_seconds=600,replay_cap_seconds=900,consumer_cap_seconds=900,
        preregistered_fillers=['all_zero','finite_alternating'],frames=128,actual_operator_calls_required=256,
        physical=[4],logical=[0],unused_arena_reconstruction=True,default_enabled=False,prepared_only=True,
        precision_change=False,original_numerical_failure_preserved=True,formal_success=False)
    ir=C.write(new/'INPUTS.json',y);E.source(C,ir);_,_,_,readset,_=E.readset(C,y)
    print(json.dumps(dict(inputs=ir,readset_count=len(readset),resources_admitted=False,NPU=False,formal_success=False)));return 0

if __name__=='__main__':raise SystemExit(main())
