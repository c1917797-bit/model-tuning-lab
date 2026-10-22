"""CPU-only controls: real Python tracing against temporary pinned pure-Python sources.

The isolated fixture replaces EXPECTED_RUNTIME_REFS only in unittest.mock.patch;
the production map is independently joined to the supplied fixed source map.
No torch, NPU, remote command or model source is imported or executed.
"""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('projection_probe_v1', HERE / 'projection_probe_v1.py')
P = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = P
spec.loader.exec_module(P)
PRODUCTION_REFS = copy.deepcopy(P.EXPECTED_RUNTIME_REFS)
EVIDENCE = HERE / 'evidence' if (HERE / 'evidence').is_dir() else HERE.parent / 'boundary_actual_review'
ALIASES = {'/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear.py': 'ascend_linear.py',
    '/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear_op.py': 'ascend_linear_op.py',
    '/vllm-workspace/vllm-ascend/vllm_ascend/utils.py': 'ascend_utils.py',
    '/vllm-workspace/vllm/vllm/model_executor/custom_op.py': 'custom_op.py',
    '/vllm-workspace/vllm/vllm/model_executor/layers/linear.py': 'vllm_linear.py'}

FIXTURE = '''\
import types
CALLS = {'reduce': 0, 'quant': 0, 'fused': 0}
def tensor_model_parallel_all_reduce(value):
    CALLS['reduce'] += 1
    value.tag += 1
    return value
def npu_mm_all_reduce_base(input_, weight, name, bias=None):
    CALLS['fused'] += 1
    return weight.output
torch_npu = types.SimpleNamespace(npu_mm_all_reduce_base=npu_mm_all_reduce_base)
class Quant:
    def apply(self, layer, x, bias=None):
        CALLS['quant'] += 1
        return layer.output
class RowParallelLinear:
    def forward(self, input_):
        output_parallel = self.quant_method.apply(self, input_, bias=None)
        if self.reduce_results and self.tp_size > 1:
            output = tensor_model_parallel_all_reduce(output_parallel)
        else:
            output = output_parallel
        return output, None
class AscendRowParallelLinear(RowParallelLinear):
    def forward(self, input_, **kwargs):
        self.native_calls += 1
        if self.custom_op is not None:
            return self.custom_op.apply(input_)
        return super().forward(input_)
class CustomRowParallelOp:
    def apply(self, input_):
        output, output_bias = self.apply_impl(input_)
        return output, output_bias
class MatmulAllreduceRowParallelOp(CustomRowParallelOp):
    def apply_impl(self, input_):
        output = torch_npu.npu_mm_all_reduce_base(
            input_, self.layer.weight, 'fake-name', bias=None
        )
        output_bias = None
        return output, output_bias
class SequenceRowParallelOp(CustomRowParallelOp):
    def apply_impl(self, input_):
        output = self.matmul_and_reduce(input_, None)
        output_bias = None
        return output, output_bias
    def matmul_and_reduce(self, input_parallel, bias_):
        output_parallel = self.layer.quant_method.apply(self.layer, input_parallel, bias=bias_)
        return tensor_model_parallel_all_reduce(output_parallel)
'''


def ref(path):
    body = Path(path).read_bytes()
    return dict(path=str(path), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())


class Contract:
    ref = staticmethod(ref)

    @staticmethod
    def checked(reference):
        assert ref(reference['path']) == reference
        return Path(reference['path'])

    @classmethod
    def obj(cls, reference):
        return json.loads(cls.checked(reference).read_bytes())


class Tensor:
    def __init__(self, shape, tag=7):
        self.shape = tuple(shape)
        self.tag = tag
        self._version = 0
        self.logical_bytes = 2
        for extent in shape:
            self.logical_bytes *= extent


class Writer:
    def __init__(self):
        self.files = {}

    def put(self, name, data):
        assert name not in self.files
        self.files[name] = data
        return dict(path='/owned/receipt/BOUNDARY-R0/' + name, bytes=len(data),
                    sha256=hashlib.sha256(data).hexdigest())


