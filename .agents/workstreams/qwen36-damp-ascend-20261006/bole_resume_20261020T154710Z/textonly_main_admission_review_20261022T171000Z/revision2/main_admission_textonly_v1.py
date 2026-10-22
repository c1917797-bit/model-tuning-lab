"""MAIN-only text-only continuation launcher draft. Default OFF and not frozen.

No dispatch is possible until MAIN freezes this source, supplies exact current
Refs, and writes a genuine review. It execs the unchanged source-owned model
command: original live resource/create, 3600-second phase and shared180 cleanup
remain authoritative. Snapshot restoration alone never grants resources.
"""
import argparse
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import stat
import sys
import time

sys.dont_write_bytecode = True
REVIEWED_FROZEN = False
WS = Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
SCOPE = 'textonly_20261022T171000Z'
SOURCE = WS / ('bound-boundary-ON-v4-' + SCOPE)
OUTPUT = Path('/opt/host/vnf/austinov/run-bole-boundary-ON-v4-' + SCOPE)
EVIDENCE = Path('/opt/host/vnf/austinov/run-bole-textonly-main-admission-v1-' + SCOPE)
LOCK = WS / 'MAIN_ADMISSION.lock'
START, CUT, OLD_REPORT_CUT = 1792689000, 1792710600, 1792672721
PHASE, CLEANUP, PREPARE = 3600, 180, 3780
IMAGE = 'sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
OWNER = 'bole-root-r6-20261017-001'
HOST_SHA = '20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30'
OLD_CIDS = {
    '40c6b48039182b29b47a4a4283ba17f414570f5a5465d6c2865a0b595866b45a',
    '54246001fc180995c8e021a27f8f5b14f237fe6e92dd62dcb4acadc3dfae0411',
    'c4a669cc4b20e5f013e92ce22ac89f6eccf7236286464bd2f7b7b8ac9bf3bdc9',
    '961b3501d0b739216264e2027115a3245d0e391709a408ed9ac2943bcd1f083d',
    '6433f9740a1acc4be305d35456436dbccdaf0a91d6884e283259ea22dec99ef5',
    'a25d55a819562ffbf2135ba1017bb52ae2e3ca9c3ee2998486540bbbaebd4cf0',
    '0a5ed053d4d08915b8748e0f6facbc6f3fad820ff1f46d1eefe0f4bc6626d955',
    'eb21e660585ed4e758476504bc0b409a02b777d875516e2925f00a9e8efaa8cf'}
OLD_UNITS = (
    'bole-short-on-v2-model-20261021t123841z.service',
    'bole-short-off-v2-model-20261021t123841z.service',
    'bole-boundary-on-v1-model-20261022t080000z.service',
    'bole-boundary-on-v3-continuation-20261022t120055z-u3.service')
SNAPSHOT_HELPER = dict(path=str(WS/'boundary_admission_v4_20261022/fresh_snapshot_v4.py'),
    bytes=19376, sha256='8c0b3105354708f3942f798d67a057ef16e11c5b10b538106166dafce61c1968')
SNAPSHOT_PROGRAM_PIN = None  # MAIN binds actual reviewed new producer bytes.
RESTORE_PIN = {'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/continuation_main_admission_v4_20261022T120055Z/restore_snapshot_mounts_v1.py', 'bytes': 6438, 'sha256': '8177437cda4df4d85db41392588fff18ce8422598d73bdc163ab950b26a32f9c'}  # MAIN binds final helper bytes during source review.
HISTORICAL_CONTEXT_PIN = None  # MAIN binds actual reviewed new historical context bytes.
COMPLETE_RECEIPT_PIN = {'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/continuation_main_admission_v4_20261022T120055Z/complete_inspect_receipt_v1.py', 'bytes': 3807, 'sha256': '05d212afa6d84af8f0a665c4d1605c756e1e603b52c533e983bc866e13804e5a'}

