"""Authenticate retained geometry bytes; observations never grant execution.

Pure CPU/stdlib. The original model report and every embedded Ref are retained.
This reads the producer's complete JSONL and joins it to the saved active pool
inventory before accounting for the bytes the producer actually charged.
"""
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

MAX_ROWS = 400
MAX_BYTES = 1024 * 1024
CONTROL_CAP = 16 * 1024**2
ALLOCATED_CAP = 15 * 1024**3 // 2
GUEST_ROOT = Path('/adakv-results/model/capture')
ROW_SCHEMA = 'deltalog.pre-registration-geometry-observation/v1'
SIDECAR_SCHEMA = 'deltalog.geometry-witness-refs/v1'
DTYPES = {'torch.uint8': ('u8', 1), 'torch.bfloat16': ('bf16', 2),
          'torch.float32': ('f32', 4), 'torch.int32': ('i32', 4),
          'torch.int64': ('i64', 8)}
ROW_KEYS = frozenset(('schema', 'source', 'model_source', 'domain', 'pid',
    'prefix', 'group', 'role', 'tensor_identity', 'shape', 'stride',
    'storage_offset', 'element_bytes', 'dtype', 'device', 'numel',
    'contiguous', 'pointer', 'storage_pointer', 'storage_bytes',
    'storage_identity', 'qualification', 'numerical_executed',
    'format_code', 'format_error', 'predicate'))
_SEAL = object()


def need(value, reason):
    if not value:
        raise ValueError(reason)


def ref3(value):
    need(type(value) is dict and set(value) == {'path', 'bytes', 'sha256'},
         'geometry exact Ref3')
    need(type(value['path']) is str, 'geometry Ref path string')
    path = Path(value['path'])
    need(path.is_absolute() and '..' not in path.parts
         and str(path) == value['path'], 'geometry exact absolute ordinary path')
    need(type(value['bytes']) is int and value['bytes'] > 0
         and type(value['sha256']) is str
         and re.fullmatch('[0-9a-f]{64}', value['sha256']) is not None,
         'geometry positive exact Ref size and SHA256')
    return path


def _stat_key(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size,
            s.st_mtime_ns, s.st_ctime_ns)


def read_ordinary_ref(value, *, max_bytes):
    """One no-follow descriptor, full hash, stable file and parent identities."""
    path = ref3(value)
    need(value['bytes'] <= max_bytes, 'geometry bounded complete evidence')
    parents = [(p, p.lstat()) for p in path.parents]
    need(all(stat.S_ISDIR(s.st_mode) and not stat.S_ISLNK(s.st_mode)
             for _, s in parents), 'geometry ordinary parent directories')
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_size == value['bytes'],
         'geometry ordinary complete regular file')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        need(_stat_key(before) == _stat_key(opened), 'geometry stable opened identity')
        chunks = []
        used = 0
        while True:
            block = os.read(fd, min(65536, max_bytes + 1 - used))
            if not block:
                break
            chunks.append(block)
            used += len(block)
            need(used <= value['bytes'] and used <= max_bytes,
                 'geometry no growth or uncharged tail')
        raw = b''.join(chunks)
        need(len(raw) == value['bytes']
             and hashlib.sha256(raw).hexdigest() == value['sha256'],
             'geometry whole original bytes SHA256')
        need(_stat_key(before) == _stat_key(os.fstat(fd))
             == _stat_key(path.lstat()), 'geometry stable full read')
        for p, s in parents:
            now = p.lstat()
            need(stat.S_ISDIR(now.st_mode)
                 and (s.st_dev, s.st_ino, s.st_mode) ==
                     (now.st_dev, now.st_ino, now.st_mode),
                 'geometry unchanged ordinary parent identity')
        return raw
    finally:
        os.close(fd)


def strict_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value, 'geometry no duplicate JSON keys')
            value[key] = item
        return value

    def constant(value):
        raise ValueError('geometry no nonfinite JSON constant ' + value)

    return json.loads(raw.decode('utf8'), object_pairs_hook=pairs,
                      parse_constant=constant)


