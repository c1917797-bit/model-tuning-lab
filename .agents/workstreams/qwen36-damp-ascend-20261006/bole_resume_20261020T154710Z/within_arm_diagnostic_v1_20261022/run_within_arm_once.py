"""Bound one retained-evidence diagnosis; no containers, Torch, or NPU work."""
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

sys.dont_write_bytecode = True
SOURCE = Path(__file__).parent / 'within_arm_diagnostic_v1.py'
EXPECTED = 'f552d60119f77816cd5c29091b7335d90c4dd457b64665e95308b9d0a4ab71c6'
OUTPUT = Path('/opt/host/vnf/austinov/run-bole-within-arm-diagnostic-v1-20261022T074559Z')

def ref(p):
    b = p.read_bytes()
    return dict(path=str(p), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())

def exclusive(p, obj):
    with p.open('x') as f:
        json.dump(obj, f, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n')

def limits():
    resource.setrlimit(resource.RLIMIT_AS, (512*2**20, 512*2**20))
    resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16*2**20, 16*2**20))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

def main():
    before = ref(SOURCE)
    if before['bytes'] != 19935 or before['sha256'] != EXPECTED:
        raise RuntimeError('exact reviewed diagnostic source required')
    OUTPUT.mkdir(exist_ok=False)
    (OUTPUT/'tmp').mkdir()
    env = dict(os.environ, TMPDIR=str(OUTPUT/'tmp'), PYTHONDONTWRITEBYTECODE='1')
    started = time.time()
    command = ['/usr/bin/python3', '-I', '-B', str(SOURCE), '--output', str(OUTPUT/'WITHIN_ARM_DIAGNOSTIC.json')]
    timed_out = False
    with (OUTPUT/'stdout').open('xb') as stdout, (OUTPUT/'stderr').open('xb') as stderr:
        try:
            completed = subprocess.run(command, stdout=stdout, stderr=stderr, env=env,
                timeout=120, preexec_fn=limits, check=False)
            code = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            code = 124
    after = ref(SOURCE)
    evidence = dict(schema='bole.retained-within-arm-diagnostic-execution/v1',
        source_before=before, source_after=after, source_unchanged=before==after,
        runner=ref(Path(__file__)), command=command, started_epoch=started,
        ended_epoch=time.time(), exit_code=code, timed_out=timed_out,
        stdout=ref(OUTPUT/'stdout'), stderr=ref(OUTPUT/'stderr'),
        diagnostic=None if not (OUTPUT/'WITHIN_ARM_DIAGNOSTIC.json').exists() else ref(OUTPUT/'WITHIN_ARM_DIAGNOSTIC.json'),
        NPU_executed=False, paired_gate_pass=False, performance_admitted=False)
    exclusive(OUTPUT/'EXECUTION.json', evidence)
    print(json.dumps(dict(execution=ref(OUTPUT/'EXECUTION.json'), **evidence), sort_keys=True))
    if before != after:
        raise RuntimeError('diagnostic source changed')
    return code

if __name__ == '__main__':
    raise SystemExit(main())
