"""Two exclusive, bounded execution scopes for the frozen read-only reader.

--controls-only runs exactly the fifteen new CPU projection controls in its own output.
Actual mode requires all three real Ref3 operands and runs only the reader.
Neither mode invokes a model, container, device, paired gate, or performance test.
MAIN must pin this wrapper's final SHA before deployment; no self-hash claim is
hardcoded into its own source. Existing output directories are never reused.
"""
import argparse
import hashlib
import json
import os
import resource
import signal
import stat
import subprocess
import sys
import time
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
WS = Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
PACKAGE = WS/'projection_result_reader_v1_20261022'
ACTUAL_OUTPUT = Path('/opt/host/vnf/austinov/run-bole-projection-reader-v1-20261022T100000Z')
CONTROLS_OUTPUT = Path('/opt/host/vnf/austinov/run-bole-projection-reader-controls-v1-20261022T100000Z')
SOURCE = WS/'bound-boundary-ON-v2-20261022T100000Z/SOURCE_BOUND.json'
HOST_RESULT = Path('/opt/host/vnf/austinov/run-bole-boundary-ON-v2-20261022T100000Z/RESULT.json')
SOURCE_AUDIT = Path('/opt/host/vnf/austinov/run-bole-boundary-source-audit-v3-20261022T100000Z/SOURCE_AUDIT.json')
PYTHON = '/usr/bin/python3'
REVIEWED_WRAPPER_FROZEN = False
PINS = {
    'read_projection_result_v1.py': (None, None),
    'test_projection_reader_v1.py': (None, None),
}
UNITTEST_PINS = {
    '/usr/local/lib/qwen35-pytest-8.4.2-py39/site-packages/unittest/__init__.py':
        (3761, '07bdf1fff20e4121ba61cfb64ea3c404d54ac56b053475a3a105907f48685210'),
    '/usr/local/lib/qwen35-pytest-8.4.2-py39/site-packages/unittest/mock.py':
        (99215, '883176927e3c64d328716635b294523a9be16bbe3ac0f5792947897535f34844'),
}
AS_CAP, CPU_SECONDS, WALL_SECONDS, FILE_CAP = 512 * 2**20, 180, 240, 64 * 2**20
JSON_CAP, SOURCE_CAP, META_CAP = 8 * 2**20, 2**20, 2**20
CLEANUP_RESERVE = 12

# The real child checks the existing host site-supplied unittest origins.
# -I -B intentionally retains site; -S would remove the already repaired module.
CONTROL_WRAPPER = '''import hashlib,json,runpy,sys
from pathlib import Path
import unittest,unittest.mock
expected=json.loads(sys.argv[1]); script=sys.argv[2]; rows=[]
if sys.version_info[:3] != (3,9,9):
    raise ValueError('exact observed host Python3.9.9 runtime')
for module,want in zip((unittest,unittest.mock),expected):
    path=Path(module.__file__)
    if str(path)!=want['path'] or not path.is_file() or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('exact ordinary actual unittest import origin')
    before=path.stat()
    with path.open('rb') as stream:
        data=stream.read(want['bytes']+1)
    after=path.stat()
    identity=lambda v:(v.st_dev,v.st_ino,v.st_mode,v.st_size,v.st_mtime_ns,v.st_ctime_ns)
    actual=dict(path=str(path),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    if actual!=want or identity(before)!=identity(after):
        raise ValueError('exact stable whole actual unittest import source Ref')
    rows.append(actual)
print(json.dumps(dict(schema='bole.projection-reader-control-runtime/v1',actual_unittest_import_origins=rows,
    controls_only=True,source_only=True,NPU_executed=False,paired_gate_pass=False,performance_admitted=False)),flush=True)
sys.argv=[script]
runpy.run_path(script,run_name='__main__')
'''


