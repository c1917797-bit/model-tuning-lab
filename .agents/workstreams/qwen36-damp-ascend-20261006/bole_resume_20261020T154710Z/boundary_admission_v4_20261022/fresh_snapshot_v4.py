"""Read-only host observations for MAIN review; never an owner admission.

No model imports, Docker exec/start/stop/create, signals to existing processes,
bind/listen, flock, or filesystem writes. JSON goes to stdout; MAIN retains it
in a fresh owned path. A timed-out read CLI created by this helper is stopped.
All IDs, lock paths and old units are supplied by MAIN from actual old receipts.
Inspection limits bound this helper only, never replace source-owned thresholds.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import selectors
import shutil
import stat
import subprocess
import time

CUTOFF = 1792672721
DOCKER = '/usr/bin/docker'
PRLIMIT = '/usr/bin/prlimit'
SMI = '/usr/local/sbin/npu-smi'
MAX_COMMAND_BYTES = 8 * 1024**2
MAX_FINAL_BYTES = 16 * 1024**2
MAX_INSPECTION_SECONDS = 180
ERRORS = []
START = None


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def fail(message):
    ERRORS.append(str(message))


def need(value, message):
    if not value:
        raise ValueError(message)


def bounded():
    need(time.monotonic() - START < MAX_INSPECTION_SECONDS,
         'inspection deadline exhausted; no complete snapshot')


def read(path, limit=1024**2):
    bounded()
    with open(path, 'rb') as stream:
        raw = stream.read(limit + 1)
    need(len(raw) <= limit, 'inspection read cap: ' + str(path))
    return raw


def wrapper(argv):
    return [PRLIMIT, "--as=unlimited", "--", *argv] if argv[0] == DOCKER else list(argv)


def rss(actual_argv):
    own = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    child = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    need(own + child <= 512 * 1024,
         'host+CLI cumulative peak512MiB; own_kib=%r child_kib=%r aggregate_kib=%r cap_kib=%r actual_argv=%r'
         % (own, child, own + child, 512 * 1024, list(actual_argv)))
    return dict(host_peak_rss_kib=own, child_peak_rss_kib=child,
                aggregate_rss_kib=own + child)


def configure_address_space():
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    need(hard == resource.RLIM_INFINITY, 'original Go child AS wrapper requires infinite hard AS')
    resource.setrlimit(resource.RLIMIT_AS, (512 * 2**20, hard))


def run(argv, cap=20):
    """Only caller-fixed read commands; enforce a real bounded pipe buffer."""
    bounded()
    began = time.monotonic()
    requested = list(argv)
    actual = wrapper(requested)
    p = subprocess.Popen(actual, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, close_fds=True)
    output = {'stdout': bytearray(), 'stderr': bytearray()}
    selector = selectors.DefaultSelector()
    for key in output:
        selector.register(getattr(p, key), selectors.EVENT_READ, key)
    error = None
    try:
        while selector.get_map():
            bounded()
            need(time.monotonic() - began < cap, 'read command timeout')
            for key, _ in selector.select(.1):
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                output[key.data].extend(chunk)
                need(sum(map(len, output.values())) <= MAX_COMMAND_BYTES,
                     'read command output cap; no truncation accepted')
        p.wait(timeout=1)
    except BaseException as exc:
        error = type(exc).__name__ + ': ' + str(exc)
        # Only our own newly created read-only CLI may be terminated on timeout.
        # No existing process, service, container or lock is changed.
        p.kill()
        p.wait(timeout=2)
    finally:
        selector.close()
        p.stdout.close()
        p.stderr.close()
    usage = rss(actual)
    result = dict(argv=actual, requested_argv=requested, actual_argv=actual,
                  rss=usage, observed_utc=utc(), exit_code=p.returncode,
                  error=error, **{k: bytes(v).decode('utf8', 'replace')
                                 for k, v in output.items()})
    if error or p.returncode:
        fail('read command incomplete: ' + repr(argv))
    return result


def proc(pid):
    root = Path('/proc') / str(pid)
    first = read(root / 'stat').decode()
    fields = first[first.rfind(')') + 2:].split()
    status = read(root / 'status').decode()
    command = read(root / 'cmdline')
    value = dict(pid=pid, start_ticks=int(fields[19]), state=fields[0],
                 executable=os.readlink(root / 'exe'),
                 cgroup=read(root / 'cgroup').decode(),
                 status={line.split(':', 1)[0]: line.split(':', 1)[1].strip()
                         for line in status.splitlines()
                         if line.startswith(('Name:', 'Uid:', 'Gid:', 'NSpid:',
                                             'Cpus_allowed_list:', 'Mems_allowed_list:',
                                             'VmRSS:', 'Threads:'))},
                 cpu_affinity=sorted(os.sched_getaffinity(pid)),
                 cmdline_sha256=hashlib.sha256(command).hexdigest(),
                 cmdline_bytes=len(command))
    last = read(root / 'stat').decode()
    need(int(last[last.rfind(')') + 2:].split()[19]) == value['start_ticks'],
         'PID identity changed during read')
    # No environment or arbitrary command-line secrets are copied to stdout.
    return value


def path_info(path):
    p = Path(path)
    value = dict(path=str(p), exists=p.exists(), lexists=os.path.lexists(p),
                 is_symlink=p.is_symlink())
    nearest = p
    while not nearest.exists():
        need(nearest != nearest.parent, 'no existing path ancestor')
        nearest = nearest.parent
    usage = shutil.disk_usage(nearest)
    value.update(nearest_existing=str(nearest), resolved=str(p.resolve()),
                 filesystem_dev=nearest.stat().st_dev,
                 disk_total_bytes=usage.total, disk_used_bytes=usage.used,
                 disk_free_bytes=usage.free)
    if value['lexists']:
        s = p.lstat()
        value.update(mode=stat.S_IMODE(s.st_mode), uid=s.st_uid, gid=s.st_gid,
                     inode=s.st_ino, device=s.st_dev, size=s.st_size,
                     mtime_ns=s.st_mtime_ns)
    return value


def device_holders(lock):
    device_nodes = {}
    for index in range(8):
        p = Path('/dev/davinci' + str(index))
        s = p.stat()
        need(stat.S_ISCHR(s.st_mode), 'davinci node not a character device')
        device_nodes[index] = dict(path=str(p), major=os.major(s.st_rdev),
                                  minor=os.minor(s.st_rdev), rdev=s.st_rdev)
    lock_stat = lock.stat() if lock.exists() else None
    records, lock_holders, races = [], [], []
    roots = [p for p in Path('/proc').iterdir() if p.name.isdigit()]
    need(len(roots) <= 16384, 'original process inventory cap exceeded')
    for root in roots:
        bounded()
        try:
            fds = list((root / 'fd').iterdir())
            need(len(fds) <= 16384, 'original per-process FD cap exceeded')
            hits, locks = [], []
            for fd in fds:
                try:
                    s = fd.stat()
                    for index, node in device_nodes.items():
                        if stat.S_ISCHR(s.st_mode) and s.st_rdev == node['rdev']:
                            hits.append(dict(fd=int(fd.name), physical=index,
                                             target=os.readlink(fd)))
                    if lock_stat and (s.st_dev, s.st_ino) == (lock_stat.st_dev, lock_stat.st_ino):
                        locks.append(int(fd.name))
                except FileNotFoundError:
                    continue
            if hits or locks:
                who = proc(int(root.name))
                if hits:
                    records.append(dict(**who, device_fds=hits))
                if locks:
                    lock_holders.append(dict(**who, lock_fds=locks))
        except (FileNotFoundError, ProcessLookupError):
            races.append(int(root.name))
        except PermissionError:
            fail('unreadable actual FD ownership at ' + str(root))
    return dict(nodes=device_nodes, actual_holders=records,
                actual_lock_fd_holders=lock_holders,
                disappeared_processes=races, process_count=len(roots))


def inspect(ids):
    commands = []
    projected = []
    for cid in ids:
        result = run([DOCKER, 'inspect', cid])
        raw = result.pop('stdout')
        result['stdout_bytes'] = len(raw.encode())
        result['stdout_sha256'] = hashlib.sha256(raw.encode()).hexdigest()
        commands.append(result)
        if result['error'] or result['exit_code']:
            continue
        rows = json.loads(raw)
        need(type(rows) is list and len(rows) == 1 and type(rows[0]) is dict and
             rows[0].get('Id') == cid, 'one complete exact requested CID inspect')
        row = rows[0]
        h, c = row['HostConfig'], row['Config']
        projected.append(dict(Id=row['Id'], Name=row['Name'], Image=row['Image'],
            State=row['State'], ExecIDs=row.get('ExecIDs'),
            labels={k:v for k,v in (c.get('Labels') or {}).items()
                    if k.startswith('model-tuning-lab.')},
            resources={k:h.get(k) for k in ('Memory', 'MemorySwap', 'NanoCpus',
                'CpusetCpus', 'CpusetMems', 'PidsLimit', 'Privileged', 'IpcMode',
                'NetworkMode', 'ShmSize', 'ReadonlyRootfs', 'DeviceRequests',
                'DeviceCgroupRules', 'Devices', 'PortBindings', 'LogConfig')},
            mounts=[{k:m.get(k) for k in ('Type','Source','Destination','RW')}
                    for m in row.get('Mounts', [])],
            visible_devices=[s for s in (c.get('Env') or [])
                             if s.startswith('ASCEND_RT_VISIBLE_DEVICES=')]))
    # Raw inspect includes arbitrary environment; neither success nor failure
    # can retain or print it. Each command receipt contains size/SHA only.
    return dict(commands=commands, containers=projected)


def old_identity(rows, expected):
    by_id = {r['Id']:r for r in rows}
    out = []
    for want in expected:
        row = by_id.get(want['id'])
        same = bool(row and row['Id'] == want['id'] and row['Image'] == want['image'])
        full = bool(same and all(k in want for k in ('name', 'labels')) and
                    row['Name'] == want['name'] and row['labels'] == want['labels'])
        released = bool(same and row['State']['Running'] is False and
                        row['State']['Pid'] == 0 and not row['ExecIDs'] and
                        row['State']['OOMKilled'] is False)
        out.append(dict(id=want['id'], expected_identity_matches=same,
                        complete_historical_owner_identity_checked=full,
                        stopped_pid0_noexec_nooom_observed=released))
    return out


def lock_matches(path, raw):
    if not path.exists():
        return []
    s = path.stat()
    wanted = (os.major(s.st_dev), os.minor(s.st_dev), s.st_ino)
    matches = []
    for line in raw.splitlines():
        for field in line.split():
            match = re.fullmatch('([0-9a-fA-F]+):([0-9a-fA-F]+):([0-9]+)', field)
            if match and (int(match[1], 16), int(match[2], 16), int(match[3])) == wanted:
                matches.append(line)
    return matches


def main():
    global START
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--config', required=True)
    parser.add_argument('--execute-readonly', action='store_true')
    args = parser.parse_args()
    if not args.execute_readonly:
        print(json.dumps(dict(enabled=False, NPU=False, resources_admitted=False)))
        return 0
    START = time.monotonic()
    config = json.loads(read(args.config))
    if 'old_containers' in config:
        old = config['old_containers']
    else:
        # MAIN's old CID list is sufficient for read-only exact-ID inspection.
        # It does not replace the original OWNED/source/name/label join.
        old = [dict(id=cid, image='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1')
               for cid in config['old_cids']]
    need(len(old) == 4 and len({r['id'] for r in old}) == 4,
         'MAIN must provide all four distinct exact old CIDs')
    for r in old:
        need(re.fullmatch('[0-9a-f]{64}', r['id']) and
             re.fullmatch('sha256:[0-9a-f]{64}', r['image']), 'exact historical IDs required')
        if 'labels' in r or 'name' in r:
            need(r['name'].startswith('/') and
                 set(r['labels']) == {'model-tuning-lab.owner','model-tuning-lab.run',
                    'model-tuning-lab.arm','model-tuning-lab.source-manifest-sha256',
                    'model-tuning-lab.controller-sha256'}, 'complete optional historical owner identity')
    units = config['old_units']
    need(units and all(re.fullmatch('[A-Za-z0-9_.@:-]+\\.(service|scope)', u)
                       for u in units), 'MAIN must supply exact old unit names')
    lock = Path(config['main_lock'] if 'main_lock' in config else config['MAIN_lock'])
    paths = config.get('new_outputs') or [config['output_root'], config['output_root']+'-CPU']
    need(config.get('fixed_cutoff', CUTOFF) == CUTOFF and
         config.get('model_root', '/cache/efim/Qwen3.6-27B') == '/cache/efim/Qwen3.6-27B',
         'unchanged original deadline and model')
    need(lock.is_absolute() and len(paths) == 2 and len(set(paths)) == 2 and
         all(Path(p).is_absolute() for p in paths), 'explicit absolute MAIN lock and two new output roots')
    result = dict(schema='bole.fresh-readonly-host-snapshot/v2', observed_start_utc=utc(),
        readonly=True, NPU=False, container_started=False, container_modified=False,
        resources_admitted=False, candidate_qualification=False,
        inspection_caps_not_owner_thresholds=dict(seconds=MAX_INSPECTION_SECONDS,
            command_bytes=MAX_COMMAND_BYTES, final_bytes=MAX_FINAL_BYTES))
    try:
        os.sched_setaffinity(0, {166})
        need(os.sched_getaffinity(0) == {166}, 'actual original host166 affinity')
        configure_address_space()
        epoch = time.time()
        result['clock'] = dict(epoch=epoch, cutoff_epoch=CUTOFF,
            seconds_until_cutoff=CUTOFF-epoch,
            original_source_whole3600_fits=epoch+3600<CUTOFF,
            original_prepare3780_fits=epoch+3780<CUTOFF)
        result['self_process'] = proc(os.getpid())
        result['smi_before'] = run([SMI, 'info'])
        result['memory_before'] = read('/proc/meminfo').decode()
        result['main_lock'] = path_info(lock)
        result['kernel_locks_before'] = read('/proc/locks').decode()
        result['main_lock_kernel_matches_before'] = lock_matches(lock, result['kernel_locks_before'])
        result['devices_and_actual_holders'] = device_holders(lock)
        result['new_outputs'] = [path_info(p) for p in paths]
        result['new_outputs_absent'] = all(not r['lexists'] for r in result['new_outputs'])
        result['model_path'] = path_info('/cache/efim/Qwen3.6-27B')
        if 'source_root' in config:
            result['source_path'] = path_info(config['source_root'])
        name_filters = ['name=' + Path(p).name for p in paths]
        result['new_output_family_inventory'] = dict(
            scope='two new output basename name-filters; diagnostic only; original exact owner-name gate remains',
            filters=name_filters,
            queries=[run([DOCKER, 'ps', '-a', '--no-trunc', '--filter', item, '--format',
                '{{json .ID}}\t{{json .Names}}\t{{json .State}}\t{{json .Status}}\t{{json .Image}}'])
                for item in name_filters])
        running = run([DOCKER, 'ps', '-q', '--no-trunc'])
        result['running_inventory'] = running
        ids = sorted(set(running['stdout'].split()) | {r['id'] for r in old})
        need(len(ids) <= 4096 and all(re.fullmatch('[0-9a-f]{64}', i) for i in ids),
             'bounded complete actual Docker inventory')
        result['inspect_before'] = inspect(ids)
        result['old_before'] = old_identity(result['inspect_before']['containers'], old)
        result['docker_top'] = [run([DOCKER, 'top', cid, '-eo',
                                    'pid,ppid,uid,lstart,comm'])
                                for cid in running['stdout'].split()]
        result['old_units'] = [run(['/usr/bin/systemctl', 'show', unit, '--no-pager',
            '--property=Id,LoadState,ActiveState,SubState,MainPID,ControlPID,Result,ExecMainStatus,ControlGroup'])
                              for unit in units]
        result['docker_unit'] = run(['/usr/bin/systemctl', 'show', 'docker.service',
            '--no-pager', '--property=MainPID,ControlGroup,ActiveState,SubState'])
        result['host_listeners_8230'] = run(['/usr/sbin/ss', '-lntp', 'sport = :8230'])
        result['host_listener_note'] = ('Container network=none has its own loopback namespace; '
            'a host listener is observational only, not a source-proven conflict predicate.')
        engine = run([DOCKER, 'info', '--format', '{{json .}}'])
        if engine['exit_code'] == 0 and not engine['error']:
            info = json.loads(engine['stdout'])
            result['engine'] = {k:info.get(k) for k in ('NCPU','DockerRootDir','ServerVersion','CgroupDriver','CgroupVersion')}
            result['docker_disk'] = path_info(info['DockerRootDir'])
        else:
            raw = engine.pop('stdout')
            engine['stdout_bytes'] = len(raw.encode())
            engine['stdout_sha256'] = hashlib.sha256(raw.encode()).hexdigest()
            result['engine_error'] = engine
        result['memory_after'] = read('/proc/meminfo').decode()
        result['inspect_old_after'] = inspect([r['id'] for r in old])
        result['old_after'] = old_identity(result['inspect_old_after']['containers'], old)
        initial = {r['Id']:r for r in result['inspect_before']['containers']}
        final = {r['Id']:r for r in result['inspect_old_after']['containers']}
        result['old_identity_state_stable_during_snapshot'] = all(
            cid in initial and cid in final and all(initial[cid][k] == final[cid][k]
                for k in ('Id','Name','Image','State','ExecIDs','labels'))
            for cid in (r['id'] for r in old))
        result['smi_after'] = run([SMI, 'info'])
        result['kernel_locks_after'] = read('/proc/locks').decode()
        result['main_lock_kernel_matches_after'] = lock_matches(lock, result['kernel_locks_after'])
    except Exception as exc:
        fail(type(exc).__name__ + ': ' + str(exc))
    result.update(observed_end_utc=utc(), elapsed_seconds=time.monotonic()-START,
                  errors=ERRORS, complete=not ERRORS,
                  remaining_required=('Original source-bound protected0_3/idle_one/RSS/CPU ancestor quotas, '
                    'fresh source/output/owner admission and model fullhash remain authoritative. '
                    'No permit or ready value is produced by this snapshot.'))
    encoded = json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False)
    need(len(encoded.encode()) <= MAX_FINAL_BYTES, 'snapshot output cap; do not retain truncated JSON')
    print(encoded)
    return 0 if not ERRORS else 2


if __name__ == '__main__':
    raise SystemExit(main())
