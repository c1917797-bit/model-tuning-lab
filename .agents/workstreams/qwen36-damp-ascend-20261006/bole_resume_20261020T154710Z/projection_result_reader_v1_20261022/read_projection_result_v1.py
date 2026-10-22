"""Read one completed ON boundary diagnostic; never run a model or grant a gate.

Inputs are exact SOURCE, RESULT and pre-run SOURCE_AUDIT Ref3 JSON operands.
Only --output is written, exclusively, after complete validation and rereads.
G1/G2 are distinct requests; neither identical initial state nor causality is
assumed.  The unchanged original single-arm reader is used, never R.compare.
"""
import argparse
import ast
import hashlib
import importlib
import json
import math
import os
import stat
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
WORKSTREAM = Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
SOURCE_ROOT = WORKSTREAM / 'bound-boundary-ON-v2-20261022T100000Z'
OUTPUT_ROOT = Path('/opt/host/vnf/austinov/run-bole-boundary-ON-v2-20261022T100000Z')
SOURCE_AUDIT_PATH = Path('/opt/host/vnf/austinov/run-bole-boundary-source-audit-v3-20261022T100000Z/SOURCE_AUDIT.json')
# Set to True only after all source/schema pins are independently reviewed.
REVIEWED_EXTENSION_FROZEN = False
AUDIT_PROGRAM_REF = dict(path=str(WORKSTREAM/'boundary_source_audit_v3_20261022/audit_boundary_source_v3.py'),
    bytes=None, sha256=None)
ORIGINAL_AUDIT_REF = dict(path=str(WORKSTREAM/'boundary_probe_prepare_v1_20261022/audit_boundary_source.py'),
    bytes=4631, sha256='318abb0246fce440ba877c8428cbcc1dd90caea7846be76a884c5e26cb4b5533')
V4_ROOT = WORKSTREAM / 'short_pair_reader_v4_20261022'
V4_PINS = {
    'compare_completed_short.py': (3300, 'dd653ae8be7d83f3b83c0f1d069b64af4d4be2a72ec5d60dff49f0024a21d8df'),
    'cleanup_summary.py': (3957, '1c2e014303bec214cff2e19d8c428eee1a13d69c3f8b525308b3ae958faf9687'),
}
ORIGINAL_PINS = {
    'compare_state_digest.py': (8418, 'a7bdff799d6bc214b69e2da69d3bb8d78ee19dd73c30ef48a22317b27064c826'),
    'short_state_digest.py': (11410, '21d95e3cec1b90260229a4fa156981e48bbdaa9a7d466a230c63fbf4d9099ec8'),
    'bole_performance_profile.py': (4979, 'f1ffb4485d8963c06eab882f6c2d8b5700de74025b9663cc705e5df5c88c67f8'),
}
BOUNDARY_PINS = {
    'boundary_probe_v1.py': (None, None),
    'boundary_delta.py': (None, None),
    'boundary_integration.py': (None, None),
    'boundary_validation.py': (None, None),
    'projection_probe_v1.py': (None, None),
}

SCHEMA = 'bole.native-prefill-boundary-repeatability/v1'
LAYERS = tuple(i for i in range(64) if i % 4 != 3)
PHASES = ('post_native_prefill_registered', 'calibration_before',
          'calibration_after', 'initial_mtp_before', 'initial_mtp_after')
RAW_SHAPES = {
    'layer0_core_output': (131, 12, 128),
    'layer0_gated_norm': (1572, 128),
    'layer0_out_projection': (131, 5120),
    'layer0_post_norm_hidden': (131, 5120),
    'layer0_post_norm_residual': (131, 5120),
    'layer0_mlp': (131, 5120),
    'layer1_mixed_qkv': (131, 2560),
    'layer1_b': (131, 12),
    'layer1_a': (131, 12),
}
DIGESTS = ('state', 'conv_full', 'conv_leading3')
RAW_CAP, META_CAP, DEVICE_READ_CAP = 836352, 512 * 1024, 512 * 2**20
FILE_CAP, JSON_CAP, READSET_CAP, TOTAL_CAP = 128 * 2**20, 8 * 2**20, 16384, 2**31
OUTPUT_CAP = 32 * 2**20
SEMANTICS = ('prompt', 'length', 'version', 'tokens', 'processed_nodes', 'emitted_tokens')
ENCODING = 'little-endian IEEE bfloat16; contiguous logical order'
PROJECTION_SCHEMA = 'bole.native-projection-internal/v1'
PROJECTION_STAGES = ('projection_input', 'quant_return', 'pre_reduce', 'post_reduce', 'projection_return')
PROJECTION_ENVELOPE_CAP = 8192
PROJECTION_READ_CAP_GENERATION = 8 * 2**20
PROJECTION_READ_CAP_TOTAL = 16 * 2**20
PROJECTION_RUNTIME_REFS = {'/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear.py': {'bytes': 21354, 'path': '/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear.py', 'sha256': '3f14a92019a6612158ba41a26c358c8f164cbda66b743c518a5e4019694b5dc3'}, '/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear_op.py': {'bytes': 30813, 'path': '/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear_op.py', 'sha256': '0333d3229dbfed3010413510b76395a9ad89138dfd1d578caab057573b6cd0fb'}, '/vllm-workspace/vllm-ascend/vllm_ascend/utils.py': {'bytes': 67646, 'path': '/vllm-workspace/vllm-ascend/vllm_ascend/utils.py', 'sha256': '575b45d684eabdb7ac3195d33de48bd5f3233081f78886c08be92a4a2fd2fc02'}, '/vllm-workspace/vllm/vllm/model_executor/custom_op.py': {'bytes': 13924, 'path': '/vllm-workspace/vllm/vllm/model_executor/custom_op.py', 'sha256': '4b4ba01623005d6a93698eaec007a934dd512bf9ec7241090927de819621de2e'}, '/vllm-workspace/vllm/vllm/model_executor/layers/linear.py': {'bytes': 63273, 'path': '/vllm-workspace/vllm/vllm/model_executor/layers/linear.py', 'sha256': 'a5e099997f868a5ce670aa2afe94da90222fceace36aef4e1275f3830ee257ab'}}
PROJECTION_SNAPSHOTS = {'/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear.py': 'evidence/ascend_linear.py', '/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear_op.py': 'evidence/ascend_linear_op.py', '/vllm-workspace/vllm-ascend/vllm_ascend/utils.py': 'evidence/ascend_utils.py', '/vllm-workspace/vllm/vllm/model_executor/custom_op.py': 'evidence/custom_op.py', '/vllm-workspace/vllm/vllm/model_executor/layers/linear.py': 'evidence/vllm_linear.py'}



def need(value, message):
    if not value:
        raise ValueError(message)


def sha(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def uint(value, maximum=2**64):
    return type(value) is int and 0 <= value < maximum


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('utf-8')


def canonical_ref(value):
    raw = canonical(value)
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                encoding='canonical parsed JSON; UTF-8, sorted keys, compact separators, ASCII escapes, no newline; not original HTTP wire bytes')


def typed_ref(reference, cap=FILE_CAP):
    need(type(reference) is dict and set(reference) == {'path', 'bytes', 'sha256'}, 'exact input Ref3')
    need(type(reference['path']) is str and '\x00' not in reference['path'] and
         uint(reference['bytes'], cap + 1) and sha(reference['sha256']), 'typed bounded input Ref3')
    path = Path(reference['path'])
    need(path.is_absolute() and str(path) == reference['path'] and '..' not in path.parts,
         'canonical absolute input path')
    return path


def file_identity(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
            value.st_uid, value.st_gid, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def parents_identity(path):
    result = []
    for parent in path.parents:
        value = parent.lstat()
        need(stat.S_ISDIR(value.st_mode), 'ordinary input ancestors, no symlink')
        result.append((str(parent), value.st_dev, value.st_ino, value.st_mode))
    return tuple(result)


def whole_file(path, *, cap, expected=None, keep=True):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts, 'absolute read path')
    parents = parents_identity(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= cap, 'regular bounded whole input')
    if expected is not None:
        need(before.st_size == expected['bytes'], 'exact input byte count before read')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    digest, blocks, size = hashlib.sha256(), [], 0
    with os.fdopen(fd, 'rb') as stream:
        need(file_identity(os.fstat(stream.fileno())) == file_identity(before), 'stable opened input')
        while True:
            block = stream.read(min(2**20, cap + 1 - size))
            if not block:
                break
            size += len(block)
            need(size <= cap, 'bounded full read, never a prefix hash')
            digest.update(block)
            if keep:
                blocks.append(block)
        need(file_identity(os.fstat(stream.fileno())) == file_identity(before), 'stable input during read')
    need(file_identity(path.lstat()) == file_identity(before) and
         parents_identity(path) == parents and size == before.st_size, 'stable complete input path')
    reference = dict(path=str(path), bytes=size, sha256=digest.hexdigest())
    need(expected is None or reference == expected, 'exact whole-file input SHA')
    return reference, b''.join(blocks) if keep else None, file_identity(before)


class Readset:
    def __init__(self):
        self.refs, self.identities, self.total = {}, {}, 0

    def read(self, reference, cap=JSON_CAP, *, keep=True):
        path = typed_ref(reference, cap)
        key = str(path)
        need(key not in self.refs or self.refs[key] == reference, 'unique immutable Ref for each path')
        actual, raw, identity = whole_file(path, cap=cap, expected=reference, keep=keep)
        if key not in self.refs:
            need(len(self.refs) < READSET_CAP and self.total + reference['bytes'] <= TOTAL_CAP,
                 'bounded complete readset')
            self.refs[key], self.identities[key] = actual, identity
            self.total += reference['bytes']
        else:
            need(self.identities[key] == identity, 'input identity unchanged since first read')
        return raw

    def discover(self, path, cap=JSON_CAP):
        reference, raw, identity = whole_file(path, cap=cap)
        key = reference['path']
        if key in self.refs:
            need(self.refs[key] == reference and self.identities[key] == identity, 'discovered input unchanged')
        else:
            need(len(self.refs) < READSET_CAP and self.total + reference['bytes'] <= TOTAL_CAP, 'bounded discovered readset')
            self.refs[key], self.identities[key] = reference, identity
            self.total += reference['bytes']
        return reference, raw

    def obj(self, reference, cap=JSON_CAP):
        return strict_json(self.read(reference, cap))

    def discovered_obj(self, path, cap=JSON_CAP):
        reference, raw = self.discover(path, cap)
        return reference, strict_json(raw)

    def summary2(self, summary, expected_path):
        need(type(summary) is dict and set(summary) == {'path', 'sha256'} and
             summary['path'] == str(expected_path) and sha(summary['sha256']), 'exact observed producer Ref2')
        reference, raw = self.discover(expected_path, 2**22)
        need(reference['sha256'] == summary['sha256'], 'whole SHA of producer Ref2')
        return reference, strict_json(raw)

    def finish(self):
        before = [self.refs[path] for path in sorted(self.refs)]
        after = []
        for reference in before:
            self.read(reference, FILE_CAP, keep=False)
            after.append(dict(reference))
        need(before == after, 'complete diagnostic input readset unchanged')
        return before, after


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'no duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('non-finite JSON constant: ' + value)))


