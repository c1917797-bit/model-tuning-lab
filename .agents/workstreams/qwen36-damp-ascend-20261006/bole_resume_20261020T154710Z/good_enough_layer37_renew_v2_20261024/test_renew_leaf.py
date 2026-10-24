"""Stdlib source/entry controls only; synthetic authority objects are not tickets."""
import argparse
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import types
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import renew_leaf as R


def mirrored_parents():
    root = HERE.parents[1] / 'mxr' / 'good_enough_current_leaf_prepare_v1'
    files = {}
    for name, ref in R.PARENTS.items():
        raw = (root / name).read_bytes()
        # The approved local transport appended one LF. Recover it ONLY when
        # the entire recovered payload matches MAIN's actual remote Ref3.
        if R.digest(raw) != ref['sha256']:
            R.need(raw.endswith(b'\n') and R.digest(raw[:-1]) == ref['sha256'], 'exact approved transport recovery')
            raw = raw[:-1]
        R.need(len(raw) == ref['bytes'], 'whole remote size, never normalize source')
        files[name] = raw
    return files


def module(raw, name, file):
    m = types.ModuleType(name)
    m.__file__ = str(file)
    exec(compile(raw, str(file), 'exec'), m.__dict__)
    return m


def function_ast(raw, name):
    tree = ast.parse(raw)
    return ast.dump(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name), include_attributes=False)