# One already failed historical startup may be accepted only as a completed
# lifecycle chain. This never rewrites its primary or claims model readiness.
FAILED_HISTORY_SOURCE = {'bytes': 1638841, 'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-boundary-ON-v3-continuation_20261022T120055Z/SOURCE_BOUND.json', 'sha256': 'd28e57b46ae913182ff8ebc0f35a1c631f12fce647376af495a4b59c4d8e10df'}
FAILED_HISTORY_RESULT = {'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/RESULT.json', 'bytes': 2375646, 'sha256': '4ad705377892c1136dbc945c8353904739e6189ed4b52dea2df3cc12731ef1da'}
FAILED_HISTORY_CIDS = {'0a5ed053d4d08915b8748e0f6facbc6f3fad820ff1f46d1eefe0f4bc6626d955', 'eb21e660585ed4e758476504bc0b409a02b777d875516e2925f00a9e8efaa8cf'}
FAILED_HISTORY_PRIMARY = 'TimeoutExpired([\'/usr/bin/prlimit\', \'--as=unlimited\', \'--\', \'/usr/bin/docker\', \'exec\', \'eb21e660585ed4e758476504bc0b409a02b777d875516e2925f00a9e8efaa8cf\', \'/bin/bash\', \'-c\', \'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"\', \'kvbp-diagnostic\', \'/usr/local/python3.12.13/bin/python3\', \'-B\', \'-c\', "import urllib.request;assert urllib.request.urlopen(\'http://127.0.0.1:8230/health\',timeout=2).status==200"], 4)'
FAILED_HISTORY_FIELDS = {'BOLE_diagnostic': False,
 'actual_host_argv': ['/usr/bin/python3',
                      '-I',
                      '-B',
                      '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-boundary-ON-v3-continuation_20261022T120055Z/host_service.py',
                      '--execute',
                      '--source-ref',
                      '{"path": '
                      '"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-boundary-ON-v3-continuation_20261022T120055Z/SOURCE_BOUND.json", '
                      '"bytes": 1638841, "sha256": '
                      '"d28e57b46ae913182ff8ebc0f35a1c631f12fce647376af495a4b59c4d8e10df"}',
                      '--output',
                      '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z'],
 'candidate_qualification': False,
 'cleanup_seconds': 180,
 'cleanup_spent': 40.35200875008013,
 'cpu_only': False,
 'elapsed': 1097.174797869986,
 'formal_performance': False,
 'host_pid': 4184444,
 'model_ready': False,
 'performance_gain_measured': False,
 'phase_seconds': 3600,
 'primary': "TimeoutExpired(['/usr/bin/prlimit', '--as=unlimited', '--', '/usr/bin/docker', 'exec', "
            "'eb21e660585ed4e758476504bc0b409a02b777d875516e2925f00a9e8efaa8cf', '/bin/bash', '-c', 'source "
            '/usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"\', \'kvbp-diagnostic\', '
            '\'/usr/local/python3.12.13/bin/python3\', \'-B\', \'-c\', "import urllib.request;assert '
            'urllib.request.urlopen(\'http://127.0.0.1:8230/health\',timeout=2).status==200"], 4)',
 'scheduler_committed': False,
 'schema': 'bole.actual-three-node-model-owned/v131',
 'secondary': [],
 'source': {'bytes': 1638841,
            'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-boundary-ON-v3-continuation_20261022T120055Z/SOURCE_BOUND.json',
            'sha256': 'd28e57b46ae913182ff8ebc0f35a1c631f12fce647376af495a4b59c4d8e10df'},
 'successful_raw_replay_available': False,
 'summary': {'CPU_child': {'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/cpu-preflight/CPU-CHILD.json',
                           'sha256': '06cb14fa2d7da0e4228994312a543687b6a93bd18eb91131c98f102849d7050c'},
             'CPU_release': {'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/cpu-preflight/cleanup.json',
                             'sha256': 'd6bac282789816103226cf8e273acb2e1791673561919111c803c239cdc7c0fb'},
             'CPU_report': {'bytes': 5707,
                            'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/cpu-preflight/CPU.json',
                            'sha256': 'd21968d44c51fc84fc5d1eafd808f150448624b34e3a3930318caf8676f6326a'},
             'actual_software_child': {'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/cpu-preflight/SOFTWARE-CHILD.json',
                                       'sha256': '66ded479d88a5a86f84582039b57bf8bdb423e9138bdbafd60e27bd167527fb0'},
             'all_observers_disabled': False,
             'canary': {'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/dense/CANARY-CHILD.json',
                        'sha256': '615b56d6dc9bd049b10b18fe4a4411afc9d562f0ba79c0bff1fbde1a0376179d'},
             'diagnostic_channel_cold_handoff': {'applicable': False,
                                                 'reason': 'no diagnostic channel in this successor; '
                                                           'original parent proof separately reopened'},
             'diagnostic_channel_enabled': False,
             'first_host_fault': {'bytes': 3218,
                                  'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/HOST-FIRST-FAULT.json'},
             'independent_cpu_ack_enabled': False,
             'performance_arm': 'bole'},
 'task_accuracy': False,
 'timing_is_formal': False}
FAILED_HISTORY_OWNERS = {'0a5ed053d4d08915b8748e0f6facbc6f3fad820ff1f46d1eefe0f4bc6626d955': {'cid': '0a5ed053d4d08915b8748e0f6facbc6f3fad820ff1f46d1eefe0f4bc6626d955',
                                                                      'owned_ref': {'bytes': 1414912,
                                                                                    'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/cpu-preflight/OWNED.json',
                                                                                    'sha256': 'bd5297f2d8e8bfcea5d02b1fdb4612faf453db55bfdf3c5a1a4c87b7f4008316'},
                                                                      'cleanup_ref': {'bytes': 3665,
                                                                                      'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/cpu-preflight/cleanup.json',
                                                                                      'sha256': 'd6bac282789816103226cf8e273acb2e1791673561919111c803c239cdc7c0fb'},
                                                                      'source_ref': {'bytes': 1638841,
                                                                                     'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-boundary-ON-v3-continuation_20261022T120055Z/SOURCE_BOUND.json',
                                                                                     'sha256': 'd28e57b46ae913182ff8ebc0f35a1c631f12fce647376af495a4b59c4d8e10df'},
                                                                      'host_result_ref': {'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/RESULT.json',
                                                                                          'bytes': 2375646,
                                                                                          'sha256': '4ad705377892c1136dbc945c8353904739e6189ed4b52dea2df3cc12731ef1da'}},
 'eb21e660585ed4e758476504bc0b409a02b777d875516e2925f00a9e8efaa8cf': {'cid': 'eb21e660585ed4e758476504bc0b409a02b777d875516e2925f00a9e8efaa8cf',
                                                                      'owned_ref': {'bytes': 1414866,
                                                                                    'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/dense/OWNED.json',
                                                                                    'sha256': '45859b745214ec0f19d728d018d438a02dcff61104084726446baedf29e74ba8'},
                                                                      'cleanup_ref': {'bytes': 1733,
                                                                                      'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/dense/cleanup.json',
                                                                                      'sha256': '8529bd3c5d26385a59dd634696297826b719253553280303cb3604f10c285679'},
                                                                      'source_ref': {'bytes': 1638841,
                                                                                     'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-boundary-ON-v3-continuation_20261022T120055Z/SOURCE_BOUND.json',
                                                                                     'sha256': 'd28e57b46ae913182ff8ebc0f35a1c631f12fce647376af495a4b59c4d8e10df'},
                                                                      'host_result_ref': {'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/RESULT.json',
                                                                                          'bytes': 2375646,
                                                                                          'sha256': '4ad705377892c1136dbc945c8353904739e6189ed4b52dea2df3cc12731ef1da'}}}
