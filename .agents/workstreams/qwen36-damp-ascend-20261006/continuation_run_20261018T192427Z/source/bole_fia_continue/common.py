"""New fixed-frame source identity; no device selection or resource admission.

This source is a successor to the executed single-card paged component.  It is
not a shorter whole-model phase and cannot consume another source's CPU ticket.
"""
import hashlib
import importlib.util
import json
import os
import re
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = '/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-fia-fixed-frame-replay-continue-20261018T192427Z-v1'
OUTBASE = '/opt/host/vnf/austinov/run-bole-fia-fixed-frame-replay-MAIN-CONTINUE-20261018T192427Z-v1'
OUTROOT = OUTBASE+'/replay'
SCHEMA = 'bole.fia-fixed-frame-owned-source/v1'
START, CUT = 1792351467, 1792437867
IMAGE = 'sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
AUTHORITY = {'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/continuation_run_20261018T192427Z/AUTHORITY.json', 'bytes': 5610, 'sha256': '12644bad0403760aa7e976411572251f89c021e0182184c847b3c841ab6bab52'}
BATCH_ID = 'MAIN-CONTINUE-20261018T192427Z-v1'
REUSE_SCOPE = {'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/continuation_run_20261018T192427Z/REUSE_SCOPE.json', 'bytes': 3394, 'sha256': '99ba96aef815229a2db96cd977f3d1fe12b46774d42bcb79e765d74bfe192259'}
PREDECESSOR_SOURCE = {'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-fia-fixed-frame-replay-renew24h-20261018-001/SOURCE_MANIFEST.json', 'bytes': 12699, 'sha256': '535848eb04738414f099c2d261ba372611c080577fb06c3e0ebcad01b702c5e1'}
COMPONENT_ROOT = '/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-paged-tree-owned-new24h-v1-118t-repair1'
COMPONENT = dict(path=COMPONENT_ROOT+'/SOURCE_MANIFEST.json', bytes=25737, sha256='fdafbb8872ad9da1ff8150ddafa1e66acae3a80e05aa2b62bb04202da6e33faa')
COMPONENT_EXECUTION = dict(path='/opt/host/vnf/austinov/run-bole-paged-tree118trepair1-MAIN-20261016-001/paged/numeric/RESULT.json', bytes=1684, sha256='e7d9250ab7ab6add24aa53be4cae153ec3400a186cc96ae3e5fd5567aa9b0299')
REQUIRED_FILES = {'common.py', 'owner.py', 'cpu_owner.py', 'cpu_guest.py', 'guest.py',
                  'ticket.py', 'bind.py', 'test_owner.py', 'probe.py', 'plan.py',
                  'PLAN.json', 'test_probe.py', 'DONOR_NPU_OWNER.py', 'DONOR_CPU_OWNER.py'}
RESOURCE_CONTRACT = dict(whole_NPU_seconds=900, whole_CPU_seconds=1000,
                         guest_seconds=600, actual_FIA_seconds=560,
                         cleanup_seconds=90, call_cleanup_reserve_seconds=180,
                         ordinary_ram_floor=17716740096,
                         host_memory_bytes=536870912, guest_memory_bytes=8589934592,
                         guest_cpu_count=1, reserve_bytes=8589934592,
                         physical_device=4, logical_device=0,
                         raw_FIA_cap=67108864, whole_output_cap=1073741824,
                         live_free_bytes=9126805504, initial_free_bytes=10200547328)


def need(value, message):
    if not value:
        raise ValueError(message)


def ref(path):
    path = Path(path)
    before = path.stat()
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            digest.update(block)
            size += len(block)
    after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'stable complete file')
    return dict(path=str(path), bytes=size, sha256=digest.hexdigest())


def checked(value):
    need(type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}, 'exact Ref3')
    need(type(value['path']) is str and type(value['bytes']) is int and value['bytes'] >= 0
         and type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}', value['sha256']),
         'typed Ref3')
    path = Path(value['path'])
    need(path.is_absolute() and path.is_file() and
         not any(p.is_symlink() for p in (path, *path.parents)), 'ordinary immutable input')
    need(ref(path) == value, 'complete immutable input bytes')
    return path


