"""Actual CPU tensor controls. No source or stage fixture is NPU evidence."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

P = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_analysis120_tested', P / 'analyze.py')
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        cls.t = torch; torch.set_num_threads(1)
        cls.direct = A.load(A.ref(P / 'direct_round.py'), '_analysis120_test_RNE')

    def test_01_defaultoff_cold_I(self):
        r = subprocess.run([sys.executable, '-I', '-B', str(P / 'analyze.py')], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), dict(enabled=False, NPU=False, qualification=False))

    def test_02_independent_rounding_controls(self):
        self.assertEqual(self.direct.controls(self.t)['controls'], 16)
        x = self.t.tensor([[1 + 2**-8 + 2**-30, -1 - 2**-8 - 2**-30]], dtype=self.t.float64)
        report = A.round_cells(self.t, x.to(self.t.bfloat16), x, self.direct)
        self.assertEqual(report['changed_bitpatterns'], 2)
        self.assertEqual(report['operational_torch_cast_vs_direct_changed'], 2)
        self.assertEqual(report['max_ULP_distance'], 1)
        self.assertGreater(report['nonzero_minimum_midpoint_margin'], 0)

    def test_03_midpoint_signedzero_and_wrongdtype(self):
        t = self.t
        x = t.tensor([[1 + 2**-8, -1 - 2**-8, 0., -0.]], dtype=t.float64)
        b = self.direct.round_bf16(t, x); b[0, 3] = 0.
        r = A.round_cells(t, b, x, self.direct)
        self.assertEqual(r['exact_midpoints'], 2)
        self.assertEqual(r['signed_zero_only'], 1)
        with self.assertRaisesRegex(ValueError, 'actual BF16'):
            A.round_cells(t, x.float(), x, self.direct)

    def test_04_residual_original_lower_A(self):
        t = self.t; a = t.tensor([[0., 0.], [.5, 0.]], dtype=t.float64)
        inverse = t.tensor([[1., 0.], [-.5, 1.]], dtype=t.float64)
        self.assertEqual(A.residual(t, a, inverse)['max_abs'], 0)
        inverse[1, 0] += .01
        self.assertGreater(A.residual(t, a, inverse)['max_abs'], .009)

    def test_05_vector_decomposition_and_cancellation(self):
        t = self.t
        rows = {name: dict(state=t.tensor([v], dtype=t.float32)) for name, v in [('saved_candidate', 3.), ('native', 5.), ('cpu64_cast', 2.)]}
        r = A.vector_decomposition(t, rows, dict(state=t.tensor([1.], dtype=t.float64)))
        self.assertEqual(r['vector_closure_max_abs'], 0)
        self.assertEqual(r['squared_norm_identity_residual'], 0)
        self.assertNotEqual(sum(r['component_relative_l2'].values()), r['total_relative_l2'])
        self.assertFalse(r['native_truth_assumed'])

    def test_06_state_classification_is_not_success(self):
        def reg(c, n, i):
            return {k: dict(state=dict(pass_=v, **{'pass': v})) for k, v in zip(('saved_candidate', 'native', 'cpu64_cast'), (c, n, i))}
        self.assertEqual(A.classify(reg(False, False, True)), 'ONLY_CPU64CAST_RECOVERS_WORKING_STATE')
        self.assertIn('REFERENCE_UNRESOLVED', A.classify(reg(False, False, False)))
        self.assertIn('CANDIDATE_SPECIFIC', A.classify(reg(False, True, True)))

    def test_07_actual_original_consumer_to_extension_2K(self):
        t = self.t
        fixture = json.loads((P / 'SOFTWARE_FIXTURE_SOURCES.json').read_bytes())
        if sys.platform != 'linux':
            # Local software fixtures relocate bytes only; never qualification.
            locations = dict(metrics=P.parent / 'mxr-r118-capture-20261013-001/consume_capture.py', working=P.parent / 'mxr-two-residual-model-new24h-098-repair5/boundary_oracle.py')
            for key, path in locations.items():
                actual = A.ref(path); self.assertEqual((actual['bytes'], actual['sha256']), (fixture[key]['bytes'], fixture[key]['sha256'])); fixture[key] = actual
            for key, old in fixture['base']['files'].items():
                actual = A.ref(P.parent / 'mxr-r5-prefill-counterfactual-new24h-120-repair2' / key)
                self.assertEqual((actual['bytes'], actual['sha256']), (old['bytes'], old['sha256'])); fixture['base']['files'][key] = actual
        with tempfile.TemporaryDirectory() as td, A.original_consumer(fixture['base']) as (G, C):
            d = Path(td)
            q = t.zeros((1, 2048, 4, 128), dtype=t.bfloat16)
            v = t.zeros((1, 2048, 12, 128), dtype=t.bfloat16)
            a = t.zeros((1, 2048, 12, 64), dtype=t.float32)
            b = t.zeros_like(a, dtype=t.bfloat16)
            for start in range(0, 2048, 64):
                b[0, start:start + 64] = t.eye(64, dtype=t.bfloat16)[:, None, :].expand(64, 12, 64)
            state = t.zeros((1, 12, 128, 128)); gate = t.zeros((1, 2048, 12))
            cu = t.tensor([0, 2048], dtype=t.int32)
            x = dict(q=q, k=q.clone(), v=v, g=gate, beta=t.ones((1, 2048, 12), dtype=t.bfloat16), initial_state=state, cu_seqlens=cu, scale=128**-.5, already_normalized=True)
            fp = {k: G.fp(t, z) for k, z in x.items() if t.is_tensor(z)}
            saved = dict(inputs=x, inputs_after=fp, normalized_inputs=x, normalized_inputs_after=fp, output=v, final_state=state, solve=dict(A=a, output=b, cu=cu), FP32_policy=dict(allow_hf32=False, common_to_all_arms=True), block044={})
            bogus = dict(path='/software-only/not-NPU-evidence', bytes=1, sha256='0'*64)
            launch = dict(source=bogus, build=bogus, library=bogus, symbol='call_mxr_y16_compensated')
            pr = d / 'prerequisite.json'; pr.write_bytes(json.dumps(launch).encode())
            m = dict(original_metrics=fixture['metrics'], original_working_oracle=fixture['working'], variant_ref=bogus, actual037_prerequisite=G.ref(pr))
            rows = []
            for arm in G.ARMS:
                z = dict(arm=arm, A=a, G=gate, B=b, W=v, U=v, Hentry=t.zeros((1, 12, 32, 128, 128), dtype=t.bfloat16), Vnew=v.transpose(1, 2).contiguous(), Hend_final=state, state=state, output=v, inputs_after={k: fp[k] for k in ('q', 'k', 'v', 'g', 'beta', 'initial_state', 'cu_seqlens')})
                if arm == 'saved_candidate':
                    z['actual_X2'] = dict(variant_ref=bogus, trace=None, solver_identity=launch)
                target = d / (arm + '.pt'); t.save(z, target); rows.append(dict(arm=arm, raw=G.ref(target)))
            rawref = bogus; G.RAW = rawref
            result = dict(rows=rows, candidate_anchor_bitwise=True, same_actual_A_G=True, raw_bytes=sum(r['raw']['bytes'] for r in rows))
            stage = dict(schema='mxr.prefill-three-arm-stage/v084', source=bogus, authority=G.AUTHORITY, primary=None, NPU=True, qualified=False, raw=rawref, result=result)
            base = C.consume_case(t, m, stage, saved)
            extended = A.analyze_case(t, G, m, dict(raw=rawref), dict(result=result), saved, base, self.direct)
            self.assertEqual(len(extended['tiles']), 384)
            self.assertEqual(len(extended['actual_vs_working_checkpoints']['native']), 32)
            self.assertFalse(extended['qualification'])
            self.assertTrue(all(z['actual_A_vs_working_A']['max_abs'] == 0 for z in extended['tiles']))
            self.assertEqual(extended['state_vector_decomposition']['vector_closure_max_abs'], 0)
            # Test native repeat reader on actual serialized CPU records, not a bool fixture.
            outer = dict(source=bogus, primary=None, NPU=True, result=dict(cases=[dict(case_id='software-only', raw=rawref, result=result)]))
            repeated = A.repeat_comparison(t, G, outer, outer)
            self.assertTrue(repeated['cases'][0]['arms']['native']['state']['bitwise'])
            wrong = dict(outer, source=dict(bogus, sha256='1'*64))
            with self.assertRaisesRegex(ValueError, 'same-source'):
                A.repeat_comparison(t, G, outer, wrong)
            # Perturbed actual candidate cannot enter extension attribution.
            candidate = t.load(rows[0]['raw']['path'], weights_only=True); candidate['state'] = state.clone(); candidate['state'][0, 0, 0, 0] = 1
            t.save(candidate, rows[0]['raw']['path']); rows[0]['raw'] = G.ref(rows[0]['raw']['path']); result['raw_bytes'] = sum(r['raw']['bytes'] for r in rows)
            with self.assertRaisesRegex(ValueError, 'candidate bitwise anchor'):
                C.consume_case(t, m, stage, saved)


if __name__ == '__main__':
    unittest.main()
