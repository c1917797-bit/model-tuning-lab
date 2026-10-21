"""MAIN source-only actual private025 compile/inverse diagnostic; no admission."""
import argparse
import importlib.util
import json
import marshal
import os
from pathlib import Path
import sys
import time
import traceback


class ExpectedSourceOnlyExit(Exception):pass


def code_detail(actual,expected,S):
    a=actual.__code__;b=expected.__code__
    return dict(actual_globals_is_S=actual.__globals__ is vars(S),actual_filename=a.co_filename,expected_filename=b.co_filename,
        actual_qualname=getattr(a,'co_qualname',a.co_name),expected_qualname=getattr(b,'co_qualname',b.co_name),
        actual_flags=a.co_flags,expected_flags=b.co_flags,whole_marshal_equal=marshal.dumps(a)==marshal.dumps(b),
        actual_marshal_sha256=__import__('hashlib').sha256(marshal.dumps(a)).hexdigest(),
        expected_marshal_sha256=__import__('hashlib').sha256(marshal.dumps(b)).hexdigest(),
        code_fields_different=[name for name in dir(a)if name.startswith('co_')and not callable(getattr(a,name))and getattr(a,name)!=getattr(b,name)])


def main():
    start=time.monotonic();p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    p.add_argument('--probe',action='store_true');p.add_argument('--v1-inputs-ref');p.add_argument('--v2-profile-ref')
    p.add_argument('--unused-output-root',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.probe:print('{"enabled":false,"NPU":false,"resources_admitted":false}');return 0
    if not all((a.v1_inputs_ref,a.v2_profile_ref,a.unused_output_root,a.output)):p.error('exact old input/new profile refs and fresh probe output required')
    if os.environ.get('BOLE_NATIVE_FIA_NAMESPACE_PROBE_ENABLE')!='1':raise ValueError('MAIN explicit source-only namespace probe')
    sys.dont_write_bytecode=True;old=json.loads(a.v1_inputs_ref);profile_ref=json.loads(a.v2_profile_ref)
    s=importlib.util.spec_from_file_location('_fia_probe_original_common',Path(__file__).parent/'ar_owner_common.py')
    C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
    C.need(profile_ref==C.ref(Path(__file__).parent/'singleton_profile.py'),'exact new sibling singleton source')
    y=C.obj(old);R=C.load(y['files']['replay_common.py'],'_fia_probe_v1_source');R.source(C,old);lock=R.held_main_lock(C)
    m,on=C.host_source(y['AR_source'])
    NS=C.load(y['files']['ar_saved_namespace.py'],'_fia_probe_actual_original_namespace')
    V1=C.load(y['files']['singleton_profile.py'],'_fia_probe_v1_singleton')
    V2=C.load(profile_ref,'_fia_probe_v2_singleton')
    C.need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists()and
        a.unused_output_root.is_absolute()and not a.unused_output_root.exists(),'new exact source-only report and unused namespace leaf; never mkdir/admit')
    path_object=sys.path;path_values=list(sys.path);primary=None;rows={};v1_failure=None;entered_v2=False;forced_exception=False
    original_attrs={};methods={};D=None;E=None;d_before={};e_before=None;controller=None;S=None
    manager=NS.open_namespace(C,dict(authority=y['authority'],output_root=str(a.unused_output_root)),on)
    try:
        with manager as(c,S,H,namespace):
            # Inspect this genuine contextmanager's strong original object refs,
            # not reconstructed strings or a claim based on source syntax.
            locals_=manager.gen.gi_frame.f_locals
            D=locals_['D'];E=locals_['E'];d_before=dict(locals_['original']);e_before=locals_['old_external']
            original_attrs={name:getattr(S,name)for name in('device_map','environment','create_argv','validate_inspect')}
            controller=S.Controller;methods={name:getattr(controller,name)for name in('observe','resources','remaining','create_owned','inspect','cleanup')}
            body=Path(S.__file__).read_bytes()
            previous1,_,_=V1.derive_external_singleton(E,body,S.__file__,dict(vars(S),_EXTERNAL=S._EXTERNAL))
            previous2,_,_=V2.derive_external_singleton(E,body,S.__file__,dict(vars(S),_EXTERNAL=S._EXTERNAL))
            rows={name:dict(v1=code_detail(getattr(S,name),previous1[name],S),v2=code_detail(getattr(S,name),previous2[name],S))
                for name in('device_map','create_argv','validate_inspect')}
            try:
                with V1.install(C,c,S,H,on):raise AssertionError('old real guard unexpectedly passed')
            except ValueError as error:v1_failure=repr(error)
            C.need(v1_failure is not None and 'device_map'in v1_failure and
                all(getattr(S,n)is value for n,value in original_attrs.items()),'actual v1 rejection reproduced before any profile mutation')
            C.need(all(v['v2']['actual_globals_is_S']and v['v2']['whole_marshal_equal']for v in rows.values()),
                'new full original compile + actual two-function readonly pipeline matches all3 whole code objects')
            with V2.install(C,c,S,H,on)as proof:
                entered_v2=True
                C.need(S.PHYSICAL==(4,5,6,7)and len(S.device_map())==4 and
                    S.Controller is controller and all(getattr(controller,n)is v for n,v in methods.items()),
                    'actual source-only singleton scope and unchanged original controller method objects')
                # Exercise BOTH real finally paths with one unique deliberate
                # exception, without constructing a controller or touching NPU.
                raise ExpectedSourceOnlyExit('real singleton then namespace finally identity probe')
    except ExpectedSourceOnlyExit:forced_exception=True
    except BaseException as error:primary=dict(error=repr(error),traceback=traceback.format_exc())
    profile_inverse=bool(S is not None and original_attrs and all(getattr(S,n)is v for n,v in original_attrs.items())and
        S.Controller is controller and all(getattr(controller,n)is v for n,v in methods.items()))
    namespace_inverse=bool(D is not None and d_before and all(getattr(D,n)is v for n,v in d_before.items())and
        E.OUT is e_before and sys.path is path_object and sys.path==path_values)
    passed=primary is None and entered_v2 and forced_exception and profile_inverse and namespace_inverse and time.monotonic()-start<=120
    value=dict(schema='bole.native-AR-FIA-actual-source-only-namespace-compile-probe/v2',v1_inputs=old,new_profile=profile_ref,
        probe_source=C.ref(__file__),actual_host_python=sys.version,actual_host_argv=sys.argv,MAIN_lock=lock,functions=rows,
        v1_actual_guard_failure=v1_failure,v2_actual_profile_entered=entered_v2,unique_exception_exercised=forced_exception,
        singleton_finally_restored_original_objects=profile_inverse,namespace_finally_restored_original_objects=namespace_inverse,
        unused_output_root=str(a.unused_output_root),unused_output_root_absent=not a.unused_output_root.exists(),
        elapsed=time.monotonic()-start,source_only_probe_pass=passed,primary=primary,controller_constructed=False,
        resources_admitted=False,container_created=False,NPU=False,whole_host_readset_recomputed=False,
        mathematical_qualification=False,formal_success=False)
    C.write(a.output,value);print(json.dumps(dict(output=C.ref(a.output),source_only_probe_pass=passed,NPU=False)))
    return 0 if passed else 3

if __name__=='__main__':raise SystemExit(main())