def obj(value):
    return json.loads(checked(value).read_bytes())


def load(value, name):
    spec = importlib.util.spec_from_file_location(name, checked(value))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path, value):
    path = Path(path)
    need(path.is_absolute() and path.parent.is_dir() and
         not any(p.is_symlink() for p in (path.parent, *path.parent.parents)), 'ordinary owned parent')
    data = (json.dumps(value, sort_keys=True, allow_nan=False)+'\n').encode()
    need(len(data) <= 16*2**20, 'bounded metadata')
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return ref(path)


def dedup(refs):
    result = {}
    for value in refs:
        old = result.setdefault(value['path'], value)
        need(old == value, 'one immutable identity per path')
    return list(result.values())


def authority(manifest):
    need(manifest['authority_ref'] == AUTHORITY, 'exact current renewed authority')
    value = obj(AUTHORITY)
    need(value['schema'] == 'ascend.paper-portfolio.explicit-continuation-batch/v1' and
         value['start_epoch'] == START and value['cutoff_epoch'] == CUT and
         value['main_only_device_admission'] is True and value['physical_npus'] == [4, 5, 6, 7]
         and value['protected_npus'] == [0, 1, 2, 3], 'current MAIN authority unchanged')
    need(value['batch_id'] == BATCH_ID and manifest['reuse_scope_ref'] == REUSE_SCOPE,
         'exact current MAIN batch and separate reuse scope')
    scope = obj(REUSE_SCOPE)
    need(scope['schema'] == 'ascend.continuation-batch.historical-artifact-reuse/v1' and
         scope['batch_id'] == BATCH_ID and scope['base_authority'] == AUTHORITY and
         scope['start_epoch'] == START and scope['cutoff_epoch'] == CUT and
         scope['qualification'] is False and scope['numeric_qualified'] is False and
         scope['historical_capture_unchanged'] is True and scope['not_retroactive'] is True and
         value['old_window_immutable']['not_retroactive'] is True, 'exact read-only historical reuse/current authority join')
    policy = value['read_only_historical_reuse']
    need(policy['scope_document_path'] == REUSE_SCOPE['path'] and
         policy['separate_scope_ref_required_in_sources_that_reuse_historical_artifacts'] is True,
         'current authority requires the exact separate scope')
    return value


def window(manifest, whole=0):
    authority(manifest)
    now = time.time()
    need(START <= now < CUT-whole, 'entire separately registered component lease fits fixed cutoff')


def readset(manifest, source_ref=None):
    donor = obj(manifest['donor_source'])
    refs = [*([] if source_ref is None else [source_ref]),
            *manifest['files'].values(), manifest['authority_ref'], manifest['reuse_scope_ref'], manifest['predecessor_source_ref'], manifest['component_source_ref'],
            manifest['component_owner_ref'], manifest['component_cpu_owner_ref'],
            manifest['component_execution_ref'], obj(manifest['component_execution_ref'])['result'],
            manifest['donor_source'], manifest['donor_host'], manifest['cann_helper_ref'],
            *manifest['controller_files'].values(), *manifest['support_files'].values(),
            *manifest['dependencies'].values(), donor['observer_ref'],
            *[donor['files'][name] for name in ('scope_adapter.py', 'patch_scope.py', 'top_guard.py', 'terminal_fence.py')],
            *manifest['input_readset']]
    if manifest.get('prepared_template') is not None:
        refs.append(manifest['prepared_template'])
    refs = dedup(refs)
    for value in refs:
        checked(value)
    return refs


