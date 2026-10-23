"""Metadata/actual-source seam controls only; host has no Torch/NPU."""
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
from unittest import mock

HERE = Path(__file__).resolve().parent
WS = HERE.parent
sys.path.insert(0, str(HERE))
import state_capture_codec as S
import render_state_codec as R


class Tensor:
    def __init__(self, label='base', shape=(12, 128, 128), device='cpu'):
        self.label, self.shape = label, shape
        self.dtype = 'torch.float32'
        self.device = types.SimpleNamespace(type=device)

    def numel(self):
        result = 1
        for n in self.shape:
            result *= n
        return result

    def element_size(self):
        return 4

    def transpose(self, a, b):
        return Tensor(self.label + '.T', self.shape, self.device.type)

    def unsqueeze(self, a):
        return Tensor(self.label, (1,) + self.shape, self.device.type)


T = types.SimpleNamespace(Tensor=Tensor, float32='torch.float32')


def digest(t, x):
    return dict(dtype=x.dtype, shape=list(x.shape), bytes=x.numel() * x.element_size(),
                sha256=hashlib.sha256(x.label.encode()).hexdigest(), finite=True)


def owner():
    return dict(request='actual-software-fixture', generation=1, slot=0, length=2048, version=0)


def fixture():
    before = [dict(layer=i, native_state=Tensor('before%d' % i)) for i in S.LAYERS]
    after = [dict(layer=i, native_state=Tensor('after%d' % i)) for i in S.LAYERS]
    bases = ({r['layer']: r['native_state'] for r in before},
             {r['layer']: r['native_state'] for r in after})
    source = dict(path='/synthetic/source', bytes=1, sha256='0' * 64)

    def ref(i, role):
        canonical = role == 'canonical_input'
        base = bases[0 if role in ('canonical_input', 'staged_before') else 1][i]
        value = S.view(base, canonical)
        phase = ('actual_gdn_input' if canonical else 'actual_published_arena_read'
                 if role == 'observed_after' else 'before_transaction_publish')
        return dict(tag=S.TAG, source=source, rank=0, owner=owner(), layer=i, role=role,
                    view='canonical' if canonical else 'identity', witness=digest(T, value),
                    phase=phase, actual_npu_full_witness=True)
    captures = {i: dict(kind='fa') if i % 4 == 3 else
                dict(kind='gdn', state=ref(i, 'canonical_input')) for i in range(64)}
    rows, applied = [], []
    for i in range(64):
        for kind in (('key', 'value') if i % 4 == 3 else ('state', 'conv')):
            state = kind == 'state'
            rows.append(dict(layer=i, kind=kind,
                             before=ref(i, 'staged_before') if state else Tensor('other'),
                             after=ref(i, 'staged_after') if state else Tensor('other')))
            applied.append(ref(i, 'observed_after') if state else Tensor('other'))
    return dict(source=source, rank=0, owner=owner(), before_GDN=before, after_GDN=after,
                captures=captures, staged=dict(writes=rows), observed_applied=applied,
                state_capture_codec=dict(schema=S.HEADER, source=source, rank=0, owner=owner(),
                                         refs=192, base_count=96, runtime_joint_fit=False))


def decode(f):
    return S.decode(T, f, digest=digest, expected_source=f['source'], rank=0)


