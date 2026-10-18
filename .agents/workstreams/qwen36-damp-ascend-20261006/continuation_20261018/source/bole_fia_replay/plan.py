"""Immutable R6 frame selection and exact byte provenance; no device imports."""
import copy
import hashlib
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_SCHEMA = 'bole.fia-fixed-frame-owned-source/v1'
CUTOFF = 1792313000
ROOT = '/opt/host/vnf/austinov/run-bole-r6-20261017-001-MAIN'
R6_ROOT = '/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-model-root-repeat-witness-renew24h-v1-20261017-001-repair6-projection-scope'
SOURCE = dict(path=R6_ROOT+'/SOURCE_BOUND.json', bytes=81841, sha256='f3303cec9fea4c7445e81373e21cd0da5884be495b72a8847420bf4400bb92f5')
RANK_REPORT = dict(path=ROOT+'/cpu-consumer/RANK-1.json', bytes=110007, sha256='751fad500cd4d530f639bb3d35c8c07ea719c3493c798f17b02072c4f197ce32')
RECEIPT = dict(path=ROOT+'/dense/receipts/BOLE-TREE-RANK-1.json', bytes=2287, sha256='2c667174e1851ab5ca762e612d34960217fff31297039b87601e0624696a64a7')
RAW = dict(path=ROOT+'/dense/receipts/BOLE-TREE-RANK-1.pt', bytes=776474709, sha256='21ab99d4a503f45f750c1926eb383b633b7ced8e9f24b767275c107da89f1c34')
PREVIOUS = dict(path='/opt/host/vnf/austinov/run-bole-fa-rounding-binding-MAIN-RENEW24H_001/fa/consumer/RANK-1.json', bytes=38445, sha256='b70166459442dd5dd4c43f4d3fb044b71bd4b9980a5df0c20061bbf6d35d23b6')
ORIGINAL_ABI = dict(path='/opt/host/vnf/austinov/run-bole-paged-tree118trepair1-MAIN-20261016-001/paged/cpu/preflight/ACTUAL_FIA_ABI.json', bytes=5425, sha256='164f89472d6adecb55c8eeb76b23e04c774c4040dbfb8eaa3ad5d9fccd3815a2')
PRODUCERS = {
    'adapter.py': dict(path=R6_ROOT+'/adapter.py', bytes=8622, sha256='37369161fbadad74e0f727c62e769069277d6f2696f7a8b2d88d67e92d93dc59'),
    'model_entry.py': dict(path=R6_ROOT+'/model_entry.py', bytes=30536, sha256='7b2cd9e826e7d97e691b78edbd10e7fccdfed04fc3e17dd8fddb054b661a39f6'),
    'independent_model.py': dict(path=R6_ROOT+'/independent_model.py', bytes=14336, sha256='cdffc7dcb59b744788c2b736a5607e7218a9e13595b0f6a7d10f450a4fb6ad72'),
}
COMMON = dict(input_layout='BNSD', num_heads=6, num_key_value_heads=1,
              scale=0.0625, pre_tokens=2147483647, next_tokens=2147483647)
TREE_KWARGS = dict(COMMON, block_size=128, actual_seq_lengths=[3],
                   actual_seq_lengths_kv=[134], sparse_mode=1, inner_precise=2)
NATIVE_KWARGS = dict(COMMON, actual_seq_lengths=[1],
                     actual_seq_lengths_kv=[133], sparse_mode=0, inner_precise=0)
CASES = [
    dict(id='tree-r1-l43-n2', branch='tree', node=2, label='tree-node2',
         elements=1536, allowed_keys=133, original_failed_flat_indices=[573]),
    dict(id='native-r1-l43-p2-n2', branch='native', path=2, node=2,
         label='native-path2-node2', elements=1536, allowed_keys=133,
         original_failed_flat_indices=[573]),
    dict(id='tree-r1-l43-n0-pass-control', branch='tree', node=0,
         label='tree-node0', elements=1536, allowed_keys=132,
         original_failed_flat_indices=[]),
]


def need(value, message):
    if not value:
        raise ValueError(message)


def checked(reference):
    need(type(reference) is dict and set(reference) == {'path', 'bytes', 'sha256'},
         'exact Ref3')
    need(type(reference['path']) is str and type(reference['bytes']) is int and
         reference['bytes'] >= 0 and type(reference['sha256']) is str and
         re.fullmatch('[0-9a-f]{64}', reference['sha256']), 'typed Ref3')
    path = Path(reference['path'])
    need(path.is_absolute() and path.is_file() and
         not any(p.is_symlink() for p in (path, *path.parents)), 'ordinary immutable file')
    before = path.stat()
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(2**20), b''):
            digest.update(block)
    after = path.stat()
    fields = ('st_dev', 'st_ino', 'st_mtime_ns', 'st_size')
    need(all(getattr(before, k) == getattr(after, k) for k in fields) and
         after.st_size == reference['bytes'] and digest.hexdigest() == reference['sha256'],
         'stable exact bytes/SHA')
    return path


def obj(reference):
    return json.loads(checked(reference).read_bytes())