def _report_fingerprint(report):
    return hashlib.sha256(json.dumps(report, sort_keys=True,
                                    allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class GeometryWitness:
    path: str
    bytes: int
    sha256: str
    rows: int
    rank: int
    namespace_pid: int
    report_fingerprint: str
    _seal: object

    def evidence(self):
        need(self._seal is _SEAL, 'geometry validated witness only')
        return dict(schema='deltalog.independent-geometry-witness/v1',
                    geometry_ref=dict(path=self.path, bytes=self.bytes,
                                      sha256=self.sha256),
                    rows=self.rows, rank=self.rank,
                    namespace_pid=self.namespace_pid,
                    qualification=False, numerical_executed=False)


def validate_geometry_witness(report, geometry_ref, alias_io):
    """Explicit host Ref must be the exact original worker-root observation."""
    ref3(report['source'])
    ref3(report['model_source'])
    domain = report['domain']
    need(type(domain) is dict and set(domain) ==
         {'cid', 'host_pid', 'start_ticks', 'physical', 'rank'},
         'geometry exact original worker domain')
    need(type(domain['cid']) is str and domain['cid']
         and all(type(domain[k]) is int for k in
                 ('host_pid', 'start_ticks', 'physical', 'rank'))
         and domain['host_pid'] > 0 and domain['start_ticks'] > 0
         and domain['rank'] in range(4) and domain['physical'] == domain['rank'] + 4,
         'geometry actual worker PID/start/card/rank')
    pid = report['namespace_pid']
    need(type(pid) is int and pid > 0, 'geometry positive namespace PID')
    ref3(geometry_ref)
    original = dict(geometry_ref, path=str(GUEST_ROOT / (
        'FIRST-DECODE-GEOMETRY-p%d.jsonl' % pid)))
    need(alias_io.actual_ref(original) == geometry_ref,
         'geometry exact original guest-to-host worker-root alias')
    raw = read_ordinary_ref(geometry_ref, max_bytes=MAX_BYTES)
    need(raw.endswith(b'\n'), 'geometry complete newline-terminated JSONL')
    lines = raw.split(b'\n')[:-1]
    need(0 < len(lines) <= MAX_ROWS and all(line for line in lines),
         'geometry complete nonempty bounded rows')

    metadata = report['active_metadata']
    pools, selections = metadata['pools'], metadata['selections']
    need(type(pools) is list and pools and type(selections) is list,
         'geometry saved complete pool and selection inventory')
    pool_map = {}
    pool_extents = set()
    for pool in pools:
        need(type(pool) is dict and set(pool) == {'index', 'pointer', 'nbytes'}
             and all(type(pool[k]) is int for k in pool)
             and pool['index'] >= 0 and pool['pointer'] > 0 and pool['nbytes'] > 0,
             'geometry exact positive original pool descriptor')
        need(pool['index'] not in pool_map
             and (pool['pointer'], pool['nbytes']) not in pool_extents,
             'geometry no duplicate pool index or allocation descriptor')
        pool_map[pool['index']] = pool
        pool_extents.add((pool['pointer'], pool['nbytes']))
    need(set(pool_map) == set(range(len(pools))), 'geometry complete unique pool indices')
    wanted, groups, used_pools = {}, {}, set()
    for selection in selections:
        prefix, role = selection['prefix'], selection['role']
        need(type(prefix) is str and prefix and type(role) is str,
             'geometry exact layer role identity')
        key = (prefix, role)
        kind, group = selection['kind'], selection['group']
        need(key not in wanted and kind in ('GDN', 'FA')
             and type(group) is int and group >= 0,
             'geometry unique typed layer role')
        need(prefix not in groups or groups[prefix] == (kind, group),
             'geometry one actual group per layer')
        groups[prefix] = (kind, group)
        need(type(selection['pool']) is int and selection['pool'] in pool_map,
             'geometry original pool index join')
        used_pools.add(selection['pool'])
        wanted[key] = selection
    need(len(groups) == 64
         and sum(k == 'GDN' for k, _ in groups.values()) == 48
         and sum(k == 'FA' for k, _ in groups.values()) == 16,
         'geometry complete original 48 GDN and 16 FA inventory')
    for prefix, (kind, _) in groups.items():
        roles = {role for p, role in wanted if p == prefix}
        expected = {'conv', 'base', 'K', 'U', 'lambda_log', 'decay', 'length'} \
            if kind == 'GDN' else {'K', 'V'}
        need(roles == expected, 'geometry all original roles once per layer')
    need(len(wanted) == 368 and len(lines) == len(wanted)
         and used_pools == set(pool_map), 'geometry no missing row or unused pool')

    seen = set()
    for line in lines:
        row = strict_json(line)
        need(type(row) is dict and set(row) == ROW_KEYS
             and row['schema'] == ROW_SCHEMA, 'geometry exact original row schema')
        need(row['source'] == report['source']
             and row['model_source'] == report['model_source']
             and row['domain'] == domain and row['pid'] == pid
             and type(row['domain']) is dict
             and all(type(row['domain'][k]) is int for k in
                     ('host_pid', 'start_ticks', 'physical', 'rank'))
             and type(row['pid']) is int, 'geometry original source/model/domain/PID join')
        key = (row['prefix'], row['role'])
        need(key in wanted and key not in seen, 'geometry no unknown or repeated role')
        seen.add(key)
        selection = wanted[key]
        pool = pool_map[selection['pool']]
        geometry = selection['geometry']
        need(type(row['group']) is int and row['group'] == selection['group'],
             'geometry original actual group join')
        need(row['qualification'] is False and row['numerical_executed'] is False,
             'geometry observation has no numerical or execution qualification')
        need(row['contiguous'] is True and row['format_code'] == 2
             and type(row['format_code']) is int and row['format_error'] is None
             and row['predicate'] == {'contiguous': True, 'positive': True, 'ND2': True}
             and all(type(v) is bool for v in row['predicate'].values()),
             'geometry original contiguous positive ND2 gate unchanged')
        need(row['dtype'] in DTYPES
             and type(row['device']) is str
             and re.fullmatch(r'npu(?::[0-9]+)?', row['device']) is not None,
             'geometry original reviewed type and NPU device')
        dtype, element = DTYPES[row['dtype']]
        need(type(row['shape']) is list and type(row['stride']) is list
             and len(row['shape']) == len(row['stride']) >= 2
             and all(type(v) is int and v > 0
                     for v in row['shape'] + row['stride']),
             'geometry exact positive actual shape and stride')
        need(all(type(row[k]) is int and row[k] > 0 for k in
                 ('tensor_identity', 'storage_identity', 'pointer',
                  'storage_pointer', 'storage_bytes', 'element_bytes', 'numel'))
             and type(row['storage_offset']) is int and row['storage_offset'] >= 0,
             'geometry exact positive identities and byte extents')
        need(row['numel'] == math.prod(row['shape'])
             and row['element_bytes'] == element,
             'geometry full actual element and byte count')
        need(row['shape'] == geometry['shape']
             and row['stride'] == geometry['strides']
             and row['storage_offset'] == geometry['storage_offset']
             and row['pointer'] == geometry['pointer']
             and row['element_bytes'] == geometry['element_bytes']
             and dtype == geometry['dtype'] and geometry['format_code'] == 2,
             'geometry exact report typed view join')
        need(row['storage_pointer'] == pool['pointer']
             and row['storage_bytes'] == pool['nbytes']
             and row['pointer'] == pool['pointer'] + row['storage_offset'] * element,
             'geometry exact full storage pool extent and offset join')
        need(row['pointer'] + sum((n - 1) * s for n, s in
                 zip(row['shape'], row['stride'])) * element + element
             <= pool['pointer'] + pool['nbytes'],
             'geometry full view within original complete pool')
    need(seen == set(wanted), 'geometry complete original role equality')
    return GeometryWitness(geometry_ref['path'], len(raw), geometry_ref['sha256'],
                           len(lines), domain['rank'], pid,
                           _report_fingerprint(report), _SEAL)


def validate_control_accounting(report, witness, final_bytes):
    """Same original caps; add authenticated, positive observer bytes exactly."""
    need(type(witness) is GeometryWitness and witness._seal is _SEAL
         and witness.bytes > 0 and witness.rows == 368
         and witness.report_fingerprint == _report_fingerprint(report),
         'geometry same fully validated report witness')
    budget = report['storage_budget']
    prefill_bytes = budget['prefill_control']['bytes']
    need(type(prefill_bytes) is int and prefill_bytes > 0
         and type(budget['controls_before_final_bytes']) is int
         and type(final_bytes) is int and final_bytes > 0,
         'geometry actual positive serialized control bytes')
    need(budget['controls_before_final_bytes'] == prefill_bytes + witness.bytes
         and budget['controls_before_final_bytes'] + final_bytes <= CONTROL_CAP
         and budget['snapshot_bytes'] + report['raw_bytes']
             + budget['controls_before_final_bytes'] + final_bytes <= ALLOCATED_CAP,
         'all actual serialized worker evidence including geometry fits preassigned7.5GiB')
    return dict(prefill_control_bytes=prefill_bytes, geometry_bytes=witness.bytes,
                controls_before_final_bytes=budget['controls_before_final_bytes'],
                final_report_bytes=final_bytes, control_cap_bytes=CONTROL_CAP,
                allocated_worker_cap_bytes=ALLOCATED_CAP, qualification=False)


def validate_geometry_sidecar(value, consumer_sr, model_sr, payload_sr,
                              reports_ref, report_refs, host_payload_root):
    need(type(value) is dict and set(value) == {'schema', 'consumer_source',
         'model_source', 'payload_source', 'reports_ref', 'geometry'}
         and value['schema'] == SIDECAR_SCHEMA, 'geometry exact independent sidecar schema')
    need(value['consumer_source'] == consumer_sr and value['model_source'] == model_sr
         and value['payload_source'] == payload_sr and value['reports_ref'] == reports_ref,
         'geometry sidecar same separate consumer and unchanged input identities')
    entries = value['geometry']
    need(type(entries) is list and len(entries) == 4
         and type(report_refs) is list and len(report_refs) == 4,
         'geometry four actual report/witness pairs required')
    root = Path(host_payload_root)
    need(root.is_absolute() and '..' not in root.parts, 'geometry exact host payload root')
    result, pids, used_reports, used_geometry = {}, set(), set(), set()
    for entry in entries:
        need(type(entry) is dict and set(entry) ==
             {'rank', 'namespace_pid', 'report_ref', 'geometry_ref'},
             'geometry exact sidecar worker fields')
        rank, pid = entry['rank'], entry['namespace_pid']
        need(type(rank) is int and rank in range(4) and rank not in result
             and type(pid) is int and pid > 0 and pid not in pids,
             'geometry four distinct worker ranks and namespace PIDs')
        rp, gp = ref3(entry['report_ref']), ref3(entry['geometry_ref'])
        need(entry['report_ref'] in report_refs
             and rp == root / ('FIRST-DECODE-%d' % pid) / 'FIRST-DECODE-REPORT.json'
             and gp == root / ('FIRST-DECODE-GEOMETRY-p%d.jsonl' % pid)
             and str(rp) not in used_reports and str(gp) not in used_geometry,
             'geometry original four distinct exact report/root witness paths')
        result[rank] = entry
        pids.add(pid)
        used_reports.add(str(rp))
        used_geometry.add(str(gp))
    need(set(result) == {0, 1, 2, 3}
         and used_reports == {str(ref3(r)) for r in report_refs},
         'geometry complete original report inventory')
    return result
