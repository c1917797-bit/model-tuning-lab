"""Fixed, bounded stdlib checks only; never invoke either model-result consume()."""
import argparse
import datetime
import hashlib
import json
import os
import resource
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path


WS = Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
PACKAGE = WS / 'lowobs_consumer_v2_20261022'
BASELINE = WS / 'bole_performance_profile_prepare_20261021/successor_layer/formal_pair_prepare_v1/revision3'
OUTPUT = Path('/opt/host/vnf/austinov/run-bole-lowobs-consumer-source-check-v2-20261022T081000Z')
WHOLE_SECONDS, CHILD_SECONDS = 90, 25
READ_CAP, LOG_CAP, OUTPUT_CAP = 2**17, 2**20, 16 * 2**20
PINS = {
    'read_short_results_v2.py': (4850, '48bf3d952a932d0733c620bcc09a5d5f1a4f19e52d97512759b9597b42a07f69'),
    'consume_pair_v2.py': (8828, 'cee870a32b8f2087d63bb3c9f2d3dbd81efa6a317ad0eb044f86478f5943c0c0'),
    'cleanup_summary.py': (3957, '1c2e014303bec214cff2e19d8c428eee1a13d69c3f8b525308b3ae958faf9687'),
    'test_cleanup_boundary.py': (5135, '3740e69cfbcd99d1e2bfe4233959faf65ee62e502fd0e3378f6630b52bca4f18'),
    'verify_source_invariants.py': (5981, '4befbfad36cc092038626cd41bd47a2b0385c820a363aedf3f2fdf47b2d953c3'),
    'SOURCE_ONLY_MANIFEST.json': (5416, 'e8d9244c1865d1d596e0616c657aa52595e412290c4c4d5866497015b47f6686'),
    'fixtures/original_ON_v2/cpu-preflight/cleanup.json': (1245, 'f933c4c006a3eaa29745bd1de5b2939d4c407a456ead0e9d149dc20286bf69cd'),
    'fixtures/original_ON_v2/dense/cleanup.json': (1213, '54bcb155380f1d0b5762a3b22433a8592c8cf0352d355b7f53825351475d562d'),
}
BASE_PINS = {
    'read_short_results.py': (4204, 'ebcee4f6a9cc3cbb8cd6b47b3c6ce947ceb01dab83398eca8188ac68cd2102d0'),
    'consume_pair.py': (7899, '5c11717e03c958661411c102c407c8f8b773d599d45f42b245f8c257b44196d9'),
}
UNITTEST_PINS = {
    '/usr/local/lib/qwen35-pytest-8.4.2-py39/site-packages/unittest/__init__.py': (3761, '07bdf1fff20e4121ba61cfb64ea3c404d54ac56b053475a3a105907f48685210'),
    '/usr/local/lib/qwen35-pytest-8.4.2-py39/site-packages/unittest/mock.py': (99215, '883176927e3c64d328716635b294523a9be16bbe3ac0f5792947897535f34844'),
}
CONTROL_WRAPPER = '''import hashlib,json,runpy,sys
from pathlib import Path
import unittest,unittest.mock
expected=json.loads(sys.argv[1]); script=sys.argv[2]; rows=[]
for module,want in zip((unittest,unittest.mock),expected):
    path=Path(module.__file__)
    if str(path)!=want['path'] or not path.is_file() or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('exact ordinary actual unittest import origin')
    with path.open('rb') as stream:
        data=stream.read(want['bytes']+1)
    actual=dict(path=str(path),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    if actual!=want:
        raise ValueError('exact actual unittest import source Ref')
    rows.append(actual)
print(json.dumps(dict(actual_unittest_import_origins=rows,source_only=True,NPU_executed=False)),flush=True)
sys.argv=[script]
runpy.run_path(script,run_name='__main__')
'''
RUNTIME_RESULTS = ('LOWOBS_SHORT_NPU_COMPARE_v2.json', 'LOWOBS_FIXED131_PAIR_SCREEN_v2.json')


def need(value, message):
    if not value:
        raise ValueError(message)


def ordinary(path, directory=False):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts, 'exact absolute path')
    for parent in path.parents:
        need(stat.S_ISDIR(parent.lstat().st_mode), 'ordinary non-symlink ancestors')
    mode = path.lstat().st_mode
    need(stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode), 'ordinary path type')
    return path