class Renewal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = mirrored_parents()
        cls.out, cls.delta = R.adapt(cls.original)

    def test_exact_parent_outer_inverse_and_negative_bytes(self):
        self.assertEqual(R.inverse(self.out, self.delta), self.original)
        for name in R.PARENTS:
            bad = dict(self.original)
            bad[name] += b'\n'
            with self.assertRaisesRegex(ValueError, 'exact reviewed original'):
                R.adapt(bad)
        bad = dict(self.out)
        bad['successor_bindings.py'] += b'\n'
        with self.assertRaisesRegex(ValueError, 'unchanged derived'):
            R.inverse(bad, self.delta)

    def test_actual_public_default_off_missing_ticket_unknown_arguments(self):
        m = module(self.out['prepare_successor.py'], '_GE_new_public_fixture', R.PREP / 'prepare_successor.py')
        old = sys.argv
        try:
            stream = io.StringIO()
            sys.argv = [m.__file__]
            with contextlib.redirect_stdout(stream):
                m.main()
            self.assertEqual(json.loads(stream.getvalue()), dict(enabled=False, NPU=False, source_bound=False))
            sys.argv = [m.__file__, '--bind', '--template-ref', '{}']
            with self.assertRaisesRegex(ValueError, 'MAIN actual authority required'):
                m.main()
            sys.argv = [m.__file__, '--numeric']
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                m.main()
            self.assertEqual(caught.exception.code, 2)
        finally:
            sys.argv = old

    def test_generated_contract_uses_actual_new_clock_without_renewing_old_input(self):
        m = module(self.out['prepare_successor.py'], '_GE_contract_fixture', R.PREP / 'prepare_successor.py')
        original = b'START,CUT=1792226600,1792313000\nAUTHORITY_REF={}\ndef current(r,p):\n return None\n'
        result = m.current_contract(original)
        actual = module(result, '_GE_contract_result', R.ROOT / 'event_contract.py')
        self.assertEqual((actual.START, actual.CUT), (R.START, R.CUT))
        self.assertIsNone(actual.AUTHORITY_REF)
        self.assertEqual(m.RESOURCES['phase_seconds'], 600)
        self.assertEqual(m.RESOURCES['child_seconds'], 300)
        self.assertEqual(m.RESOURCES['cleanup_seconds'], 90)
        self.assertEqual(m.RESOURCES['disk_reserve_bytes'], 4 * 2**30)
        # The production source uses pathlib.Path on Linux. This local test is
        # Windows; compare its path components, not Windows path separators.
        self.assertEqual({k: v.replace('\\', '/') for k, v in m.OUTPUTS.items()}, R.OUTPUTS)

    def test_actual_authority_missing_old_window_wrong_root_budget_refused(self):
        # Exercise real derived guard; object/file I/O alone is substituted.
        # No physical authority, binding, reviewed result or device is produced.
        m = module(self.out['successor_bindings.py'], '_GE_guard_fixture', R.PREP / 'successor_bindings.py')
        with self.assertRaisesRegex(ValueError, 'authority is unbound'):
            m.validate_authority({}, None, None, clock=False)
        template = dict(path='/synthetic-only/template', bytes=1, sha256='0' * 64)
        review_ref = dict(path='/synthetic-only/review', bytes=1, sha256='1' * 64)
        auth_ref = dict(path='/synthetic-only/authority', bytes=1, sha256='2' * 64)
        value = dict(outputs=R.OUTPUTS, resources={'synthetic_only': True}, files={}, parent_source_ref={}, migration_builder_ref={}, phase_seconds=600)
        review = dict(schema='ge.MAIN-layer37-successor-source-review/v1', decision='approve', prepared_template_ref=template,
                      source_file_refs=value['files'], parent_source_ref=value['parent_source_ref'], migration_builder_ref={},
                      preparation_window_ref=R.WINDOW, resources=value['resources'], math_thresholds_unchanged=True, original96_tests_retained=True)
        authority = dict(schema='ge.MAIN-reviewed-layer37-successor-authority/v1', approved=True, preparation_window_ref=R.WINDOW,
                         prepared_template_ref=template, source_root=str(m.ROOT), outputs=R.OUTPUTS, physical=[6], protected=[0,1,2,3],
                         start_epoch=R.START, cutoff_epoch=R.CUT, resources=value['resources'], MAIN_review_ref=review_ref)
        window = dict(preparation_authorized=True, device_execution_requires_distinct_MAIN_source_review=True, start_epoch=R.START, cutoff_epoch=R.CUT)
        original_obj, original_checked, original_time = m.obj, m.checked, m.time
        try:
            m.obj = lambda ref: authority if ref == auth_ref else review if ref == review_ref else window if ref == R.WINDOW else (_ for _ in ()).throw(ValueError('unknown synthetic Ref'))
            m.checked = lambda ref: ref
            m.time = types.SimpleNamespace(time=lambda: R.START + 1)
            self.assertIs(m.validate_authority(value, template, auth_ref, clock=True), authority)
            for key, bad in [('start_epoch',1792740953), ('cutoff_epoch',1792827353), ('source_root',str(R.PARENT / 'prepared-source'))]:
                old = authority[key]; authority[key] = bad
                with self.assertRaisesRegex(ValueError, 'exact distinct source-specific'):
                    m.validate_authority(value, template, auth_ref, clock=True)
                authority[key] = old
            m.time = types.SimpleNamespace(time=lambda: R.CUT - 599)
            with self.assertRaisesRegex(ValueError, 'full original600'):
                m.validate_authority(value, template, auth_ref, clock=True)
            # Actual public bind continuation with a valid *synthetic* new
            # review: stop at whole-source verification, before any write.
            # This deliberately does not pretend the missing62 files passed.
            m.time = types.SimpleNamespace(time=lambda: R.START + 1)
            producer = module(self.out['prepare_successor.py'], '_GE_bind_continuation_fixture', R.PREP / 'prepare_successor.py')
            helper_ref = dict(path=str(R.ROOT / 'successor_bindings.py'), bytes=len(self.out['successor_bindings.py']), sha256=R.digest(self.out['successor_bindings.py']))
            value['files'] = {'successor_bindings.py': helper_ref}
            review['source_file_refs'] = value['files']
            producer.validate_template = lambda ref: value
            producer.checked = lambda ref: types.SimpleNamespace(read_bytes=lambda: self.out['successor_bindings.py']) if ref == helper_ref else (_ for _ in ()).throw(ValueError('unknown synthetic helper Ref'))
            entered = []
            class WholeSourcePending(Exception):
                pass
            def stop_before_whole(sr, manifest, root, *, clock, allow_unwritten):
                self.assertEqual(str(root), str(producer.ROOT))
                self.assertEqual(manifest['authority_ref'], auth_ref)
                self.assertFalse(manifest['prepared_only'])
                self.assertTrue(clock and allow_unwritten)
                entered.append('new-source-whole-verification')
                raise WholeSourcePending()
            producer.load = lambda *args: dict(validate_authority=m.validate_authority, validate_source=stop_before_whole)
            producer.write_json = lambda *args: self.fail('must not write a synthetic binding')
            old_argv = sys.argv
            try:
                sys.argv = [producer.__file__, '--bind', '--template-ref', json.dumps(template), '--authority-ref', json.dumps(auth_ref)]
                with self.assertRaises(WholeSourcePending):
                    producer.main()
            finally:
                sys.argv = old_argv
            self.assertEqual(entered, ['new-source-whole-verification'])
        finally:
            m.obj, m.checked, m.time = original_obj, original_checked, original_time

    def test_unchanged_original_gate_math_readset_and_public_commands(self):
        for name in ('validate_authority', 'validate_source', 'checked'):
            self.assertEqual(function_ast(self.original['successor_bindings.py'], name), function_ast(self.out['successor_bindings.py'], name))
        for name in ('bind', 'inverse', 'validate_template', 'prepare', 'main', 'check'):
            self.assertEqual(function_ast(self.original['prepare_successor.py'], name), function_ast(self.out['prepare_successor.py'], name))
        m = module(self.out['prepare_successor.py'], '_GE_registration_fixture', R.PREP / 'prepare_successor.py')
        self.assertEqual(m.PARENT_REF['sha256'], 'a262c2d8465d5d51d7541f003a4275136b2de387b269346f66c84c7b25076c9b')
        self.assertEqual(m.WINDOW_REF, R.WINDOW)
        for ref in R.PARENTS.values():
            self.assertIn(repr(ref), self.out['prepare_successor.py'].decode())

    def test_generated_files_and_actual_original_public_stage_transport(self):
        for name, raw in self.out.items():
            self.assertEqual((HERE / name).read_bytes(), raw, 'deployed draft must equal exact adapter output')
        path = HERE.parents[1] / 'mxr' / 'ge-parent' / 'run_stage.py'
        raw = path.read_bytes()
        expected = 'a5e3c3d4022c27412eeb380d4ba79387fe2cb81b8834da9afdd6cadfde39bc45'
        if hashlib.sha256(raw).hexdigest() != expected:
            R.need(raw.endswith(b'\n') and hashlib.sha256(raw[:-1]).hexdigest() == expected, 'exact parent stage transport')
            raw = raw[:-1]
        saved = {n: sys.modules.get(n) for n in ('event_contract', 'event_host', 'ge_receipt')}
        present = {n: n in sys.modules for n in saved}
        source = dict(path=str(R.ROOT / 'SOURCE_MANIFEST.json'), bytes=1, sha256='a' * 64)
        cpu = dict(path=R.OUTPUTS['CPU'] + '/RESULT.json', bytes=1, sha256='b' * 64)
        prerequisites, ge_gate = {'synthetic_transport_only': True}, {'synthetic_GE009_ref_only': True}
        calls = []
        manifest = dict(actual_input_ref={}, grouped_prerequisites=prerequisites, outputs=R.OUTPUTS)
        contract, owner, receipt = (types.ModuleType(n) for n in saved)
        contract.need = R.need
        contract.obj = lambda ref: manifest
        contract.reference = lambda p: source if str(p).endswith('SOURCE_MANIFEST.json') else cpu
        owner.main = lambda args: calls.append(args) or 0
        receipt.CONSUMER_REF = ge_gate
        try:
            sys.modules.update(event_contract=contract, event_host=owner, ge_receipt=receipt)
            entry = module(raw, '_actual_GE_run_stage_transport', R.ROOT / 'run_stage.py')
            for stage in ('audit', 'cpu', 'numeric'):
                self.assertEqual(entry.main(['--execute', '--stage', stage, '--source-sha256', source['sha256']]), 0)
            self.assertIn('--source-audit-only', calls[0])
            self.assertIn('--cpu-preflight', calls[1])
            self.assertEqual(json.loads(calls[2][calls[2].index('--prerequisites-ref') + 1]), prerequisites)
            self.assertEqual(json.loads(calls[2][calls[2].index('--cpu-preflight-ref') + 1]), cpu)
            self.assertEqual(json.loads(calls[2][calls[2].index('--ge-gate-ref') + 1]), ge_gate)
        finally:
            for name, value in saved.items():
                if present[name]:
                    sys.modules[name] = value
                else:
                    sys.modules.pop(name, None)


if __name__ == '__main__':
    unittest.main(verbosity=2)
