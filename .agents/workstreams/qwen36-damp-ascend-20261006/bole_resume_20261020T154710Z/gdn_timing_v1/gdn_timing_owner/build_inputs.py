"""Default-OFF stdlib source preparation only; creates NO device admission."""
import argparse
import importlib.util
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument('--execute', action='store_true'); p.add_argument('--source-dir', type=Path)
    p.add_argument('--timing-dir', type=Path); p.add_argument('--baseline-ref'); p.add_argument('--audit-ref')
    p.add_argument('--runtime-host-evidence'); p.add_argument('--name'); p.add_argument('--reader-name')
    p.add_argument('--output', type=Path); a = p.parse_args()
    if not a.execute:
        print(json.dumps(dict(enabled=False, prepared_only=True, NPU=False, tensor_runtime_imported=False))); return 0
    if not all((a.source_dir, a.timing_dir, a.baseline_ref, a.audit_ref, a.runtime_host_evidence,
                a.name, a.reader_name, a.output)):
        p.error('all explicit absolute prepared source paths and exact existing evidence refs required')
    source = a.source_dir
    if source != Path(__file__).resolve().parent:
        p.error('new isolated source leaf must contain this reviewed generator')
    spec = importlib.util.spec_from_file_location('_bole_prepare_timing_owner', str(source/'timing_owner_common.py'))
    C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
    audit_ref = json.loads(a.audit_ref); audit = C.obj(audit_ref)
    m = dict(schema='bole.gdn3-warmed-timing-manifest/v1',
        files={k: C.ref(a.timing_dir/k) for k in C.PINNED_TIMING},
        replay_manifest=audit['manifest'], replay_result=audit['replay'],
        replay_independent=audit['independent'], replay_release=audit['release'],
        runtime_sources=C.runtime_refs(), admission=None, configuration=C.CONFIG)
    x = dict(schema='bole.gdn3-timing-owner-inputs/v1', authority='MAIN',
        files={k: C.ref(source/k) for k in C.FILES}, baseline_owner=json.loads(a.baseline_ref),
        replay_audit=audit_ref, timing_template=m, runtime_host_evidence=json.loads(a.runtime_host_evidence),
        phase_seconds=C.PHASE, cleanup_seconds=C.CLEANUP, handoff_seconds=C.HANDOFF,
        output_cap_bytes=C.CAP, image=C.IMAGE, name=a.name, reader_name=a.reader_name)
    C.need(a.output.is_absolute() and not a.output.exists() and
           not any(z.is_symlink() for z in (a.output, *a.output.parents)), 'new ordinary INPUTS file')
    C.prior_chain(x, installed=False)
    result = C.write(a.output, x)
    print(json.dumps(dict(inputs=result, prepared_only=True, admission_created=False,
                          NPU=False, timing_complete=False, formal_success=False))); return 0


if __name__ == '__main__':
    raise SystemExit(main())
