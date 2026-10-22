"""Default-OFF pure source rendering of the next bound runtime. Never freezes or launches."""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import sys
import types

HERE=pathlib.Path(__file__).resolve().parent


def pin(path):
    raw=pathlib.Path(path).read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def main():
    parser=argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--arm',choices=('ON','OFF'))
    args=parser.parse_args()
    if not args.execute:
        print('{"enabled":false,"source_frozen":false,"NPU":false}')
        return 0
    if args.arm is None:parser.error('--arm required with --execute')
    prep=HERE/args.arm
    sys.path.insert(0,str(prep))
    import prepare_boundary as PB
    import boundary_integration as BI
    BI.require_frozen_inputs()
    old=PB.obj(PB.PARENT)
    parent=PB.obj(old['short_parent_source'])
    sys.path.insert(1,old['root'])
    import performance_binding_delta as B
    import prepare_short_gate as P
    assert P.PIN==old['short_parent_source']
    ds=BI.render_short_delta(PB.checked(old['files']['short_binding_delta.py']).read_text())
    D=types.ModuleType('_new_reduction_delta')
    exec(compile(ds,str(prep/'short_binding_delta.py'),'exec'),D.__dict__)
    originals={n:PB.checked(parent['files'][n]).read_text() for n in D.RUNTIME}
    changed=D.runtime(originals)
    changed['contract090.py']=BI.render_text_only_contract(B.bind_outputs(PB.checked(parent['files']['contract090.py']).read_text(),str(PB.OUT)))
    authority=BI.continuation_authority(PB.obj(old['authority_ref']),old['authority_ref'])
    for n in PB.CLOCK_FILES:
        changed[n]=PB.clock(changed.get(n,PB.checked(parent['files'][n]).read_text()),authority)
    changed['performance_software_stages.py']=BI.render_current_software_coordinator(PB.checked(BI.OLD_SOFTWARE_COORDINATOR_REF).read_text())
    pins={n:{k:pin(prep/n)[k] for k in ('bytes','sha256')} for n in PB.HELPERS}
    validator=BI.render_validator(PB.checked(old['files']['performance_validate.py']).read_text(),pins)
    for n,t in {**changed,'short_binding_delta.py':ds,'performance_validate.py':validator}.items():
        compile(t,n,'exec')
    def predicted(n,t):
        raw=t.encode()
        return dict(path=str(PB.ROOT/n),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    print(json.dumps(dict(schema='bole.reduction-unfrozen-render/v1',arm=args.arm,
        source_frozen=False,NPU=False,main_review_pending=True,
        parent=PB.PARENT,helper_refs=[pin(prep/n) for n in PB.HELPERS],
        predicted_runtime_refs={n:predicted(n,t) for n,t in changed.items()},
        predicted_validator=predicted('performance_validate.py',validator),
        predicted_short_delta=predicted('short_binding_delta.py',ds),
        profile=BI.expected_profile(old),authority=authority),sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
