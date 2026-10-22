"""Focused CPU controls for new projection evidence parsing only.

Fixtures below are explicitly synthetic records and ASTs. They do not execute
model code or establish device, numerical, lifecycle or performance success.
The old reader's thirteen controls are not duplicated here.
"""
import ast
import copy
import importlib.util
import math
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location('projection_reader_subject',
    Path(__file__).with_name('read_projection_result_v1.py'))
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)

SOURCE_0 = '''
class Projection:
    def forward(self, input_):
        result = self.native(input_)
        return result
class Quant:
    def apply(self, layer, x):
        return x
'''
SOURCE_1 = '''
class Custom:
    def apply(self, input_):
        return self.apply_impl(input_)
class Fused:
    def apply_impl(self, input_):
        output = torch_npu.npu_mm_all_reduce_base(input_, self.weight, group='synthetic')
        return output
class Scatter:
    def apply_impl(self, input_):
        output_parallel = self.layer.quant_method.apply(self.layer, input_)
        output = tensor_model_parallel_reduce_scatter(output_parallel, dim=0)
        output = all_gather(output)
        return output
class Sequence:
    def apply_impl(self, input_):
        return self.matmul_and_reduce(input_)
    def matmul_and_reduce(self, input_):
        output_parallel = self.layer.quant_method.apply(self.layer, input_)
        return tensor_model_parallel_all_reduce(output_parallel)
'''
SOURCE_4 = '''
class Generic:
    def forward(self, input_):
        output_parallel = self.quant_method.apply(self, input_)
        output = tensor_model_parallel_all_reduce(output_parallel)
        return output
'''


def geometry(shape, *, pointer=65536, object_id=701):
    stride, step = [], 1
    for count in reversed(shape):
        stride.append(step)
        step *= count
    return dict(object=object_id, storage_ptr=pointer, storage_bytes=step * 2,
        data_ptr=pointer, offset=0, shape=list(shape), stride=list(reversed(stride)),
        dtype='torch.bfloat16', device='npu:0', logical_bytes=step * 2)