FAILED_HISTORY_FIRST_FAULT = {'bytes': 3218,
 'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/HOST-FIRST-FAULT.json',
 'sha256': '0e92f860a05174461cd0292540786d6d3025cd9243cd445fd97aa663309645e6'}
TEXT_ONLY_CONFIG = dict(language_model_only=True, skip_mm_profiling=False,
                        enable_mm_embeds=False, limit_mm_per_prompt={})


def need(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def parse(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, 'duplicate JSON key')
            out[key] = value
        return out
    def bad(value):
        raise ValueError('nonfinite JSON forbidden')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


def typed_ref(reference):
    need(type(reference) is dict and set(reference) in
         ({'path', 'sha256'}, {'path', 'sha256', 'bytes'}), 'complete producer Ref2/Ref3')
    need(type(reference['path']) is str and re.fullmatch('[0-9a-f]{64}', reference['sha256'] or ''),
         'absolute reference path and complete SHA256')
    path = Path(reference['path'])
    need(path.is_absolute() and '..' not in path.parts and
         not any(parent.is_symlink() for parent in (path, *path.parents)),
         'ordinary absolute nonsymlink input and parents')
    if 'bytes' in reference:
        need(type(reference['bytes']) is int and reference['bytes'] >= 0, 'typed original byte size')
    return path


class Readset:
    def __init__(self):
        self.refs = {}

    def read(self, reference, keep=True):
        path = typed_ref(reference)
        before = path.stat()
        need(stat.S_ISREG(before.st_mode), 'ordinary regular input')
        if 'bytes' in reference:
            need(before.st_size == reference['bytes'], 'original Ref3 exact byte size')
        need(not keep or before.st_size <= 16 * 2**20, 'complete JSON/source read under16MiB')
        digest, chunks, size = hashlib.sha256(), [], 0
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(2**20), b''):
                digest.update(chunk)
                size += len(chunk)
                if keep:
                    chunks.append(chunk)
        after = path.stat()
        identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        need(identity(before) == identity(after) and size == before.st_size and
             digest.hexdigest() == reference['sha256'], 'whole original input stable and hash exact')
        actual = dict(path=str(path), bytes=size, sha256=digest.hexdigest())
        need(str(path) not in self.refs or self.refs[str(path)] == actual, 'one exact identity per input')
        self.refs[str(path)] = actual
        return b''.join(chunks) if keep else actual

    def obj(self, reference):
        return parse(self.read(reference))

    def verify_again(self):
        for reference in list(self.refs.values()):
            self.read(reference, keep=False)


def load_exact(readset, reference, name):
    body = readset.read(reference)
    need(name not in sys.modules, 'fresh private source namespace')
    spec = importlib.util.spec_from_file_location(name, reference['path'])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, reference['path'], 'exec'), module.__dict__)
    return module


def original_labels(owned):
    return {'model-tuning-lab.arm': owned['arm'],
        'model-tuning-lab.controller-sha256': owned['host_sha256'],
        'model-tuning-lab.owner': OWNER, 'model-tuning-lab.run': owned['name'],
        'model-tuning-lab.source-manifest-sha256': owned['source']['sha256']}


def stopped(value, cid):
    need(value['Id'] == cid and value['State']['Running'] is False and
         value['State']['Pid'] == 0 and not value.get('ExecIDs') and
         value['State']['OOMKilled'] is False,
         'exact original stopped/PID0/noExec/noOOM predicate; ExitCode need not be zero')


def command_ok(receipt):
    need(receipt['exit_code'] == 0 and receipt.get('error') is None,
         'complete successful original command receipt')


def inspect_receipt(readset, reference, owned, S):
    receipt = readset.obj(reference)
    command_ok(receipt)
    need(receipt['requested_argv'] == ['/usr/bin/docker', 'inspect', owned['cid']],
         'exact historical own inspect command')
    rows = parse(receipt['stdout'])
    need(type(rows) is list and len(rows) == 1, 'one complete original Docker inspect')
    S.validate_inspect(rows[0], owned)
    return rows[0]


def exact_created_argv(actual, owned, S):
    # OWNED.json was canonicalized with sort_keys=True. That loses the original
    # insertion order of its mount dictionary, while argv lists retain order.
    # Restore only that order from the pinned actual command; every complete
    # mount member must agree with OWNED and the entire rebuilt argv must match.
    need(type(actual) is list and all(type(part) is str for part in actual),
         'complete original create argv strings')
    known = {}
    for destination, member in owned['mounts'].items():
        need(type(member) in (list, tuple) and len(member) == 2 and
             type(member[0]) is str and type(member[1]) is bool and
             type(destination) is str and ',' not in member[0] and ',' not in destination,
             'complete typed original mount member')
        source, rw = member
        value = 'type=bind,source=' + source + ',destination=' + destination + ('' if rw else ',readonly')
        need(value not in known, 'one distinct exact original mount parameter')
        known[value] = destination
    ordered = {}
    for index, part in enumerate(actual):
        if part != '--mount':
            continue
        need(index + 1 < len(actual) and actual[index+1] in known,
             'every full original create mount parameter joined to full OWNED member')
        destination = known[actual[index+1]]
        need(destination not in ordered, 'no duplicate original create mount destination')
        ordered[destination] = owned['mounts'][destination]
    need(set(ordered) == set(owned['mounts']) and len(ordered) == len(known),
         'all and only original OWNED mounts, preserving actual command order')
    need(actual == S.create_argv(dict(owned, mounts=ordered)),
         'entire actual create argv including all labels/env/devices/resource options exact')
    return True