def load_actual():
    root = WS / 'formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole'
    files = {p.name: p.read_text() for p in root.glob('*.py')}
    spec = importlib.util.spec_from_file_location('exact_original_qualification_taps',
        WS / 'fastpath_numeric_bridge_prepare_v1/qualification_tap_delta.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    files = module.render(files)
    for n in ('fastpath_numeric_observer.py', 'fastpath_numeric_sink.py'):
        files[n] = (WS / 'fastpath_numeric_bridge_prepare_v1' / n).read_text()
    return files


class Controls(unittest.TestCase):
    def test_exact192_restore_no_input_mutation(self):
        f = fixture()
        restored = decode(f)
        self.assertEqual(restored['captures'][0]['state'].shape, (1, 12, 128, 128))
        self.assertIs(restored['staged']['writes'][0]['before'], f['before_GDN'][0]['native_state'])
        self.assertIs(restored['staged']['writes'][0]['after'], f['after_GDN'][0]['native_state'])
        self.assertIs(restored['observed_applied'][0], f['after_GDN'][0]['native_state'])
        self.assertEqual(f['captures'][0]['state']['tag'], S.TAG)

    def test_cross_owner_rank_source_layer_phase_view_and_digest_rejected(self):
        for key, value in [('owner', dict(owner(), request='other')), ('rank', 1),
                           ('source', dict(path='/other')), ('layer', 1), ('layer', False),
                           ('phase', 'after_publish_fake'), ('view', 'arbitrary.view'),
                           ('actual_npu_full_witness', False)]:
            f = fixture()
            f['captures'][0]['state'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                decode(f)
        for key, value in [('sha256', 'f' * 64), ('finite', False), ('bytes', 2),
                           ('dtype', 'torch.float16'), ('shape', [1])]:
            f = fixture()
            f['captures'][0]['state']['witness'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                decode(f)

    def test_no_path_or_extra_ref_fields_and_missing_role(self):
        for mutate in (lambda f: f['captures'][0]['state'].update(path='/foreign'),
                       lambda f: f['captures'][0].update(state=f['after_GDN'][0]['native_state']),
                       lambda f: f['staged']['writes'].pop(),
                       lambda f: f['before_GDN'][0].update(layer=False)):
            f = fixture()
            mutate(f)
            with self.assertRaises((ValueError, KeyError)):
                decode(f)

    def test_prepublication_is_actual_transaction_order_and_qualification_only(self):
        original = load_actual()
        rendered, inverse = R.adapt(original)
        self.assertEqual(R.undo(rendered, inverse), original)
        module = ast.parse(rendered['service_runner.py'])
        sample = next(n for n in ast.walk(module) if isinstance(n, ast.FunctionDef) and n.name == 'sample')
        # Execute the actual rendered sample publication suffix, not a hand-written
        # lookalike or a string-presence assertion. Stop before output allocation.
        start = next(i for i, n in enumerate(sample.body) if isinstance(n, ast.Assign)
                     and any(isinstance(x, ast.Name) and x.id == 'decision' for x in n.targets))
        stop = next(i for i, n in enumerate(sample.body) if isinstance(n, ast.Assign)
                    and any(isinstance(x, ast.Attribute) and x.attr == 'compaction_order'
                            for x in n.targets))
        func = ast.FunctionDef(name='actual_sample_publication_seam',
            args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
            body=sample.body[start:stop], decorator_list=[])
        events = []
        proposal = dict(published=False)
        qualifier = types.SimpleNamespace(before_publication=lambda p: events.append(('before', p)),
            publication=lambda b, p, r: events.append(('after', p)))
        bridge = types.SimpleNamespace(stage_selected_path=lambda *a, **k: proposal,
                                       fastpath_numeric_observer=qualifier)
        state = types.SimpleNamespace(bridge=bridge,
            live=types.SimpleNamespace(current=object(), publication=lambda r: events.append(('live', r))))
        f = types.SimpleNamespace(owner=owner(), tokens=(1, 2, 3), scheduled_nodes=3,
                                  remaining_output=8, context=object())

        def publish(*args, **kwargs):
            self.assertEqual(events[0], ('before', proposal))
            self.assertFalse(kwargs['collect_diagnostic'])
            events.append(('actual_transaction_publish', proposal))
            return dict(cache_published=True)
        ns = dict(state=state, f=f, torch=object(), group=object(), target_next=(1, 2, 3),
                  fast_performance=True,
                  eligibility=types.SimpleNamespace(decide=lambda *a, **k: types.SimpleNamespace(terminal=0)),
                  transaction=types.SimpleNamespace(publish=publish))
        exec(compile(ast.fix_missing_locations(ast.Module(body=[func], type_ignores=[])),
                     'actual-rendered-sample-suffix', 'exec'), ns)
        ns['actual_sample_publication_seam']()
        self.assertEqual([x[0] for x in events],
                         ['before', 'actual_transaction_publish', 'live', 'after'])
        # Without an actual installed qualifier, the actual transaction remains
        # unchanged and no codec hook executes.
        del bridge.fastpath_numeric_observer
        events.clear()
        ns['transaction'].publish = lambda *a, **k: dict(cache_published=True)
        ns['actual_sample_publication_seam']()
        self.assertEqual([x[0] for x in events], ['live'])
        # Mathematical/transaction code is not edited by this renderer.
        self.assertEqual({k: v for k, v in original.items() if k not in inverse},
                         {k: v for k, v in rendered.items() if k not in inverse and k != 'state_capture_codec.py'})

    def test_default_off_and_unbound_joint_gate(self):
        O = types.SimpleNamespace(m={}, current={})
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            S.enabled(O)
        with self.assertRaisesRegex(ValueError, 'joint'):
            S.require_runtime_admission(object(), {})

    def test_before_publish_records_real_digest_and_no_proposal_mutation(self):
        f = fixture()
        f['before_GDN'] = [dict(layer=i, native_state=Tensor('x%d' % i, device='npu')) for i in S.LAYERS]
        rows = [dict(layer=i, kind='state',
                     before=Tensor('x%d' % i, device='npu'),
                     after=Tensor('y%d' % i, device='npu')) for i in S.LAYERS]
        rows += [dict(layer=i, kind='conv') for i in S.LAYERS]
        rows += [dict(layer=i, kind=k) for i in range(3, 64, 4) for k in ('key', 'value')]
        proposal = dict(owner=owner(), published=False, writes=rows)
        O = types.SimpleNamespace(t=T, current=dict(owner=owner(), before_GDN=f['before_GDN']),
                                  source=f['source'], rank=0)
        after = ([dict(layer=i, native_state=Tensor('y%d' % i, device='npu')) for i in S.LAYERS], [])
        with mock.patch.object(S, 'enabled', return_value=digest):
            S._before_publication(O, proposal)
            encoded = S._encode_publication(O, proposal, after)
        self.assertIsInstance(proposal['writes'][0]['after'], Tensor)
        self.assertEqual(encoded['writes'][0]['after']['phase'], 'before_transaction_publish')
        self.assertEqual(len(O._state_before_publish), 48)
        # A correct actual input does not excuse an actual wrong proposal result.
        after[0][0]['native_state'].label = 'actual_wrong'
        with mock.patch.object(S, 'enabled', return_value=digest), self.assertRaises(S.CaptureMismatch):
            S._encode_publication(O, proposal, after)
        del O._state_before_publish
        with mock.patch.object(S, 'enabled', return_value=digest), self.assertRaises(ValueError):
            S._encode_publication(O, proposal, after)

    def test_failure_file_real_exclusive_ref_fsync_and_no_ack(self):
        # Standard-library writer ABI only. This is not Torch serialization or
        # a real tensor failure; those require the approved same-image stage.
        class C:
            need = staticmethod(S.need)

            @staticmethod
            def ref(path):
                p = Path(path)
                raw = p.read_bytes()
                return dict(path=str(p), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

            @staticmethod
            def checked(ref):
                S.need(C.ref(ref['path']) == ref, 'actual fixture file reopened')
                return Path(ref['path'])
        t = types.SimpleNamespace(Tensor=Tensor, float32=T.float32,
            save=lambda raw, stream: stream.write(b'fixture-writer-ABI-not-a-tensor'))
        with tempfile.TemporaryDirectory(prefix='bole-codec-software-writer-') as tmp:
            c = dict(t=t, C=C, source={'synthetic': True}, rank=0, root=Path(tmp),
                     used=0, metadata_bytes=0)
            O = types.SimpleNamespace(source=c['source'], rank=0, current=dict(owner=owner()), used=0)
            error = S.CaptureMismatch('fixture', actual=Tensor('wrong', device='npu'),
                                     base=Tensor('base', device='npu'), metadata=dict(synthetic=True))
            X = types.SimpleNamespace(export=lambda *a, **k: dict(logical_tensor_bytes=2*S.STATE_BYTES))
            with mock.patch.object(os, 'fsync', wraps=os.fsync) as fsync:
                result = S.partial_failure(c, O, error, X)
                self.assertEqual(fsync.call_count, 2)
            self.assertEqual(result, C.ref(result['path']))
            self.assertTrue(Path(result['path']).name.endswith('-STATE-ALIAS-FAIL.pt'))
            self.assertNotIn('ack', result)
            with self.assertRaises(ValueError):
                S.partial_failure(c, O, error, X)
            c['used'] = S.RAW_CAP
            with self.assertRaises(ValueError):
                S.partial_failure(c, O, error, X)

    def test_actual_numeric2k_composition_inverse_and_five_operand_taps(self):
        p = WS / 'numerical_2k_prefix_prepare_v1/render_numeric_2k.py'
        spec = importlib.util.spec_from_file_location('actual_numeric2k_parent', p)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        bundle = module.adapt(module.read_actual())
        original = {n: b.decode() for n, b in bundle['files'].items()}
        original['fastpath_numeric_sink.py'] = (WS / 'fastpath_numeric_bridge_prepare_v1/fastpath_numeric_sink.py').read_text()
        rendered, inverse = R.adapt(original)
        self.assertEqual(R.undo(rendered, inverse), original)
        for n in ('service_fia.py', 'numeric_prefix_2k.py', 'fastpath_numeric_consumer.py'):
            self.assertEqual(rendered[n], original[n])
        self.assertIn('fa_converted', rendered['fastpath_numeric_observer.py'])
        self.assertIn('PREFIX.require_runtime_admission', rendered['fastpath_numeric_consumer.py'])

    def test_caps_and_original_oracle_entry_retained(self):
        original = load_actual()
        rendered, _ = R.adapt(original)
        sink = rendered['fastpath_numeric_sink.py']
        self.assertIn('report=N.consume_frame(t,C,m,source,decoded,previous=previous)', sink)
        self.assertIn('c[\'used\']+2*logical+128*2**20+64*2**20<=2**30', sink)
        self.assertIn('cap_bytes=384*2**20', sink)
        self.assertIn('before_layer', rendered['fastpath_numeric_observer.py'])
        for n in ('g2_numeric.py', 'independent_model.py', 'oracle112.py',
                  'tp_transaction.py', 'transaction.py'):
            if n in original:
                self.assertEqual(rendered[n], original[n])
        self.assertEqual(S.STATE_BYTES * 48 * 4, 144 * 2**20)


if __name__ == '__main__':
    unittest.main()