def fixture(branch='generic', generation=1, previous=0):
    runtime = dict(runtime_refs=[copy.deepcopy(R.PROJECTION_RUNTIME_REFS[path])
        for path in sorted(R.PROJECTION_RUNTIME_REFS)], snapshots=[],
        trees={0: ast.parse(SOURCE_0), 1: ast.parse(SOURCE_1), 2: ast.parse(''),
               3: ast.parse(''), 4: ast.parse(SOURCE_4)})
    native = dict(prefix='model.layers.0.linear_attn', request_object=500 + generation)
    custom = branch in ('fused', 'scatter', 'sequence')
    active = dict(layer_class='synthetic.Projection', layer_object=100, gdn_object=101,
        prefix=native['prefix'] + '.out_proj', tp_rank=0, tp_size=4,
        input_is_parallel=True, reduce_results=True, return_bias=True,
        quant_class='synthetic.Quant', quant_object=200,
        custom_class='synthetic.Custom' if custom else None,
        custom_object=300 if custom else None,
        weight=dict(geometry=geometry((5120, 1536)), version=None,
                    bytes_hashed=False, format_observed=False, format=None), bias=None)
    roles = []
    nodes = {}
    def role(name, index, qualname):
        node = R.projection_function_node(runtime['trees'][index], qualname)
        nodes[name] = node
        receiver = active['layer_object'] if name.startswith('projection.') else active[
            'quant_object' if name == 'quant.apply' else 'custom_object']
        roles.append(dict(role=name, source_index=index, qualname=qualname, receiver=receiver,
                          code_sha256='a' * 64, first_line=node.lineno))
    role('projection.forward', 0, 'Projection.forward')
    role('quant.apply', 0, 'Quant.apply')
    role('projection.generic_forward', 4, 'Generic.forward')
    if custom:
        role('custom.apply', 1, 'Custom.apply')
        role('custom.apply_impl', 1, {'fused': 'Fused', 'scatter': 'Scatter', 'sequence': 'Sequence'}[branch] + '.apply_impl')
        if branch == 'sequence':
            role('custom.matmul_and_reduce', 1, 'Sequence.matmul_and_reduce')
    calls = [['projection.forward', 'call']]
    ancestry = []
    if custom:
        ancestry = ['custom.apply', 'custom.apply_impl']
        if branch == 'sequence':
            ancestry.append('custom.matmul_and_reduce')
    elif branch == 'generic':
        ancestry = ['projection.generic_forward']
    calls += [[name, 'call'] for name in ancestry]
    if branch != 'fused':
        calls += [['quant.apply', 'call'], ['quant.apply', 'return']]
    calls += [[name, 'return'] for name in reversed(ancestry)]
    calls += [['projection.forward', 'return']]
    reductions = []
    reduce_role = {'generic': 'projection.generic_forward', 'fused': 'custom.apply_impl',
                   'scatter': 'custom.apply_impl', 'sequence': 'custom.matmul_and_reduce'}.get(branch)
    if reduce_role:
        site = R.projection_reduction_sites(nodes[reduce_role])[0]
        reductions.append(dict(site, role=reduce_role, callsite_only=True,
            callee_source_pinned=False, transport_kernel_observed=False,
            alias=dict(observed=True, object=800, type='builtins.function',
                       module='synthetic', qualname='collective', code_sha256='b' * 64,
                       source_pinned=False)))
    stages = {}
    names = ['projection_input'] + ([] if branch == 'fused' else ['quant_return'])
    if reductions:
        names += ['post_reduce'] if branch == 'fused' else ['pre_reduce', 'post_reduce']
    names += ['projection_return']
    for name in R.PROJECTION_STAGES:
        if name not in names:
            stages[name] = dict(observed=False, reason='fused_no_python_local_result'
                if branch == 'fused' else 'no_reduce_callsite_executed')
            continue
        shape = (131, 1536) if name == 'projection_input' else (131, 5120)
        if branch == 'scatter' and name == 'post_reduce':
            shape = (33, 5120)  # Actual intermediate shape may differ from final output.
        geo = geometry(shape)
        source_role = ('projection.wrapper_entry' if name == 'projection_input' else
                       'quant.apply' if name == 'quant_return' else
                       'projection.forward' if name == 'projection_return' else reduce_role)
        line = 0 if name == 'projection_input' else nodes[source_role].end_lineno
        if name == 'pre_reduce':
            line = reductions[0]['line']
        if name == 'post_reduce':
            line = reductions[0]['line'] if reductions[0]['destination'] == 'return' else reductions[0]['end_line'] + 1
        stages[name] = dict(observed=True, read_ordinal=names.index(name) + 1,
            source_role=source_role, line=line, sha256='c' * 64, bytes=geo['logical_bytes'],
            dtype=geo['dtype'], shape=geo['shape'], geometry=geo, finite=True,
            full_actual_tensor=True, numerical_qualified=False)
    count = sum(stage['bytes'] for stage in stages.values() if stage['observed'])
    request = 'synthetic-request-%d' % generation
    record = dict(schema=R.PROJECTION_SCHEMA, generation=generation, request=request,
        request_object=native['request_object'], active=active, runtime_refs=runtime['runtime_refs'],
        roles=roles, calls=calls, exceptions=[], stages=stages, reductions=reductions,
        read_bytes_generation=count, read_bytes_total=previous + count,
        code_hash_algorithm='sha256(marshal.dumps(code)); producer-runtime witness',
        outer_records=dict(norm='G%d-RAW-layer0_gated_norm.json' % generation,
                           projection='G%d-RAW-layer0_out_projection.json' % generation),
        trace_restored=True, original_bound_calls=1, new_raw_bytes=0, weight_bytes_hashed=False,
        source_bound_python_callsites_only=True, collective_implementation_pinned=False,
        numerical_qualified=False, formal_performance=False, diagnostic_only=True)
    arguments = dict(generation=generation, rank=0, request=request, native0=native,
                     runtime=runtime, previous_read_bytes=previous)
    return record, arguments


def ordered_refs():
    names = ['G0-INSTALL.json']
    for generation in (1, 2):
        p = 'G%d-' % generation
        names += [p + 'NATIVE-INPUT-L00.json', p + 'NATIVE-L00.json']
        for name in R.RAW_SHAPES:
            if name == 'layer0_out_projection':
                names.append(p + 'PROJECTION-INTERNAL.json')
            names += [p + name + '.bin', p + 'RAW-' + name + '.json']
        names += [p + 'NATIVE-L%02d.json' % layer for layer in R.LAYERS if layer != 0]
        names += [p + phase + '.json' for phase in R.PHASES]
        names.append(p + 'RETIRE.json')
    return [dict(path='/synthetic/' + name, bytes=1, sha256='0' * 64) for name in names]