def historical_host_result(readset, spec, owned, result, cleanup):
    # All common original source, time and cleanup predicates are mandatory for
    # both histories. A complete failure remains a failure in the evidence.
    need(result['source'] == owned['source'] and
         result['phase_seconds'] == PHASE and result['cleanup_seconds'] == CLEANUP and
         result['secondary'] == [] and result['source_before'] == result['source_after'] and
         result['cleanup_spent'] <= CLEANUP,
         'pinned completed historical host RESULT joins original source/time scope')
    if owned['cid'] not in FAILED_HISTORY_CIDS:
        need(result['primary'] is None, 'original six historical hosts require literal null primary')
        return dict(kind='completed-null-primary', model_qualification=False)
    need(spec == FAILED_HISTORY_OWNERS[owned['cid']] and
         spec['source_ref'] == owned['source'] == FAILED_HISTORY_SOURCE and
         spec['host_result_ref'] == FAILED_HISTORY_RESULT,
         'exact two failed-startup OWNED/cleanup/source/result identities only')
    need(type(FAILED_HISTORY_PRIMARY) is str and FAILED_HISTORY_PRIMARY and
         result['primary'] == FAILED_HISTORY_PRIMARY,
         'literal observed original failed-startup primary; no generic failure allowance')
    need(set(result) == set(FAILED_HISTORY_FIELDS) | {'source_before', 'source_after'} and
         all(result[key] == value for key, value in FAILED_HISTORY_FIELDS.items()) and
         len(result['source_before']) == len(result['source_after']) == 6306,
         'exact complete original failed RESULT structure and saved failure fields preserved')
    fault = readset.obj(FAILED_HISTORY_FIRST_FAULT)
    need(fault['schema'] == 'bole.first-host-fault/v131r5' and
         fault['source'] == FAILED_HISTORY_SOURCE and fault['error_repr'] == result['primary'] and
         fault['error_type'] == 'subprocess.TimeoutExpired' and
         fault['phase'] == dict(ordinal=14, phase='dense', step='spawn-server') and
         fault['cleanup_not_started'] is True and fault['fail_closed'] is True and
         fault['recovery_attempted'] is False and
         result['summary']['first_host_fault'] ==
             {key: FAILED_HISTORY_FIRST_FAULT[key] for key in ('path', 'bytes')},
         'pinned original startup fault precedes cleanup; producer path/bytes join is exact')
    cleanup_ref2 = {key: spec['cleanup_ref'][key] for key in ('path', 'sha256')}
    if owned['arm'] == 'cpu-preflight':
        need(result['summary']['CPU_release'] == cleanup_ref2 and cleanup['primary_error'] is None,
             'original CPU release Ref2 joins whole pinned cleanup without fabricating byte field')
        join_kind = 'original-host-summary-CPU_release'
    else:
        need(owned['arm'] == 'dense' and 'model_release' not in result['summary'] and
             cleanup['primary_error'] == repr(result['primary']),
             'failed dense cleanup keeps exact repr(primary); absent model_release stays absent')
        # The exception skipped summary.model_release. The independently pinned
        # dense cleanup is joined by exact source/owner plus original first fault.
        # Its full before/stop/after/release/idle predicates were checked above.
        join_kind = 'independently-pinned-dense-cleanup-and-first-fault'
    return dict(kind='completed-failed-startup-lifecycle-only',
        host_result_ref=FAILED_HISTORY_RESULT, first_fault_ref=FAILED_HISTORY_FIRST_FAULT,
        cleanup_ref=spec['cleanup_ref'], cleanup_join=join_kind,
        original_primary_preserved=True, model_qualification=False,
        numerical_qualified=False, performance_admitted=False)