def read(path, cap=READ_CAP):
    path = ordinary(path)
    before = path.stat()
    need(0 <= before.st_size <= cap, 'bounded complete file')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        need(stat.S_ISREG(opened.st_mode), 'regular opened file')
        data = stream.read(cap + 1)
        after = os.fstat(stream.fileno())
    final = ordinary(path).stat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    need(identity(before) == identity(opened) == identity(after) == identity(final)
         and len(data) == before.st_size <= cap, 'stable bounded whole read')
    return data, dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def write(path, value):
    data = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    need(len(data) <= LOG_CAP, 'bounded metadata write')
    with Path(path).open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return read(path, LOG_CAP)[1]


def limits():
    for kind, cap in ((resource.RLIMIT_AS, 256 * 2**20), (resource.RLIMIT_CPU, 30),
                      (resource.RLIMIT_FSIZE, LOG_CAP), (resource.RLIMIT_CORE, 0)):
        _, hard = resource.getrlimit(kind)
        bounded = cap if hard == resource.RLIM_INFINITY else min(cap, hard)
        resource.setrlimit(kind, (bounded, bounded))


def child(name, argv, deadline):
    remaining = min(CHILD_SECONDS, deadline - time.monotonic() - 5)
    need(remaining > 0, 'whole source-check clock exhausted')
    stdout, stderr = OUTPUT / (name + '.stdout'), OUTPUT / (name + '.stderr')
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
           'TZ': 'UTC', 'TMPDIR': str(OUTPUT / 'tmp')}
    started = time.monotonic()
    with stdout.open('xb') as so, stderr.open('xb') as se:
        process = subprocess.Popen(argv, cwd=OUTPUT, env=env, stdout=so, stderr=se,
                                   start_new_session=True)
        timed_out, error, code = False, None, None
        try:
            code = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            timed_out = True
        except BaseException as exc:
            error = repr(exc)
        finally:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    code = process.wait(timeout=5)
                except BaseException as exc:
                    error = repr(exc)
                    code = process.poll()
            else:
                code = process.returncode
            so.flush()
            se.flush()
            os.fsync(so.fileno())
            os.fsync(se.fileno())
    row = dict(name=name, argv=argv, pid=process.pid, exit_code=code, timed_out=timed_out,
               error=error,
               elapsed_s=time.monotonic() - started, stdout=read(stdout, LOG_CAP)[1],
               stderr=read(stderr, LOG_CAP)[1], source_only=True, NPU_executed=False)
    write(OUTPUT / (name + '.json'), row)
    return row


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(enabled=False, source_only=True, NPU_executed=False)))
        return 0
    started = time.monotonic()
    deadline = started + WHOLE_SECONDS
    self_path = ordinary(Path(__file__).absolute())
    need(self_path == PACKAGE / 'remote_validate_source_only_v2.py', 'fixed reviewed runner path')
    ordinary(PACKAGE, directory=True)
    ordinary(OUTPUT.parent, directory=True)
    os.umask(0o077)
    OUTPUT.mkdir(mode=0o700)  # Refuse any existing output; never resume or overwrite.
    limits()
    before, after, staged, stages = [], [], [], []
    error, before_complete, staged_unchanged = None, False, False
    inputs = [(PACKAGE / name, pin) for name, pin in PINS.items()]
    inputs += [(BASELINE / name, pin) for name, pin in BASE_PINS.items()]
    inputs += [(Path(path), pin) for path, pin in UNITTEST_PINS.items()]
    inputs.append((self_path, None))  # MAIN pins this runner's SHA before deployment.
    try:
        data = {}
        for path, pin in inputs:
            body, reference = read(path)
            before.append(reference)
            need(pin is None or (reference['bytes'], reference['sha256']) == pin,
                 'exact pinned input: ' + str(path))
            data[path] = body
        before_complete = True
        unittest_refs = [r for r in before if r['path'] in UNITTEST_PINS]
        write(OUTPUT / 'START.json', dict(schema='bole.lowobs-consumer-source-check-start/v2',
              started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              package=str(PACKAGE), baseline=str(BASELINE), output=str(OUTPUT),
              whole_seconds=WHOLE_SECONDS, child_seconds=CHILD_SECONDS,
              stdout_stderr_cap_each=LOG_CAP, output_cap=OUTPUT_CAP,
              unittest_source_refs=unittest_refs,
              unittest_origin_basis='MAIN observed import origin exec069e and full source Refs exec069f; controls wrapper rechecks imports',
              source_only=True, NPU_executed=False, runtime_consume_executed=False))
        for name in RUNTIME_RESULTS:
            need(not (PACKAGE / name).exists(), 'no model-consumer output in source-only package')
        write(OUTPUT / 'INPUTS_BEFORE.json', before)
        zone = OUTPUT / 'controls_package'
        zone.mkdir()
        (OUTPUT / 'tmp').mkdir()
        # The unchanged test creates local temporary files: confine them here.
        copied = ('read_short_results_v2.py', 'consume_pair_v2.py', 'cleanup_summary.py',
                  'test_cleanup_boundary.py', 'fixtures/original_ON_v2/cpu-preflight/cleanup.json',
                  'fixtures/original_ON_v2/dense/cleanup.json')
        for name in copied:
            target = zone / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(data[PACKAGE / name])
                stream.flush()
                os.fsync(stream.fileno())
            actual = read(target)[1]
            need((actual['bytes'], actual['sha256']) == PINS[name], 'exact control-zone copy')
            staged.append(actual)
        write(OUTPUT / 'CONTROL_INPUTS_BEFORE.json', staged)
        python = [sys.executable, '-I', '-B']  # Existing host unittest is supplied through site; no install/edit.
        jobs = (
            ('controls', python + ['-c', CONTROL_WRAPPER, json.dumps(unittest_refs),
                                  str(zone / 'test_cleanup_boundary.py')]),
            ('invariants', python + [str(PACKAGE / 'verify_source_invariants.py'),
                                    '--baseline-dir', str(BASELINE)]),
            ('short_help', python + [str(PACKAGE / 'read_short_results_v2.py'), '--help']),
            ('screen_help', python + [str(PACKAGE / 'consume_pair_v2.py'), '--help']),
        )
        for name, argv in jobs:
            row = child(name, argv, deadline)
            stages.append(row)
            need(row['exit_code'] == 0 and not row['timed_out'] and row['error'] is None,
                 'source-only child failed: ' + name)
        controls = read(OUTPUT / 'controls.stderr', LOG_CAP)[0].decode('utf-8')
        need('Ran 7 tests' in controls and controls.rstrip().endswith('OK'), 'exact seven controls completed')
        origins = json.loads(read(OUTPUT / 'controls.stdout', LOG_CAP)[0])
        need(origins['actual_unittest_import_origins'] == unittest_refs
             and origins['source_only'] is True and origins['NPU_executed'] is False,
             'same controls child used exact pinned actual unittest origins')
        invariant = json.loads(read(OUTPUT / 'invariants.stdout', LOG_CAP)[0])
        need(invariant['source_invariants_pass'] is True and invariant['source_only'] is True
             and invariant['NPU_executed'] is False and invariant['paired_gate_pass'] is False
             and invariant['performance_admitted'] is False, 'source invariants only, no qualification promotion')
        for parent in (PACKAGE, zone):
            for name in RUNTIME_RESULTS:
                need(not (parent / name).exists(), 'runtime consume output forbidden')
        need(time.monotonic() <= deadline, 'whole source-check budget exhausted')
    except BaseException as exc:
        error = repr(exc)
    finally:
        if not (OUTPUT / 'INPUTS_BEFORE.json').exists():
            write(OUTPUT / 'INPUTS_BEFORE.json', before)
        for path, _ in inputs:
            try:
                after.append(read(path)[1])
            except BaseException as exc:
                after.append(dict(path=str(path), error=repr(exc)))
        write(OUTPUT / 'INPUTS_AFTER.json', after)
        copied_after = []
        for original in staged:
            try:
                copied_after.append(read(original['path'])[1])
            except BaseException as exc:
                copied_after.append(dict(path=original['path'], error=repr(exc)))
        write(OUTPUT / 'CONTROL_INPUTS_AFTER.json', copied_after)
        staged_unchanged = len(staged) == 6 and staged == copied_after
    unchanged = before_complete and before == after
    used = sum(path.stat().st_size for path in OUTPUT.rglob('*') if path.is_file())
    within_budget = time.monotonic() <= deadline
    passed = (error is None and unchanged and staged_unchanged and len(stages) == 4
              and used + LOG_CAP <= OUTPUT_CAP and within_budget)
    result = dict(schema='bole.lowobs-consumer-remote-source-check/v2',
                  status='PASS_SOURCE_ONLY' if passed else 'FAIL_SOURCE_ONLY',
                  error=error, source_inputs_unchanged=unchanged, control_inputs_unchanged=staged_unchanged,
                  within_whole_budget=within_budget,
                  stages=stages, elapsed_s=time.monotonic() - started, output_bytes_before_result=used,
                  source_only=True, NPU_executed=False, runtime_consume_executed=False,
                  numerical_qualification=False, paired_gate_pass=False, performance_admitted=False,
                  formal_performance=False, task_accuracy=False, technology_success=False)
    reference = write(OUTPUT / 'RESULT.json', result)
    print(json.dumps(dict(result=reference, status=result['status'], source_only=True, NPU_executed=False)))
    return 0 if passed else 3


if __name__ == '__main__':
    raise SystemExit(main())