class Owner:
    def _identity(self):
        assert not self.identity_failure

    def _geometry(self, tensor):
        assert isinstance(tensor, Tensor)
        stride, product = [], 1
        for extent in reversed(tensor.shape):
            stride.append(product)
            product *= extent
        return dict(object=id(tensor), storage_ptr=18446744073709550000,
            storage_bytes=tensor.logical_bytes, data_ptr=18446744073709550000,
            offset=0, shape=list(tensor.shape), stride=list(reversed(stride)),
            dtype='torch.bfloat16', device='npu:0', logical_bytes=tensor.logical_bytes)

    def _read(self, tensor):
        geometry = self._geometry(tensor)
        self.read_bytes += tensor.logical_bytes
        assert self.read_bytes <= 512 * 2**20
        return tensor, bytes([tensor.tag]) * tensor.logical_bytes, geometry

    def _finite(self, cpu):
        assert self.finite


class Fixture:
    def __init__(self, mode='generic', own_forward=False):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        source = self.root / 'fixture_runtime.py'
        source.write_text(FIXTURE)
        self.module = types.ModuleType('projection_fixture_runtime')
        self.module.__file__ = str(source)
        sys.modules[self.module.__name__] = self.module
        exec(compile(FIXTURE, str(source), 'exec', dont_inherit=True), self.module.__dict__)
        refs = {str(source): ref(source)}
        for number in range(4):
            path = self.root / ('unused_pinned_%d.py' % number)
            path.write_text('# pure Python fixture pin %d\n' % number)
            refs[str(path)] = ref(path)
        self.pin_patch = patch.object(P, 'EXPECTED_RUNTIME_REFS', refs)
        self.pin_patch.start()
        layer = self.module.AscendRowParallelLinear()
        layer.quant_method = self.module.Quant()
        layer.custom_op = None
        layer.native_calls = 0
        layer.weight = Tensor([5120, 1536])
        layer.output = Tensor([131, 5120])
        layer.weight.output = layer.output
        layer.bias = None
        layer.tp_rank, layer.tp_size = 0, 4
        layer.input_is_parallel = layer.reduce_results = layer.return_bias = True
        layer.prefix = 'model.layers.0.linear_attn.out_proj'
        if mode in ('fused', 'inline'):
            cls = self.module.MatmulAllreduceRowParallelOp if mode == 'fused' else self.module.SequenceRowParallelOp
            layer.custom_op = cls()
            layer.custom_op.layer = layer
        if mode == 'no_reduce':
            layer.reduce_results = False
        if own_forward:
            layer.forward = layer.forward
        self.layer = layer
        owner = Owner()
        owner.t = types.SimpleNamespace(Tensor=Tensor)
        owner.C = Contract
        owner.model = types.SimpleNamespace(layers=[types.SimpleNamespace(linear_attn=types.SimpleNamespace(out_proj=layer))])
        owner.scope, owner.failed = True, False
        owner.read_bytes, owner.rank = 0, 0
        owner.retirements = []
        owner.writer = Writer()
        owner.identity_failure, owner.finite = False, True
        owner.manifest = dict(projection_probe_profile=copy.deepcopy(P.DECLARATION),
            projection_runtime_refs=refs, files={'projection_probe_v1.py': ref(P.__file__)},
            boundary_probe_profile={'schema': 'bole.native-prefill-boundary-repeatability/v1'})
        manifest_path = self.root / 'source.json'
        manifest_path.write_bytes(P.canonical(owner.manifest))
        owner.source = ref(manifest_path)
        self.owner = owner
        self.input = Tensor([131, 1536])
        self.generation(1)
        self.observer = P.create(owner, {P.FLAG: '1'})

    def generation(self, number):
        owner = self.owner
        owner.generation = number
        owner.active = ('request-%d' % number, object())
        owner.pending = None
        owner.native = {0: (owner.model.layers[0].linear_attn,
                           types.SimpleNamespace(num_actual_tokens=131), None, owner.active[1])}
        owner.raw_seen = {'layer0_gated_norm'}

    def record(self, generation=1):
        return json.loads(self.owner.writer.files['G%d-PROJECTION-INTERNAL.json' % generation])['record']

    def close(self):
        if sys.gettrace() is self.observer.trace:
            sys.settrace(None)
        self.observer.current = None
        try:
            self.observer.uninstall()
        except ValueError:
            pass
        self.pin_patch.stop()
        sys.modules.pop(self.module.__name__, None)
        self.tmp.cleanup()