def historical_owners(readset, config, snapshot, S, manifest, history):
    specifications = config['old_owners']
    need(type(specifications) is list and len(specifications) == 8 and
         {row['cid'] for row in specifications} == OLD_CIDS,
         'all eight historical exact owners, including two completed failed-startup lifecycle chains')
    current = {key: {row['Id']: row for row in snapshot[key]['containers']}
               for key in ('inspect_before', 'inspect_old_after')}
    owners, contexts, proofs = [], {}, []
    for spec in specifications:
        owned = readset.obj(spec['owned_ref'])
        need(owned['cid'] == spec['cid'] and owned['image'] == IMAGE and
             owned['host_sha256'] == HOST_SHA and
             owned['sources']['safety_host.py'] == HOST_SHA and owned['source'] == spec['source_ref'],
             'independent full OWNED CID/image/controller/source binding')
        historical_source = readset.obj(spec['source_ref'])
        need(historical_source['root'] == str(Path(spec['source_ref']['path']).parent),
             'original source owns its exact root')
        context = history.build(readset, historical_source, owned, manifest, S)
        created = readset.obj(owned['create_receipt'])
        command_ok(created)
        need(created['stdout'] == owned['cid'] + '\n' and
             exact_created_argv(created['requested_argv'], owned, context),
             'entire original create command and returned CID match bound expected owner')
        cleanup = readset.obj(spec['cleanup_ref'])
        need(cleanup['container'] == owned['cid'] and cleanup['stopped'] is True and
             cleanup['retained'] is True and cleanup['deleted'] is False and cleanup['errors'] == [] and
             cleanup['protected_boundary']['own_on_protected'] is False,
             'original completed retained cleanup and protected-device predicate')
        inspect_receipt(readset, cleanup['before_inspect'], owned, context)
        stopped_receipt = readset.obj(cleanup['stop_receipt'])
        command_ok(stopped_receipt)
        need(stopped_receipt['requested_argv'] ==
             [S.DOCKER, 'stop', '--time', '15', owned['cid']] and
             stopped_receipt['stdout'] == owned['cid'] + '\n',
             'exact historical retained-own stop receipt and CID, no current stop')
        old_after = inspect_receipt(readset, cleanup['after_inspect'], owned, context)
        stopped(old_after, owned['cid'])
        released = readset.obj(cleanup['release_smi'])
        command_ok(released)
        need(released['requested_argv'] == [S.SMI, 'info'], 'original exact release observation')
        for physical in (4, 5, 6, 7):
            S.H.frozen().idle_one(released['stdout'], physical)
        result = readset.obj(spec['host_result_ref'])
        host_outcome = historical_host_result(readset, spec, owned, result, cleanup)
        labels = original_labels(owned)
        for key in ('inspect_before', 'inspect_old_after'):
            row = current[key][owned['cid']]
            stopped(row, owned['cid'])
            need(row['Name'] == '/' + owned['name'] and row['Image'] == IMAGE and row['labels'] == labels,
                 'complete name and all prefixed labels compared; no source-hash-only shortcut')
            mounts = row['mounts']
            expected = {dest: (source, bool(rw)) for dest, (source, rw) in owned['mounts'].items()}
            need(len(mounts) == len(expected) and all(m['Type'] == 'bind' for m in mounts) and
                 {m['Destination']: (m['Source'], m['RW']) for m in mounts} == expected,
                 'original exact full mount-member predicate after lossless reconstruction')
        a, b = (current[key][owned['cid']] for key in ('inspect_before', 'inspect_old_after'))
        need(all(a[field] == b[field] for field in ('Id', 'Name', 'Image', 'State', 'ExecIDs', 'labels')),
             'complete old identity/state stable across independent observation')
        owners.append(owned)
        contexts[owned['cid']] = context
        proofs.append(dict(context.proof, historical_host_outcome=host_outcome))
    return owners, contexts, proofs


def snapshot_inputs(readset, config, restoration):
    execution = readset.obj(config['snapshot_execution_ref'])
    program = config['snapshot_program_ref']
    need((program['bytes'], program['sha256']) == SNAPSHOT_PROGRAM_PIN,
         'exact independently reviewed lossless v4 producer')
    readset.read(program, keep=False)
    need(execution['schema'] == 'bole.final-readonly-snapshot-execution/v1' and
         execution['exit_code'] == 0 and execution['child_reaped'] is True and
         execution['timeout'] is False and execution['source_unchanged'] is True and
         execution['source_before'] == execution['source_after'] == program and
         execution['stdout'] == config['snapshot_ref'] and
         execution['NPU'] is False and execution['resource_admission'] is False,
         'actual successful outer execution, exact producer and full snapshot Ref')
    need(readset.read(execution['stderr']) == b'', 'exact empty successful snapshot stderr')
    snapshot = readset.obj(config['snapshot_ref'])
    proof = restoration.restore(snapshot)
    now = time.time()
    need(START <= execution['started_epoch'] <= snapshot['observed_end_epoch'] <=
         execution['ended_epoch'] <= now and now - execution['ended_epoch'] <= 180,
         'fresh successful observation within independent180-second predispatch freshness bound')
    need(snapshot['evidence_inputs_unchanged'] is True and
         snapshot['old_identity_state_stable_during_snapshot'] is True,
         'complete observation readset and old states stable, never inferred from diagnostics')
    return snapshot, execution, proof