def validate(manifest, *, prepared=False):
    need(manifest['schema'] == SCHEMA and manifest['root'] == ROOT == str(HERE), 'exact successor root')
    need(manifest['batch_id'] == BATCH_ID and manifest['predecessor_source_ref'] == PREDECESSOR_SOURCE,
         'exact MAIN batch and immutable bound-only predecessor')
    need(manifest['prepared_only'] is prepared and manifest['default_enabled'] is False
         and manifest['qualified'] is False and manifest['model_ready'] is False
         and manifest['performance_ready'] is False, 'defaultOFF diagnostic source')
    need(manifest['output_root'] == OUTROOT and manifest['profile'] == 'replay'
         and manifest['image'] == IMAGE and manifest['resources'] == RESOURCE_CONTRACT,
         'original component resource contract; separate CPU1000 and NPU900')
    need(all(type(value) is int for value in manifest['resources'].values()), 'typed fixed resource limits')
    authority(manifest)
    need(manifest['component_source_ref'] == COMPONENT, 'actual executed paged component source')
    need(manifest['component_execution_ref'] == COMPONENT_EXECUTION, 'actual original component execution receipt')
    executed = obj(COMPONENT_EXECUTION)
    need(executed['schema'] == 'bole.tree-owned/v118t' and executed['source'] == COMPONENT
         and executed['primary'] is None and executed['secondary'] == []
         and executed['stopped_retained'] is True and executed['physical'] == [4]
         and executed['logical'] == 0 and executed['NPU'] is True and executed['qualified'] is False,
         'actual originally executed same component scope, not a qualification grant')
    original = obj(COMPONENT)
    need(original['prepared_only'] is False and original['image'] == IMAGE
         and original['whole_NPU_seconds'] == 900 and original['whole_CPU_seconds'] == 1000
         and original['cleanup_seconds'] == 90 and original['guest_seconds'] == 600
         and original['whole_output_cap'] == 2**30 and original['ordinary_ram_floor'] == 17716740096,
         'actual original component bounds; no model PHASE change')
    need(manifest['component_owner_ref'] == original['files']['owner116.py']
         and manifest['component_cpu_owner_ref'] == original['files']['owned_cpu116.py'],
         'actual reviewed component owners')
    for field in ('donor_source', 'donor_host', 'dependencies', 'cann_helper_ref', 'header_ref'):
        need(manifest[field] == original[field], 'unchanged resource/ABI donor '+field)
    for name, value in manifest['controller_files'].items():
        need(value == original['files'][name], 'unchanged original scope helper')
    need(set(manifest['controller_files']) == {'scope_adapter112.py', 'top_guard116.py', 'patch_scope112.py'},
         'complete composed scope helpers')
    need(set(manifest['support_files']) == {'abi116.py', 'abi115.py', 'probe115.py', 'common116.py', 'ticket_alias116r5.py', 'tree_fa115.py'},
         'complete original CPU ABI and alias helpers')
    for name, value in manifest['support_files'].items():
        need(value == original['files'][name], 'actual original ABI helper')
    need(REQUIRED_FILES <= set(manifest['files']), 'all actual new source and control files')
    need(manifest['software_control_counts'] == {'test_owner.py': 24, 'test_probe.py': 20},
         'actual source must execute all forty-four CPU controls without skips')
    for name, value in manifest['files'].items():
        need(type(name) is str and '/' not in name and value['path'] == str(HERE/name), 'new files cannot impersonate donor')
        checked(value)
    expected_names = set(manifest['files']) | {'SOURCE_TEMPLATE.json'}
    if not prepared:
        expected_names.add('SOURCE_MANIFEST.json')
        need(manifest['prepared_template']['path'] == str(HERE/'SOURCE_TEMPLATE.json'),
             'exact original new-source template remains in closure')
    entries = list(HERE.iterdir())
    need({entry.name for entry in entries} == expected_names and
         all(entry.is_file() and not entry.is_symlink() for entry in entries),
         'entire RO source directory contains only bound ordinary files; no ambient files or weight directories')
    need(manifest['probe_plan_ref'] == manifest['files']['PLAN.json'], 'fixed numerical plan')
    plan = load(manifest['files']['plan.py'], '_fia_fixed_selection')
    selection = plan.consume(manifest['probe_plan_ref'])
    need(manifest['input_readset'] == selection['readset'][1:], 'complete fixed original input readset')
    readset(manifest)
    return manifest


def source(source_ref):
    manifest = obj(source_ref)
    need(source_ref['path'] == str(HERE/'SOURCE_MANIFEST.json'), 'actual bound source filename')
    return validate(manifest)