def ref_map(references):
    need(type(references) is list and 0 < len(references) <= READSET_CAP, 'bounded nonempty Ref list')
    result = {}
    for reference in references:
        typed_ref(reference)
        key = reference['path']
        need(key not in result or result[key] == reference, 'no conflicting duplicate Ref')
        result[key] = reference
    return result


def declaration():
    return dict(schema=SCHEMA, enabled=True, arm='ON', generations=2,
        input_tokens=131, output_tokens=8, raw_actual_token_slice=[123, 131],
        raw_names=list(RAW_SHAPES), phases=list(PHASES), native_gdn_layers=48,
        hash_native0_inputs=True, raw_bytes_cap_per_rank=RAW_CAP,
        metadata_bytes_cap_per_rank=META_CAP, device_read_bytes_cap_per_rank=DEVICE_READ_CAP,
        existing_other_cap_bytes=3 * 2**20, other_headroom_bytes=64 * 1024,
        formal_performance=False, numerical_qualified=False)


def projection_declaration():
    return dict(schema=PROJECTION_SCHEMA, enabled=True, arm='ON', generations=2,
        input_tokens=131, stages=list(PROJECTION_STAGES), envelope_bytes_cap=PROJECTION_ENVELOPE_CAP,
        extra_read_bytes_per_generation=PROJECTION_READ_CAP_GENERATION,
        extra_read_bytes_total=PROJECTION_READ_CAP_TOTAL, raw_bytes=0,
        full_weight_bytes_hashed=False, source_bound_python_callsites_only=True,
        numerical_qualified=False, formal_performance=False)


def projection_source_bindings(readset, manifest, audited):
    """Reopen audited host snapshots; never try to open guest-only paths."""
    need(canonical(manifest['projection_probe_profile']) == canonical(projection_declaration()),
         'exact independently reviewed hash-only projection declaration')
    need(canonical(manifest['projection_runtime_refs']) == canonical(PROJECTION_RUNTIME_REFS),
         'exact five installed-runtime Ref identities, not host path substitutions')
    references, rows, trees = [], [], {}
    for index, guest in enumerate(sorted(PROJECTION_RUNTIME_REFS)):
        runtime_ref = PROJECTION_RUNTIME_REFS[guest]
        typed_ref(runtime_ref)
        name = PROJECTION_SNAPSHOTS[guest]
        expected = dict(path=str(SOURCE_ROOT/name), bytes=runtime_ref['bytes'], sha256=runtime_ref['sha256'])
        need(manifest['files'][name] == expected and audited.get(expected['path']) == expected,
             'fixed source-owned host snapshot in complete audited readset')
        raw = readset.read(expected, 2**20)
        trees[index] = ast.parse(raw, filename=guest)
        references.append(dict(runtime_ref))
        rows.append(dict(runtime=runtime_ref, host_snapshot=expected))
    return dict(runtime_refs=references, snapshots=rows, trees=trees)


def projection_function_node(tree, qualname):
    found = []
    def visit(node, parents=()):
        for child in getattr(node, 'body', ()):
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                path = parents + (child.name,)
                if '.'.join(path) == qualname:
                    found.append(child)
                visit(child, path)
    visit(tree)
    need(len(found) == 1 and isinstance(found[0], ast.FunctionDef), 'one exact pinned-source method AST')
    return found[0]