def source_inputs(readset, config):
    sr = config['source_ref']
    need(typed_ref(sr) == SOURCE/'SOURCE_BOUND.json', 'new exact source root')
    manifest, audit, commands = [readset.obj(config[key])
        for key in ('source_ref', 'source_audit_ref', 'commands_ref')]
    need(manifest['root'] == str(SOURCE) and manifest['output_root'] == str(OUTPUT) and
         manifest['default_enabled'] is False and manifest['prepared_only'] is False,
         'fresh default-OFF bound source and output identity')
    need(manifest['text_only_config'] == TEXT_ONLY_CONFIG,
         'explicit native text-only service configuration, never implicit profile bypass')
    need(audit['schema'] == 'bole.boundary-source-admission/v1' and audit['source'] == sr and
         audit['source_validated'] is True and audit['original_inputs_unchanged'] is True and
         audit['host_readset_exact'] is True and audit['hard_cutoff'] == CUT and
         audit['historical_report_cutoff'] == OLD_REPORT_CUT and audit['old_window_extended'] is False,
         'actual new source audit with separate unchanged old report deadline')
    need(audit['audit_program_unchanged'] is True and audit['tests_executed'] is False and
         audit['NPU'] is False and audit['paired_gate_pass'] is False and
         audit['numerical_qualified'] is False and audit['performance_admitted'] is False and
         audit['formal_performance'] is False and len(audit['original_twenty_controls']) == 20,
         'source audit is complete source-only evidence, never numerical or device admission')
    need(audit['audit_program_ref'] == config['source_audit_program_ref'], 'exact current auditor identity')
    readset.read(audit['audit_program_ref'], keep=False)
    readset.read(audit['original_audit_source'], keep=False)
    build = readset.obj(config['build_record_ref'])
    need(build['schema'] == 'bole.boundary-probe-source-freeze/v1' and build['source'] == sr and
         build['commands'] == config['commands_ref'] and build['source_only'] is True and
         build['original_inputs_unchanged'] is True and build['fixed_cutoff'] == CUT and
         build['historical_report_cutoff'] == OLD_REPORT_CUT and build['old_window_extended'] is False and
         build['phase_seconds'] == PHASE and build['cleanup_seconds'] == CLEANUP and
         all(build[key] is False for key in ('owner_created', 'NPU', 'paired_gate_pass',
                                           'performance_admitted', 'formal_performance')),
         'actual complete freeze record binds new source and unchanged scope/qualification')
    readset.read(build['parent'], keep=False)
    readset.read(build['review'], keep=False)
    for reference in build['original_readset']:
        readset.read(reference, keep=False)
    audited = {}
    for reference in audit['readset']:
        path = typed_ref(reference)
        need(str(path) not in audited or audited[str(path)] == reference, 'one source readset identity')
        audited[str(path)] = reference
        readset.read(reference, keep=False)
    for reference in [sr, config['commands_ref'], manifest['authority_ref'],
                      *manifest['files'].values(), *manifest['dependencies']]:
        need(audited.get(reference['path']) == reference, 'all source/authority/commands in exact audited readset')
    authority = readset.obj(manifest['authority_ref'])
    need(authority['start_epoch'] == START and authority['cutoff_epoch'] == CUT and
         authority['cutoff_iso'] == '2026-10-22T23:10:00+00:00' and
         authority['phase_seconds'] == PHASE and authority['cleanup_seconds'] == CLEANUP and
         authority['user_authorization_ref'] == config['authorization_ref'],
         'separate real new authorization, unchanged individual phase and cleanup')
    authorization = readset.obj(config['authorization_ref'])
    need(authorization['old_window_extended'] is False and
         authorization['old_hard_report_deadline_utc'] == '2026-10-22T12:38:41+00:00' and
         authorization['internal_batch_start_epoch'] == START and
         authorization['internal_batch_cutoff_epoch'] == CUT and
         authorization['whole_prepare_admission_seconds'] == PREPARE,
         'no automatic extension of original window')
    need(audited.get(config['authorization_ref']['path']) == config['authorization_ref'] and
         audited.get(authorization['document']['path']) == authorization['document'],
         'entire explicit authorization document and JSON in audited source readset')
    readset.read(authorization['document'], keep=False)
    need(commands['bound_source'] == sr and type(commands['model']) is list,
         'one actual source-bound model command')
    sys.path.insert(0, str(SOURCE))
    C = load_exact(readset, manifest['files']['contract090.py'], 'contract090')
    current = C.source(sr)
    need(current == manifest, 'genuine original current source gate')
    import performance_validate, command_contract
    proof = performance_validate.validate(sr)
    need(proof['source'] == sr and proof['source_validated'] is True, 'original full successor source validator')
    command_contract.validate(C, sr, manifest)
    need(os.environ.get('DENSE090_EXTERNAL_OUTPUT_ENABLE') == '1',
         'original external-output opt-in required in launcher environment before source load')
    from owned_substrate import load
    from g2_host_adapter import install
    c, S, H, pairs = load(OUTPUT)
    install(C, c, S, H, manifest)
    need(S.PHASE == PHASE and S.CLEANUP == CLEANUP and c.CUTOFF == CUT and
         S.PHYSICAL == (4, 5, 6, 7) and S.MEM == 32 * 2**30 and
         S.HOST_MEM == 512 * 2**20 and S.RESERVE == 8 * 2**30 and S.WORKSPACE == 32 * 2**30,
         'genuine original controller with unchanged CPU/RAM/disk/phase/cleanup reserve')
    return manifest, commands, C, c, S, H


