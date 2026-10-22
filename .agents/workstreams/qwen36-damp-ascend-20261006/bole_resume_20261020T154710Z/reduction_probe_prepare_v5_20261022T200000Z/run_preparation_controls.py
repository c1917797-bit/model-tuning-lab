"""Default-OFF bounded source-only regression. Does not create containers or use NPUs."""
import argparse
import hashlib
import json
import os
import pathlib
import resource
import subprocess
import sys
import time

HERE=pathlib.Path(__file__).resolve().parent


def ref(path):
    path=pathlib.Path(path)
    raw=path.read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def write(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,sort_keys=True,allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())
    return ref(path)


def main():
    parser=argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--output',type=pathlib.Path)
    args=parser.parse_args()
    if not args.execute:
        print('{"enabled":false,"NPU":false,"source_frozen":false}')
        return 0
    out=args.output
    if out is None or not out.is_absolute() or out.parent!=HERE or out.exists():
        parser.error('fresh direct child output under this preparation required')
    for key,cap in ((resource.RLIMIT_AS,512*2**20),(resource.RLIMIT_CPU,90),(resource.RLIMIT_FSIZE,8*2**20),(resource.RLIMIT_CORE,0)):
        soft,hard=resource.getrlimit(key)
        value=cap if hard==resource.RLIM_INFINITY else min(cap,hard)
        resource.setrlimit(key,(value,value))
    out.mkdir(mode=0o700)
    os.umask(0o077)
    source=[ref(p) for p in sorted(HERE.glob('*.py'))]
    source += [ref(p) for arm in ('ON','OFF') for p in sorted((HERE/arm).glob('*.py'))]
    write(out/'SOURCE_BEFORE.json',source)
    start=time.monotonic()
    jobs=[('controls',[sys.executable,'-B',str(HERE/'test_reduction_preparation.py'),'-v'])]
    jobs += [('audit_contract',[sys.executable,'-I','-B',str(HERE/'test_auditor_launcher_contract.py'),'-v'])]
    jobs += [('render_'+arm,[sys.executable,'-I','-B',str(HERE/'render_preparation.py'),'--execute','--arm',arm]) for arm in ('ON','OFF')]
    results=[];error=None
    for name,argv in jobs:
        so=out/(name+'.stdout');se=out/(name+'.stderr')
        try:
            with so.open('xb') as stdout,se.open('xb') as stderr:
                child=subprocess.run(argv,cwd=HERE,stdout=stdout,stderr=stderr,timeout=30,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
            row=dict(name=name,argv=argv,exit_code=child.returncode,stdout=ref(so),stderr=ref(se))
            results.append(row)
            if child.returncode:raise ValueError('source control child failed: '+name)
        except BaseException as exc:
            error=repr(exc);break
    after=[ref(r['path']) for r in source]
    passed=error is None and source==after and len(results)==4
    rr=write(out/'RESULT.json',dict(schema='bole.reduction-source-controls/v1',passed=passed,error=error,
        source_before=source,source_after=after,stages=results,elapsed_s=time.monotonic()-start,
        source_frozen=False,main_review_pending=True,NPU=False,same_image_verified=False,
        original_twenty_controls_replaced=False,numerical_qualified=False,formal_performance=False))
    print(json.dumps(dict(result=rr,passed=passed,NPU=False,source_frozen=False)))
    return 0 if passed else 1

if __name__=='__main__':
    raise SystemExit(main())
