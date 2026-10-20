"""Default-OFF MAIN finite same-image physical4/guest0 timing, then Devices[].

Prepared from the exact successful replay-v2 controller. Never invoke while
another MAIN unit owns admission. Containers are stopped and retained.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
import traceback

D = '/usr/bin/docker'
SMI = '/usr/local/sbin/npu-smi'
PYTHON = '/usr/local/python3.12.13/bin/python3'


def bootstrap(r):
    def checked(q):
        p = Path(q['path']); b = p.read_bytes()
        if (not p.is_absolute() or any(z.is_symlink() for z in (p, *p.parents)) or
                len(b) != q['bytes'] or hashlib.sha256(b).hexdigest() != q['sha256']):
            raise ValueError('exact owner source before imports')
        return p, b
    _, b = checked(r); x = json.loads(b); p, _ = checked(x['files']['timing_owner_common.py'])
    s = importlib.util.spec_from_file_location('_bole_timing_owner_common', str(p))
    C = importlib.util.module_from_spec(s); s.loader.exec_module(C)
    return C, C.package(r, __file__)


def main():
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument('--execute', action='store_true'); ap.add_argument('--inputs-ref'); ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    if not a.execute:
        print(json.dumps(dict(enabled=False, NPU=False, tensor_runtime_imported=False,
                              prepared_only=True, timing_complete=False, formal_success=False))); return 0
    if os.environ.get('BOLE_GDN3_TIMING_OWNER_ENABLE') != '1' or not a.inputs_ref or a.output is None:
        ap.error('explicit MAIN owner opt-in, exact reviewed inputs Ref3 and fresh output required')
    ir = json.loads(a.inputs_ref); C, x = bootstrap(ir); OUT = a.output
    C.need(OUT.is_absolute() and not OUT.exists() and not any(z.is_symlink() for z in (OUT, *OUT.parents)),
           'new ordinary output leaf; no replacement of prior replay/timing results')
    C.need(re.fullmatch(r'bole-gdn3-timing-[a-z0-9-]{1,72}', x['name']) and
           re.fullmatch(r'bole-gdn3-timing-reader-[a-z0-9-]{1,64}', x['reader_name']) and
           x['name'] != x['reader_name'], 'new unique preregistered owned names')
    OUT.mkdir(mode=0o700)
    start = time.monotonic(); cid = cpu_cid = None; primary = None; secondary = []
    manifest_ref = admission_ref = result_ref = release_ref = npu_owner_ref = independent_ref = None
    before = {}; child = None; original_admission = None

    def budget():
        C.need(time.monotonic()-start < C.PHASE, 'finite whole source/timing/consumer phase')
        used = sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
        C.need(used <= C.CAP, 'bounded whole-unit evidence/log output')

    def call(label, args, timeout=25):
        budget(); r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        C.need(len(r.stdout.encode())+len(r.stderr.encode()) <= 2**20, 'bounded controller command output')
        rr = C.write(OUT/(label+'-'+str(time.time_ns())+'.json'),
            dict(argv=args, exit_code=r.returncode, stdout=r.stdout, stderr=r.stderr,
                 elapsed=time.monotonic()-start))
        C.need(r.returncode == 0, label+' failed: '+r.stderr[-2000:])
        return r.stdout, rr

    def inspect(label, identity):
        s, _ = call(label, [D, 'inspect', identity]); rows = json.loads(s)
        C.need(type(rows) is list and len(rows) == 1, 'actual one-element Docker inspect')
        rr = C.write(OUT/(label+'-RAW-'+str(time.time_ns())+'.json'), rows)
        return rows[0], rr

    def smi(label):
        text, _ = call(label, [SMI, 'info'])
        rows = [tuple(map(int, m.groups())) for m in re.finditer(
            r'^\|\s*(\d+)\s+(\d+)\s*\|\s*(\d+)\s*\|', text, re.M)]
        for physical, chip, pid in rows:
            if physical not in (0, 1, 2, 3, 4):
                continue
            proc = Path('/proc')/str(pid)
            if not proc.exists():
                fresh, _ = call(label+'-FRESH', [SMI, 'info'])
                C.need(not re.search(r'^\|\s*'+str(physical)+r'\s+\d+\s*\|\s*'+str(pid)+r'\s*\|', fresh, re.M),
                       'unresolved observed PID disappearance')
                continue
            cg = (proc/'cgroup').read_text()
            if physical == 4:
                C.need(cid is not None and cid in cg and chip == 0, 'foreign physical4 process')
            else:
                C.need(cid is None or cid not in cg, 'owned process on protected physical0..3')
        return text

    def holders():
        dev = Path('/dev/davinci4').stat().st_rdev; found = []
        for p in Path('/proc').iterdir():
            if not p.name.isdigit(): continue
            try:
                for fd in (p/'fd').iterdir():
                    try:
                        if fd.stat().st_rdev == dev:
                            found.append(int(p.name)); break
                    except (FileNotFoundError, PermissionError, ProcessLookupError): pass
            except (FileNotFoundError, PermissionError, ProcessLookupError): pass
        return found

    def create_args(name, cpu=False):
        memory = '1g' if cpu else '8g'; cpus = '145' if cpu else '0,1,2,3'
        args = [D, 'create', '--name', name, '--label', 'model-tuning-lab.owner='+name,
            '--network=none', '--memory='+memory, '--memory-swap='+memory,
            '--cpus='+('1' if cpu else '4'), '--cpuset-cpus='+cpus,
            '--pids-limit='+('128' if cpu else '512'), '--read-only',
            '--tmpfs=/tmp:rw,exec,size='+str(64*2**20 if cpu else 2**30),
            '--shm-size='+('64m' if cpu else '1g'), '--cap-drop=ALL', '--security-opt=no-new-privileges']
        env = dict(C.ENV)
        if cpu:
            env.update(ASCEND_RT_VISIBLE_DEVICES='', BOLE_GDN3_TIMING_ENABLE='0',
                       BOLE_GDN3_TRITON_ENABLE='0', BOLE_GDN3_TIMING_CONSUME_ENABLE='1')
        for k, v in env.items(): args += ['--env', k+'='+v]
        mounts = {str(Path(r['path']).parent) for r in before.values()}
        for path in sorted(mounts):
            C.need(path != str(OUT) and not Path(path).is_relative_to(OUT), 'source/evidence never inside new writable output')
            args += ['--mount', 'type=bind,src='+path+',dst='+path+',readonly']
        args += ['--mount', 'type=bind,src='+str(OUT)+',dst='+str(OUT)]
        return args

    def stop_owned(identity, label, cpu=False):
        # No global kill/rm, no device reset. Cleanup rechecks only exact owned identity.
        value, _ = inspect(label+'-PRE', identity)
        name = x['reader_name'] if cpu else x['name']
        C.need(value['Id'] == identity and value['Image'] == C.IMAGE and
               value['Config']['Labels']['model-tuning-lab.owner'] == name, 'exact owned cleanup identity')
        if value['State']['Running']:
            call(label+'-STOP', [D, 'stop', '--time', '10', identity], 25)
        value, rr = inspect(label+'-FINAL', identity)
        C.device_inspection(value, cid=identity, running=False, name=name, cpu=cpu)
        return rr

    def logs_until_done(identity, label, cpu=False):
        nonlocal child
        with (OUT/(label+'.stdout')).open('x') as so, (OUT/(label+'.stderr')).open('x') as se:
            child = subprocess.Popen([D, 'logs', '--follow', identity], stdout=so, stderr=se)
            while True:
                budget()
                for path in (OUT/(label+'.stdout'), OUT/(label+'.stderr')):
                    C.need(path.stat().st_size <= 8*2**20, 'bounded retained child logs')
                value, _ = inspect(label+'-LIVE', identity)
                if not value['State']['Running']: break
                if not cpu: smi('LIVE')
                time.sleep(2)
            child.wait(timeout=15); child = None
        rr = C.write(OUT/(label+'-CHILD.json'), dict(exit_code=value['State']['ExitCode'],
            stdout=C.ref(OUT/(label+'.stdout')), stderr=C.ref(OUT/(label+'.stderr'))))
        C.need(value['State']['ExitCode'] == 0, 'actual '+label+' child failed')
        return rr

    def deadline(*_):
        raise TimeoutError('finite MAIN unit deadline')

    oldterm = signal.signal(signal.SIGTERM, deadline); oldalarm = signal.signal(signal.SIGALRM, deadline)
    signal.alarm(C.PHASE)
    try:
        driver, H, replay, receipts, original_admission, audit = C.prior_chain(x, installed=False)
        del driver, H, receipts, audit
        before = C.snapshot(x, ir)
        mem = next(int(v.split()[1])*1024 for v in Path('/proc/meminfo').read_text().splitlines()
                   if v.startswith('MemAvailable:'))
        disk = os.statvfs(OUT)
        C.need(mem >= 17*2**30 and disk.f_bavail*disk.f_frsize >= 2*2**30, 'bounded host memory/disk admission')
        text = smi('NPU-BEFORE'); C.need('No running processes found in NPU 4' in text and not holders(),
                                     'physical4 unoccupied before singleton admission')
        r23cid = C.inspection(original_admission['r23_controller_inspection'])['Id']
        old, old_ref = inspect('R23', r23cid)
        C.need(old['Image'] == C.IMAGE and old['State']['Running'] is False, 'actual original r23 remains stopped')
        C.write(OUT/'RESOURCE-ADMISSION.json', dict(owner_source=C.ref(__file__), inputs=ir,
            source_before=before, mem_available=mem, physical=[4], protected=[0, 1, 2, 3],
            phase_seconds=C.PHASE, cleanup_seconds=C.CLEANUP, output_cap_bytes=C.CAP,
            runtime_host_evidence=x['runtime_host_evidence'], runtime_container_refs=C.runtime_refs()))
        args = create_args(x['name'])
        args += ['--mount', 'type=bind,src=/usr/local/Ascend/driver,dst=/usr/local/Ascend/driver,readonly']
        for host, guest in (('/dev/davinci4', '/dev/davinci0'), ('/dev/davinci_manager', '/dev/davinci_manager'),
                            ('/dev/devmm_svm', '/dev/devmm_svm'), ('/dev/hisi_hdc', '/dev/hisi_hdc')):
            args += ['--device', host+':'+guest]
        args += ['--entrypoint', '/bin/bash', C.IMAGE, '-c',
            'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"', 'bole-gdn3-timing-bootstrap',
            PYTHON, '-I', '-B', x['files']['timing_boot.py']['path'], '--execute',
            '--inputs-ref', json.dumps(ir), '--root', str(OUT)]
        s, _ = call('CREATE', args); cid = s.strip(); C.need(re.fullmatch('[0-9a-f]{64}', cid), 'full created identity')
        value, _ = inspect('CREATED', cid)
        C.device_inspection(value, cid=cid, running=False, name=x['name'])
        C.write(OUT/'OWNED.json', dict(cid=cid, image=C.IMAGE, owner_source=C.ref(__file__), inputs=ir))
        call('START', [D, 'start', cid]); value, raw_ref = inspect('RUNNING', cid)
        C.device_inspection(value, cid=cid, running=True, name=x['name'])
        admission_ref = C.write(OUT/'ADMISSION.json', dict(schema='bole.gdn3-timing-owned-admission/v1',
            authority='MAIN', actual_source=replay['actual_source'], replay_result=x['timing_template']['replay_result'],
            independent_replay=x['timing_template']['replay_independent'], physical_devices=[4], logical_devices=[0],
            guest_device_path='/dev/davinci0', allow_hf32=False, image_digest=C.IMAGE,
            owned_container_id=cid, controller_inspection=raw_ref, environment=C.ENV))
        m = dict(x['timing_template'], admission=admission_ref)
        manifest_ref = C.write(OUT/'MANIFEST.json', m)
        C.final_manifest(x, manifest_ref, current=False)
        (OUT/'data').mkdir()
        # Atomic pointer is published only after real Running raw inspect/admission.
        temp = OUT/'MANIFEST-REF.pending'; C.write(temp, manifest_ref); os.rename(temp, OUT/'MANIFEST-REF.json')
        child_ref = logs_until_done(cid, 'TIMING')
        result_ref = C.ref(OUT/'data/TIMING-RESULT.json')
        stopped_ref = stop_owned(cid, 'TIMING-RELEASE')
        release_ref = C.write(OUT/'RELEASE.json', dict(schema='bole.gdn3-timing-owner-released/v1',
            authority='MAIN', timing_result=result_ref, admission=admission_ref,
            owner_stop_completed=True, controller_inspection=stopped_ref))
        smi('TIMING-AFTER'); C.need(not holders(), 'physical4 FD remains after owned stop')
        C.need(C.unchanged(before), 'all prior evidence/source bytes unchanged after actual timing')
        npu_owner_ref = C.write(OUT/'NPU-OWNER.json', dict(schema='bole.gdn3-finite-timing-npu-owner/v1',
            authority='MAIN', inputs=ir, owner_source=C.ref(__file__), cid=cid, manifest=manifest_ref,
            admission=admission_ref, timing_result=result_ref, release=release_ref, child=child_ref,
            source_before=before, source_after={p: C.ref(p) for p in before}, primary=None, secondary=[],
            physical=[4], protected=[0, 1, 2, 3], model_ready=False, E2E_measured=False, formal_success=False))
        (OUT/'consumer').mkdir()
        args = create_args(x['reader_name'], cpu=True)
        args += ['--entrypoint', PYTHON, C.IMAGE, '-I', '-B', x['files']['consume_timing.py']['path'],
            '--execute', '--inputs-ref', json.dumps(ir), '--manifest-ref', json.dumps(manifest_ref),
            '--result-ref', json.dumps(result_ref), '--owner-release-ref', json.dumps(release_ref),
            '--npu-owner-ref', json.dumps(npu_owner_ref), '--output', str(OUT/'consumer')]
        s, _ = call('CPU-CREATE', args); cpu_cid = s.strip()
        C.need(re.fullmatch('[0-9a-f]{64}', cpu_cid), 'full created Devices[] reader identity')
        value, cpu_created_ref = inspect('CPU-CREATED', cpu_cid)
        C.device_inspection(value, cid=cpu_cid, running=False, name=x['reader_name'], cpu=True)
        # Reader verifies this actual created inspection and its own cgroup after start.
        reader_admission = C.write(OUT/'READER-ADMISSION.json', dict(schema='bole.gdn3-timing-reader-admission/v1',
            authority='MAIN', cid=cpu_cid, image=C.IMAGE, controller_inspection=cpu_created_ref, inputs=ir))
        del reader_admission
        call('CPU-START', [D, 'start', cpu_cid]); logs_until_done(cpu_cid, 'READER', cpu=True)
        independent_ref = C.ref(OUT/'consumer/TIMING-INDEPENDENT.json')
        report = C.obj(independent_ref)
        C.need(report['independent_statistics_pass'] is True and report['NPU'] is False and
               report['timing_result'] == result_ref and report['owner_release'] == release_ref,
               'successful Devices[] all-frame statistics reader')
        C.need(C.unchanged(before), 'all source/prior evidence unchanged after reader')
    except BaseException as e:
        primary = dict(error=repr(e), traceback=traceback.format_exc())
    finally:
        signal.alarm(0); signal.signal(signal.SIGTERM, signal.SIG_IGN)
        # Independent finite cleanup window; callbacks still retain complete failure evidence.
        cleanup_start = time.monotonic()
        signal.signal(signal.SIGALRM, deadline); signal.alarm(C.CLEANUP)
        def budget():
            C.need(time.monotonic()-cleanup_start < C.CLEANUP, 'finite retained-owned cleanup')
        for identity, label, cpu in ((cpu_cid, 'CPU-CLEANUP', True), (cid, 'NPU-CLEANUP', False)):
            if identity:
                try: stop_owned(identity, label, cpu=cpu)
                except BaseException as e: secondary.append(dict(action=label, error=repr(e)))
        if child is not None:
            try:
                child.terminate(); child.wait(timeout=5)
            except BaseException as e: secondary.append(dict(action='OWNED-LOG-CLIENT', error=repr(e)))
        try: smi('NPU-AFTER'); C.need(not holders(), 'physical4 holder remains after cleanup')
        except BaseException as e: secondary.append(dict(action='FINAL-OBSERVATION', error=repr(e)))
        try:
            after = {p: C.ref(p) for p in before}; C.need(before == after, 'source/evidence changed')
        except BaseException as e:
            after = {}; secondary.append(dict(action='SOURCE-AFTER', error=repr(e)))
        signal.alarm(0); signal.signal(signal.SIGTERM, oldterm); signal.signal(signal.SIGALRM, oldalarm)
        result = dict(schema='bole.gdn3-finite-timing-owner/v1', authority='MAIN', owner_source=C.ref(__file__),
            inputs=ir, source_before=before, source_after=after, cid=cid, cpu_cid=cpu_cid,
            manifest=manifest_ref, admission=admission_ref, timing_result=result_ref, release=release_ref,
            npu_owner=npu_owner_ref, independent=independent_ref, primary=primary, secondary=secondary,
            elapsed=time.monotonic()-start, physical=[4], protected=[0, 1, 2, 3],
            containers_stopped_retained=not secondary, model_ready=False, E2E_measured=False,
            ten_percent_E2E_claim=False, formal_success=False)
        C.write(OUT/'RESULT.json', result)
        print(json.dumps({k: v for k, v in result.items() if k not in ('source_before', 'source_after')}, allow_nan=False))
    return 0 if primary is None and not secondary else 3


if __name__ == '__main__':
    raise SystemExit(main())