def current_live_checks(F, S, owners, contexts, receipt_codec):
    before = F.run([F.SMI, 'info'])
    command_ok(before)
    original = S.H.frozen()
    protected_before = original.protected(before['stdout'])
    for physical in (4, 5, 6, 7):
        original.idle_one(before['stdout'], physical)
        S.actual_hbm(before['stdout'], physical)
    need(not S.fd_holders(), 'original actual4-7 device-holder gate; declarations are not occupancy')
    full = F.device_holders(LOCK)
    need(not any(any(fd['physical'] in (4, 5, 6, 7) for fd in holder['device_fds'])
                 for holder in full['actual_holders']), 'independent actual target-node holders absent')
    old_current_receipts = []
    for owned in owners:
        receipt = F.run([F.DOCKER, 'inspect', owned['cid']])
        command_ok(receipt)
        values = parse(receipt['stdout'])
        need(type(values) is list and len(values) == 1, 'one current full old-owner inspect')
        contexts[owned['cid']].validate_inspect(values[0], owned)
        stopped(values[0], owned['cid'])
        labels = {k: v for k, v in (values[0]['Config'].get('Labels') or {}).items()
                  if k.startswith('model-tuning-lab.')}
        need(labels == original_labels(owned), 'current complete exact prefixed label equality')
        old_current_receipts.append(dict(cid=owned['cid'], complete_receipt=receipt_codec.pack(receipt)))
    units = []
    for unit in OLD_UNITS:
        value = F.run(['/usr/bin/systemctl', 'show', unit, '--no-pager',
                      '--property=Id,ActiveState,SubState,MainPID,ControlPID,ControlGroup'])
        command_ok(value)
        fields = dict(line.split('=', 1) for line in value['stdout'].splitlines() if '=' in line)
        need(fields['Id'] == unit and fields['MainPID'] == fields['ControlPID'] == '0' and
             (fields['ActiveState'] in ('inactive', 'failed') or
              (fields['ActiveState'], fields['SubState']) == ('active', 'exited')),
             'all original host units terminal; exited oneshot is not a running PID')
        units.append(value)
    memory = {line.split(':')[0]: int(line.split()[1]) * 1024
              for line in Path('/proc/meminfo').read_text().splitlines()
              if line.startswith(('MemAvailable:', 'SwapTotal:', 'SwapFree:', 'Hugetlb:'))}
    need(memory['SwapTotal'] == memory['SwapFree'] and
         memory['MemAvailable'] >= S.MEM + S.RESERVE + S.HOST_MEM,
         'unchanged ordinary40.5GiB initial RAM; HugeTLB not additive')
    need(shutil.disk_usage(OUTPUT.parent).free >= S.WORKSPACE + S.RESERVE + S.HOST_MEM,
         'unchanged32GiB output plus8.5GiB disk reserve')
    engine = F.run([F.DOCKER, 'info', '--format', '{{json .}}'])
    command_ok(engine)
    info = parse(engine['stdout'])
    need(info['NCPU'] >= 7 and shutil.disk_usage(info['DockerRootDir']).free >= S.RESERVE + S.HOST_MEM,
         'independent Docker8.5GiB reserve and engine CPU inventory')
    cpu = S.cpu_admission(S.H.cpu_view(os.getpid()), S.H.daemon_view())
    listeners = F.run(['/usr/sbin/ss', '-lntp', 'sport = :8230'])
    command_ok(listeners)
    after = F.run([F.SMI, 'info'])
    command_ok(after)
    for physical in (4, 5, 6, 7):
        original.idle_one(after['stdout'], physical)
        S.actual_hbm(after['stdout'], physical)
    protected = S.protected_boundary(protected_before, original.protected(after['stdout']),
                                    [owner['cid'] for owner in owners], [os.getpid()])
    return dict(smi_before=before, smi_after=after, device_holders=full, old_units=units,
        memory=memory, cpu_allocation=cpu, protected_boundary=protected, host_listeners_8230=listeners,
        complete_current_old_inspect_receipts=old_current_receipts,
        proc_races_preserved_not_claimed_zero=full['disappeared_processes'],
        resources_admitted=False, source_controller_must_recheck_before_every_create=True)


def require_exec_limits():
    # These limits are inherited across exec. A short auditor's CPU/FSIZE caps
    # must never be silently passed to the original 3600-second model owner.
    need(resource.getrlimit(resource.RLIMIT_CPU) == (resource.RLIM_INFINITY, resource.RLIM_INFINITY),
         'no inherited CPU-time cap from a short preflight/auditor')
    need(resource.getrlimit(resource.RLIMIT_FSIZE) == (resource.RLIM_INFINITY, resource.RLIM_INFINITY),
         'no inherited file-size cap replacing original owner output accounting')
    need(resource.getrlimit(resource.RLIMIT_AS) == (512 * 2**20, resource.RLIM_INFINITY) and
         os.sched_getaffinity(0) == {166}, 'exact original host512MiB soft-AS and CPU166')


