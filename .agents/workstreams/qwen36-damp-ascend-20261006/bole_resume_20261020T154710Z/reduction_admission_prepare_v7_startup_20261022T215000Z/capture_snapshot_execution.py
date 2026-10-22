"""MAIN exact readonly snapshot child capture. Default OFF, exclusive outputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent
PROGRAM = HERE / "final_snapshot_ON_v7_startup.py"
PIN = (41681, 'faa3690519541a31fb28b57bd377c3e8a6b2e6f992880684f26af6e40cd4e53f')
OUTPUT = Path('/opt/host/vnf/austinov/run-bole-reduction-v7-startup-snapshot-20261022T215000Z-v1')
CAP = 16 * 2**20

def ref(path):
    assert path.is_file() and not any(p.is_symlink() for p in (path, *path.parents))
    b = path.read_bytes()
    return dict(path=str(path), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())

def write(path, body):
    with path.open("xb") as f:
        assert f.write(body) == len(body)
        f.flush()
        os.fsync(f.fileno())
    return ref(path)

def main():
    p = argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument("--execute-readonly", action="store_true")
    a = p.parse_args()
    if not a.execute_readonly:
        print(json.dumps(dict(enabled=False, NPU=False)))
        return 0
    before = ref(PROGRAM)
    assert (before["bytes"], before["sha256"]) == PIN
    assert not OUTPUT.exists() and not any(p.is_symlink() for p in OUTPUT.parents)
    assert time.time() + 3780 < 1792710600
    OUTPUT.mkdir(mode=0o700)
    os.umask(0o077)
    argv = ["/usr/bin/python3", "-I", "-B", str(PROGRAM), "--execute-readonly"]
    started = time.time()
    timedout = False
    child = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    try:
        stdout, stderr = child.communicate(timeout=195)
    except subprocess.TimeoutExpired:
        timedout = True
        os.killpg(child.pid, signal.SIGTERM)
        try:
            stdout, stderr = child.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            stdout, stderr = child.communicate(timeout=5)
    ended = time.time()
    after = ref(PROGRAM)
    assert len(stdout) <= CAP and len(stderr) <= 2**20
    outref = write(OUTPUT / "SNAPSHOT.json", stdout)
    errref = write(OUTPUT / "snapshot.stderr", stderr)
    record = dict(schema="bole.final-readonly-snapshot-execution/v1", actual_argv=argv,
        started_epoch=started, ended_epoch=ended, exit_code=child.returncode,
        child_reaped=child.poll() is not None, timeout=timedout,
        source_before=before, source_after=after, source_unchanged=before == after,
        stdout=outref, stderr=errref, NPU=False, resource_admission=False)
    rr = write(OUTPUT / "EXECUTION.json", (json.dumps(record, sort_keys=True)+"\n").encode())
    print(json.dumps(dict(execution=rr, snapshot=outref, exit_code=child.returncode, timeout=timedout)))
    return 0 if child.returncode == 0 and not timedout and before == after and not stderr else 3

if __name__ == "__main__":
    raise SystemExit(main())