def need(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode()


def json_value(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value, 'no duplicate input JSON key')
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON ' + value)))


def typed_ref(reference, cap=JSON_CAP):
    need(type(reference) is dict and set(reference) == {'path', 'bytes', 'sha256'}, 'exact complete Ref3 operand')
    need(type(reference['path']) is str and '\x00' not in reference['path'] and
         type(reference['bytes']) is int and 0 <= reference['bytes'] <= cap and
         type(reference['sha256']) is str and len(reference['sha256']) == 64 and
         all(c in '0123456789abcdef' for c in reference['sha256']), 'typed bounded Ref3 operand')
    path = Path(reference['path'])
    need(path.is_absolute() and str(path) == reference['path'] and '..' not in path.parts, 'exact absolute operand path')
    return path


def identity(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
            value.st_uid, value.st_gid, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def parents(path):
    rows = []
    for parent in Path(path).parents:
        value = parent.lstat()
        need(stat.S_ISDIR(value.st_mode), 'ordinary non-symlink ancestors')
        rows.append((str(parent), value.st_dev, value.st_ino, value.st_mode))
    return tuple(rows)


def read(path, cap, expected=None, keep=True):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts, 'absolute whole read path')
    prior_parents = parents(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= cap, 'regular bounded complete input')
    if expected is not None:
        need(str(path) == expected['path'] and before.st_size == expected['bytes'], 'exact expected path and length')
    digest, pieces, size = hashlib.sha256(), [], 0
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(fd, 'rb') as stream:
        need(identity(os.fstat(stream.fileno())) == identity(before), 'unchanged opened input identity')
        while True:
            block = stream.read(min(2**20, cap + 1 - size))
            if not block:
                break
            size += len(block)
            need(size <= cap, 'full bounded input; no prefix SHA')
            digest.update(block)
            if keep:
                pieces.append(block)
        need(identity(os.fstat(stream.fileno())) == identity(before), 'unchanged input during read')
    need(identity(path.lstat()) == identity(before) and parents(path) == prior_parents and
         size == before.st_size, 'unchanged complete input path')
    reference = dict(path=str(path), bytes=size, sha256=digest.hexdigest())
    need(expected is None or reference == expected, 'exact whole-file SHA and byte count')
    return reference, b''.join(pieces) if keep else None, identity(before)


def write(path, value):
    data = canonical(value) + b'\n'
    need(len(data) <= META_CAP, 'bounded complete wrapper metadata')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        need(stream.write(data) == len(data), 'complete exclusive wrapper metadata')
        stream.flush(); os.fsync(stream.fileno())
    return read(path, META_CAP, keep=False)[0]


def write_trace(path, text):
    data = text.encode('utf-8', 'backslashreplace')
    need(len(data) <= META_CAP, 'bounded raw wrapper failure traceback')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        need(stream.write(data) == len(data), 'complete original wrapper traceback')
        stream.flush(); os.fsync(stream.fileno())
    return read(path, META_CAP, keep=False)[0]


def limits():
    values = []
    for label, kind, wanted in (('address_space_bytes', resource.RLIMIT_AS, AS_CAP),
                                ('cpu_seconds', resource.RLIMIT_CPU, CPU_SECONDS),
                                ('file_bytes', resource.RLIMIT_FSIZE, FILE_CAP),
                                ('core_bytes', resource.RLIMIT_CORE, 0)):
        _, hard = resource.getrlimit(kind)
        cap = wanted if hard == resource.RLIM_INFINITY else min(wanted, hard)
        resource.setrlimit(kind, (cap, cap))
        actual = resource.getrlimit(kind)
        need(actual == (cap, cap), 'actual hard and soft owned-process resource limit')
        values.append(dict(name=label, requested=wanted, soft=actual[0], hard=actual[1]))
    return values


def start_ticks(pid):
    # Linux /proc/<pid>/stat's comm may contain spaces/parentheses.
    raw = Path('/proc/%d/stat' % pid).read_text()
    end = raw.rfind(')')
    need(end > 0, 'actual owned child proc identity')
    fields = raw[end + 2:].split()
    need(len(fields) >= 20, 'complete actual owned child stat')
    return int(fields[19])


def child(argv, output, label, deadline):
    stdout, stderr = output/(label + '.stdout'), output/(label + '.stderr')
    process = None
    timed_out = False
    primary = None
    cleanup = []
    code, ticks = None, None
    started_mono, started_epoch = time.monotonic(), time.time()
    env = dict(PATH='/usr/bin:/bin', LANG='C.UTF-8', LC_ALL='C.UTF-8',
               TZ='UTC', TMPDIR=str(output/'tmp'))
    with stdout.open('xb') as so, stderr.open('xb') as se:
        try:
            need(deadline - time.monotonic() > CLEANUP_RESERVE, 'whole read-only execution budget remains')
            process = subprocess.Popen(argv, cwd=output, env=env, stdin=subprocess.DEVNULL,
                stdout=so, stderr=se, close_fds=True, start_new_session=True)
            # Popen's successful exec boundary and its own process handle are
            # authoritative. /proc identity is additional evidence, if still live.
            if process.poll() is None:
                try:
                    ticks = start_ticks(process.pid)
                    need(os.getpgid(process.pid) == process.pid and os.getsid(process.pid) == process.pid,
                         'owned child has its own actual process group/session')
                except ProcessLookupError:
                    need(process.poll() is not None, 'owned process disappeared only after exit')
                except FileNotFoundError:
                    need(process.poll() is not None, 'owned proc record disappeared only after exit')
            while process.poll() is None:
                remaining = deadline - time.monotonic() - CLEANUP_RESERVE
                if remaining <= 0:
                    timed_out = True
                    break
                try:
                    process.wait(timeout=min(1., remaining))
                except subprocess.TimeoutExpired:
                    continue
            code = process.poll()
        except BaseException:
            primary = traceback.format_exc()
        finally:
            if process is not None:
                if process.poll() is None:
                    try:
                        if ticks is not None:
                            need(start_ticks(process.pid) == ticks, 'same owned child identity before cleanup')
                        need(os.getpgid(process.pid) == process.pid and os.getsid(process.pid) == process.pid,
                             'only signal the newly owned child group/session')
                        os.killpg(process.pid, signal.SIGTERM)
                        cleanup.append(dict(signal='SIGTERM', target_owned_group=process.pid))
                    except ProcessLookupError:
                        pass
                    except BaseException as exc:
                        cleanup.append(dict(error=repr(exc), action='owned SIGTERM'))
                    try:
                        code = process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        try:
                            if ticks is not None:
                                need(start_ticks(process.pid) == ticks, 'same owned child identity before kill')
                            need(os.getpgid(process.pid) == process.pid and os.getsid(process.pid) == process.pid,
                                 'only kill the newly owned child group/session')
                            os.killpg(process.pid, signal.SIGKILL)
                            cleanup.append(dict(signal='SIGKILL', target_owned_group=process.pid))
                        except ProcessLookupError:
                            pass
                        except BaseException as exc:
                            cleanup.append(dict(error=repr(exc), action='owned SIGKILL'))
                        try:
                            code = process.wait(timeout=3)
                        except BaseException as exc:
                            cleanup.append(dict(error=repr(exc), action='owned child reap'))
                    except BaseException as exc:
                        cleanup.append(dict(error=repr(exc), action='owned child wait'))
                else:
                    code = process.returncode
                # A completed source reader should leave no process group. Do
                # not sweep or signal unrelated processes if this check fails.
                group_absent = False
                try:
                    os.killpg(process.pid, 0)
                except ProcessLookupError:
                    group_absent = True
                except BaseException as exc:
                    cleanup.append(dict(error=repr(exc), action='owned group absence'))
            else:
                group_absent = True
            so.flush(); se.flush(); os.fsync(so.fileno()); os.fsync(se.fileno())
    row = dict(argv=argv, label=label, spawned=process is not None,
        pid=process.pid if process is not None else None, process_group=process.pid if process is not None else None,
        start_ticks=ticks, started_epoch=started_epoch, ended_epoch=time.time(),
        elapsed_seconds=time.monotonic() - started_mono, exit_code=code, timed_out=timed_out,
        wrapper_child_exception=primary, owned_cleanup=cleanup, owned_group_absent=group_absent,
        owned_child_reaped=process is None or process.poll() is not None,
        stdout=read(stdout, FILE_CAP, keep=False)[0], stderr=read(stderr, FILE_CAP, keep=False)[0])
    write(output/'CHILD_EXECUTION.json', row)
    return row


def validate_control_result(command, output, unittest_refs):
    stdout = read(output/'controls.stdout', FILE_CAP)[1]
    stderr = read(output/'controls.stderr', FILE_CAP)[1].decode('utf-8', 'strict')
    value = json_value(stdout)
    need(value == dict(schema='bole.projection-reader-control-runtime/v1',
        actual_unittest_import_origins=unittest_refs, controls_only=True, source_only=True,
        NPU_executed=False, paired_gate_pass=False, performance_admitted=False),
        'same actual controls child used the two exact pinned unittest origins')
    # unittest emits one terminal count and final OK. Any skip/expected failure
    # changes the final line; no cached PASS and no count inferred from exit0.
    lines = stderr.splitlines()
    counts = [line for line in lines if line.startswith('Ran ') and line.endswith('s')]
    need(len(counts) == 1 and counts[0].startswith('Ran 15 tests in ') and
         lines and lines[-1] == 'OK', 'exact fifteen focused projection CPU controls, none skipped')
    need(not (output/'PROJECTION_DIAGNOSTIC.json').exists(), 'controls-only mode never writes an actual diagnostic result')
    return dict(controls_only=True, tests=15, all_controls_passed=True,
                actual_unittest_import_origins=unittest_refs, fresh_model_result_read=False)


def validate_actual_result(command, output, arguments, reader_ref):
    path = output/'PROJECTION_DIAGNOSTIC.json'
    reference, raw, _ = read(path, FILE_CAP)
    value = json_value(raw)
    stdout = json_value(read(output/'reader.stdout', FILE_CAP)[1])
    need(stdout['result'] == reference and stdout['diagnostic_only'] is True and
         stdout['original_inputs_unchanged'] is True and stdout['paired_gate_pass'] is False and
         stdout['numerical_admitted'] is False and stdout['performance_admitted'] is False and
         stdout['model_ready'] is False and stdout['NPU_executed_by_reader'] is False,
         'actual read-only reader stdout and retained result agree')
    need(value['schema'] == 'bole.completed-projection-within-arm-diagnostic/v1' and
         value['source'] == arguments.source_ref and value['actual_host_result'] == arguments.result_ref and
         value['source_audit'] == arguments.source_audit_ref and value['comparison_source'] == reader_ref and
         value['diagnostic_only'] is True and value['source_only'] is False and value['model_ready'] is False and
         value['paired_gate_pass'] is False and value['numerical_admitted'] is False and
         value['performance_admitted'] is False and value['formal_performance'] is False and
         value['task_accuracy'] is False and value['NPU_executed_by_reader'] is False and
         value['original_host_and_single_arm_gates_revalidated'] is True and
         value['boundary_record_integrity_validated'] is True and
         value['projection_internal_integrity_validated'] is True and
         value['complete_boundary_files_per_rank'] == 150 and value['complete_boundary_files_all_ranks'] == 600 and
         value['complete_whole_sha_readset_unchanged'] is True and value['file_identity_unchanged'] is True and
         value['original_inputs_unchanged'] is True and value['inputs_before'] == value['inputs_after'],
         'exit0 means complete read-only diagnostic integrity, never numerical or performance admission')
    return dict(diagnostic_result=reference, complete_readonly_integrity=True,
        actual_input_ref_count=value['readset_count'], original_inputs_unchanged=True,
        causes_or_numerical_thresholds_admitted=False)


def main():
    need(REVIEWED_WRAPPER_FROZEN is True, 'projection reader wrapper source pins not yet frozen')
    parser = argparse.ArgumentParser(allow_abbrev=False, description=__doc__)
    parser.add_argument('--controls-only', action='store_true')
    parser.add_argument('--source-ref', type=json_value)
    parser.add_argument('--result-ref', type=json_value)
    parser.add_argument('--source-audit-ref', type=json_value)
    args = parser.parse_args()
    supplied = [args.source_ref, args.result_ref, args.source_audit_ref]
    if args.controls_only:
        need(all(value is None for value in supplied), 'controls-only has no actual model/result operands')
    else:
        need(all(value is not None for value in supplied), 'actual mode requires all three exact existing Ref3 operands')
        need(typed_ref(args.source_ref) == SOURCE and typed_ref(args.result_ref) == HOST_RESULT and
             typed_ref(args.source_audit_ref) == SOURCE_AUDIT, 'fixed actual source/result and workstream audit identity')
    output = CONTROLS_OUTPUT if args.controls_only else ACTUAL_OUTPUT
    label = 'controls' if args.controls_only else 'reader'
    self_path = Path(__file__).absolute()
    need(self_path == PACKAGE/'run_projection_reader_once_v1.py', 'one fixed reviewed deployed wrapper')
    parents(self_path)
    need(stat.S_ISREG(self_path.lstat().st_mode), 'ordinary deployed wrapper')
    parents(output)
    os.umask(0o077)
    output.mkdir(mode=0o700)  # Exclusive: no resumption, clearing or overwrite.
    (output/'tmp').mkdir(mode=0o700)
    started, deadline = time.monotonic(), time.monotonic() + WALL_SECONDS
    before, after, identities, expected = [], [], {}, []
    before_complete, unchanged = False, False
    before_ref, after_ref = None, None
    error, trace_ref, command, outcome = None, None, None, None
    runtime, bounds = {}, []
    try:
        bounds = limits()  # Applied to wrapper and inherited by its only child.
        need(sys.version_info[:3] == (3, 9, 9) and sys.flags.isolated == 1 and
             sys.flags.dont_write_bytecode == 1 and sys.flags.no_site == 0 and
             sys.dont_write_bytecode and os.path.samefile(sys.executable, PYTHON),
             'actual observed host Python3.9.9 under -I -B, retaining existing site')
        for name, (size, digest) in PINS.items():
            expected.append((dict(path=str(PACKAGE/name), bytes=size, sha256=digest), SOURCE_CAP))
        for path, (size, digest) in UNITTEST_PINS.items():
            expected.append((dict(path=path, bytes=size, sha256=digest), SOURCE_CAP))
        self_ref, _, self_identity = read(self_path, SOURCE_CAP, keep=False)
        expected.append((self_ref, SOURCE_CAP))
        # Observe the actual executable before/after. No reviewed binary SHA was
        # provided, so this is recorded as an observation, not a fabricated pin.
        executable = Path(sys.executable).resolve(strict=True)
        binary_ref, _, _ = read(executable, FILE_CAP, keep=False)
        expected.append((binary_ref, FILE_CAP))
        runtime = dict(python_argv=PYTHON, actual_executable=str(executable),
            python_version=sys.version, observed_python_binary=binary_ref,
            python_binary_preexisting_reviewed_sha=False,
            isolated=True, dont_write_bytecode=True, site_disabled=False)
        if not args.controls_only:
            expected.extend((reference, JSON_CAP) for reference in supplied)
        for reference, cap in expected:
            actual, _, actual_identity = read(typed_ref(reference, cap), cap, expected=reference, keep=False)
            before.append(actual); identities[actual['path']] = actual_identity
        before_complete = True
        before_ref = write(output/'INPUTS_BEFORE.json', before)
        unittest_refs = [reference for reference in before if reference['path'] in UNITTEST_PINS]
        need(len(unittest_refs) == 2, 'two exact actual unittest source operands')
        write(output/'START.json', dict(schema='bole.projection-reader-wrapper-start/v1',
            controls_only=args.controls_only, package=str(PACKAGE), output=str(output),
            whole_wall_seconds=WALL_SECONDS, owned_cleanup_reserve_seconds=CLEANUP_RESERVE,
            limits=bounds, runtime=runtime, actual_operands=[] if args.controls_only else supplied,
            actual_model_result_read=not args.controls_only, NPU_executed=False,
            paired_gate_pass=False, numerical_qualified=False, performance_admitted=False))
        if args.controls_only:
            argv = [PYTHON, '-I', '-B', '-c', CONTROL_WRAPPER,
                    canonical(unittest_refs).decode(), str(PACKAGE/'test_projection_reader_v1.py')]
        else:
            argv = [PYTHON, '-I', '-B', str(PACKAGE/'read_projection_result_v1.py'),
                    '--source-ref', canonical(args.source_ref).decode(),
                    '--result-ref', canonical(args.result_ref).decode(),
                    '--source-audit-ref', canonical(args.source_audit_ref).decode(),
                    '--output', str(output/'PROJECTION_DIAGNOSTIC.json')]
        command = child(argv, output, label, deadline)
        need(command['spawned'] is True and command['exit_code'] == 0 and command['timed_out'] is False and
             command['wrapper_child_exception'] is None and command['owned_child_reaped'] is True and
             command['owned_group_absent'] is True and not any('error' in row for row in command['owned_cleanup']),
             'owned read-only child completed with exact terminal and clean release')
        if args.controls_only:
            outcome = validate_control_result(command, output, unittest_refs)
        else:
            reader_ref = next(reference for reference in before if reference['path'] == str(PACKAGE/'read_projection_result_v1.py'))
            outcome = validate_actual_result(command, output, args, reader_ref)
    except BaseException as exc:
        error = repr(exc)
        trace_ref = write_trace(output/'WRAPPER_TRACEBACK.txt', traceback.format_exc())
    finally:
        if not (output/'INPUTS_BEFORE.json').exists():
            before_ref = write(output/'INPUTS_BEFORE.json', before)
        for reference, cap in expected:
            try:
                actual, _, actual_identity = read(reference['path'], cap, expected=reference, keep=False)
                need(identities.get(actual['path']) == actual_identity, 'wrapper input identity unchanged since initial read')
                after.append(actual)
            except BaseException as exc:
                after.append(dict(path=reference['path'], error=repr(exc)))
        after_ref = write(output/'INPUTS_AFTER.json', after)
        unchanged = before_complete and before == after
    within_wall = time.monotonic() <= deadline
    passed = error is None and unchanged and within_wall and command is not None and outcome is not None
    actual_result_ref = None
    if (output/'PROJECTION_DIAGNOSTIC.json').exists():
        actual_result_ref = read(output/'PROJECTION_DIAGNOSTIC.json', FILE_CAP, keep=False)[0]
    execution = dict(schema='bole.projection-reader-wrapper-execution/v1',
        status=('PASS_CONTROLS_ONLY' if args.controls_only else 'PASS_READONLY_DIAGNOSTIC_INTEGRITY') if passed else
               ('FAIL_CONTROLS_ONLY' if args.controls_only else 'FAIL_READONLY_DIAGNOSTIC'),
        controls_only=args.controls_only, source_only=args.controls_only,
        actual_reader_executed=not args.controls_only and command is not None and command['spawned'],
        actual_integrity_passed=passed and not args.controls_only,
        controls_passed=passed and args.controls_only,
        focused_projection_control_count=15 if args.controls_only else None,
        fresh_model_result_read=not args.controls_only and args.result_ref in before,
        wrapper_inputs_unchanged=unchanged, inputs_before=before_ref,
        inputs_after=after_ref, wrapper_input_count=len(before),
        error=error, wrapper_traceback=trace_ref, command=command, outcome=outcome,
        retained_diagnostic_output=actual_result_ref,
        retained_output_may_be_partial=actual_result_ref is not None and not (passed and not args.controls_only),
        runtime=runtime, limits=bounds, within_whole_wall_budget=within_wall,
        elapsed_seconds=time.monotonic()-started, NPU_executed=False, container_action=False,
        model_ready=False, numerical_qualified=False, paired_gate_pass=False,
        performance_admitted=False, formal_performance=False, task_accuracy=False,
        technology_success=False,
        interpretation='Controls mode proves only current CPU reader controls. Actual mode exit0 proves complete read-only evidence integrity and diagnostics, never state-pair, numerical, performance or task-accuracy admission.')
    execution_ref = write(output/'EXECUTION.json', execution)
    print(json.dumps(dict(execution=execution_ref, status=execution['status'],
        controls_only=args.controls_only, NPU_executed=False, paired_gate_pass=False,
        numerical_qualified=False, performance_admitted=False), sort_keys=True))
    return 0 if passed else 3


if __name__ == '__main__':
    raise SystemExit(main())
