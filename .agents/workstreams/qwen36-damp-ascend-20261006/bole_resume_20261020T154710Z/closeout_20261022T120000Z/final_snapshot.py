"""Explicit read-only final host snapshot; stdout only, no resource admission.

Loads one exact previously reviewed helper. No model imports, NPU requests,
new owners, container mutation, stop/delete, bind/listen or filesystem writes.
Only newly spawned read-only CLI children can be stopped by that frozen helper
if their own inspection deadline expires. Arbitrary container env is not emitted.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import signal
import sys
import time

sys.dont_write_bytecode = True
WS = Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
HELPER = dict(path=str(WS/'boundary_admission_v4_20261022/fresh_snapshot_v4.py'),
    bytes=19376, sha256='8c0b3105354708f3942f798d67a057ef16e11c5b10b538106166dafce61c1968')
CONFIG = WS/'boundary_admission_v4_20261022/CONFIG.json'
DIAGNOSTIC = dict(path='/opt/host/vnf/austinov/run-bole-boundary-reader-v2-20261022T080000Z/BOUNDARY_DIAGNOSTIC.json',
    bytes=5011374, sha256='c2260812c8bda323b4b0b363f770c6becb9a613ee1e1c850b456f6a9a852d9f2')
OLD_OUTPUT = Path('/opt/host/vnf/austinov/run-bole-boundary-ON-v1-20261022T080000Z')
NEW_OUTPUT = Path('/opt/host/vnf/austinov/run-bole-boundary-ON-v2-20261022T100000Z')
IMAGE = 'sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
BOUNDARY_SOURCE_SHA = '702e3feba7de9e4365b472189c9bf0662fdc35f1e08e0e535c863b62e132dbdc'
FIRST_FOUR = {
    '40c6b48039182b29b47a4a4283ba17f414570f5a5465d6c2865a0b595866b45a',
    '54246001fc180995c8e021a27f8f5b14f237fe6e92dd62dcb4acadc3dfae0411',
    'c4a669cc4b20e5f013e92ce22ac89f6eccf7236286464bd2f7b7b8ac9bf3bdc9',
    '961b3501d0b739216264e2027115a3245d0e391709a408ed9ac2943bcd1f083d'}
LATEST = {
    'cpu-preflight': '6433f9740a1acc4be305d35456436dbccdaf0a91d6884e283259ea22dec99ef5',
    'dense': 'a25d55a819562ffbf2135ba1017bb52ae2e3ca9c3ee2998486540bbbaebd4cf0'}
UNITS = ('bole-short-on-v2-model-20261021t123841z.service',
         'bole-short-off-v2-model-20261021t123841z.service',
         'bole-boundary-on-v1-model-20261022t080000z.service')
CUTOFF = 1792672721
CAP = 16 * 2**20


def need(value, why):
    if not value:
        raise ValueError(why)


def read_ref(path, cap=8 * 2**20, expected=None):
    path = Path(path)
    need(path.is_absolute() and path.is_file() and
         not any(p.is_symlink() for p in (path, *path.parents)),
         'ordinary absolute read-only input')
    before = path.stat()
    need(0 <= before.st_size <= cap, 'whole input read cap')
    with path.open('rb') as stream:
        body = stream.read(cap + 1)
    identity = lambda value: (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
        value.st_uid, value.st_gid, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    need(len(body) <= cap and identity(path.stat()) == identity(before),
         'whole input identity unchanged during read; access-time changes excluded')
    actual = dict(path=str(path), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    need(expected is None or actual == expected, 'exact whole expected input Ref3')
    return actual, body


def latest_identities(H, manifest):
    """Use only saved inspect Ref3s inside the independently pinned readset.

    Missing historical join stays explicit. Current Docker inspect cannot be
    used to fabricate a historical name/label expectation.
    """
    references = manifest['inputs_before']
    need(type(references) is list and len(references) <= 16384,
         'bounded original independent input set')
    pins = {}
    for ref in references:
        need(type(ref) is dict and set(ref) == {'path', 'bytes', 'sha256'} and
             type(ref['path']) is str and type(ref['bytes']) is int and
             type(ref['sha256']) is str and re.fullmatch('[0-9a-f]{64}', ref['sha256']),
             'typed original input Ref3')
        need(ref['path'] not in pins or pins[ref['path']] == ref, 'unique original input identity')
        pins[ref['path']] = ref
    expected, evidence = [], []
    for arm, cid in LATEST.items():
        baseline = dict(id=cid, image=IMAGE)
        candidates = sorted((ref for ref in pins.values()
            if Path(ref['path']).parent == OLD_OUTPUT/arm and
            re.fullmatch('inspect-[0-9]+\\.json', Path(ref['path']).name)),
            key=lambda ref: ref['path'], reverse=True)
        row = dict(arm=arm, id=cid, historical_join_proven=False,
            candidate_count=len(candidates), inspected_refs=[],
            reason='no matching saved inspect in independently pinned readset')
        need(len(candidates) <= 32, 'bounded saved-inspect candidate closure')
        for candidate in candidates:
            H.bounded()
            try:
                pin, body = read_ref(candidate['path'], expected=candidate)
                envelope = json.loads(body)
                need(type(envelope) is dict and type(envelope.get('stdout')) is str,
                     'saved inspect command envelope with literal stdout')
                values = json.loads(envelope['stdout'])
                need(type(values) is list and len(values) == 1 and type(values[0]) is dict,
                     'one complete saved Docker inspect object')
                actual = values[0]
                row['inspected_refs'].append(pin)
                if actual.get('Id') != cid:
                    continue
                labels = {k:v for k,v in (actual['Config'].get('Labels') or {}).items()
                          if k.startswith('model-tuning-lab.')}
                need(actual['Image'] == IMAGE and type(actual['Name']) is str and
                     actual['Name'].startswith('/') and
                     labels.get('model-tuning-lab.source-manifest-sha256') == BOUNDARY_SOURCE_SHA and
                     labels.get('model-tuning-lab.arm') == arm and
                     labels.get('model-tuning-lab.run') == actual['Name'][1:],
                     'saved exact historical CID/image/source/name/arm join')
                baseline.update(name=actual['Name'], labels=labels)
                row.update(historical_join_proven=True, reason=None, saved_inspect=pin)
                break
            except Exception as exc:
                row['reason'] = type(exc).__name__ + ': ' + str(exc)
                H.fail('historical saved inspect read/join failed for exact arm ' + arm)
                break
        expected.append(baseline)
        evidence.append(row)
    return expected, evidence


def ids_from_inventory(H, result):
    need(result['exit_code'] == 0 and result['error'] is None, 'complete running container inventory')
    ids = result['stdout'].split()
    need(len(ids) <= 4096 and len(set(ids)) == len(ids) and
         all(re.fullmatch('[0-9a-f]{64}', cid) for cid in ids),
         'bounded exact running Docker CIDs')
    return ids


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--execute-readonly', action='store_true')
    args = parser.parse_args()
    if not args.execute_readonly:
        print(json.dumps(dict(enabled=False, NPU=False, resources_admitted=False)))
        return 0
    started = time.monotonic()
    result = dict(schema='bole.final-readonly-host-snapshot/v1', readonly=True,
        NPU=False, owner_created=False, container_started=False, container_modified=False,
        existing_process_signalled=False, resources_admitted=False,
        candidate_qualification=False, numerical_qualified=False,
        paired_gate_pass=False, performance_admitted=False, formal_performance=False)
    H = None
    errors = []
    rereads = []
    def alarm(signum, frame):
        raise TimeoutError('final read-only snapshot whole180-second guard')
    signal.signal(signal.SIGALRM, alarm)
    signal.alarm(180)
    try:
        os.sched_setaffinity(0, {166})
        need(os.sched_getaffinity(0) == {166}, 'host CPU166 inspection affinity')
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        need(hard == resource.RLIM_INFINITY, 'infinite hard AS required for frozen Go CLI wrapper')
        resource.setrlimit(resource.RLIMIT_AS, (512 * 2**20, hard))
        helper_ref, helper_body = read_ref(HELPER['path'], cap=2**20, expected=HELPER)
        spec = importlib.util.spec_from_file_location('_bole_frozen_final_snapshot_helper', HELPER['path'])
        H = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = H
        spec.loader.exec_module(H)
        H.START = started
        H.ERRORS = errors
        need(H.CUTOFF == CUTOFF and H.MAX_INSPECTION_SECONDS == 180 and
             H.MAX_FINAL_BYTES == CAP and H.DOCKER == '/usr/bin/docker' and
             H.SMI == '/usr/local/sbin/npu-smi', 'unchanged reviewed helper constants')
        rereads.append(helper_ref)
        result['observed_start_utc'] = H.utc()
        epoch = time.time()
        result['clock'] = dict(epoch=epoch, cutoff_epoch=CUTOFF,
            seconds_until_cutoff=CUTOFF-epoch, original_prepare3780_fits=epoch+3780<CUTOFF,
            original_source_whole3600_fits=epoch+3600<CUTOFF,
            time_observation_is_not_authority_extension=True)
        config_ref, config_body = read_ref(CONFIG)
        rereads.append(config_ref)
        config = json.loads(config_body)
        old = config['old_containers']
        need(type(old) is list and len(old) == 4 and {r['id'] for r in old} == FIRST_FOUR and
             all(r['image'] == IMAGE and type(r.get('name')) is str and
                 type(r.get('labels')) is dict for r in old),
             'exact first four configured historical owners')
        lock = Path(config.get('main_lock', config.get('MAIN_lock', '')))
        need(lock == WS/'MAIN_ADMISSION.lock' and config.get('fixed_cutoff') == CUTOFF,
             'one original MAIN lock and unchanged hard deadline')
        diagnostic_ref, diagnostic_body = read_ref(DIAGNOSTIC['path'], expected=DIAGNOSTIC)
        rereads.append(diagnostic_ref)
        latest, joins = latest_identities(H, json.loads(diagnostic_body))
        old = list(old) + latest
        need(len(old) == 6 and len({r['id'] for r in old}) == 6,
             'all six distinct exact historical CIDs')
        result['historical_identity_inputs'] = dict(helper=helper_ref, config=config_ref,
            first_four_from_config=True, first_four_OWNED_not_rederived_here=True,
            independent_diagnostic=diagnostic_ref, latest_two_saved_inspect_joins=joins)
        for row in joins:
            rereads.extend(row['inspected_refs'])
        result['self_process'] = H.proc(os.getpid())
        result['smi_before'] = H.run([H.SMI, 'info'])
        result['memory_before'] = H.read('/proc/meminfo').decode()
        result['main_lock'] = H.path_info(lock)
        result['kernel_locks_before'] = H.read('/proc/locks').decode()
        result['main_lock_kernel_matches_before'] = H.lock_matches(lock, result['kernel_locks_before'])
        result['devices_and_actual_holders'] = H.device_holders(lock)
        result['device_note'] = ('Physical0-7 inspected read-only; only physical4-7 are task targets. '
            'Declarations and visibility variables are not proof of actual allocation.')
        paths = [Path('/cache/efim/Qwen3.6-27B'), WS, OLD_OUTPUT,
                 WS/'bound-boundary-ON-v1-20261022T080000Z',
                 WS/'bound-boundary-ON-v2-20261022T100000Z', NEW_OUTPUT, Path(str(NEW_OUTPUT)+'-CPU')]
        result['paths_and_disks'] = [H.path_info(path) for path in paths]
        result['running_inventory_before'] = H.run([H.DOCKER, 'ps', '-q', '--no-trunc'])
        running = ids_from_inventory(H, result['running_inventory_before'])
        all_ids = sorted(set(running) | {r['id'] for r in old})
        need(len(all_ids) <= 4096, 'bounded full current/old Docker union')
        result['inspect_before'] = H.inspect(all_ids)
        result['old_before'] = H.old_identity(result['inspect_before']['containers'], old)
        result['docker_top_before'] = [H.run([H.DOCKER, 'top', cid, '-eo',
            'pid,ppid,uid,lstart,comm']) for cid in running]
        result['old_units'] = [H.run(['/usr/bin/systemctl', 'show', unit, '--no-pager',
            '--property=Id,LoadState,ActiveState,SubState,MainPID,ControlPID,Result,ExecMainStatus,ControlGroup'])
            for unit in UNITS]
        result['docker_unit'] = H.run(['/usr/bin/systemctl', 'show', 'docker.service', '--no-pager',
            '--property=MainPID,ControlGroup,ActiveState,SubState'])
        result['host_listeners_8230'] = H.run(['/usr/sbin/ss', '-lntp', 'sport = :8230'])
        result['host_listener_note'] = 'Host namespace observation only; network-none containers have their own loopback.'
        engine = H.run([H.DOCKER, 'info', '--format', '{{json .}}'])
        raw = engine.pop('stdout')
        engine.update(stdout_bytes=len(raw.encode()), stdout_sha256=hashlib.sha256(raw.encode()).hexdigest())
        result['engine_command'] = engine
        if not engine['error'] and engine['exit_code'] == 0:
            info = json.loads(raw)
            result['engine'] = {k:info.get(k) for k in ('NCPU','DockerRootDir','ServerVersion','CgroupDriver','CgroupVersion')}
            result['docker_disk'] = H.path_info(info['DockerRootDir'])
        result['memory_after'] = H.read('/proc/meminfo').decode()
        result['inspect_old_after'] = H.inspect([r['id'] for r in old])
        result['old_after'] = H.old_identity(result['inspect_old_after']['containers'], old)
        before = {r['Id']:r for r in result['inspect_before']['containers']}
        after = {r['Id']:r for r in result['inspect_old_after']['containers']}
        result['old_identity_state_stable_during_snapshot'] = all(
            cid in before and cid in after and all(before[cid][k] == after[cid][k]
                for k in ('Id','Name','Image','State','ExecIDs','labels')) for cid in (r['id'] for r in old))
        result['running_inventory_after'] = H.run([H.DOCKER, 'ps', '-q', '--no-trunc'])
        running_after = ids_from_inventory(H, result['running_inventory_after'])
        result['running_inventory_stable'] = set(running) == set(running_after)
        new_running = sorted(set(running_after) - set(running))
        result['newly_running_inspect'] = H.inspect(new_running)
        result['newly_running_top'] = [H.run([H.DOCKER, 'top', cid, '-eo',
            'pid,ppid,uid,lstart,comm']) for cid in new_running]
        result['smi_after'] = H.run([H.SMI, 'info'])
        result['kernel_locks_after'] = H.read('/proc/locks').decode()
        result['main_lock_kernel_matches_after'] = H.lock_matches(lock, result['kernel_locks_after'])
        for reference in rereads:
            read_ref(reference['path'], expected=reference)
        result['evidence_inputs_unchanged'] = True
        result['aggregate_peak_rss'] = H.rss(['final_snapshot.py'])
    except BaseException as exc:
        errors.append(type(exc).__name__ + ': ' + str(exc))
    finally:
        signal.alarm(0)
    result.update(observed_end_epoch=time.time(), elapsed_seconds=time.monotonic()-started,
        errors=errors, complete=not errors, input_refs=rereads,
        remaining_required='Observation only; no owner/resource/model-readiness or experimental admission is produced.')
    encoded = json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False)
    if len(encoded.encode()) > CAP:
        encoded = json.dumps(dict(schema=result['schema'], complete=False,
            error='snapshot exceeds unchanged16MiB final cap; observations omitted, not truncated JSON',
            NPU=False, resources_admitted=False, original_encoded_bytes=len(encoded.encode())), sort_keys=True)
        print(encoded)
        return 2
    print(encoded)
    return 0 if not errors else 2


if __name__ == '__main__':
    raise SystemExit(main())
