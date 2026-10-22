"""Run only reviewed host CPU observer controls in one fresh bounded output."""
import argparse
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

WS = Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
ROOT = WS / 'boundary_probe_prepare_v2_20261022'
OLD = WS / 'bole_performance_profile_prepare_20261021/successor_layer/bound-short-ON-v2'
OUT = Path('/opt/host/vnf/austinov/run-bole-boundary-source-controls-v2-20261022T100000Z')
UNITTEST = [
    dict(path='/usr/local/lib/qwen35-pytest-8.4.2-py39/site-packages/unittest/__init__.py', bytes=3761,
         sha256='07bdf1fff20e4121ba61cfb64ea3c404d54ac56b053475a3a105907f48685210'),
    dict(path='/usr/local/lib/qwen35-pytest-8.4.2-py39/site-packages/unittest/mock.py', bytes=99215,
         sha256='883176927e3c64d328716635b294523a9be16bbe3ac0f5792947897535f34844')]


def need(value, message):
    if not value:
        raise ValueError(message)


def ref(path):
    path = Path(path)
    need(path.is_absolute() and path.is_file() and
         not any(p.is_symlink() for p in (path, *path.parents)), 'ordinary input or output')
    need(path.stat().st_size <= 8 * 2**20, 'bounded whole source/evidence read')
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def checked(reference):
    need(type(reference) is dict and set(reference) == {'path', 'bytes', 'sha256'} and
         ref(reference['path']) == reference, 'exact complete Ref')
    return Path(reference['path'])


def write(path, value):
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return ref(path)


def child(name, arguments, deadline):
    stdout, stderr = OUT / (name + '.stdout'), OUT / (name + '.stderr')
    env = dict(PATH='/usr/bin:/bin', LANG='C.UTF-8', LC_ALL='C.UTF-8', TZ='UTC', TMPDIR=str(OUT/'tmp'))
    started = time.monotonic()
    proc = None
    timed_out = False
    with stdout.open('xb') as so, stderr.open('xb') as se:
        try:
            proc = subprocess.Popen(arguments, cwd=OUT, env=env, stdout=so, stderr=se, start_new_session=True)
            try:
                code = proc.wait(timeout=max(.1, min(30, deadline - time.monotonic())))
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(proc.pid, signal.SIGKILL)
                code = proc.wait(timeout=5)
        finally:
            if proc is not None and proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=5)
            so.flush(); se.flush()
            os.fsync(so.fileno()); os.fsync(se.fileno())
    row = dict(name=name, argv=arguments, exit_code=code, timed_out=timed_out,
               elapsed_s=time.monotonic()-started, stdout=ref(stdout), stderr=ref(stderr))
    write(OUT/(name+'.json'), row)
    return row


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--inputs-ref', type=json.loads, required=True)
    args = parser.parse_args()
    need(Path(__file__).resolve() == ROOT/'run_boundary_controls.py', 'one reviewed runner identity')
    need(not OUT.exists() and OUT.parent.is_dir(), 'fresh controls output, no failed rerun')
    inputs = json.loads(checked(args.inputs_ref).read_bytes())
    need(inputs['schema'] == 'bole.boundary-preparation-inputs/v1' and
         inputs['source_only'] is True and inputs['NPU'] is False, 'source-only preparation descriptor')
    expected = [args.inputs_ref, *inputs['files'], *UNITTEST]
    unique = {}
    for reference in expected:
        checked(reference)
        need(reference['path'] not in unique or unique[reference['path']] == reference, 'unique input path')
        unique[reference['path']] = reference
    need(unique.get(str(ROOT/'run_boundary_controls.py')) == ref(__file__), 'runner is a pinned preparation input')
    need(all(str(ROOT/name) in unique for name in
         ('test_boundary_probe_v1.py', 'test_boundary_integration.py', 'metadata_envelope.py',
          'boundary_probe_v1.py', 'boundary_delta.py', 'boundary_integration.py', 'boundary_validation.py',
          'projection_probe_v1.py', 'test_projection_probe_v1.py',
          'evidence/ascend_linear.py', 'evidence/ascend_linear_op.py', 'evidence/ascend_utils.py',
          'evidence/custom_op.py', 'evidence/vllm_linear.py')),
         'complete current observer/control source closure')
    OUT.mkdir(mode=0o700); (OUT/'tmp').mkdir()
    os.umask(0o077)
    for key, cap in ((resource.RLIMIT_AS, 512*2**20), (resource.RLIMIT_CPU, 90),
                     (resource.RLIMIT_FSIZE, 8*2**20), (resource.RLIMIT_CORE, 0)):
        soft, hard = resource.getrlimit(key)
        value = cap if hard == resource.RLIM_INFINITY else min(cap, hard)
        resource.setrlimit(key, (value, value))
    started = time.monotonic(); deadline = started + 120
    before = list(unique.values()); write(OUT/'INPUTS_BEFORE.json', before)
    rows = []; error = None; capacity = None
    try:
        python = [sys.executable, '-I', '-B']
        jobs = [('probe_controls', python+[str(ROOT/'test_boundary_probe_v1.py')]),
                ('integration_controls', python+[str(ROOT/'test_boundary_integration.py'), '--original-root', str(OLD)]),
                ('projection_controls', python+[str(ROOT/'test_projection_probe_v1.py')]),
                ('metadata_capacity', python+[str(ROOT/'metadata_envelope.py')])]
        for name, argv in jobs:
            need(time.monotonic() < deadline, 'remaining complete source-control budget')
            row = child(name, argv, deadline); rows.append(row)
            need(row['exit_code'] == 0 and not row['timed_out'], 'failed source-control child '+name)
        for row, count in zip(rows[:3], (11, 8, 16)):
            text = checked(row['stderr']).read_text()
            need(('Ran %d tests' % count) in text and text.rstrip().endswith('OK'), 'exact separate current control count')
        capacity = json.loads(checked(rows[3]['stdout']).read_bytes())
        need(capacity['fabricated_bounds_only'] is True and capacity['NPU'] is False and
             capacity['qualification'] is False and capacity['all_files'] == 150 and
             capacity['metadata_upper_bound_bytes'] <= capacity['metadata_cap'] and
             capacity['exact_raw_bytes'] == capacity['raw_cap'] and
             capacity['bounded_device_read_bytes'] <= capacity['device_read_cap'] and
             capacity['bounded_other_total_with_headroom'] <= capacity['original_other_cap'],
             'bounded source-only capacity calculation, not a tensor observation')
    except BaseException as exc:
        error = repr(exc)
    after = []
    for reference in before:
        try:
            after.append(ref(reference['path']))
        except BaseException as exc:
            after.append(dict(path=reference['path'], error=repr(exc)))
    write(OUT/'INPUTS_AFTER.json', after)
    passed = error is None and before == after and len(rows) == 4 and time.monotonic() <= deadline
    result = dict(schema='bole.boundary-host-source-controls/v2', source_only=True,
        status='PASS_SOURCE_ONLY' if passed else 'FAIL_SOURCE_ONLY', error=error, stages=rows,
        inputs_unchanged=before == after, elapsed_s=time.monotonic()-started,
        probe_controls=11, integration_controls=8, projection_controls=16, capacity=capacity,
        NPU=False, original_twenty_sameimage_tests_replaced=False,
        numerical_qualified=False, paired_gate_pass=False, performance_admitted=False,
        formal_performance=False, task_accuracy=False)
    rr = write(OUT/'RESULT.json', result)
    print(json.dumps(dict(result=rr, status=result['status'], NPU=False)))
    return 0 if passed else 3


if __name__ == '__main__':
    raise SystemExit(main())