def main():
    entry_start = time.monotonic()
    parser = argparse.ArgumentParser(allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--check-only', action='store_true')
    modes.add_argument('--execute', action='store_true')
    parser.add_argument('--config-ref')
    parser.add_argument('--review-ref')
    args = parser.parse_args()
    if not (args.check_only or args.execute):
        print(json.dumps(dict(enabled=False, frozen=REVIEWED_FROZEN, NPU=False, resources_admitted=False)))
        return 0
    lock_fd = None
    try:
        need(REVIEWED_FROZEN is True and RESTORE_PIN is not None and
             HISTORICAL_CONTEXT_PIN is not None and COMPLETE_RECEIPT_PIN is not None and
             SNAPSHOT_PROGRAM_PIN is not None and FAILED_HISTORY_PRIMARY is not None and
             set(FAILED_HISTORY_OWNERS) == FAILED_HISTORY_CIDS,
             'draft is not frozen/reviewed; no active read or dispatch permitted')
        need(args.config_ref and args.review_ref, 'exact complete config and genuine MAIN review Refs required')
        signal.signal(signal.SIGALRM, lambda signum, frame: (_ for _ in ()).throw(TimeoutError('whole180-second MAIN predispatch cap')))
        signal.alarm(180)
        os.sched_setaffinity(0, {166})
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        need(hard == resource.RLIM_INFINITY, 'infinite hard AS for original Go wrapper')
        resource.setrlimit(resource.RLIMIT_AS, (512 * 2**20, hard))
        require_exec_limits()
        need(START <= time.time() and time.time() + PREPARE < CUT, 'entire3780 preparation+phase must fit new explicit scope')
        rs = Readset()
        config_ref, review_ref = parse(args.config_ref), parse(args.review_ref)
        cfg, review = rs.obj(config_ref), rs.obj(review_ref)
        need(cfg['scope'] == SCOPE and cfg['source_root'] == str(SOURCE) and
             cfg['output_root'] == str(OUTPUT) and cfg['evidence_root'] == str(EVIDENCE) and
             cfg['main_lock'] == str(LOCK) and cfg['template'] is False,
             'exact new separate scope and fresh output identities')
        need(review['schema'] == 'bole.continuation-main-review/v1' and
             review['reviewer'] == 'MAIN' and review['approved_dispatch'] is True and
             review['config_ref'] == config_ref and review['scope'] == SCOPE and
             review['snapshot_ref'] == cfg['snapshot_ref'] and review['source_ref'] == cfg['source_ref'] and
             review['source_audit_ref'] == cfg['source_audit_ref'] and
             review['build_record_ref'] == cfg['build_record_ref'] and
             review['historical_owners'] == cfg['old_owners'], 'genuine exact MAIN review, never manufactured by this draft')
        self_ref = rs.read(review['launcher_ref'], keep=False)
        need(Path(self_ref['path']) == Path(__file__).resolve(), 'MAIN reviewed these complete launcher bytes')
        restoration = load_exact(rs, RESTORE_PIN, '_bole_continuation_mount_restore')
        snapshot, execution, restoration_proof = snapshot_inputs(rs, cfg, restoration)
        manifest, commands, C, c, S, H = source_inputs(rs, cfg)
        history = load_exact(rs, HISTORICAL_CONTEXT_PIN, '_bole_private_historical_owner_context')
        receipt_codec = load_exact(rs, COMPLETE_RECEIPT_PIN, '_bole_complete_command_receipt')
        owners, historical_contexts, history_proofs = historical_owners(rs, cfg, snapshot, S, manifest, history)
        if args.execute:
            need(os.environ.get('BOLE_CONTINUATION_MAIN_ENABLE') == '1', 'separate explicit MAIN dispatcher opt-in')
            need(LOCK.is_file() and not LOCK.is_symlink(), 'existing ordinary shared MAIN lock')
            lock_fd = os.open(LOCK, os.O_RDWR | os.O_NOFOLLOW)
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            need(os.fstat(lock_fd).st_ino == LOCK.stat().st_ino and
                 os.fstat(lock_fd).st_dev == LOCK.stat().st_dev, 'same actual locked inode')
        F = load_exact(rs, SNAPSHOT_HELPER, '_bole_continuation_readonly_helper')
        F.START = entry_start
        live = current_live_checks(F, S, owners, historical_contexts, receipt_codec)
        need(F.ERRORS == [], 'all current read-only inspections complete')
        for path in (OUTPUT, Path(str(OUTPUT) + '-CPU'), EVIDENCE):
            need(not os.path.lexists(path) and not any(p.is_symlink() for p in path.parents),
                 'all registered outputs new and ordinary; no reuse/delete')
        rs.verify_again()
        F.rss(['continuation-main-predispatch'])
        need(time.monotonic() - entry_start <= 180 and time.time() + PHASE < CUT and
             time.time() - execution['ended_epoch'] <= 180,
             'one bounded preparation, still-fresh input and full original phase/cleanup fit')
        receipt = dict(schema='bole.continuation-main-predispatch/v1', scope=SCOPE,
            config_ref=config_ref, review_ref=review_ref, source=cfg['source_ref'],
            snapshot=cfg['snapshot_ref'], restoration=restoration_proof, live=live,
            historical_contexts=history_proofs,
            inputs=list(rs.refs.values()), old_window_extended=False, old_report_cutoff=OLD_REPORT_CUT,
            new_internal_cutoff=CUT, phase_seconds=PHASE, shared_cleanup_seconds=CLEANUP,
            resources_admitted=False, NPU=False, model_qualified=False, performance_admitted=False)
        if args.check_only:
            receipt['dispatch_performed'] = False
            encoded = canonical(receipt) + b'\n'
            need(len(encoded) <= 16 * 2**20, 'complete bounded check-only evidence; never truncate')
            sys.stdout.buffer.write(encoded)
            return 0
        EVIDENCE.mkdir(mode=0o700)
        with (EVIDENCE/'PREDISPATCH.json').open('xb') as stream:
            raw = canonical(receipt) + b'\n'
            need(len(raw) <= 16 * 2**20, 'complete bounded predispatch evidence')
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        require_exec_limits()
        need(os.fstat(lock_fd).st_ino == LOCK.stat().st_ino and
             os.fstat(lock_fd).st_dev == LOCK.stat().st_dev, 'MAIN lock inode still current before exec')
        os.set_inheritable(lock_fd, True)
        need(os.get_inheritable(lock_fd), 'shared MAIN lock FD must survive exact owner exec')
        signal.alarm(0)
        # env replaces itself with the exact /usr/bin/python3 -I -B owner.
        # The inherited lock survives; the owner controls every create/cleanup.
        os.execv(commands['model'][0], commands['model'])
    except BaseException as exc:
        print(json.dumps(dict(schema='bole.continuation-main-blocked/v1',
            error=type(exc).__name__ + ': ' + str(exc), resources_admitted=False,
            NPU=False, dispatch_performed=False, performance_admitted=False), sort_keys=True))
        return 2
    finally:
        signal.alarm(0)
        if lock_fd is not None:
            os.close(lock_fd)


if __name__ == '__main__':
    raise SystemExit(main())
