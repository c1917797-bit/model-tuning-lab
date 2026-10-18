"""One Devices[] CPU child; one original raw load, three fixed diagnostic cases."""
import argparse
import gc
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import owner as C
import plan as R


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--source-ref')
    parser.add_argument('--plan-ref')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.execute:
        print('{"enabled":false,"NPU":false}')
        return 0
    C.need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD') == '0' and
           os.environ.get('ASCEND_RT_VISIBLE_DEVICES') == '' and
           os.environ.get('ASCEND_VISIBLE_DEVICES') == '' and
           not list(Path('/dev').glob('davinci*')), 'same-image Devices[] CPU boundary')
    source_ref = json.loads(args.source_ref)
    manifest = C.obj(source_ref)
    C.need(manifest['root'] == str(HERE) and
           manifest['schema'] == 'bole.fa-probability-quantization-source/v1' and
           manifest['files']['recover.py'] == C.ref(__file__), 'actual immutable source and entry')
    for reference in manifest['files'].values():
        C.checked(reference)
    C.need(json.loads(args.plan_ref) == manifest['recovery_plan_ref'] and
           args.output == Path(manifest['output_root'])/'consumer', 'exact plan and consumer leaf')
    proof = R.consume(C, manifest['recovery_plan_ref'])
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern='test_probe.py',
                                               top_level_dir=str(HERE))
    control = unittest.TextTestRunner().run(suite)
    C.need(control.wasSuccessful() and control.testsRun == 12 and not control.skipped,
           'all twelve same-image arithmetic controls, no skip')
    C.write(args.output/'SOFTWARE.json', dict(tests=12, passed=True, NPU=False))
    import torch
    import probe
    C.need(C.ref(probe.__file__) == manifest['files']['probe.py'], 'exact delivered arithmetic source')
    torch.set_num_threads(1)
    blob = torch.load(C.checked(R.RAW), map_location='cpu', weights_only=False)
    C.need(blob['schema'] == 'bole.model-diagnostic-primitives/v1' and
           blob['logical_tensor_bytes'] <= 2**30, 'original raw serialization/budget')
    result = probe.run_retained(torch, blob['payload'], proof['plan'], proof['previous'])
    result.update(source=source_ref, plan=manifest['recovery_plan_ref'],
                  original_raw=R.RAW, original_source=R.SOURCE,
                  original_rank_report=R.RANK_REPORT, previous_diagnostic=R.PREVIOUS,
                  script=manifest['files']['probe.py'])
    encoded = (json.dumps(result, sort_keys=True, allow_nan=False)+'\n').encode()
    C.need(len(encoded) <= 16*2**20, 'scalar-only diagnostic output at most16MiB')
    destination = args.output/'PROBE.json'
    with destination.open('xb') as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    del blob
    gc.collect()
    for reference in proof['readset']:
        C.checked(reference)
    attribution = dict(schema='bole.fa-probability-quantization-attribution/v1',
                       source=source_ref, plan=manifest['recovery_plan_ref'],
                       probe=C.ref(destination), diagnostic_complete=True, cases_completed=3,
                       original_numeric_failures_unchanged=True, kernel_path_proven=False,
                       qualified=False, original_owner_pass=False, lifecycle_qualified=False, NPU=False)
    C.write(args.output/'ATTRIBUTION.json', attribution)
    print(json.dumps(C.ref(args.output/'ATTRIBUTION.json')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