def ref(path):
    path = Path(path)
    data = path.read_bytes()
    return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def write(path, value):
    path = Path(path)
    need(path.is_absolute() and path.parent.is_dir() and
         not any(p.is_symlink() for p in (path.parent, *path.parent.parents)),
         'owned ordinary output parent')
    data = (json.dumps(value, sort_keys=True, allow_nan=False)+'\n').encode()
    need(len(data) <= 16*2**20, 'scalar report at most16MiB')
    with path.open('xb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    return ref(path)


def expected():
    return dict(schema='bole.fia-fixed-frame-selection/v1', original_source=SOURCE,
                rank=1, layer=43, original_rank_report=RANK_REPORT,
                original_receipt=RECEIPT, original_raw=RAW,
                previous_rounding=PREVIOUS, original_abi=ORIGINAL_ABI,
                original_producers=PRODUCERS, cases=CASES,
                input_readset=[SOURCE, RANK_REPORT, RECEIPT, RAW, PREVIOUS,
                               ORIGINAL_ABI, *PRODUCERS.values()],
                tree_original=TREE_KWARGS, native_original=NATIVE_KWARGS,
                tree_intervention_inner_precise=0, native_intervention_inner_precise=2,
                both_complete_baselines_required=True,
                tree_query_count=3, tree_full_elements=4608, native_full_elements=1536,
                atol=0.001, rtol=0.01, original_failures_unchanged=True,
                inner_precise_numeric_semantics=None, qualified=False,
                whole_model_qualified=False, cutoff=CUTOFF)


def source(source_ref):
    manifest = obj(source_ref)
    need(manifest['schema'] == SOURCE_SCHEMA and manifest['root'] == str(HERE),
         'actual immutable delivered replay source')
    for filename in ('probe.py', 'plan.py', 'PLAN.json', 'test_probe.py'):
        need(manifest['files'][filename] == ref(HERE/filename),
             'exact delivered probe/plan/control file')
    need(manifest['files']['PLAN.json'] == manifest['probe_plan_ref'], 'fixed plan binding')
    for reference in manifest['files'].values():
        checked(reference)
    return manifest


def consume(plan_ref):
    plan = obj(plan_ref)
    need(plan == expected(), 'exact preregistered three frames and original FIA calls')
    original = obj(SOURCE)
    need(original['prepared_only'] is False and original['whole_numerical_qualification'] is False,
         'original executed nonqualified R6 source')
    for name, reference in PRODUCERS.items():
        need(original['files'][name] == reference, 'original producer/oracle source binding')
        checked(reference)
    rank = obj(RANK_REPORT)
    need(rank['source'] == SOURCE and rank['receipt'] == RECEIPT and rank['raw'] == RAW and
         rank['report']['component_checks_pass'] is False and
         rank['report']['whole_numerical_qualified'] is False,
         'original model failure remains unchanged')
    layer = [row for row in rank['report']['rows'] if row['layer'] == 43]
    need(len(layer) == 1 and layer[0]['kind'] == 'fa' and
         layer[0]['attention']['double']['pointwise_pass'] is False,
         'original rank1 layer43 FA gate failure')
    receipt = obj(RECEIPT)
    need(receipt['source'] == SOURCE and receipt['rank'] == 1 and
         receipt['primary'] is None and receipt['raw'] == RAW, 'original producer/raw join')
    checked(RAW)
    previous = obj(PREVIOUS)
    need(previous['schema'] == 'bole.saved-fa-compensated-rounding-diagnostic/v1' and
         previous['rank'] == 1 and previous['original_source'] == SOURCE and
         previous['original_raw'] == RAW and previous['rank_report'] == RANK_REPORT and
         previous['qualified'] is False and previous['NPU'] is False and
         previous['original_failures_preserved'] is True, 'fixed previous diagnostic receipt')
    rows = [row for row in previous['rows'] if row['layer'] == 43]
    need(len(rows) == 1, 'unique original layer43')
    for case in CASES:
        group = 'tree' if case['branch'] == 'tree' else 'native_own_inputs'
        matches = [row for row in rows[0][group] if row['label'] == case['label']]
        need(len(matches) == 1, 'unique fixed original case')
        row = matches[0]
        wanted = case['original_failed_flat_indices']
        need(row['elements'] == 1536 and row['failed'] == row['compensated_failed'] == len(wanted)
             and row['failed_set_changed'] is False and
             [p['head']*256+p['channel'] for p in row['failed_values']] == wanted,
             'fixed original whole-vector failure identities')
    abi = obj(ORIGINAL_ABI)
    need(abi['schema'] == 'bole.actual-FIA-installed-ABI/v115' and
         abi['NPU'] is False and abi['operator_executed'] is False and
         abi['operator'] == 'npu::npu_fused_infer_attention_score' and
         'inner_precise' in abi['argument_names'], 'original actual installed ABI receipt')
    readset = [plan_ref, SOURCE, RANK_REPORT, RECEIPT, RAW, PREVIOUS, ORIGINAL_ABI,
               *PRODUCERS.values()]
    return dict(plan=plan, previous_layer=rows[0], original_abi=abi, readset=readset,
                qualified=False)


def call_parameters(branch, intervention=False):
    need(type(intervention) is bool and branch in ('tree', 'native'), 'known original branch')
    result = copy.deepcopy(TREE_KWARGS if branch == 'tree' else NATIVE_KWARGS)
    if intervention:
        result['inner_precise'] = 0 if branch == 'tree' else 2
    return result
