"""Device-free actual helper lifecycle controls; native/model work is a fixture."""
import ast
import copy
import os
from pathlib import Path
import textwrap
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import model_entry as E
import model_process_calibration as PC
import prefill_tail as T
import worker_entry as W
import layer_slots131r10 as S
import live_owner as L


class CalibrationTests(unittest.TestCase):
    def fixture(self):
        op = object()
        target = NS(default=op)
        t = NS(ops=NS(_C_ascend=NS(npu_causal_conv1d_custom=target)))
        worker = NS(model_runner=object())
        model = object()
        sr, oldref, ref = {'source': 1}, {'old': 1}, {'actual': 1}
        own = dict(files={'a': {'source_file': 1}}, runtime_sources={'r': {'runtime_file': 1}})
        original = dict(registration={'libraries': ['exact']}, actual_schema_family={'schema': 'exact'})
        value = dict(callable_object_id=id(op), actual_schema_family={'schema': 'exact'},
            registration={'libraries': ['exact']}, registration_after={'libraries': ['exact']})
        identity = dict(extension={'extension': 1}, opapi=[{'opapi': 1}])
        objects = [(sr, own), (oldref, original)]
        C = NS(obj=lambda key: next(v for k, v in objects if k == key), checked=lambda r: r)
        registration = NS(actual=lambda *a, **kw: {'libraries': ['exact']})
        handle = PC.ProcessCalibration(worker=worker, model=model, source_ref=sr, own=own, rank=0, old_ref=oldref)
        args = dict(worker=worker, model=model, source_ref=sr, own=own, rank=0,
            old_ref=oldref, native_registration=registration)
        mocks = [patch.object(PC.MC, 'own_module'),
            patch.object(PC.MC, 'identity', return_value=identity),
            patch.object(PC.MC, 'expected', return_value=identity),
            patch.object(PC.MC, 'schema_family', return_value={'schema': 'exact'}),
            patch.object(PC.MC, 'run', return_value=ref),
            patch.object(PC.MC, 'validate', return_value=value)]
        for mock in mocks:
            mock.start()
            self.addCleanup(mock.stop)
        return handle, t, C, args, target, value, own

    def test_original_matrix_once_and_all_original_receipts_revalidated_for_second_request(self):
        h, t, C, args, target, value, own = self.fixture()
        first = h.acquire(t, C, request_epoch=1, **args)
        second = h.acquire(t, C, request_epoch=2, **args)
        self.assertEqual(first[0], second[0])
        self.assertTrue(first[2]['created'])
        self.assertTrue(second[2]['reused'])
        self.assertEqual(h.generations, [1, 2])
        self.assertEqual(PC.MC.run.call_count, 1)
        self.assertEqual(PC.MC.validate.call_count, 2)
        self.assertIs(h.operator, target.default)

    def test_preexisting_calibration_is_not_a_reuse_path(self):
        h, t, C, args, target, value, own = self.fixture()
        PC.MC.run.side_effect = ValueError('unique existing owned calibration leaf')
        with self.assertRaisesRegex(ValueError, 'unique existing'):
            h.acquire(t, C, request_epoch=1, **args)
        self.assertIsNone(h.ref)
        self.assertEqual(h.generations, [])

    def test_reuse_rejects_changed_worker_model_source_rank_operator_or_generation(self):
        for changed in ('worker', 'model', 'source', 'rank', 'operator', 'generation', 'runtime', 'registration'):
            with self.subTest(changed=changed):
                h, t, C, args, target, value, own = self.fixture()
                h.acquire(t, C, request_epoch=1, **args)
                args = dict(args)
                generation = 2
                if changed == 'worker':
                    args['worker'] = NS(model_runner=args['worker'].model_runner)
                elif changed == 'model':
                    args['model'] = object()
                elif changed == 'source':
                    own['files']['a'] = {'changed': 1}
                elif changed == 'rank':
                    args['rank'] = 1
                elif changed == 'operator':
                    target.default = object()
                elif changed == 'runtime':
                    t = NS(ops=t.ops)
                elif changed == 'registration':
                    args['native_registration'].actual = lambda *a, **kw: {'libraries': ['exact']}
                else:
                    generation = 1
                with self.assertRaises(ValueError):
                    h.acquire(t, C, request_epoch=generation, **args)
                self.assertEqual(h.generations, [1])

    def test_reuse_reopens_receipts_and_rejects_changed_abi_and_complete_library_set(self):
        for changed in ('receipt', 'abi', 'library', 'callable_id'):
            with self.subTest(changed=changed):
                h, t, C, args, target, value, own = self.fixture()
                h.acquire(t, C, request_epoch=1, **args)
                if changed == 'receipt':
                    PC.MC.validate.side_effect = ValueError('changed original raw receipt')
                elif changed == 'abi':
                    PC.MC.schema_family.return_value = {'schema': 'changed'}
                elif changed == 'library':
                    PC.MC.identity.return_value = dict(extension={'extension': 2}, opapi=[])
                else:
                    value['callable_object_id'] += 1
                with self.assertRaises(ValueError):
                    h.acquire(t, C, request_epoch=2, **args)
                self.assertEqual(h.generations, [1])


