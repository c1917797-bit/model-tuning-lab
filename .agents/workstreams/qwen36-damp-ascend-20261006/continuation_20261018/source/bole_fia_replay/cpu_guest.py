"""Actual Devices[] same-source controls, installed FIA ABI and saved inputs.

This child does not select a device or execute an NPU operator. The original
complete CPU owner supplies the image, CANN environment and bounded resources.
"""
import argparse
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C

STAGE_SCHEMA = 'bole.fia-replay-CPU-stage/v1'
CONTROLS_SCHEMA = 'bole.fia-replay-software-controls/v1'
CONTROL_NAMES = {'test_owner.py', 'test_probe.py'}


def bootstrap(manifest):
    helper = C.load(manifest['cann_helper_ref'], '_fia_replay_real_CANN')
    root = '/usr/local/Ascend/cann-9.1.0/python/site-packages'
    C.need(helper.ROOT == root, 'actual CANN source path')
    helper.cached()
    helper.file_identity('/usr/local/Ascend/cann-9.1.0/set_env.sh', 5112,
                         'de50f1bf5b960f8305792ef407e3bfc3fc1b6d82931d0feae39ac4c965690aaf')
    direct = helper.spec_identity(importlib.machinery.PathFinder.find_spec('acl', [root]))
    sys.path.insert(0, root)
    C.need(helper.spec_identity(importlib.util.find_spec('acl')) == direct,
           'actual ACL extension not fake module')
    return direct


def cpu_guard():
    C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES') == ''
           and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD') == '0'
           and not list(Path('/dev').glob('davinci*')), 'actual Devices[] CPU guard')
    for path in Path('/proc/self/fd').iterdir():
        try:
            target = os.readlink(path)
        except FileNotFoundError:
            continue
        C.need(not any(token in target for token in ('davinci', 'devmm_svm', 'hisi_hdc')),
               'actual CPU preflight has no device FDs')


def control_count(stderr):
    rows = re.findall(r'^Ran ([0-9]+) tests? in [0-9.eE+-]+s$', stderr, re.MULTILINE)
    C.need(len(rows) == 1 and int(rows[0]) > 0, 'one complete actual unittest execution count')
    C.need(stderr.strip().splitlines()[-1] == 'OK', 'all original controls pass with no skips')
    return int(rows[0])


def software_controls(source_ref, manifest, output):
    counts = manifest['software_control_counts']
    C.need(type(counts) is dict and set(counts) == CONTROL_NAMES
           and all(type(n) is int and n > 0 for n in counts.values()),
           'two exact actual control files and frozen positive counts')
    declared = {name for name in manifest['files'] if name.startswith('test_') and name.endswith('.py')}
    C.need(declared == CONTROL_NAMES, 'complete declared source test inventory')
    rows, primary = [], None
    start = time.monotonic()
    try:
        for name in sorted(counts):
            script = manifest['files'][name]
            remaining = 180 - (time.monotonic() - start)
            C.need(remaining > 0, 'original whole software-control subprocess budget180')
            process = subprocess.run([sys.executable, '-I', '-B', str(C.checked(script))],
                                     capture_output=True, text=True, timeout=remaining)
            row = dict(script=script, expected=counts[name], exit_code=process.returncode,
                       stdout=process.stdout, stderr=process.stderr, executed=None, no_skip=False)
            rows.append(row)
            C.need(process.returncode == 0, 'whole actual source control process: ' + name)
            row['executed'] = control_count(process.stderr)
            row['no_skip'] = True
            C.need(row['executed'] == counts[name], 'exact actual noSkip case count: ' + name)
    except BaseException as error:
        primary = repr(error)
        raise
    finally:
        C.write(output / 'SOFTWARE_CONTROLS.json', dict(schema=CONTROLS_SCHEMA,
            source=source_ref, expected_counts=counts, rows=rows,
            executed=sum(row['executed'] or 0 for row in rows),
            expected=sum(counts.values()), pass_gate=primary is None and len(rows) == 2,
            primary=primary, elapsed=time.monotonic()-start, NPU=False, qualified=False))
    return C.ref(output / 'SOFTWARE_CONTROLS.json')