class ProjectionReaderControls(unittest.TestCase):
    def valid(self, record, arguments):
        return R.validate_projection_record(record, **arguments)

    def reject(self, record, arguments):
        with self.assertRaises((ValueError, KeyError, TypeError)):
            self.valid(record, arguments)

    def test_nonfused_fused_inline_return_scatter_and_no_reduction(self):
        for branch, reads in (('generic', 5), ('fused', 3), ('sequence', 5), ('scatter', 5), ('none', 3)):
            with self.subTest(branch=branch):
                record, args = fixture(branch)
                checked = self.valid(record, args)
                self.assertEqual(sum(v['observed'] for v in record['stages'].values()), reads)
                self.assertEqual(checked['extra_read_bytes'], record['read_bytes_generation'])
                self.assertIs(checked['caller_source_validated'], True)
                self.assertIs(checked['callee_source_validated'], False)
        record, args = fixture('scatter')
        self.assertNotEqual(record['stages']['post_reduce']['shape'], record['stages']['projection_return']['shape'])
        self.valid(record, args)

    def test_each_read_is_charged_again_across_two_generations(self):
        first, args = fixture()
        self.valid(first, args)
        second, args2 = fixture(generation=2, previous=first['read_bytes_generation'])
        self.valid(second, args2)
        self.assertEqual(first['read_bytes_generation'], 5768192)
        self.assertEqual(second['read_bytes_total'], 11536384)
        for field in ('read_bytes_generation', 'read_bytes_total'):
            bad = copy.deepcopy(second)
            bad[field] -= 1
            self.reject(bad, args2)
        bad = copy.deepcopy(second)
        bad['stages']['projection_return']['read_ordinal'] = 4
        self.reject(bad, args2)

    def test_single_generation_and_total_read_caps_are_independent(self):
        record, args = fixture()
        for stage in record['stages'].values():
            geo = geometry((1, 2**20))
            stage.update(bytes=geo['logical_bytes'], shape=geo['shape'], geometry=geo)
        record['read_bytes_generation'] = record['read_bytes_total'] = 10 * 2**20
        self.reject(record, args)
        record, args = fixture('fused')
        args['previous_read_bytes'] = R.PROJECTION_READ_CAP_TOTAL - record['read_bytes_generation'] + 1
        record['read_bytes_total'] = args['previous_read_bytes'] + record['read_bytes_generation']
        self.reject(record, args)
        record, args = fixture('fused')
        stage = record['stages']['projection_input']
        geo = geometry((1, 2**20 + 1))
        extra = geo['logical_bytes'] - stage['bytes']
        stage.update(bytes=geo['logical_bytes'], shape=geo['shape'], geometry=geo)
        record['read_bytes_generation'] += extra
        record['read_bytes_total'] += extra
        self.reject(record, args)

    def test_fusion_absence_requires_actual_source_callsite(self):
        record, args = fixture('fused')
        for mutation in ('missing_reduction', 'wrong_kind', 'wrong_target', 'wrong_line', 'wrong_reason'):
            bad = copy.deepcopy(record)
            if mutation == 'missing_reduction':
                bad['reductions'] = []
            elif mutation == 'wrong_kind':
                bad['reductions'][0]['kind'] = 'tensor_model_parallel_all_reduce'
            elif mutation == 'wrong_target':
                bad['reductions'][0]['target'] = 'unbound.npu_mm_all_reduce_base'
            elif mutation == 'wrong_line':
                bad['reductions'][0]['line'] += 1
            else:
                bad['stages']['quant_return']['reason'] = 'no_reduce_callsite_executed'
            with self.subTest(mutation=mutation):
                self.reject(bad, args)

    def test_complete_stage_schema_and_finite_witness_are_strict(self):
        record, args = fixture()
        changes = [('finite', False), ('observed', 1), ('read_ordinal', True),
                   ('full_actual_tensor', False), ('numerical_qualified', True), ('sha256', 'A' * 64)]
        for key, value in changes:
            bad = copy.deepcopy(record)
            bad['stages']['projection_input'][key] = value
            with self.subTest(key=key):
                self.reject(bad, args)
        for mode in ('missing', 'extra', 'missing_stage'):
            bad = copy.deepcopy(record)
            if mode == 'missing':
                del bad['stages']['projection_input']['geometry']
            elif mode == 'extra':
                bad['stages']['projection_input']['synthetic_extra'] = True
            else:
                del bad['stages']['pre_reduce']
            self.reject(bad, args)

    def test_geometry_mismatch_and_outside_actual_callsite_rejected(self):
        record, args = fixture()
        for mutation in ('logical_bytes', 'storage_bytes', 'shape', 'pre_line', 'post_line'):
            bad = copy.deepcopy(record)
            if mutation in ('logical_bytes', 'storage_bytes'):
                bad['stages']['projection_input']['geometry'][mutation] -= 2
            elif mutation == 'shape':
                bad['stages']['projection_input']['shape'] = [131, 1535]
            elif mutation == 'pre_line':
                bad['stages']['pre_reduce']['line'] -= 1
            else:
                bad['stages']['post_reduce']['line'] = bad['reductions'][0]['end_line']
            with self.subTest(mutation=mutation):
                self.reject(bad, args)

    def test_receiver_source_index_method_and_call_ancestry_rejected(self):
        record, args = fixture()
        for mutation in ('receiver', 'source', 'qualname', 'first_line', 'code_sha', 'root_twice', 'crossed_returns'):
            bad = copy.deepcopy(record)
            if mutation == 'receiver':
                bad['roles'][0]['receiver'] = 999
            elif mutation == 'source':
                bad['roles'][0]['source_index'] = 2
            elif mutation == 'qualname':
                bad['roles'][0]['qualname'] = 'Missing.forward'
            elif mutation == 'first_line':
                bad['roles'][0]['first_line'] += 1
            elif mutation == 'code_sha':
                bad['roles'][0]['code_sha256'] = 'invalid'
            elif mutation == 'root_twice':
                bad['calls'].insert(1, ['projection.forward', 'call'])
                bad['calls'].insert(-1, ['projection.forward', 'return'])
            else:
                bad['calls'][3], bad['calls'][4] = bad['calls'][4], bad['calls'][3]
            with self.subTest(mutation=mutation):
                self.reject(bad, args)

    def test_request_prefix_and_original_call_identity(self):
        record, args = fixture()
        for mutation in ('request', 'request_object', 'generation', 'prefix', 'calls', 'trace'):
            bad = copy.deepcopy(record)
            if mutation == 'request':
                bad['request'] = 'another-request'
            elif mutation == 'request_object':
                bad['request_object'] += 1
            elif mutation == 'generation':
                bad['generation'] = True
            elif mutation == 'prefix':
                bad['active']['prefix'] = 'model.layers.1.linear_attn.out_proj'
            elif mutation == 'calls':
                bad['original_bound_calls'] = 2
            else:
                bad['trace_restored'] = False
            with self.subTest(mutation=mutation):
                self.reject(bad, args)

    def test_caller_alias_never_promoted_to_callee_or_kernel_pin(self):
        record, args = fixture()
        for key in ('callee_source_pinned', 'transport_kernel_observed'):
            bad = copy.deepcopy(record)
            bad['reductions'][0][key] = True
            self.reject(bad, args)
        bad = copy.deepcopy(record)
        bad['reductions'][0]['alias']['source_pinned'] = True
        self.reject(bad, args)
        bad = copy.deepcopy(record)
        bad['collective_implementation_pinned'] = True
        self.reject(bad, args)
        record['reductions'][0]['alias'] = dict(observed=False, reason='descriptor_or_dynamic_receiver_not_evaluated')
        self.valid(record, args)

    def test_weight_and_format_remain_explicitly_unobserved(self):
        record, args = fixture()
        for mutation in ('bytes_hashed', 'format_observed', 'format', 'version'):
            bad = copy.deepcopy(record)
            bad['active']['weight'][mutation] = ('invented' if mutation == 'format' else
                                                -1 if mutation == 'version' else True)
            self.reject(bad, args)
        bad = copy.deepcopy(record)
        bad['weight_bytes_hashed'] = True
        self.reject(bad, args)

    def test_observed_hash_differences_are_not_new_equality_gate(self):
        record, args = fixture()
        record['stages']['pre_reduce']['sha256'] = 'd' * 64
        self.valid(record, args)
        observed = R.projection_stage_join(record['stages']['quant_return'], record['stages']['pre_reduce'], 'quant', 'pre')
        self.assertIs(observed['logical_hash_equal'], False)
        self.assertIs(observed['equality_required'], False)
        self.assertIs(observed['magnitude_threshold_applied'], False)
        absent = dict(observed=False, reason='fused_no_python_local_result')
        unknown = R.projection_stage_join(absent, record['stages']['projection_return'], 'absent', 'return')
        self.assertIsNone(unknown['logical_hash_equal'])
        self.assertIsNone(unknown['same_logical_metadata'])
        self.assertIs(unknown['both_observed'], False)

    def test_reshape_join_and_cross_rank_shards_keep_separate_metadata(self):
        record, _ = fixture()
        stage = record['stages']['projection_input']
        outer = dict(logical_sha256=stage['sha256'], logical_bytes=stage['bytes'],
                     logical_shape=[1572, 128], logical_geometry=geometry((1572, 128)))
        value = R.projection_stage_join(outer, stage, 'norm', 'input')
        self.assertIs(value['logical_hash_equal'], True)
        self.assertIs(value['same_logical_metadata'], False)
        boundaries = []
        for rank in range(4):
            by_generation = {}
            for generation in (1, 2):
                row, _ = fixture('fused', generation=generation)
                row['stages']['projection_input']['sha256'] = str(rank) * 64
                by_generation[generation] = dict(record=row)
            boundaries.append(dict(projection_records=by_generation))
        cross = R.compare_projection_ranks(boundaries)
        self.assertIs(cross[0]['full_logical_hashes_equal'], False)
        self.assertIs(cross[0]['equality_required'], False)
        self.assertIsNone(cross[1]['full_logical_hashes_equal'])
        self.assertIsNone(cross[1]['same_logical_metadata'])

    def test_projection_file_closure_and_exact_native0_seam(self):
        names = R.expected_names()
        self.assertEqual(len(names), 150)
        self.assertEqual(sum(name.endswith('.json') for name in names), 132)
        refs = ordered_refs()
        self.assertEqual(len(refs), 149)
        order = R.validate_order(refs)
        self.assertEqual(len(order), 65)
        for mode in ('missing', 'duplicate', 'before_norm', 'after_native1'):
            bad = copy.deepcopy(refs)
            pos = next(i for i, r in enumerate(bad) if r['path'].endswith('G1-PROJECTION-INTERNAL.json'))
            row = bad.pop(pos)
            if mode == 'missing':
                pass
            elif mode == 'duplicate':
                bad[pos:pos] = [row, row]
            elif mode == 'before_norm':
                target = next(i for i, r in enumerate(bad) if r['path'].endswith('G1-layer0_gated_norm.bin'))
                bad.insert(target, row)
            else:
                target = next(i for i, r in enumerate(bad) if r['path'].endswith('G1-NATIVE-L01.json'))
                bad.insert(target + 1, row)
            with self.subTest(mode=mode):
                with self.assertRaises((ValueError, KeyError)):
                    R.validate_order(bad)

    def test_source_binding_requires_fixed_declaration_guest_and_owned_snapshot(self):
        class NoRead:
            def read(self, *args):
                raise AssertionError('invalid binding reached I/O')
        manifest = dict(projection_probe_profile=R.projection_declaration(),
            projection_runtime_refs=copy.deepcopy(R.PROJECTION_RUNTIME_REFS), files={})
        for path, runtime in R.PROJECTION_RUNTIME_REFS.items():
            name = R.PROJECTION_SNAPSHOTS[path]
            manifest['files'][name] = dict(runtime, path=str(R.SOURCE_ROOT/name))
        audited = {ref['path']: ref for ref in manifest['files'].values()}
        for mode in ('declaration', 'guest', 'audit', 'host'):
            m, a = copy.deepcopy(manifest), copy.deepcopy(audited)
            first = sorted(R.PROJECTION_RUNTIME_REFS)[0]
            name = R.PROJECTION_SNAPSHOTS[first]
            if mode == 'declaration':
                m['projection_probe_profile']['extra_read_bytes_total'] += 1
            elif mode == 'guest':
                m['projection_runtime_refs'][first]['sha256'] = '0' * 64
            elif mode == 'audit':
                del a[m['files'][name]['path']]
            else:
                m['files'][name]['path'] = first
            with self.subTest(mode=mode):
                with self.assertRaises(ValueError):
                    R.projection_source_bindings(NoRead(), m, a)

    def test_exception_witness_is_retained_without_invented_failure(self):
        record, args = fixture()
        node = R.projection_function_node(args['runtime']['trees'][0], 'Projection.forward')
        record['exceptions'] = [dict(role='projection.forward', line=node.lineno + 1, type='builtins.KeyError')]
        self.valid(record, args)
        record['exceptions'][0]['line'] = 99999
        self.reject(record, args)


if __name__ == '__main__':
    unittest.main(verbosity=2)