class Controls(unittest.TestCase):
    def fixture(self, *args, **kwargs):
        fixture = Fixture(*args, **kwargs)
        self.addCleanup(fixture.close)
        return fixture

    def test_disabled_has_no_owner_or_instrumentation_access(self):
        class Bomb:
            def __getattribute__(self, key):
                raise AssertionError('disabled owner accessed')
        for value in (None, '', '0'):
            env = {} if value is None else {P.FLAG: value}
            self.assertIsNone(P.create(Bomb(), env))
            self.assertIsNone(P.create(None, env))
        self.assertIsNone(sys.gettrace())

    def test_declaration_exact_and_no_implicit_enable(self):
        for env, declaration in (({}, P.DECLARATION), ({P.FLAG: 'true'}, P.DECLARATION),
                                 ({P.FLAG: '1'}, None)):
            with self.assertRaises(ValueError):
                P.select(env, declaration)

    def test_fixed_production_refs_equal_supplied_map(self):
        self.assertEqual(set(P.EXPECTED_RUNTIME_REFS), set(ALIASES))
        for guest, alias in ALIASES.items():
            actual = ref(EVIDENCE / alias)
            self.assertEqual({k: actual[k] for k in ('bytes', 'sha256')},
                             {k: P.EXPECTED_RUNTIME_REFS[guest][k] for k in ('bytes', 'sha256')})

    def test_generic_once_exact_return_and_immediate_read(self):
        f = self.fixture()
        f.observer.install()
        result = f.layer.forward(f.input)
        self.assertIs(result[0], f.layer.output)
        self.assertEqual(f.layer.native_calls, 1)
        self.assertEqual(f.module.CALLS, dict(reduce=1, quant=1, fused=0))
        record = f.record()
        self.assertEqual([s for s in P.STAGES if record['stages'][s]['observed']], list(P.STAGES))
        self.assertEqual(record['read_bytes_generation'], 5768192)
        self.assertEqual(f.owner.read_bytes, 5768192)
        self.assertEqual(record['stages']['quant_return']['sha256'], record['stages']['pre_reduce']['sha256'])
        self.assertNotEqual(record['stages']['pre_reduce']['sha256'], record['stages']['post_reduce']['sha256'])
        self.assertEqual(record['stages']['post_reduce']['sha256'], record['stages']['projection_return']['sha256'])
        self.assertIsNone(sys.gettrace())

    def test_two_actual_generations_and_exact_instance_restoration(self):
        for own in (False, True):
            with self.subTest(own_forward=own):
                f = self.fixture(own_forward=own)
                original = f.layer.__dict__.get('forward', P._MISSING)
                f.observer.install()
                for generation in (1, 2):
                    f.generation(generation)
                    f.layer.forward(input_=f.input)
                    f.observer.before_retire(generation)
                    f.owner.retirements.append(generation)
                self.assertIs(f.layer.__dict__.get('forward', P._MISSING), original)
                self.assertEqual(len(f.owner.writer.files), 2)
                self.assertEqual(f.observer.extra_read_bytes, 11536384)
                f.observer.uninstall()
                f.close()
                self._cleanups.pop()

    def test_fused_never_manufactures_quant_or_pre_reduce(self):
        f = self.fixture('fused')
        f.observer.install()
        result = f.layer.forward(f.input)
        record = f.record()
        self.assertIs(result[0], f.layer.output)
        self.assertEqual(f.module.CALLS, dict(reduce=0, quant=0, fused=1))
        self.assertEqual([s for s in P.STAGES if record['stages'][s]['observed']],
                         ['projection_input', 'post_reduce', 'projection_return'])
        for stage in ('quant_return', 'pre_reduce'):
            self.assertEqual(record['stages'][stage], dict(observed=False, reason='fused_no_python_local_result'))
        self.assertEqual(record['read_bytes_generation'], 3085312)

    def test_inline_return_and_no_reduce_branch(self):
        f = self.fixture('inline')
        f.observer.install()
        f.layer.forward(f.input)
        record = f.record()
        self.assertEqual(len(record['roles']), 6)
        self.assertEqual(record['reductions'][0]['destination'], 'return')
        self.assertTrue(record['stages']['post_reduce']['observed'])
        self.assertEqual(record['read_bytes_generation'], 5768192)
        f.close()
        self._cleanups.pop()
        f = self.fixture('no_reduce')
        f.observer.install()
        f.layer.forward(f.input)
        record = f.record()
        self.assertEqual(record['reductions'], [])
        for stage in ('pre_reduce', 'post_reduce'):
            self.assertEqual(record['stages'][stage], dict(observed=False, reason='no_reduce_callsite_executed'))

    def test_complete_source_binding_rejects_modified_code(self):
        f = self.fixture()
        function = f.layer.forward.__func__
        original = function.__code__
        self.addCleanup(setattr, function, '__code__', original)
        function.__code__ = original.replace(co_firstlineno=original.co_firstlineno + 1)
        with self.assertRaisesRegex(ValueError, 'complete-source exact'):
            P.source_code(Contract, f.layer.forward, f.owner.manifest['projection_runtime_refs'], {})

    def test_wrong_scope_fails_before_original_and_failure_is_sticky(self):
        f = self.fixture()
        f.observer.install()
        f.owner.native[1] = f.owner.native[0]
        with self.assertRaises(ValueError):
            f.layer.forward(f.input)
        self.assertEqual(f.layer.native_calls, 0)
        self.assertTrue(f.observer.failed and f.owner.failed)
        self.assertEqual(f.owner.writer.files, {})

    def test_existing_trace_and_profile_preserved(self):
        for kind in ('trace', 'profile'):
            with self.subTest(kind=kind):
                f = self.fixture()
                f.observer.install()
                foreign = lambda *args: None
                setter, getter = (sys.settrace, sys.gettrace) if kind == 'trace' else (sys.setprofile, sys.getprofile)
                setter(foreign)
                try:
                    with self.assertRaises(ValueError):
                        f.layer.forward(f.input)
                    self.assertIs(getter(), foreign)
                    self.assertEqual(f.layer.native_calls, 0)
                finally:
                    setter(None)
                f.close()
                self._cleanups.pop()

    def test_failed_read_charged_and_trace_restored(self):
        f = self.fixture()
        f.observer.install()
        original_finite = f.owner._finite
        def finite(cpu):
            if f.layer.native_calls:
                raise ValueError('CPU fixture nonfinite witness')
            return original_finite(cpu)
        f.owner._finite = finite
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            f.layer.forward(f.input)
        self.assertIsNone(sys.gettrace())
        self.assertEqual(f.owner.read_bytes, 1743872)
        self.assertEqual(f.observer.extra_read_bytes, 1743872)
        self.assertTrue(f.observer.failed)
        self.assertEqual(f.owner.writer.files, {})

    def test_foreign_trace_installed_during_native_call_is_preserved(self):
        f = self.fixture()
        f.observer.install()
        original = f.module.tensor_model_parallel_all_reduce
        foreign = lambda *args: None
        def replace_trace(value):
            result = original(value)
            sys.settrace(foreign)
            return result
        f.module.tensor_model_parallel_all_reduce = replace_trace
        try:
            with self.assertRaisesRegex(ValueError, 'trace ownership changed'):
                f.layer.forward(f.input)
            self.assertIs(sys.gettrace(), foreign)
            self.assertTrue(f.observer.failed)
            self.assertEqual(f.owner.writer.files, {})
        finally:
            sys.settrace(None)

    def test_partial_installation_rolls_back_exact_instance_slot(self):
        f = self.fixture()
        def partial_setattr(layer, key, value):
            object.__setattr__(layer, key, value)
            if key == 'forward' and value is f.observer.wrapper:
                raise ValueError('fixture failure after actual attribute write')
        with patch.object(type(f.layer), '__setattr__', partial_setattr):
            with self.assertRaisesRegex(ValueError, 'failure after'):
                f.observer.install()
        self.assertNotIn('forward', f.layer.__dict__)
        self.assertTrue(f.observer.failed and f.owner.failed)
        self.assertFalse(f.observer.installed)

    def test_read_caps_and_foreign_wrapper_not_overwritten(self):
        f = self.fixture()
        f.observer.install()
        with self.assertRaisesRegex(ValueError, 'bounded extra'):
            f.layer.forward(Tensor([131, 16384]))
        self.assertEqual(f.layer.native_calls, 0)
        self.assertEqual(f.owner.read_bytes, 0)
        foreign = lambda value: value
        f.layer.forward = foreign
        with self.assertRaisesRegex(ValueError, 'foreign forward'):
            f.observer.uninstall()
        self.assertIs(f.layer.forward, foreign)

    def test_original_disabled_scope_bypass_and_duplicate_fail(self):
        f = self.fixture()
        f.observer.install()
        f.owner.scope = False
        f.layer.forward(f.input)
        self.assertEqual(f.owner.read_bytes, 0)
        f.owner.scope = True
        f.layer.forward(f.input)
        self.assertEqual(len(f.owner.writer.files), 1)
        with self.assertRaises(ValueError):
            f.layer.forward(f.input)
        self.assertEqual(f.layer.native_calls, 2)

    def test_runtime_source_ast_seams_and_max_envelope(self):
        root = EVIDENCE
        names = {'vllm_linear.py': ['RowParallelLinear.forward'],
                 'ascend_linear_op.py': ['MatmulAllreduceRowParallelOp.apply_impl',
                     'SequenceRowParallelOp.matmul_and_reduce', 'Flashcomm2OProjRowParallelOp.apply_impl']}
        for filename, functions in names.items():
            tree = ast.parse((root / filename).read_bytes())
            for function in functions:
                node = P._function_node(tree, function)
                self.assertTrue(P.reduction_sites(node), function)
        f = self.fixture('inline')
        f.observer.install()
        f.layer.forward(f.input)
        envelope = json.loads(next(iter(f.owner.writer.files.values())))
        # Use actual longest six supported source roles, actual fixed long source
        # Refs, 64-bit identity widths and maximum declared request/prefix strings.
        record = envelope['record']
        record['runtime_refs'] = [PRODUCTION_REFS[k] for k in sorted(PRODUCTION_REFS)]
        envelope['pid'] = 2**31 - 1
        record['request'] = 'r' * 128
        record['request_object'] = 2**64 - 1
        active = record['active']
        active.update(layer_class='vllm_ascend.ops.linear.AscendRowParallelLinear',
            quant_class='vllm_ascend.ops.linear.AscendUnquantizedLinearMethod',
            custom_class='vllm_ascend.ops.linear_op.SequenceRowParallelOp',
            layer_object=2**64 - 1, gdn_object=2**64 - 1, quant_object=2**64 - 1,
            custom_object=2**64 - 1, prefix='p' * 128)
        names = {'projection.forward': 'AscendRowParallelLinear.forward',
            'projection.generic_forward': 'RowParallelLinear.forward',
            'quant.apply': 'AscendUnquantizedLinearMethod.apply',
            'custom.apply': 'CustomRowParallelOp.apply',
            'custom.apply_impl': 'SequenceRowParallelOp.apply_impl',
            'custom.matmul_and_reduce': 'SequenceRowParallelOp.matmul_and_reduce'}
        for role in record['roles']:
            role.update(qualname=names[role['role']], receiver=2**64 - 1, first_line=9999)
        for stage in record['stages'].values():
            if stage['observed']:
                stage['line'] = 9999
                for key in ('object', 'storage_ptr', 'data_ptr'):
                    stage['geometry'][key] = 2**64 - 1
        for key in ('object', 'storage_ptr', 'data_ptr'):
            active['weight']['geometry'][key] = 2**64 - 1
        active['weight']['version'] = 2**64 - 1
        reduction = record['reductions'][0]
        reduction.update(line=9998, end_line=9999)
        reduction['alias'].update(object=2**64 - 1,
            module='vllm.distributed.communication_op', qualname='tensor_model_parallel_all_reduce')
        record['calls'] += [['projection.generic_forward', 'call'], ['projection.generic_forward', 'return']]
        record['exceptions'] = [dict(role='custom.matmul_and_reduce', line=9999, type='builtins.AssertionError')]
        self.assertLessEqual(len(P.canonical(envelope)), P.ENVELOPE_CAP)
        print('ENVELOPE_SEQUENCE_MAX_ADDRESSES_BYTES=%d' % len(P.canonical(envelope)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