def support_modules(manifest):
    """Use complete original modules after every declared support Ref is read."""
    roots = set()
    for filename, reference in manifest['support_files'].items():
        path = C.checked(reference)
        C.need(path.name == filename, 'same original support module filename')
        roots.add(path.parent)
        name = filename.removesuffix('.py')
        if name in sys.modules:
            C.need(C.ref(sys.modules[name].__file__) == reference,
                   'no ambient replacement of original CPU ABI support')
    C.need(len(roots) == 1, 'one exact original component support source root')
    root = str(next(iter(roots)))
    if root not in sys.path:
        sys.path.insert(1, root)
    return C.load(manifest['support_files']['abi116.py'], '_fia_replay_actual_abi116')


def own_plan(manifest):
    reference = manifest['files']['plan.py']
    if 'plan' in sys.modules:
        C.need(C.ref(sys.modules['plan'].__file__) == reference, 'same exact new numerical plan module')
    else:
        sys.modules['plan'] = C.load(reference, 'plan')
    return sys.modules['plan']


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--source-ref')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.execute:
        print('{"enabled":false,"NPU":false}')
        return 0
    source_ref = json.loads(args.source_ref)
    manifest = C.source(source_ref)
    C.window(manifest)
    cpu_guard()
    C.need(args.output == Path('/adakv-results/preflight') and not args.output.exists()
           and args.output.parent.is_dir(), 'fresh exact owned CPU ABI output')
    args.output.mkdir()
    actual = controls = input_ref = input_preflight = None
    primary = None
    C.write(args.output / 'PROCESS.json', dict(source=source_ref, actual_argv=sys.argv,
        backend_autoload=os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD'),
        ASCEND=os.environ.get('ASCEND_RT_VISIBLE_DEVICES'), NPU=False))
    try:
        controls = software_controls(source_ref, manifest, args.output)
        C.write(args.output / 'CANN.json', dict(source=manifest['cann_helper_ref'],
                                               actual=bootstrap(manifest), NPU=False))
        own_plan(manifest)
        abi = support_modules(manifest)
        import torch as torch
        import torch_npu
        torch.set_num_threads(1)
        abi.record(torch, torch_npu, source_ref, manifest['header_ref'], args.output / 'ACTUAL_FIA_ABI.json')
        actual = C.ref(args.output / 'ACTUAL_FIA_ABI.json')
        probe = C.load(manifest['files']['probe.py'], '_fia_replay_saved_input_preflight')
        input_preflight = probe.prepare_cpu(source_ref, args.output)
        C.need(input_preflight['actual_saved_inputs_checked'] is True
               and input_preflight['original_failure_sets_reproduced'] is True
               and input_preflight['qualified'] is False and input_preflight['NPU'] is False,
               'actual unchanged original saved frames and failures extracted on CPU')
        input_ref = input_preflight['input_binding_ref']
        C.need(input_ref == C.ref(args.output / 'INPUT_BINDING.json'), 'actual saved input binding file')
        cpu_guard()
        C.readset(manifest, source_ref)
        C.window(manifest)
    except BaseException as error:
        primary = repr(error)
        C.write(args.output / 'FAILURE.json', dict(primary=primary,
            traceback=traceback.format_exc(), source=source_ref, NPU=False))
    if controls is None and (args.output / 'SOFTWARE_CONTROLS.json').is_file():
        controls = C.ref(args.output / 'SOFTWARE_CONTROLS.json')
    C.write(args.output / 'STAGE_RESULT.json', dict(schema=STAGE_SCHEMA,
        source=source_ref, authority=manifest['authority_ref'], actual_abi_ref=actual,
        actual_conv_abi_ref=None, conv_abi_pending=True,
        conv_abi_pending_reason='actual116R3-GDN-import-requires-HAL',
        input_binding_ref=input_ref, input_preflight=input_preflight,
        software_controls=controls, actual_meta=dict(pass_gate=primary is None,
            kind='actual-installed-FIA-schema-and-fixed-saved-input-CPU-preflight',
            operator_executed=False, NPU=False),
        primary=primary, NPU=False, qualified=False))
    return 0 if primary is None else 3


if __name__ == '__main__':
    raise SystemExit(main())
