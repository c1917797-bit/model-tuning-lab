"""Independent continuation source auditor; exact recorded command operand.

The numerical gates and original budgets remain unchanged. This new auditor
has its own exact Ref, exclusive output, and separately authorized finite batch.
It performs source validation only and creates no execution authority.
"""
import argparse
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

WS = Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
PREP = WS/'boundary_source_audit_v5_textonly_20261022T171000Z'
ROOT = WS/'bound-boundary-ON-v4-textonly_20261022T171000Z'
OUT = Path('/opt/host/vnf/austinov/run-bole-boundary-source-audit-v5-textonly_20261022T171000Z')


def need(value, why):
    if not value:
        raise ValueError(why)


def write(path, value):
    body = (json.dumps(value, sort_keys=True, allow_nan=False)+'\n').encode()
    with path.open('xb') as stream:
        stream.write(body); stream.flush(); os.fsync(stream.fileno())
    return dict(path=str(path), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())


def main():
    parser=argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--source-ref', required=True)
    parser.add_argument('--audit-program-ref', type=json.loads, required=True)
    args=parser.parse_args()
    recorded_argument=args.source_ref
    args.source_ref=json.loads(recorded_argument)
    program=Path(__file__).absolute()
    need(type(args.audit_program_ref) is dict and set(args.audit_program_ref)=={'path','bytes','sha256'} and
         args.audit_program_ref['path']==str(program) and not any(p.is_symlink() for p in (program,*program.parents)) and
         program.is_file() and 0<program.stat().st_size<=1024*1024,
         'exact ordinary independent auditor identity')
    program_bytes=program.read_bytes()
    need(args.audit_program_ref==dict(path=str(program),bytes=len(program_bytes),sha256=hashlib.sha256(program_bytes).hexdigest()),
         'whole independent auditor Ref before validation')
    need(Path(__file__).resolve()==PREP/'audit_boundary_source_v5.py' and
         Path(args.source_ref['path'])==ROOT/'SOURCE_BOUND.json' and not OUT.exists(),
         'fresh exact source-audit identity')
    need(1792689000<=time.time() and time.time()+3780<1792710600,
         'unchanged complete phase must fit the separately authorized finite continuation')
    OUT.mkdir(mode=0o700); os.umask(0o077)
    for key,cap in ((resource.RLIMIT_AS,512*2**20),(resource.RLIMIT_CPU,150),
                    (resource.RLIMIT_FSIZE,16*2**20),(resource.RLIMIT_CORE,0)):
        _,hard=resource.getrlimit(key); value=cap if hard==resource.RLIM_INFINITY else min(cap,hard)
        resource.setrlimit(key,(value,value))
    started=time.monotonic(); error=None; proof=None; rr=None
    try:
        # This executable is already a separate -I/-B process. No preparation
        # modules have been imported before this one exact new root is selected.
        sys.path.insert(0,str(ROOT))
        import sourceio as C
        import performance_validate as V
        m=C.obj(args.source_ref)
        need(C.ref(__file__)==args.audit_program_ref, 'actual independent v5 text-only auditor exact source')
        original_auditor=dict(path=str(WS/'boundary_probe_prepare_v1_20261022/audit_boundary_source.py'),
            bytes=4631,sha256='318abb0246fce440ba877c8428cbcc1dd90caea7846be76a884c5e26cb4b5533')
        need(original_auditor in m['dependencies'], 'original v1 auditor remains in unchanged runtime readset')
        C.checked(original_auditor)
        commands=C.obj(C.ref(ROOT/'COMMANDS.json'))
        need(type(commands['model']) is list and type(commands['CPU']) is list and
             commands['model'].count('--source-ref')==1 and commands['CPU'].count('--source-ref')==1,
             'one literal source operand in each bound MODEL and CPU command')
        actual_argument=commands['model'][commands['model'].index('--source-ref')+1]
        need(recorded_argument==actual_argument and commands['bound_source']==args.source_ref,
             'literal source argument exactly as immutable actual MODEL command')
        cpu_argument=commands['CPU'][commands['CPU'].index('--source-ref')+1]
        need(recorded_argument==cpu_argument, 'MODEL and CPU retain identical recorded source argument')
        proof=V.validate(args.source_ref)
        need(proof['source']==args.source_ref and proof['source_validated'] is True and
             proof['tests_executed'] is False and proof['NPU'] is False and
             proof['actual_NPU_two_generation_qualified'] is False and
             len(proof['tests'])==20, 'complete unchanged original source proof only')
        seen={}
        for reference in proof['readset']:
            C.checked(reference)
            need(reference['path'] not in seen or seen[reference['path']]==reference, 'unique exact full readset')
            seen[reference['path']]=reference
        write(OUT/'VALIDATOR_PROOF.json',proof)
        # Reopen exactly the host's actual binding/command/dependency readset.
        import bind_model,command_contract
        actual={r['path']:r for r in bind_model.readset(args.source_ref)+m['dependencies']+command_contract.validate(C,args.source_ref,m)}
        need(actual==seen, 'source proof and actual host before/after readset are exactly the same set')
        for reference in seen.values():
            C.checked(reference)
        C.checked(args.audit_program_ref)
        need(time.monotonic()-started<180, 'bounded whole source audit')
        rr=write(OUT/'SOURCE_AUDIT.json',dict(schema='bole.boundary-source-admission/v1',
            source=args.source_ref,source_validated=True,readset=list(seen.values()),
            original_inputs_unchanged=True,host_readset_exact=True,tests_executed=False,
            audit_program_ref=args.audit_program_ref,audit_program_unchanged=True,
            original_audit_source=original_auditor,recorded_source_argument=recorded_argument,
            original_twenty_controls=list(proof['tests']),NPU=False,paired_gate_pass=False,
            numerical_qualified=False,performance_admitted=False,formal_performance=False,
            hard_cutoff=1792710600,historical_report_cutoff=1792672721,
            old_window_extended=False,elapsed_s=time.monotonic()-started))
    except BaseException as exc:
        error=repr(exc)
        import traceback
        write(OUT/'FAILURE.json',dict(error=error,traceback=traceback.format_exc(),source=args.source_ref,
             source_only=True,NPU=False,performance_admitted=False))
    result=write(OUT/'RESULT.json',dict(schema='bole.boundary-source-audit-execution/v1',
        source=args.source_ref,error=error,audit=rr,status='PASS_SOURCE_ONLY'if error is None else'FAIL_SOURCE_ONLY',
        source_only=True,NPU=False,performance_admitted=False,elapsed_s=time.monotonic()-started))
    print(json.dumps(dict(result=result,audit=rr,error=error,source_only=True,NPU=False)))
    return 0 if error is None else 3


if __name__=='__main__':
    raise SystemExit(main())