def projection_reduction_sites(node):
    """Independently recover direct supported callsites, not callee source."""
    reducers = {'tensor_model_parallel_all_reduce', 'tensor_model_parallel_reduce_scatter',
                'reduce_scatter', 'npu_mm_all_reduce_base', 'npu_mm_reduce_scatter_base'}
    fused = {'npu_mm_all_reduce_base', 'npu_mm_reduce_scatter_base'}
    def target(value):
        if isinstance(value, ast.Name):
            return value.id
        if isinstance(value, ast.Attribute):
            parent = target(value.value)
            return None if parent is None else parent + '.' + value.attr
        return None
    result = []
    def visit(value, root=False):
        if not root and isinstance(value, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            return
        call, destination = None, None
        if isinstance(value, ast.Assign) and len(value.targets) == 1 and isinstance(value.targets[0], ast.Name):
            call, destination = value.value, value.targets[0].id
        elif isinstance(value, ast.Return):
            call, destination = value.value, 'return'
        if isinstance(call, ast.Call):
            name = target(call.func)
            kind = None if name is None else name.rsplit('.', 1)[-1]
            if kind in reducers:
                need(destination in ('output', 'return'), 'fixed supported reduction result site')
                need(kind in fused or call.args and isinstance(call.args[0], ast.Name) and
                     call.args[0].id == 'output_parallel', 'fixed complete nonfused reduction operand')
                result.append(dict(line=value.lineno, end_line=value.end_lineno, target=name,
                                   kind=kind, destination=destination, fused=kind in fused))
        for child in ast.iter_child_nodes(value):
            visit(child)
    visit(node, root=True)
    return result


def projection_text(value, limit=192, *, empty=True):
    need(type(value) is str and len(value) <= limit and (empty or bool(value)), 'bounded projection metadata string')
    return value


def projection_tensor_metadata(value):
    need(type(value) is dict and set(value) == {'geometry', 'version', 'bytes_hashed', 'format_observed', 'format'} and
         value['bytes_hashed'] is False and value['format_observed'] is False and value['format'] is None and
         (value['version'] is None or uint(value['version'])), 'weight/bias metadata without invented content or format proof')
    geometry(value['geometry'])


def projection_alias(value):
    need(type(value) is dict and type(value.get('observed')) is bool, 'typed actual callsite alias observation')
    if value['observed'] is False:
        need(set(value) == {'observed', 'reason'} and
             value['reason'] == 'descriptor_or_dynamic_receiver_not_evaluated', 'honest unavailable alias')
        return
    need(set(value) == {'observed', 'object', 'type', 'module', 'qualname', 'code_sha256', 'source_pinned'} and
         uint(value['object']) and value['object'] > 0 and value['source_pinned'] is False and
         (value['code_sha256'] is None or sha(value['code_sha256'])), 'alias identity is not an independently pinned callee')
    for key in ('type', 'module', 'qualname'):
        projection_text(value[key], empty=key != 'type')


def validate_projection_record(record, *, generation, rank, request, native0, runtime, previous_read_bytes):
    keys = {'schema', 'generation', 'request', 'request_object', 'active', 'runtime_refs', 'roles', 'calls',
            'exceptions', 'stages', 'reductions', 'read_bytes_generation', 'read_bytes_total', 'code_hash_algorithm',
            'outer_records', 'trace_restored', 'original_bound_calls', 'new_raw_bytes', 'weight_bytes_hashed',
            'source_bound_python_callsites_only', 'collective_implementation_pinned', 'numerical_qualified',
            'formal_performance', 'diagnostic_only'}
    need(type(record) is dict and set(record) == keys and record['schema'] == PROJECTION_SCHEMA and
         type(record['generation']) is int and record['generation'] == generation and
         record['request'] == request and record['request_object'] == native0['request_object'] and
         uint(record['request_object']) and record['request_object'] > 0,
         'exact projection generation and genuine native request join')
    projection_text(record['request'], 128, empty=False)
    need(record['runtime_refs'] == runtime['runtime_refs'] and
         record['code_hash_algorithm'] == 'sha256(marshal.dumps(code)); producer-runtime witness' and
         record['trace_restored'] is True and type(record['original_bound_calls']) is int and
         record['original_bound_calls'] == 1 and type(record['new_raw_bytes']) is int and record['new_raw_bytes'] == 0 and
         record['weight_bytes_hashed'] is False and record['source_bound_python_callsites_only'] is True and
         record['collective_implementation_pinned'] is False and record['numerical_qualified'] is False and
         record['formal_performance'] is False and record['diagnostic_only'] is True and
         record['outer_records'] == dict(norm='G%d-RAW-layer0_gated_norm.json' % generation,
                                        projection='G%d-RAW-layer0_out_projection.json' % generation),
         'exact source/runtime witness, original-call count, no callee or numerical admission')
    active = record['active']
    need(type(active) is dict and set(active) == {'layer_class', 'layer_object', 'gdn_object', 'prefix', 'tp_rank', 'tp_size',
         'input_is_parallel', 'reduce_results', 'return_bias', 'quant_class', 'quant_object', 'custom_class',
         'custom_object', 'weight', 'bias'}, 'complete actual projection owner and dispatch metadata')
    for key in ('layer_class', 'quant_class'):
        projection_text(active[key], empty=False)
    projection_text(active['prefix'], 128, empty=False)
    need(active['prefix'] == native0['prefix'] + '.out_proj' and
         all(uint(active[key]) and active[key] > 0 for key in ('layer_object', 'gdn_object', 'quant_object')) and
         active['layer_object'] != active['gdn_object'] and
         type(active['tp_size']) is int and 1 <= active['tp_size'] <= 4 and
         type(active['tp_rank']) is int and 0 <= active['tp_rank'] < active['tp_size'] and
         all(type(active[key]) is bool for key in ('input_is_parallel', 'reduce_results', 'return_bias')),
         'actual bounded operator TP metadata and native layer0 prefix')
    if active['custom_class'] is None:
        need(active['custom_object'] is None, 'absent custom operation has no synthetic object')
    else:
        projection_text(active['custom_class'], empty=False)
        need(uint(active['custom_object']) and active['custom_object'] > 0, 'actual custom operation identity')
    projection_tensor_metadata(active['weight'])
    if active['bias'] is not None:
        projection_tensor_metadata(active['bias'])
    roles = record['roles']
    need(type(roles) is list and 2 <= len(roles) <= 6 and
         all(type(row) is dict and type(row.get('role')) is str for row in roles),
         'bounded exact method role inventory')
    role_names = [row['role'] for row in roles]
    expected_roles = ['projection.forward', 'quant.apply']
    if 'projection.generic_forward' in role_names:
        expected_roles.append('projection.generic_forward')
    if active['custom_class'] is not None:
        expected_roles.extend(('custom.apply', 'custom.apply_impl'))
        if 'custom.matmul_and_reduce' in role_names:
            expected_roles.append('custom.matmul_and_reduce')
    need(role_names == expected_roles, 'complete ordered actual method inventory without duplicate or invented role')
    allowed_sources = {'projection.forward': {0, 4}, 'projection.generic_forward': {4}, 'quant.apply': {0, 4},
                       'custom.apply': {1}, 'custom.apply_impl': {1}, 'custom.matmul_and_reduce': {1}}
    suffix = {'projection.forward': 'forward', 'projection.generic_forward': 'forward', 'quant.apply': 'apply',
              'custom.apply': 'apply', 'custom.apply_impl': 'apply_impl', 'custom.matmul_and_reduce': 'matmul_and_reduce'}
    methods = {}
    for row in roles:
        role = row['role']
        need(set(row) == {'role', 'source_index', 'qualname', 'receiver', 'code_sha256', 'first_line'} and
             type(row['source_index']) is int and row['source_index'] in allowed_sources[role] and
             uint(row['receiver']) and row['receiver'] > 0 and sha(row['code_sha256']) and
             uint(row['first_line']) and row['first_line'] > 0, 'typed fixed-source role and producer-runtime code hash')
        projection_text(row['qualname'], empty=False)
        need(row['qualname'].rsplit('.', 1)[-1] == suffix[role], 'role refers to its actual method kind')
        node = projection_function_node(runtime['trees'][row['source_index']], row['qualname'])
        first = min([node.lineno] + [item.lineno for item in node.decorator_list])
        need(row['first_line'] in (first, node.lineno), 'role line belongs to exact complete source method')
        owner = active['layer_object'] if role.startswith('projection.') else active[
            'quant_object' if role == 'quant.apply' else 'custom_object']
        need(row['receiver'] == owner, 'role receiver joins actual strongly held target object')
        methods[role] = dict(node=node, sites=projection_reduction_sites(node), row=row)
    calls = record['calls']
    need(type(calls) is list and 2 <= len(calls) <= 48 and
         calls[0] == ['projection.forward', 'call'] and calls[-1] == ['projection.forward', 'return'],
         'bounded original root call trace')
    stack = []
    for call in calls:
        need(type(call) is list and len(call) == 2 and call[0] in methods and call[1] in ('call', 'return'),
             'only actually source-bound method events')
        if call[1] == 'call':
            need(bool(stack) or call == calls[0], 'all nested roles belong to one original projection')
            stack.append(call[0])
        else:
            need(stack and stack.pop() == call[0], 'balanced native method ancestry and return order')
    need(not stack and calls.count(['projection.forward', 'call']) == calls.count(['projection.forward', 'return']) == 1,
         'one complete original root method, not replay or recursion')
    exceptions = record['exceptions']
    need(type(exceptions) is list and len(exceptions) <= 4, 'bounded observed exception events retained without hiding them')
    for event in exceptions:
        need(set(event) == {'role', 'line', 'type'} and event['role'] in methods and
             type(event['line']) is int and methods[event['role']]['node'].lineno <= event['line'] <=
             methods[event['role']]['node'].end_lineno, 'exception event belongs to bound caller source')
        projection_text(event['type'], empty=False)
    reductions = record['reductions']
    need(type(reductions) is list and len(reductions) <= 1, 'at most one actual supported reduction callsite')
    for reduction in reductions:
        need(set(reduction) == {'line', 'end_line', 'target', 'kind', 'destination', 'fused', 'role', 'callsite_only',
             'callee_source_pinned', 'transport_kernel_observed', 'alias'} and reduction['role'] in methods and
             reduction['callsite_only'] is True and reduction['callee_source_pinned'] is False and
             reduction['transport_kernel_observed'] is False and type(reduction['fused']) is bool and
             [reduction['role'], 'call'] in calls, 'executed source-bound caller, no pinned communication implementation claim')
        site = {key: reduction[key] for key in ('line', 'end_line', 'target', 'kind', 'destination', 'fused')}
        need(any(canonical(site) == canonical(actual) for actual in methods[reduction['role']]['sites']),
             'exact reduction line, target, operand/destination and fusion kind from complete pinned source')
        projection_alias(reduction['alias'])
    stages = record['stages']
    need(type(stages) is dict and set(stages) == set(PROJECTION_STAGES), 'all five observed-or-explicitly-unavailable stages')
    fused = bool(reductions and reductions[0]['fused'])
    observed_names = ['projection_input'] + ([] if fused else ['quant_return']) + (
        (['post_reduce'] if fused else ['pre_reduce', 'post_reduce']) if reductions else []) + ['projection_return']
    read_bytes, ordinal = 0, 0
    for name in PROJECTION_STAGES:
        value = stages[name]
        need(type(value) is dict and type(value.get('observed')) is bool, 'typed stage availability, never absence defaulted to equality')
        if name not in observed_names:
            reason = 'fused_no_python_local_result' if fused else 'no_reduce_callsite_executed'
            need(set(value) == {'observed', 'reason'} and value['observed'] is False and value['reason'] == reason,
                 'missing stage is justified by the actual recorded supported-callsite branch')
            continue
        need(set(value) == {'observed', 'read_ordinal', 'source_role', 'line', 'sha256', 'bytes', 'dtype', 'shape', 'geometry',
             'finite', 'full_actual_tensor', 'numerical_qualified'} and value['observed'] is True and
             sha(value['sha256']) and uint(value['bytes'], 2 * 2**20 + 1) and value['bytes'] > 0 and
             value['finite'] is True and value['full_actual_tensor'] is True and value['numerical_qualified'] is False,
             'complete bounded finite logical stage witness, no numerical equality gate')
        ordinal += 1
        need(type(value['read_ordinal']) is int and value['read_ordinal'] == ordinal, 'each actual independent stage read counted once in order')
        geometry(value['geometry'], expected_shape=value['shape'], expected_dtype=value['dtype'])
        need(value['bytes'] == value['geometry']['logical_bytes'] and type(value['line']) is int,
             'stage metadata and complete logical geometry agree')
        if name == 'projection_input':
            need(value['source_role'] == 'projection.wrapper_entry' and value['line'] == 0, 'actual wrapper input before one original call')
        else:
            expected_role = ('quant.apply' if name == 'quant_return' else 'projection.forward' if name == 'projection_return'
                             else reductions[0]['role'])
            need(value['source_role'] == expected_role and [expected_role, 'call'] in calls,
                 'observed tensor belongs to its actual native source role')
            node = methods[expected_role]['node']
            need(node.lineno <= value['line'] <= node.end_lineno, 'stage source line within actual bound method')
            if name == 'pre_reduce':
                need(reductions[0]['line'] <= value['line'] <= reductions[0]['end_line'],
                     'actual local result immediately before its recorded nonfused callsite')
            elif name == 'post_reduce':
                need(value['line'] >= reductions[0]['line'] and
                     (reductions[0]['destination'] == 'return' or value['line'] > reductions[0]['end_line']),
                     'actual source result observed after supported reduction return/assignment')
        read_bytes += value['bytes']
    need(calls.count(['quant.apply', 'call']) == calls.count(['quant.apply', 'return']) == (0 if fused else 1),
         'fused absence is witnessed, never inferred from a missing quant event alone')
    need(type(record['read_bytes_generation']) is int and record['read_bytes_generation'] == read_bytes <= PROJECTION_READ_CAP_GENERATION and
         type(record['read_bytes_total']) is int and record['read_bytes_total'] == previous_read_bytes + read_bytes <= PROJECTION_READ_CAP_TOTAL,
         'independently recomputed per-generation and cumulative extra D2H bytes')
    return dict(record=record, extra_read_bytes=read_bytes, total_extra_read_bytes=record['read_bytes_total'],
                source_snapshots=runtime['snapshots'], caller_source_validated=True, callee_source_validated=False)


def independent_audit_lineage(readset, source_ref, audit_ref, manifest, audit, audited):
    need(typed_ref(audit_ref) == SOURCE_AUDIT_PATH,
         'exact new independent v3 source-audit output identity')
    need(audit['audit_program_ref'] == AUDIT_PROGRAM_REF and audit['audit_program_unchanged'] is True and
         audit['original_audit_source'] == ORIGINAL_AUDIT_REF and
         ORIGINAL_AUDIT_REF in manifest['dependencies'] and
         audited.get(ORIGINAL_AUDIT_REF['path']) == ORIGINAL_AUDIT_REF,
         'exact independent auditor v3 and retained unchanged original runtime auditor')
    # These complete Ref reads also enter the common final before/after reread.
    # The new independent auditor is not inserted into the old host readset.
    readset.read(AUDIT_PROGRAM_REF, 2**20)
    readset.read(ORIGINAL_AUDIT_REF, 2**20)
    command_path = str(SOURCE_ROOT/'COMMANDS.json')
    need(command_path in audited, 'unchanged original bound commands in actual host readset')
    commands = readset.obj(audited[command_path])
    recorded = audit['recorded_source_argument']
    need(type(recorded) is str and strict_json(recorded) == source_ref and commands['bound_source'] == source_ref,
         'recorded command operand parses to the same exact source Ref')
    for key in ('model', 'CPU'):
        argv = commands[key]
        need(type(argv) is list and argv.count('--source-ref') == 1 and
             argv.index('--source-ref') + 1 < len(argv) and
             argv[argv.index('--source-ref') + 1] == recorded,
             'literal source argument unchanged from actual ' + key + ' command')


def source_and_audit(readset, source_ref, result_ref, audit_ref):
    need(typed_ref(source_ref) == SOURCE_ROOT/'SOURCE_BOUND.json' and
         typed_ref(result_ref) == OUTPUT_ROOT/'RESULT.json', 'one exact new ON source/output identity')
    need(typed_ref(audit_ref) == SOURCE_AUDIT_PATH, 'one exact independent v3 audit result path before any read')
    m, result, audit = [readset.obj(reference) for reference in (source_ref, result_ref, audit_ref)]
    need(m['root'] == str(SOURCE_ROOT) and m['output_root'] == str(OUTPUT_ROOT) and
         m['model_receipt_root'] == str(OUTPUT_ROOT/'dense/receipts') and
         m['prepared_only'] is False and m['default_enabled'] is False and
         m['short_state_digest_profile']['observation'] == 'ON' and 'observation_only_profile' not in m,
         'exact default-disabled bounded ON source')
    need(canonical(m['boundary_probe_profile']) == canonical(declaration()), 'exact reviewed boundary declaration')
    need(audit['schema'] == 'bole.boundary-source-admission/v1' and audit['source'] == source_ref and
         audit['source_validated'] is True and audit['original_inputs_unchanged'] is True and
         audit['host_readset_exact'] is True and audit['NPU'] is False and audit['tests_executed'] is False and
         audit['paired_gate_pass'] is False and audit['numerical_qualified'] is False and
         audit['performance_admitted'] is False and audit['formal_performance'] is False and
         audit['hard_cutoff'] == 1792672721 and type(audit['original_twenty_controls']) is list and
         len(audit['original_twenty_controls']) == len(set(audit['original_twenty_controls'])) == 20 and
         all(type(case) is str for case in audit['original_twenty_controls']),
         'exact retained complete pre-NPU source audit, not a fresh test claim')
    audited = ref_map(audit['readset'])
    independent_audit_lineage(readset, source_ref, audit_ref, m, audit, audited)
    source_map = {path: reference['sha256'] for path, reference in audited.items()}
    need(result['source_before'] == result['source_after'] == source_map,
         'host before/after exactly the complete source-audit readset')
    for reference in audited.values():
        readset.read(reference, FILE_CAP, keep=False)
    for name, reference in m['files'].items():
        path = typed_ref(reference)
        need(path == SOURCE_ROOT/name and SOURCE_ROOT in path.parents and '..' not in Path(name).parts and
             audited.get(str(path)) == reference, 'all source-owned files in complete audited closure')
    for reference in [source_ref, m['prepared_template'], m['authority_ref'], *m['dependencies']]:
        need(audited.get(reference['path']) == reference, 'all manifest dependencies in complete source closure')
    need(set(m['boundary_reviewed_helpers']) == set(BOUNDARY_PINS), 'exact five reviewed boundary modules')
    for name, (size, digest) in BOUNDARY_PINS.items():
        pin = dict(bytes=size, sha256=digest)
        need(m['boundary_reviewed_helpers'][name] == pin and
             pin == {key: m['files'][name][key] for key in ('bytes', 'sha256')}, 'fixed reviewed observer/helper whole-file pin')
    return m, result, audit, audited


def original_readers(readset, manifest):
    names = ('bole_performance_profile', 'short_state_digest', 'compare_state_digest',
             'cleanup_summary', 'compare_completed_short')
    need(not any(name in sys.modules for name in names), 'fresh interpreter with no preloaded reader substitutes')
    for name, (size, digest) in ORIGINAL_PINS.items():
        reference = dict(path=str(SOURCE_ROOT/name), bytes=size, sha256=digest)
        need(manifest['files'][name] == reference, 'unchanged original single-arm reader source')
        readset.read(reference)
    for name, (size, digest) in V4_PINS.items():
        readset.read(dict(path=str(V4_ROOT/name), bytes=size, sha256=digest))
    sys.path.insert(0, str(SOURCE_ROOT))
    for name in names[:3]:
        importlib.import_module(name)
    sys.path.insert(0, str(V4_ROOT))
    V4 = importlib.import_module('compare_completed_short')
    imported = []
    for name in names:
        module = sys.modules[name]
        path = str(Path(module.__file__))
        need(path in readset.refs, 'actually imported source in exact pinned readset')
        readset.read(readset.refs[path])
        imported.append(dict(module=name, source=readset.refs[path]))
    need(not any(name == 'torch' or name.startswith(('torch.', 'torch_npu')) for name in sys.modules),
         'stdlib evidence reader without Torch or device import')
    return V4, imported


def owned_ref(readset, reference, root, cap=JSON_CAP):
    path = typed_ref(reference, cap)
    need(root in path.parents, 'reference stays in exact owned output subtree')
    return readset.obj(reference, cap)


def validate_host(readset, source_ref, result_ref, manifest, result, audit, V4):
    # This is the actual fixed v4 host predicate, including its strict cleanup
    # helper. The new reader does not copy, relax, or replace the old predicate.
    m, output, host_refs = V4.host(source_ref)
    need(m == manifest and output == OUTPUT_ROOT and host_refs[0] == result_ref, 'provided exact host RESULT')
    for reference in host_refs:
        readset.read(reference)
    for field in ('model_ready', 'scheduler_committed', 'timing_is_formal',
                  'candidate_qualification', 'performance_gain_measured', 'formal_performance', 'task_accuracy'):
        need(result[field] is False, 'host retains diagnostic-only field ' + field)
    summary = result['summary']
    need('first_host_fault' not in summary and summary['performance_arm'] == 'bole', 'no retained host fault')
    cpu_ref = summary['CPU_report']
    need(typed_ref(cpu_ref) == OUTPUT_ROOT/'cpu-preflight/CPU.json', 'actual source-owned CPU report')
    cpu = readset.obj(cpu_ref)
    need(cpu['source'] == source_ref and cpu['pass_preflight'] is True and cpu['Devices'] == [] and
         cpu['native_runtime_parser_checked'] is True and cpu['registry_arch_enumerated'] is True,
         'original real same-image CPU preflight')
    software_child_ref, software_child = readset.summary2(summary['actual_software_child'],
        OUTPUT_ROOT/'cpu-preflight/SOFTWARE-CHILD.json')
    software_ref, software = readset.discovered_obj(OUTPUT_ROOT/'cpu-preflight/PERFORMANCE-SOFTWARE/RESULT.json')
    need(software['schema'] == 'bole.actual-performance-sameimage-software/v1' and software['source'] == source_ref and
         software['all_tests_passed'] is True and software['tests'] == 20 and software['skipped'] == 0 and
         software['parent381_freshly_executed'] is False and software['NPU'] is False and
         software['aggregate_cap_seconds'] == 300 and 0 <= software['controls_total_elapsed_seconds'] <= 60,
         'actual original twenty controls completed under original budget')
    control = software['control_result']
    need(control['schema'] == 'bole.actual-performance-successor-only-unittest/v1' and
         control['all_tests_passed'] is True and control['tests'] == 20 and control['skipped'] == 0 and
         control['cached_PASS_reused'] is False and control['source'] == source_ref and control['NPU'] is False,
         'fresh original twenty-control result, not the source audit')
    need(control['cases'] == audit['original_twenty_controls'] == software['source_validated']['tests'],
         'actual executed cases are exactly the original source-audited twenty controls')
    bindings_ref = summary['worker_bindings']
    need(typed_ref(bindings_ref) == OUTPUT_ROOT/'dense/WORKER_BINDINGS.json', 'exact host worker binding file')
    bindings = readset.obj(bindings_ref)
    snapshots = summary['worker_snapshots']
    need(type(bindings) is list and len(bindings) == len(snapshots) == 4, 'all four actual worker bindings')
    by_rank, pids, host_pids = {}, set(), set()
    for row in bindings:
        need(set(row) == {'guest', 'host'}, 'actual guest/host binding shape')
        guest, host = row['guest'], row['host']
        need(guest in snapshots and snapshots.count(guest) == 1 and
             guest['schema'] == 'dense.native-worker-snapshot/v090' and guest['source_ref'] == source_ref and
             guest['native_core'] is True and guest['native_inverse'] is True and guest['allow_hf32'] is False and
             guest['qualification'] is False and guest['tensor_capture'] is False,
             'native restored core/inverse and HF32 policy on each actual worker')
        need(uint(guest['pid']) and guest['pid'] > 0 and uint(host['pid']) and host['pid'] > 0 and
             guest['pid'] in host['namespace_pids'] and host['pid'] in host['namespace_pids'] and
             guest['cgroup'] == host['cgroup'] and host['chip'] == 0 and
             host['physical'] in (4, 5, 6, 7) and host['stage'] == 'model-snapshot-AFTER-PERFORMANCE-BARRIER',
             'genuine namespace/process/device worker binding')
        rank = host['physical'] - 4
        need(host['argv'] == ['VLLM::Worker_TP%d' % rank] and rank not in by_rank and
             guest['pid'] not in pids and host['pid'] not in host_pids, 'all distinct TP4 workers on physical4-7')
        by_rank[rank] = row
        pids.add(guest['pid']); host_pids.add(host['pid'])
        for key, prefix in (('raw_observation', 'observation-raw-'), ('smi', 'smi-')):
            reference = host[key]
            path = Path(reference['path'])
            need(path.parent == OUTPUT_ROOT/'dense' and path.name.startswith(prefix) and path.suffix == '.json',
                 'actual owned retained worker-device observation')
            readset.summary2(reference, path)
    need(set(by_rank) == set(range(4)), 'complete physical4-7 mapping')
    receipt_root = OUTPUT_ROOT/'dense/receipts'
    snapshot_files = sorted(receipt_root.glob('worker-*-snapshot-*.json'))
    need(4 <= len(snapshot_files) <= 16, 'bounded actual worker snapshot files')
    retained = [readset.discovered_obj(path)[1] for path in snapshot_files]
    need(all(retained.count(row) == 1 for row in snapshots), 'host snapshots equal the actual retained worker records')
    return by_rank, dict(host_refs=host_refs, CPU_report=cpu_ref, software_child=software_child_ref,
        actual_software_result=software_ref, worker_bindings=bindings_ref,
        original_twenty_controls_reopened=True, fresh_tests_executed_by_reader=False)


def validate_original_arm(readset, source_ref, manifest, result, V4, workers):
    root = OUTPUT_ROOT/'dense/receipts'
    entries = list(root.iterdir())
    need(len(entries) <= 20000 and not any('FAILURE' in path.name for path in entries), 'no retained runtime FAILURE evidence')
    sv = result['summary']['streaming_validation']
    need(sv['schema'] == 'bole.short-state-single-arm-consumption/v1' and sv['source'] == source_ref and
         sv['arm_state_receipts_verified'] is True and sv['ON_OFF_state_equality'] is False and
         sv['formal_performance'] is False and sv['task_accuracy'] is False, 'original diagnostic single-arm consumption only')
    http_ref = sv['http']
    need(typed_ref(http_ref) == OUTPUT_ROOT/'dense/performance-client/HTTP_RESULT.json', 'actual HTTP result')
    frozen = ref_map(sv['readset'])
    for reference in frozen.values():
        path = Path(reference['path'])
        need(reference == source_ref or path == Path(http_ref['path']) or path.parent == root,
             'single-arm readset source and exact owned receipts')
        readset.read(reference)
    # Every original glob operand is bounded and fully checked before R opens it.
    state_paths = sorted(root.glob('STATE-*.json'))
    need(48 <= len(state_paths) <= 72, 'bounded two-generation original state receipts')
    for path in state_paths:
        need(str(path) in frozen, 'all original state files included in consumer readset')
        readset.read(frozen[str(path)], 256 * 1024)
    m, evidence, operands = V4.R.load_arm(source_ref, root, http_ref, 'ON')
    need(m == manifest and ref_map(operands) == frozen and len(evidence) == sv['rank_frames'],
         'unchanged original complete single-arm reader and exact consumer readset')
    http = readset.obj(http_ref)
    begin, retire = {}, {}
    for rank in range(4):
        for generation in (1, 2):
            begin[rank, generation] = readset.obj(frozen[str(root/('STATE-BEGIN-G%d-O-1-R%d.json' % (generation, rank)))])['record']
            retire[rank, generation] = readset.obj(frozen[str(root/('STATE-RETIRE-G%d-O-1-R%d.json' % (generation, rank)))])['record']
            cal = begin[rank, generation]['calibration']
            need(cal['pid'] == workers[rank]['guest']['pid'], 'same calibration and actual worker process')
            cal_ref = cal['calibration_ref']
            owned_ref(readset, cal_ref, root)
    return http, http_ref, evidence, begin, retire, operands


def expected_names():
    names = {'G0-INSTALL.json', 'G2-COMPLETE.json'}
    for generation in (1, 2):
        events = ['NATIVE-INPUT-L00', *('NATIVE-L%02d' % layer for layer in LAYERS),
                  *('RAW-' + name for name in RAW_SHAPES), 'PROJECTION-INTERNAL', *PHASES, 'RETIRE']
        names.update('G%d-%s.json' % (generation, event) for event in events)
        names.update('G%d-%s.bin' % (generation, name) for name in RAW_SHAPES)
    need(len(names) == 150, 'fixed complete boundary plus two projection file set')
    return names


def geometry(value, *, expected_shape=None, expected_dtype=None):
    need(type(value) is dict and set(value) == {'object', 'storage_ptr', 'storage_bytes', 'data_ptr',
         'offset', 'shape', 'stride', 'dtype', 'device', 'logical_bytes'}, 'exact tensor geometry schema')
    need(type(value['shape']) is list and type(value['stride']) is list and
         1 <= len(value['shape']) <= 5 and len(value['shape']) == len(value['stride']) and
         all(uint(n) for n in value['shape'] + value['stride']) and all(uint(value[k]) for k in
             ('object', 'storage_ptr', 'storage_bytes', 'data_ptr', 'offset', 'logical_bytes')),
         'typed finite tensor geometry')
    need(type(value['device']) is str and value['device'].startswith('npu:') and len(value['device']) <= 16 and
         type(value['dtype']) is str and len(value['dtype']) <= 24, 'actual NPU geometry metadata')
    if expected_shape is not None:
        need(value['shape'] == list(expected_shape), 'exact observed logical tensor shape')
    if expected_dtype is not None:
        need(value['dtype'] == expected_dtype, 'exact observed tensor dtype')
    sizes = {'torch.float32': 4, 'torch.bfloat16': 2, 'torch.float16': 2,
             'torch.int32': 4, 'torch.int64': 8, 'torch.uint8': 1, 'torch.int8': 1, 'torch.bool': 1}
    if value['dtype'] in sizes:
        unit = sizes[value['dtype']]
        need(value['logical_bytes'] == math.prod(value['shape']) * unit and
             value['data_ptr'] == value['storage_ptr'] + value['offset'] * unit,
             'complete logical byte count and actual storage offset')
        if all(value['shape']):
            end = value['offset'] + sum((n - 1) * stride for n, stride in zip(value['shape'], value['stride'])) + 1
            need(end * unit <= value['storage_bytes'], 'logical view fits actual backing storage')
    return value


def slot_record(value):
    need(set(value) == {*DIGESTS, 'state_finite', 'conv_leading3_finite', 'conv_extra_numerical_gate', 'geometry'} and
         all(sha(value[k]) for k in DIGESTS) and value['state_finite'] is True and
         value['conv_leading3_finite'] is True and value['conv_extra_numerical_gate'] is False,
         'complete native selected state/conv hashes and original finite range')
    g = value['geometry']
    need(set(g) == {'state_arena', 'conv_arena', 'selected_state', 'selected_conv', 'selected_slot',
                   'conv_numerical_active_extent', 'conv_full_storage_extent'}, 'exact native slot geometry')
    state = geometry(g['state_arena'], expected_dtype='torch.float32')
    conv = geometry(g['conv_arena'], expected_dtype='torch.bfloat16')
    need(len(state['shape']) == 4 and state['shape'][1:] == [12, 128, 128] and
         len(conv['shape']) == 3 and 3 <= conv['shape'][1] <= 16 and conv['shape'][2] == 2560 and
         uint(g['selected_slot']) and g['selected_slot'] < min(state['shape'][0], conv['shape'][0]),
         'actual selected TP4 state and complete bounded convolution slot')
    geometry(g['selected_state'], expected_shape=(12, 128, 128), expected_dtype='torch.float32')
    geometry(g['selected_conv'], expected_shape=conv['shape'][1:], expected_dtype='torch.bfloat16')
    for parent, selected in ((state, g['selected_state']), (conv, g['selected_conv'])):
        need(all(parent[key] == selected[key] for key in ('storage_ptr', 'storage_bytes', 'device', 'dtype')) and
             selected['stride'] == parent['stride'][1:] and
             selected['offset'] == parent['offset'] + g['selected_slot'] * parent['stride'][0],
             'selected slot is a genuine view of the witnessed arena')
    need(g['conv_numerical_active_extent'] == [0, 3] and
         g['conv_full_storage_extent'] == [0, conv['shape'][1]], 'active conv range distinguished from extra extent')


def inventory(value):
    need(set(value) == {'drafter_object', 'draft_model_object', 'cache_storage_inventory',
         'draft_actual_write_footprint_known', 'alias_exclusion_proven',
         'shared_allocation_alone_is_not_alias_bug_evidence', 'limitation'} and
         uint(value['drafter_object']) and uint(value['draft_model_object']) and
         value['draft_actual_write_footprint_known'] is False and value['alias_exclusion_proven'] is False and
         value['shared_allocation_alone_is_not_alias_bug_evidence'] is True and
         value['limitation'] == 'active draft slots/write extents not source-proved by this observer' and
         type(value['cache_storage_inventory']) is list and len(value['cache_storage_inventory']) <= 8,
         'actual bounded draft storage witness does not claim disjoint write extents')
    for row in value['cache_storage_inventory']:
        need(set(row) == {'module', 'module_object', 'item', 'geometry'} and type(row['module']) is str and
             len(json.dumps(row['module'], ensure_ascii=True)) <= 130 and
             uint(row['module_object']) and uint(row['item']), 'bounded actual draft cache row')
        geometry(row['geometry'])


def validate_order(references):
    names = [Path(reference['path']).name for reference in references]
    position = {name: i for i, name in enumerate(names)}
    need(len(position) == len(names) == 149 and names[0] == 'G0-INSTALL.json' and
         names[-1] == 'G2-RETIRE.json', 'complete unique pre-terminal append order')
    previous = 0
    orders = []
    for generation in (1, 2):
        prefix = 'G%d-' % generation
        start = position[prefix + 'NATIVE-INPUT-L00.json']
        native = [position[prefix + 'NATIVE-L%02d.json' % layer] for layer in LAYERS]
        phases = [position[prefix + phase + '.json'] for phase in PHASES]
        retire = position[prefix + 'RETIRE.json']
        need(previous < start < native[0] and native == sorted(native) and native[-1] < phases[0] and
             phases == sorted(phases) and phases[-1] < retire,
             'actual ordered native/registration/calibration/MTP/retirement boundaries')
        for name in RAW_SHAPES:
            binary = position[prefix + name + '.bin']
            record = position[prefix + 'RAW-' + name + '.json']
            need(start < binary < record < phases[0] and record == binary + 1,
                 'each complete raw binary immediately precedes its referenced record')
        need(position[prefix + 'NATIVE-L00.json'] <
             position[prefix + 'RAW-layer0_gated_norm.json'] <
             position[prefix + 'PROJECTION-INTERNAL.json'] <
             position[prefix + 'layer0_out_projection.bin'] <
             position[prefix + 'NATIVE-L01.json'],
             'projection record follows native0/norm and precedes original out-projection raw hook and native1')
        need(all(previous < position[name] <= retire for name in names if name.startswith(prefix)),
             'generations never interleave after real native retirement')
        orders.append([name[len(prefix):-5] for name in names if name.startswith(prefix) and name.endswith('.json')])
        previous = retire
    need(orders[0] == orders[1], 'same complete observed event ordering across the two requests')
    return orders[0]


def validate_boundary_rank(readset, source_ref, rank, worker, begin, retire, projection_runtime):
    root = OUTPUT_ROOT/'dense/receipts'/('BOUNDARY-R%d' % rank)
    parents_identity(root/'placeholder')
    entries = list(root.iterdir())
    names = expected_names()
    need(len(entries) == 150 and {path.name for path in entries} == names and
         all(stat.S_ISREG(path.lstat().st_mode) for path in entries), 'exact complete ordinary boundary directory, no partial/extra file')
    complete_ref, complete = readset.discovered_obj(root/'G2-COMPLETE.json', 128 * 1024)
    terminal = complete['record']
    references = terminal['references']
    closure = ref_map(references)
    need(len(references) == len(closure) == 149 and
         {Path(path).name for path in closure} == names - {'G2-COMPLETE.json'} and
         all(Path(path).parent == root for path in closure), 'exact COMPLETE reference closure without self reference')
    order = validate_order(references)
    documents, raw, by_event = {}, {}, {}
    for reference in references:
        path = Path(reference['path'])
        if path.suffix == '.bin':
            raw[path.name] = readset.read(reference, 96 * 1024)
        else:
            cap = PROJECTION_ENVELOPE_CAP if path.name.endswith('-PROJECTION-INTERNAL.json') else 128 * 1024
            documents[path.name] = readset.obj(reference, cap)
    documents['G2-COMPLETE.json'] = complete
    need(len(documents) == 132 and len(raw) == 18, 'complete 132 metadata and18 original raw files')
    metadata_bytes = sum(reference['bytes'] for reference in [*references, complete_ref] if reference['path'].endswith('.json'))
    raw_bytes = sum(reference['bytes'] for reference in references if reference['path'].endswith('.bin'))
    need(metadata_bytes <= META_CAP and raw_bytes == RAW_CAP, 'unchanged bounded metadata/raw totals')
    for name, document in documents.items():
        need(set(document) == {'schema', 'source_sha256', 'rank', 'pid', 'generation', 'event', 'record',
                               'numerical_qualified', 'formal_performance'} and
             document['schema'] == SCHEMA and document['source_sha256'] == source_ref['sha256'] and
             type(document['rank']) is int and document['rank'] == rank and
             type(document['pid']) is int and document['pid'] == worker['guest']['pid'] and
             type(document['generation']) is int and document['generation'] in (0, 1, 2) and
             name == 'G%d-%s.json' % (document['generation'], document['event']) and
             document['numerical_qualified'] is False and document['formal_performance'] is False,
             'source/process/rank/generation/event identity of every boundary record')
        by_event[document['generation'], document['event']] = document['record']
    install = by_event[0, 'INSTALL']
    need(set(install) == {'source', 'worker', 'runner', 'model', 'hooks', 'hooks_return_none', 'native_math_replaced',
                         'blocking_D2H_observation', 'explicit_stream_or_event_manipulation'} and
         install['source'] == source_ref and all(uint(install[k]) for k in ('worker', 'runner', 'model')) and
         install['hooks'] == 4 and install['hooks_return_none'] is True and install['native_math_replaced'] is False and
         install['blocking_D2H_observation'] is True and install['explicit_stream_or_event_manipulation'] is False,
         'actual four non-replacing hooks; observation changes timing')
    need(set(terminal) == {'source', 'references', 'requests', 'hooks_removed', 'device_read_bytes', 'raw_bytes',
         'metadata_bytes_before_index', 'observation_complete', 'draft_actual_write_footprint_known',
         'alias_exclusion_proven', 'diagnostic_only', 'projection_observer_restored', 'projection_records'} and
         terminal['source'] == source_ref and terminal['hooks_removed'] is True and terminal['observation_complete'] is True and
         terminal['draft_actual_write_footprint_known'] is False and terminal['alias_exclusion_proven'] is False and
         terminal['diagnostic_only'] is True and terminal['projection_observer_restored'] is True and
         type(terminal['projection_records']) is int and terminal['projection_records'] == 2 and
         terminal['raw_bytes'] == raw_bytes and
         terminal['metadata_bytes_before_index'] == metadata_bytes - complete_ref['bytes'],
         'terminal observation/hook retirement and exact retained counters')
    requests, request_objects, projection_records = [], [], {}
    expected_read_bytes = 0
    projection_read_bytes = 0
    for generation in (1, 2):
        original_begin, original_retire = begin[rank, generation], retire[rank, generation]
        rid = original_retire['request']
        requests.append(rid)
        inputs = by_event[generation, 'NATIVE-INPUT-L00']
        need(set(inputs) == {'rows', 'layer', 'before_original_native_core', 'full_actual131_inputs', 'raw_values_preserved'} and
             inputs['layer'] == 0 and inputs['before_original_native_core'] is True and
             inputs['full_actual131_inputs'] is True and inputs['raw_values_preserved'] is False and
             set(inputs['rows']) == {'mixed_qkv', 'b', 'a'}, 'actual native0 inputs before original core, full131 hashes')
        for name, row in inputs['rows'].items():
            shape = RAW_SHAPES['layer1_' + name]
            need(set(row) == {'sha256', 'bytes', 'shape', 'dtype', 'finite', 'geometry'} and sha(row['sha256']) and
                 row['bytes'] == math.prod(shape) * 2 and row['shape'] == list(shape) and
                 row['dtype'] == 'torch.bfloat16' and row['finite'] is True, 'complete finite native0 projected input hash')
            geometry(row['geometry'], expected_shape=shape, expected_dtype='torch.bfloat16')
            expected_read_bytes += row['bytes']
        native = {}
        object_ids = set()
        for layer in LAYERS:
            record = by_event[generation, 'NATIVE-L%02d' % layer]
            need(set(record) == {'layer', 'prefix', 'request', 'request_object', 'metadata_object',
                 'core_return_observed_before_registration', 'slot'} and record['layer'] == layer and
                 record['request'] == rid and record['core_return_observed_before_registration'] is True and
                 type(record['prefix']) is str and 0 < len(json.dumps(record['prefix'])) <= 130 and
                 uint(record['request_object']) and uint(record['metadata_object']), 'every actual ordered native GDN return')
            object_ids.add(record['request_object'])
            slot_record(record['slot'])
            native[layer] = record['slot']
            expected_read_bytes += 6 * (record['slot']['geometry']['selected_state']['logical_bytes'] +
                                         record['slot']['geometry']['selected_conv']['logical_bytes'])
        need(len(object_ids) == 1, 'one strongly held request object across all48 native layers')
        request_objects.append(next(iter(object_ids)))
        for name, shape in RAW_SHAPES.items():
            record = by_event[generation, 'RAW-' + name]
            need(set(record) == {'name', 'logical_shape', 'logical_sha256', 'logical_bytes', 'logical_finite',
                 'logical_geometry', 'actual_token_slice', 'raw', 'raw_slice_is_full_tensor',
                 'raw_slice_numerical_qualification', 'element_encoding'} and record['name'] == name and
                 record['logical_shape'] == list(shape) and sha(record['logical_sha256']) and
                 record['logical_bytes'] == math.prod(shape) * 2 and record['logical_finite'] is True and
                 record['actual_token_slice'] == [123, 131] and record['raw_slice_is_full_tensor'] is False and
                 record['raw_slice_numerical_qualification'] is False and record['element_encoding'] == ENCODING,
                 'nine original finite logical131 stages and explicit last8 BF16 retention')
            geometry(record['logical_geometry'], expected_shape=shape, expected_dtype='torch.bfloat16')
            path = root/('G%d-%s.bin' % (generation, name))
            need(closure.get(str(path)) == record['raw'] and
                 record['raw']['bytes'] == record['logical_bytes'] // 131 * 8,
                 'actual raw slice exact whole Ref in COMPLETE closure')
            expected_read_bytes += record['logical_bytes']
        for phase in PHASES:
            record = by_event[generation, phase]
            need(set(record) == {'rows', 'context', 'state_finite', 'conv_leading3_finite',
                 'conv_extra_numerical_gate', 'storage_geometry_equal_native', 'numerical_equality_is_observed_not_required'} and
                 record['state_finite'] is True and record['conv_leading3_finite'] is True and
                 record['conv_extra_numerical_gate'] is False and record['storage_geometry_equal_native'] is True and
                 record['numerical_equality_is_observed_not_required'] is True and
                 type(record['rows']) is list and [row['layer'] for row in record['rows']] == list(LAYERS),
                 'complete exact48 registered boundary and unchanged numerical active range')
            for row in record['rows']:
                need(set(row) == {'layer', 'slot', 'digest'} and row['slot'] == native[row['layer']]['geometry']['selected_slot'] and
                     set(row['digest']) == set(DIGESTS) and all(sha(row['digest'][key]) for key in DIGESTS),
                     'all selected native slots and three full hashes at every phase')
            context = record['context']
            if phase == PHASES[0]:
                need(context == {}, 'registration context has no synthetic request payload')
            elif phase in ('calibration_before', 'calibration_after'):
                expected = dict(generation=generation, created=generation == 1)
                if phase == 'calibration_after':
                    expected['calibration_ref'] = original_begin['calibration']['calibration_ref']
                need(canonical(context) == canonical(expected), 'same original created/reused calibration boundary and Ref')
            else:
                need(set(context) == {'draft'}, 'actual MTP inventory context')
                inventory(context['draft'])
        projection = validate_projection_record(by_event[generation, 'PROJECTION-INTERNAL'],
            generation=generation, rank=rank, request=rid, native0=by_event[generation, 'NATIVE-L00'],
            runtime=projection_runtime, previous_read_bytes=projection_read_bytes)
        projection_records[generation] = projection
        projection_read_bytes = projection['total_extra_read_bytes']
        expected_read_bytes += projection['extra_read_bytes']
        retirement = by_event[generation, 'RETIRE']
        need(set(retirement) == {'original_record_sha256', 'request', 'generation', 'original_retirement_schema',
             'original_retirement_steps', 'output_token_ids', 'actual_native_request_absent',
             'device_read_bytes', 'raw_bytes', 'metadata_bytes_before_record'} and
             retirement['original_record_sha256'] == hashlib.sha256(canonical(original_retire) + b'\n').hexdigest() and
             retirement['request'] == rid and retirement['generation'] == generation and
             retirement['original_retirement_schema'] == original_retire['retirement']['schema'] and
             retirement['original_retirement_steps'] == original_retire['retirement']['steps'] and
             retirement['output_token_ids'] == original_retire['output_token_ids'] and
             retirement['actual_native_request_absent'] is True and retirement['device_read_bytes'] == expected_read_bytes,
             'exact original actual native retirement and normalized record SHA')
        before_name = 'G%d-RETIRE.json' % generation
        pos = next(i for i, reference in enumerate(references) if Path(reference['path']).name == before_name)
        previous = references[:pos]
        need(retirement['raw_bytes'] == sum(reference['bytes'] for reference in previous if reference['path'].endswith('.bin')) and
             retirement['metadata_bytes_before_record'] == sum(reference['bytes'] for reference in previous if reference['path'].endswith('.json')),
             'retirement counters equal actual preceding complete files')
    need(len(set(requests)) == len(set(request_objects)) == 2 and terminal['requests'] == requests and
         terminal['device_read_bytes'] == expected_read_bytes <= DEVICE_READ_CAP,
         'two distinct actually retired requests, complete bounded device-read witness')
    need(projection_records[1]['record']['roles'] == projection_records[2]['record']['roles'],
         'same strongly held source-bound native methods across both generations')
    for key in ('layer_object', 'gdn_object', 'quant_object', 'custom_object'):
        need(projection_records[1]['record']['active'][key] == projection_records[2]['record']['active'][key],
             'same held projection owner object across genuine request retirement')
    return dict(rank=rank, root=str(root), complete_ref=complete_ref, metadata_bytes=metadata_bytes,
                raw_bytes=raw_bytes, ordered_events=order, events=by_event, raw=raw,
                closure=[*references, complete_ref], requests=requests, projection_records=projection_records)


def terminal_budget(readset, source_ref, result, boundaries):
    """Independently count/hash the exact source-declared original g3 buckets."""
    terminal = result['summary']['boundary_terminal_budget']
    need(set(terminal) == {'schema', 'source', 'ranks', 'after_actual_final_worker_snapshots',
         'original_other_cap', 'original_metadata_cap', 'original_raw_cap',
         'probe_raw_and_metadata_charged_inside_other', 'numerical_qualified',
         'formal_performance', 'device_operations_in_accounting'} and
         terminal['schema'] == 'bole.boundary-terminal-budget/v1' and terminal['source'] == source_ref and
         terminal['after_actual_final_worker_snapshots'] is True and terminal['original_other_cap'] == 3 * 2**20 and
         terminal['original_metadata_cap'] == 64 * 2**20 and terminal['original_raw_cap'] == 2**30 and
         terminal['probe_raw_and_metadata_charged_inside_other'] is True and
         terminal['numerical_qualified'] is False and terminal['formal_performance'] is False and
         terminal['device_operations_in_accounting'] is False and
         [row['rank'] for row in terminal['ranks']] == list(range(4)),
         'actual post-worker-snapshot terminal accounting inside unchanged original caps')
    base, channel = OUTPUT_ROOT/'dense/receipts', OUTPUT_ROOT/'dense/receipts/STREAM'
    rows = []
    event_caps = dict(FRAME=2048, ACK=3072, RELEASE=1536, REPORT=4000)
    for rank, witness in enumerate(terminal['ranks']):
        caldir = base/('CONV-MODEL-CALIBRATION-RANK-%d' % rank)
        cal = {path for path in caldir.iterdir() if path.is_file()} if caldir.is_dir() else set()
        journals = set(base.glob('IDENTITY-rank%d-*.json' % rank))
        events = set(channel.glob('*RANK-%d-*.json' % rank)) | set(channel.glob('*RANK-%d-*.json.pending' % rank))
        need(len({path.name.rsplit('-', 1)[-1] for path in events}) <= 1027, 'original finite event count')
        for path in events:
            key = path.name.split('-', 1)[0]
            need(key in event_caps and path.stat().st_size <= event_caps[key], 'original individual event cap')
        finals = {path for pattern in ('*.json', '*.json.pending') for path in channel.glob(pattern) if 'RANK-' not in path.name}
        finals.update(channel.glob('*RANK-%d.json' % rank))
        finals.update(base.glob('BOLE-TREE-RANK-%d.*' % rank))
        other = set(base.glob('*RANK-%d.json' % rank)) - finals
        other.update(base.glob('worker-*-snapshot-*.json'))
        other.update(base.glob('MTP-LOAD-*.json'))
        other.update(Path(boundaries[rank]['root']).iterdir())
        for pattern in ('MTP-LOAD-*', '.MTP-LOAD-*', 'worker-*-snapshot-*.json*', '.worker-*-snapshot-*.json.pending-*'):
            other.update(base.glob(pattern))
        short = set(base.glob('STATE-*-R%d.json' % rank)) | set(base.glob('.STATE-*-R%d.json.pending-*' % rank))
        sets = dict(calibration=cal, identity=journals, events=events, other=other, final=finals, short_digest=short)
        need(all(len(paths) <= 20000 for paths in sets.values()), 'bounded original accounting file sets')
        references = {}
        for path in sorted(set().union(*sets.values())):
            reference, _ = readset.discover(path, 16 * 2**20)
            references[str(path)] = reference
        charges = {key: sum(references[str(path)]['bytes'] for path in paths) for key, paths in sets.items()}
        total = sum(charges.values())
        need(charges['calibration'] <= 16 * 2**20 and charges['identity'] <= 8 * 2**20 and
             charges['other'] <= 3 * 2**20 and charges['final'] <= 16 * 2**20 and
             charges['events'] <= 1027 * sum(event_caps.values()) and total + 8 * 2**20 <= 64 * 2**20 and
             total + (384 + 448 + 128) * 2**20 <= 2**30, 'all unchanged original actual aggregate caps')
        need(set(witness) == {'rank', 'charges', 'bytes', 'boundary_complete_ref'} and
             witness['charges'] == charges and witness['bytes'] == total and
             witness['boundary_complete_ref'] == boundaries[rank]['complete_ref'],
             'terminal reported charges equal independently reopened exact retained file sets')
        rows.append(dict(rank=rank, charges=charges, bytes=total,
                         files_by_bucket={key: [references[str(path)] for path in sorted(paths)] for key, paths in sets.items()}))
    return dict(source=source_ref, terminal_report=terminal, independently_reopened_ranks=rows,
                original_caps_unchanged=True, diagnostic_only=True, numerical_qualified=False)


def differences(first, second):
    return {key: dict(generation_1=first.get(key), generation_2=second.get(key),
                     generation_1_present=key in first, generation_2_present=key in second)
            for key in sorted(set(first) | set(second))
            if key not in first or key not in second or canonical(first[key]) != canonical(second[key])}


def tokens(first, second):
    return [dict(index=i, generation_1=first[i] if i < len(first) else None,
                 generation_2=second[i] if i < len(second) else None)
            for i in range(max(len(first), len(second)))
            if i >= len(first) or i >= len(second) or first[i] != second[i]]


def bf16_compare(first, second):
    need(type(first) is bytes and type(second) is bytes and len(first) == len(second) and
         0 < len(first) <= 96 * 1024 and len(first) % 2 == 0, 'equal bounded complete BF16 slices')
    a_bits = [row[0] for row in struct.iter_unpack('<H', first)]
    b_bits = [row[0] for row in struct.iter_unpack('<H', second)]
    a = [struct.unpack('<f', struct.pack('<I', value << 16))[0] for value in a_bits]
    b = [struct.unpack('<f', struct.pack('<I', value << 16))[0] for value in b_bits]
    finite = [(x, y) for x, y in zip(a, b) if math.isfinite(x) and math.isfinite(y)]
    diff = [abs(x - y) for x, y in finite]
    squared_error = math.fsum(d * d for d in diff)
    norm1 = math.sqrt(math.fsum(x * x for x, _ in finite))
    norm2 = math.sqrt(math.fsum(y * y for _, y in finite))
    l2 = math.sqrt(squared_error)
    count = len(a)
    return dict(elements=count, bytes_per_generation=len(first),
        identical_bits=sum(x == y for x, y in zip(a_bits, b_bits)),
        different_bits=sum(x != y for x, y in zip(a_bits, b_bits)),
        equal_numeric_values=sum(x == y for x, y in zip(a, b)),
        different_numeric_values=sum(x != y for x, y in zip(a, b)),
        generation_1_finite=sum(math.isfinite(x) for x in a), generation_2_finite=sum(math.isfinite(x) for x in b),
        all_finite=len(finite) == count, finite_pairs=len(finite), max_abs=max(diff) if diff else None,
        mean_abs=math.fsum(diff) / len(diff) if diff else None,
        rms=math.sqrt(squared_error / len(diff)) if diff else None, l2_error=l2,
        generation_1_l2_norm=norm1, generation_2_l2_norm=norm2,
        norm_relative_to_generation_1=l2 / norm1 if norm1 else None,
        norm_relative_to_generation_2=l2 / norm2 if norm2 else None,
        generation_1_zero_norm=norm1 == 0, generation_2_zero_norm=norm2 == 0,
        metrics_scope='Complete retained last8-token slice only; no full131 magnitude claim.',
        threshold_applied=False, numerical_qualification=False)


def hash_comparison(first, second):
    return {kind: dict(generation_1=first[kind], generation_2=second[kind], equal=first[kind] == second[kind])
            for kind in DIGESTS}


def compare_rank(boundary, evidence):
    rank, events, order = boundary['rank'], boundary['events'], boundary['ordered_events']
    native_rows, phase_rows, raw_rows, input_rows = [], [], [], []
    by_event_differences = {}
    for layer in LAYERS:
        event = 'NATIVE-L%02d' % layer
        a, b = events[1, event]['slot'], events[2, event]['slot']
        h = hash_comparison(a, b)
        native_rows.append(dict(layer=layer, hashes=h, geometry_equal=a['geometry'] == b['geometry'],
            geometry_generation_1=a['geometry'], geometry_generation_2=b['geometry']))
        by_event_differences[event] = [dict(layer=layer, field=kind) for kind in DIGESTS if not h[kind]['equal']]
    for phase in PHASES:
        a, b = events[1, phase], events[2, phase]
        records = []
        changed = []
        for row1, row2 in zip(a['rows'], b['rows']):
            h = hash_comparison(row1['digest'], row2['digest'])
            records.append(dict(layer=row1['layer'], slot_generation_1=row1['slot'], slot_generation_2=row2['slot'], hashes=h))
            changed.extend(dict(layer=row1['layer'], field=kind) for kind in DIGESTS if not h[kind]['equal'])
        phase_rows.append(dict(phase=phase, rows=records, different_fields=changed,
            context_generation_1=a['context'], context_generation_2=b['context'],
            context_differences=differences(a['context'], b['context'])))
        by_event_differences[phase] = changed
    for name in RAW_SHAPES:
        event = 'RAW-' + name
        a, b = events[1, event], events[2, event]
        metrics = bf16_compare(boundary['raw']['G1-' + name + '.bin'], boundary['raw']['G2-' + name + '.bin'])
        need(metrics['all_finite'], 'actual retained BF16 slice obeys original finite gate')
        raw_rows.append(dict(name=name, logical_shape=a['logical_shape'], logical_bytes=a['logical_bytes'],
            full131_sha256_generation_1=a['logical_sha256'], full131_sha256_generation_2=b['logical_sha256'],
            full131_sha256_equal=a['logical_sha256'] == b['logical_sha256'],
            full131_hash_scope='Source-bound producer witness; only last8 values retained, so full131 hash cannot be recomputed from this raw slice.',
            raw_generation_1=a['raw'], raw_generation_2=b['raw'],
            actual_token_slice=[123, 131], raw_sha256_equal=a['raw']['sha256'] == b['raw']['sha256'],
            logical_geometry_equal=a['logical_geometry'] == b['logical_geometry'],
            raw_last8_metrics=metrics))
        by_event_differences[event] = [] if a['logical_sha256'] == b['logical_sha256'] else [dict(field='full131_logical_sha256')]
    a, b = events[1, 'NATIVE-INPUT-L00']['rows'], events[2, 'NATIVE-INPUT-L00']['rows']
    for name in ('mixed_qkv', 'b', 'a'):
        input_rows.append(dict(name=name, generation_1=a[name], generation_2=b[name],
            full131_sha256_equal=a[name]['sha256'] == b[name]['sha256'],
            metadata_equal={k: v for k, v in a[name].items() if k not in ('sha256', 'geometry')} ==
                           {k: v for k, v in b[name].items() if k not in ('sha256', 'geometry')},
            geometry_equal=a[name]['geometry'] == b[name]['geometry'], raw_values_preserved=False))
    by_event_differences['NATIVE-INPUT-L00'] = [dict(field=name) for name in a if a[name]['sha256'] != b[name]['sha256']]
    ordered = [dict(event=event, different_hash_fields=by_event_differences[event])
               for event in order if event in by_event_differences]
    earliest = next((row for row in ordered if row['different_hash_fields']), None)
    transitions = []
    for generation in (1, 2):
        previous_name = 'native_core_return_by_layer'
        previous = {layer: {kind: events[generation, 'NATIVE-L%02d' % layer]['slot'][kind] for kind in DIGESTS} for layer in LAYERS}
        for phase in PHASES:
            current = {row['layer']: row['digest'] for row in events[generation, phase]['rows']}
            changes = [dict(layer=layer, field=kind, before_sha256=previous[layer][kind], after_sha256=current[layer][kind])
                       for layer in LAYERS for kind in DIGESTS if previous[layer][kind] != current[layer][kind]]
            transitions.append(dict(generation=generation, before=previous_name, after=phase,
                                    changed_hashes=changes, all_observed_hashes_equal=not changes))
            previous_name, previous = phase, current
        short = {(row['layer'], row['kind']): row for row in evidence[rank, generation, 0]['rows'] if row['kind'] in ('state', 'conv')}
        changes = []
        for layer in LAYERS:
            for kind, digest_name in (('state', 'state'), ('conv', 'conv_leading3')):
                after = short[layer, kind]['before']['sha256']
                if previous[layer][digest_name] != after:
                    changes.append(dict(layer=layer, field=digest_name,
                        before_sha256=previous[layer][digest_name], after_sha256=after))
        transitions.append(dict(generation=generation, before='initial_mtp_after',
            after='original_STATE_STEP_O0_selected_path_staging_before_publication',
            changed_hashes=changes, all_observed_hashes_equal=not changes,
            interval_contains_unobserved_work=True))
    first = {field: evidence[rank, 1, 0][field] for field in SEMANTICS}
    second = {field: evidence[rank, 2, 0][field] for field in SEMANTICS}
    return dict(rank=rank, complete_ref=boundary['complete_ref'], closure=boundary['closure'],
        metadata_bytes=boundary['metadata_bytes'], raw_bytes=boundary['raw_bytes'], requests=boundary['requests'],
        native48_return_state_conv=native_rows, registered_phases=phase_rows,
        native0_full131_input_hashes=input_rows, raw9_stages=raw_rows,
        ordered_observed_boundary_differences=ordered, first_observed_difference=earliest,
        no_difference_observed_at_retained_boundaries=earliest is None,
        within_generation_observed_transitions=transitions,
        original_first_frame_semantics=dict(generation_1=first, generation_2=second,
            differences=differences(first, second), tokens=tokens(first['tokens'], second['tokens']),
            emitted_tokens=tokens(first['emitted_tokens'], second['emitted_tokens'])),
        initial_state_equivalence_assumed=False, cause_determined=False)


def compare_http(http, reference):
    a, b = http['rows'][:2]
    first, second = a['request'], b['request']
    return dict(reference=reference, request_generation_1=first, request_generation_2=second,
        request_canonical_generation_1=canonical_ref(first), request_canonical_generation_2=canonical_ref(second),
        request_payload_equal=canonical(first) == canonical(second), request_differences=differences(first, second),
        prompt_equal=first['prompt'] == second['prompt'],
        prompt_canonical_generation_1=canonical_ref(first['prompt']), prompt_canonical_generation_2=canonical_ref(second['prompt']),
        both_explicit_seeds_present='seed' in first and 'seed' in second,
        same_explicit_seed='seed' in first and 'seed' in second and canonical(first['seed']) == canonical(second['seed']),
        output_tokens_generation_1=a['token_ids'], output_tokens_generation_2=b['token_ids'],
        output_token_differences=tokens(a['token_ids'], b['token_ids']),
        distinct_request_ids=[a['id'], b['id']], identical_initial_state_assumed=False)


def projection_stage_join(first, second, first_name, second_name):
    observed = first.get('observed', True) is True and second.get('observed', True) is True
    if not observed:
        return dict(before=first_name, after=second_name, both_observed=False,
                    logical_hash_equal=None, same_logical_metadata=None,
                    generation_values=[first, second], equality_required=False)
    def describe(value):
        if 'logical_sha256' in value:
            return dict(sha256=value['logical_sha256'], bytes=value['logical_bytes'],
                        shape=value['logical_shape'], dtype=value['logical_geometry']['dtype'],
                        geometry=value['logical_geometry'])
        return {key: value[key] for key in ('sha256', 'bytes', 'shape', 'dtype', 'geometry')}
    a, b = describe(first), describe(second)
    return dict(before=first_name, after=second_name, both_observed=True,
        before_value=a, after_value=b, logical_hash_equal=a['sha256'] == b['sha256'],
        same_logical_metadata=all(a[key] == b[key] for key in ('bytes', 'shape', 'dtype')),
        byte_count_equal=a['bytes'] == b['bytes'], geometry_differences=differences(a['geometry'], b['geometry']),
        equality_required=False, magnitude_threshold_applied=False)


def compare_projection_rank(boundary):
    a, b = [boundary['projection_records'][generation]['record'] for generation in (1, 2)]
    rows, joins = [], []
    for name in PROJECTION_STAGES:
        first, second = a['stages'][name], b['stages'][name]
        both = first['observed'] is True and second['observed'] is True
        rows.append(dict(stage=name, generation_1=first, generation_2=second, both_observed=both,
            availability_equal=first['observed'] == second['observed'],
            full_logical_sha256_equal=first['sha256'] == second['sha256'] if both else None,
            same_logical_metadata=all(first[key] == second[key] for key in ('bytes', 'shape', 'dtype')) if both else None,
            geometry_differences=differences(first['geometry'], second['geometry']) if both else None,
            producer_hash_witness=True, raw_values_preserved=False, numerical_qualification=False))
    for generation, record in ((1, a), (2, b)):
        stages = record['stages']
        events = boundary['events']
        observed_joins = [
            projection_stage_join(events[generation, 'RAW-layer0_gated_norm'], stages['projection_input'],
                                  'original_gated_norm_logical131', 'actual_projection_input_full_tensor'),
            projection_stage_join(stages['quant_return'], stages['pre_reduce'],
                                  'actual_quant_return', 'actual_supported_reduction_input'),
            projection_stage_join(stages['post_reduce'], stages['projection_return'],
                                  'actual_supported_reduction_output', 'actual_projection_return'),
            projection_stage_join(stages['projection_return'], events[generation, 'RAW-layer0_out_projection'],
                                  'actual_projection_return_full_tensor', 'original_out_projection_logical131'),
        ]
        joins.append(dict(generation=generation, joins=observed_joins,
            active=record['active'], roles=record['roles'], calls=record['calls'], exceptions=record['exceptions'],
            reductions=record['reductions'], read_bytes_generation=record['read_bytes_generation'],
            read_bytes_total=record['read_bytes_total'], trace_restored=record['trace_restored'],
            weight_bytes_hashed=False, backend_format_observed=False))
    first_difference = next((dict(stage=row['stage'], same_logical_metadata=row['same_logical_metadata'])
                             for row in rows if row['full_logical_sha256_equal'] is False), None)
    first_coverage_difference = next((row['stage'] for row in rows if not row['availability_equal']), None)
    return dict(rank=boundary['rank'], stages=rows, generations=joins,
        first_observed_projection_hash_difference=first_difference,
        first_projection_stage_coverage_difference=first_coverage_difference,
        active_metadata_differences=differences(a['active'], b['active']),
        calls_equal=a['calls'] == b['calls'], reductions_equal=a['reductions'] == b['reductions'],
        complete_records=[boundary['projection_records'][generation]['record'] for generation in (1, 2)],
        caller_source_validated=True, collective_implementation_pinned=False,
        weight_content_equality_proven=False, same_initial_state_assumed=False,
        cause_determined=False, paired_gate_pass=False, numerical_admitted=False, performance_admitted=False)


def compare_projection_ranks(boundaries):
    rows = []
    for generation in (1, 2):
        for name in PROJECTION_STAGES:
            stages = [boundary['projection_records'][generation]['record']['stages'][name] for boundary in boundaries]
            all_observed = all(stage['observed'] is True for stage in stages)
            rows.append(dict(generation=generation, stage=name,
                ranks=[dict(rank=rank, observation=stage) for rank, stage in enumerate(stages)],
                all_four_observed=all_observed,
                full_logical_hashes_equal=len({stage['sha256'] for stage in stages}) == 1 if all_observed else None,
                same_logical_metadata=len({canonical({key: stage[key] for key in ('bytes', 'shape', 'dtype')})
                                          for stage in stages}) == 1 if all_observed else None,
                equality_required=False, numerical_qualification=False,
                comparison_scope='Different TP ranks may contain different shards; cross-rank equality is an observation, not a requirement.'))
    return rows


def main():
    need(REVIEWED_EXTENSION_FROZEN is True, 'projection reader source/schema pins are not yet reviewed and frozen')
    parser = argparse.ArgumentParser(allow_abbrev=False, description=__doc__)
    parser.add_argument('--source-ref', required=True, type=strict_json)
    parser.add_argument('--result-ref', required=True, type=strict_json)
    parser.add_argument('--source-audit-ref', required=True, type=strict_json)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output
    need(output.is_absolute() and '..' not in output.parts and output.parent.is_dir() and
         not output.exists() and not output.is_symlink() and
         not any(root == output or root in output.parents for root in (SOURCE_ROOT, OUTPUT_ROOT, V4_ROOT)),
         'new exclusive diagnostic output outside original source/evidence')
    parents_identity(output)
    readset = Readset()
    own_ref, _ = readset.discover(Path(__file__).absolute())
    m, result, audit, audited = source_and_audit(readset, args.source_ref, args.result_ref, args.source_audit_ref)
    projection_runtime = projection_source_bindings(readset, m, audited)
    need(str(output) not in readset.refs, 'no input overwritten by diagnostic output')
    V4, imported = original_readers(readset, m)
    workers, host_validation = validate_host(readset, args.source_ref, args.result_ref, m, result, audit, V4)
    http, http_ref, evidence, begin, retire, original_operands = validate_original_arm(
        readset, args.source_ref, m, result, V4, workers)
    boundaries = [validate_boundary_rank(readset, args.source_ref, rank, workers[rank], begin, retire,
                                        projection_runtime) for rank in range(4)]
    budget = terminal_budget(readset, args.source_ref, result, boundaries)
    comparisons = [compare_rank(boundary, evidence) for boundary in boundaries]
    # Recheck exact directory closure after all numeric/semantic analysis.
    for boundary in boundaries:
        need({path.name for path in Path(boundary['root']).iterdir()} == expected_names(), 'boundary directory unchanged after analysis')
    before, after = readset.finish()
    value = dict(schema='bole.completed-projection-within-arm-diagnostic/v1', diagnostic_only=True,
        source_only=False, model_ready=False, paired_gate_pass=False, numerical_admitted=False,
        independent_algorithm_numerical_qualification=False, performance_admitted=False,
        formal_performance=False, task_accuracy=False, NPU_executed_by_reader=False,
        cause_determined=False, original_pair_gate_replaced=False, original_pair_gate_rerun=False,
        source=args.source_ref, actual_host_result=args.result_ref, source_audit=args.source_audit_ref,
        source_validation_reopened=True, original_host_and_single_arm_gates_revalidated=True,
        boundary_record_integrity_validated=True, imported_reader_sources=imported,
        comparison_source=own_ref, host_validation=host_validation,
        terminal_budget_validation=budget,
        actual_worker_bindings=[workers[rank] for rank in range(4)],
        actual_physical_devices=[4, 5, 6, 7], original_state_reader_operands=original_operands,
        complete_boundary_files_per_rank=150, complete_boundary_files_all_ranks=600,
        HTTP=compare_http(http, http_ref), ranks=comparisons,
        projection_internal_integrity_validated=True,
        projection_runtime_sources=projection_runtime['snapshots'],
        projection_internal=[compare_projection_rank(boundary) for boundary in boundaries],
        projection_cross_rank=compare_projection_ranks(boundaries),
        limitations=[
            'Only G1 versus G2 within this ON diagnostic is compared. These are distinct native requests; same prompt/seed does not establish identical incoming state.',
            'The first differing retained boundary is the first observed difference, not proof of the causal origin. Work before, between, and outside the retained observations remains unobserved.',
            'Native0 qkv/b/a and full131 stage hashes are source-bound producer witnesses; only last8-token BF16 values of nine stages are retained and independently decoded.',
            'Full state, active conv leading3, and full conv storage are reported separately. Extra conv extent has no numerical finite/equality gate.',
            'Blocking CPU copies can change device scheduling. Repeatability under this observer cannot exclude a race in the unobserved execution.',
            'MTP backing storage inventory does not prove actual draft write extents or alias exclusion. Shared storage by itself is not a defect.',
            'No magnitude threshold is introduced. Bit equality, numerical differences and finite values here do not grant the original numerical, paired-state, performance, or task-accuracy gates.',
            'Projection stages are full actual logical tensor hash witnesses without new raw values. Shapes can differ at reduce-scatter, padding, gather, or other native processing; a hash difference is not automatically a same-span numerical difference.',
            'Weight content and backend-private format are not hashed or proved. Recorded version/object/storage metadata does not establish weight equality.',
            'The five runtime sources and supported Python callsites are pinned; recorded aliases, communication implementation, HCCL transport and device kernels are not independently source-pinned.',
            'no_reduce_callsite_executed means no supported reduction callsite was recorded. Other communication such as all_gather can still execute. Fused stages absent from Python are explicitly unavailable, never treated as equal.',
            'Method code SHA values use the producer runtime marshal format. This host reader validates their typed witness, pinned complete source, AST ownership, and cross-generation stability; it does not pretend to recompile bytecode across Python versions.',
        ],
        source_audit_readset_count=len(audited), readset_count=len(before), total_input_bytes=readset.total,
        inputs_before=before, inputs_after=after, original_inputs_unchanged=True,
        complete_whole_sha_readset_unchanged=True, file_identity_unchanged=True)
    raw = canonical(value) + b'\n'
    need(len(raw) <= OUTPUT_CAP, 'bounded complete diagnostic result')
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        need(stream.write(raw) == len(raw), 'complete exclusive diagnostic output')
        stream.flush(); os.fsync(stream.fileno())
    reference, _, _ = whole_file(output, cap=OUTPUT_CAP, keep=False)
    print(json.dumps(dict(result=reference, diagnostic_only=True, original_inputs_unchanged=True,
        paired_gate_pass=False, numerical_admitted=False, performance_admitted=False,
        model_ready=False, NPU_executed_by_reader=False), sort_keys=True))


if __name__ == '__main__':
    main()