class HookLifecycleTests(unittest.TestCase):
    def test_g1_owner_allows_one_frame_and_requires_real_removal_after_two_outputs(self):
        class CPUIds:
            def __getitem__(self, index):
                return NS(tolist=lambda: [4])
        request = NS(output_token_ids=[4])
        batch = NS(req_ids=['native-2'], req_id_to_index={'native-2': 0},
            num_computed_tokens_cpu=[131], num_tokens_no_spec=[132], token_ids_cpu=CPUIds())
        runner = NS(requests={'native-2': request}, input_batch=batch)
        owner = E.Owner('native-2', 2, 0, 131, 0)
        live = L.LiveOwner(runner, [], owner, max_steps=1)
        live.record_draft(4, (5, 6))
        schedule = NS(num_scheduled_tokens={'native-2': 1}, scheduled_spec_decode_tokens={})
        frame = live.make_frame(schedule, [1])
        publication = dict(owner=frame.owner, emitted_tokens=(7,), next_length=132, next_version=1,
            cache_published=True, scheduler_ack_pending=True)
        live.publication(publication)
        live.close_frame(['native-2'], (7,))
        with self.assertRaises(ValueError):
            live.retire({'native-2'})
        request.output_token_ids.append(7)
        with self.assertRaises(ValueError):
            live.retire({'native-2'})
        runner.requests = {}
        batch.req_ids = []
        proof = live.retire({'native-2'})
        self.assertEqual(proof['generation'], 2)
        self.assertEqual(proof['steps'], 1)
        self.assertTrue(proof['final_ack_by_retirement_pending'])
        with self.assertRaises(ValueError):
            live.record_draft(7, (8, 9))

    def test_actual_runner_retirement_hook_restores_request_scope_then_process_scope(self):
        # Execute the exact nested producer hook with controlled native seam
        # dependencies. No replacement lifecycle implementation is tested here.
        source = Path(__file__).with_name('service_runner.py').read_text()
        tree = ast.parse(source)
        install = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'install')
        hook = next(n for n in install.body if isinstance(n, ast.FunctionDef) and n.name == 'update_states')
        body = textwrap.dedent(ast.get_source_segment(source, hook))
        log = []
        native_removed = []
        def live(generation):
            rid = 'native-%d' % generation
            def retire(finished):
                self.assertIn(rid, native_removed)
                self.assertIn(rid, finished)
                log.append('retire-%d' % generation)
                return {'generation': generation}
            return NS(initial=NS(request=rid), request=NS(output_token_ids=[4, 7]), retire=retire)
        state = NS(prefill={'actual': 1}, completed=False, live=live(1), steps=[{'actual': 1}],
            completed_requests=[], request_restorers=[lambda: log.append('head-1')],
            restorers=[lambda: log.append('runner-A'), lambda: log.append('runner-B')],
            bridge=NS(restore=lambda: log.append('bridge-1')), generation=1)
        def old_update(schedule):
            log.append('native-update')
            native_removed.extend(schedule.finished_req_ids)
            return 'actual-native-result'
        def rearm(*args, **kw):
            log.append('rearm-48')
            return lambda: log.append('tail-2-restored')
        namespace = dict(state=state, old_update=old_update, E=E, T=NS(install_capture=rearm),
            worker=object(), torch=object(), C=object(), get_forward_context=object(),
            refs={'gdn': {}, 'forward_context': {}},
            freeze_request=lambda: {'generation': state.generation},
            freeze=lambda: log.append('publish-aggregate'),
            restore_native_prefill=lambda: log.append('native-prefill-process'))
        exec('def factory():\n restore_tail = None\n' +
            textwrap.indent(body, ' ') + '\n return update_states\n', namespace)
        update = namespace['factory']()
        self.assertEqual(update(None, NS(finished_req_ids=['native-1'])), 'actual-native-result')
        self.assertEqual(log, ['native-update', 'retire-1', 'head-1', 'bridge-1', 'rearm-48'])
        self.assertIsNone(state.prefill)
        self.assertFalse(state.completed)
        self.assertEqual(state.generation, 2)
        self.assertEqual(len(state.restorers), 2)
        state.prefill, state.live, state.steps = {'actual': 2}, live(2), [{'actual': 2}]
        state.request_restorers = [lambda: log.append('head-2')]
        state.bridge = NS(restore=lambda: log.append('bridge-2'))
        update(None, NS(finished_req_ids=['native-2']))
        self.assertEqual(log[-8:], ['native-update', 'retire-2', 'head-2', 'bridge-2',
            'runner-B', 'runner-A', 'native-prefill-process', 'publish-aggregate'])
        self.assertTrue(state.completed)
        self.assertEqual(state.completed_requests, [{'generation': 1}, {'generation': 2}])

    def test_actual_after_prefill_wrapper_admits_two_distinct_requests_and_leaves_barrier_native(self):
        class Inner:
            def __init__(self):
                self.calls = []
            def forward(self, input_ids, positions, intermediate_tensors=None, inputs_embeds=None):
                self.calls.append(list(input_ids))
                return input_ids
        inner = Inner()
        batch = NS(req_ids=[], req_id_to_index={})
        runner = NS(input_batch=batch, requests={})
        worker = NS(_bole_model_objects={'inner': inner}, model_runner=runner)
        context = NS(attn_metadata={'actual': NS(num_prefills=1)}, in_profile_run=False)
        callbacks = []
        def callback(**kw):
            callbacks.append((kw['request_id'], kw['request'], kw['hidden']))
        with patch.dict(os.environ, BOLE_MODEL_OBJECT_AUDIT_ENABLE='1'), patch.object(W, 'code_source'):
            restore = W.install_after_native_prefill(worker, NS(), qwen_next_ref={},
                get_forward_context=lambda: context, context_source_ref={}, callback=callback,
                callback_source_ref={}, request_limit=2)
            requests = [object(), object(), object()]
            for i, request in enumerate(requests):
                rid = 'request-%d' % i
                runner.requests = {rid: request}
                batch.req_ids = [rid]
                batch.req_id_to_index = {rid: 0}
                inner.forward([i], [0])
                if i == 0:
                    # Another call for the same native request is never a new epoch.
                    inner.forward([i], [0])
            self.assertEqual([v[0] for v in callbacks], ['request-0', 'request-1'])
            self.assertEqual(len(inner.calls), 4)
            restore()
            self.assertNotIn('forward', inner.__dict__)

    def test_all48_native_prefill_observers_can_be_restored_then_rearmed(self):
        class Layer:
            def _forward_core(self, **kw):
                return None
        objects = [Layer() for _ in range(48)]
        worker = NS(_bole_model_objects={'inner': NS(layers=[NS(layer_type='linear_attention',
            linear_attn=obj) for obj in objects])})
        with patch.object(E, 'code_source'):
            for generation in (1, 2):
                restore = T.install_capture(worker, NS(), NS(),
                    get_forward_context=lambda: None, gdn_ref={}, context_ref={})
                self.assertTrue(all('_forward_core' in obj.__dict__ for obj in objects))
                restore()
                self.assertTrue(all('_forward_core' not in obj.__dict__ and
                    obj._forward_core.__func__ is Layer._forward_core for obj in objects))

    def test_reused_physical_slot_requires_new_strong_request_and_matching_generation(self):
        class Vector:
            ndim = 1
            device = NS(type='cpu')
            def __init__(self, values):
                self.values = values
            def cpu(self):
                return self
            def tolist(self):
                return self.values
        class Table(Vector):
            def __getitem__(self, index):
                return Vector(self.values[index[0]][index[1]])
        cpu = Table([[2]])
        table = NS(num_blocks_per_row=[1], get_cpu_tensor=lambda: cpu)
        group = NS(layer_names=['actual-layer'])
        batch = NS(req_ids=[], req_id_to_index={}, block_table=[table])
        runner = NS(requests={}, input_batch=batch, kv_cache_config=NS(kv_cache_groups=[group]))
        layer = NS(kv_cache=(object(), object()))
        bindings = []
        with patch.object(S, 'tensor_id', side_effect=id):
            for generation in (1, 2):
                rid = 'native-%d' % generation
                request = NS(block_ids=[(2,)])
                runner.requests = {rid: request}
                batch.req_ids, batch.req_id_to_index = [rid], {rid: 0}
                meta = NS(prefill_state_indices=Vector([2]), non_spec_state_indices_tensor=Vector([2]),
                    non_spec_prefill_metadata=NS(causal_conv1d=NS(cache_indices=Vector([2]))))
                layer._bole_pure_prefill_observation = dict(metadata=meta, request=request, slot=2)
                binding = S.Binding('actual-layer', 0, 2, runner, rid, request, group, table,
                    (2,), meta, layer, id(layer.kv_cache[0]), id(layer.kv_cache[1]), 131, generation)
                owner = E.Owner(rid, generation, 0, 131, 0)
                self.assertEqual(binding.check(owner), 2)
                self.assertEqual(binding.identity()['generation'], generation)
                with self.assertRaises(ValueError):
                    binding.check(E.Owner(rid, 3-generation, 0, 131, 0))
                if bindings:
                    with self.assertRaises(ValueError):
                        bindings[0].check(E.Owner('native-1', 1, 0, 131, 0))
                bindings.append(binding)


if __name__ == '__main__':
    unittest.main()
