"""Focused source-only controls; never added to the original twenty tests."""
import argparse
import ast
import copy
import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import boundary_integration as I

ORIGINAL_ROOT = Path(I.PARENT_ROOT)


class BoundaryIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_delta = (ORIGINAL_ROOT/'short_binding_delta.py').read_text()
        cls.old_validator = (ORIGINAL_ROOT/'performance_validate.py').read_text()
        cls.old_coordinator = (ORIGINAL_ROOT/'performance_software_stages.py').read_text()
        cls.old_authority = json.loads((ORIGINAL_ROOT/'SHORT_AUTHORITY.json').read_bytes())
        cls.old_contract = I.pinned_text((ORIGINAL_ROOT/'contract090.py').read_text(), I.TEXT_ONLY_CONTROL_CONTRACT_REF)
        cls.pins = {name: dict(bytes=10, sha256='a'*64) for name in I.REVIEWED_HELPERS}

    def test_delta_reversible_exact_old_body(self):
        text = I.render_short_delta(self.old_delta)
        text = I.once(text, 'import boundary_delta\n', '')
        original_node = next(node for node in ast.parse(self.old_delta).body
                            if isinstance(node, ast.Assign) and any(
                            isinstance(target, ast.Name) and target.id == 'RUNTIME' for target in node.targets))
        text = I.once(text, 'RUNTIME = '+repr(I.RUNTIME), ast.get_source_segment(self.old_delta, original_node))
        text = I.once(text, " P.need(type(old) is dict and set(old)==set(RUNTIME),'complete boundary runtime input set')\n", '')
        text = I.once(text, ' out=boundary_delta.runtime(old,out)\n', '')
        text = I.once(text, " P.need(type(out) is dict and set(out)==set(RUNTIME),'complete boundary runtime output set')\n", '')
        self.assertEqual(text, self.old_delta)

    def test_validator_reversible_exact_old_body(self):
        pins = I.normalize_reviewed_helpers(self.pins)
        text = I.render_validator(self.old_validator, pins)
        text = I.once(text, 'BOUNDARY_REVIEWED_FILES = '+repr(pins)+'\n', '')
        text = I.once(text, ' import boundary_validation as BV\n BV.validate(C,sr,m,reviewed=BOUNDARY_REVIEWED_FILES)\n', '')
        text = I.once(text, I.CONTINUATION_VALIDATOR_AUTHORITY_GATE, I.ORIGINAL_VALIDATOR_AUTHORITY_GATE)
        text = I.once(text, I.TEXT_ONLY_VALIDATOR_RENDER_LINE, '')
        self.assertEqual(text, self.old_validator)
        coordinator = I.render_current_software_coordinator(self.old_coordinator)
        self.assertEqual(coordinator.count(str(I.CUTOFF_EPOCH)), 3)
        self.assertEqual(coordinator.replace(str(I.CUTOFF_EPOCH), str(I.OLD_REPORT_CUTOFF)),
                         self.old_coordinator)

        # This is a pure source/guard control, not the native parser or a ModelConfig.
        contract = I.render_text_only_contract(self.old_contract)
        self.assertEqual(I.reverse_text_only_contract(contract), self.old_contract)
        with self.assertRaises(ValueError):
            I.render_text_only_contract(contract)
        node = next(n for n in ast.parse(contract).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'text_only_config')
        namespace = dict(need=I.need)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                     '<new-pure-text-only-guard>', 'exec'), namespace)
        guard = namespace['text_only_config']
        manifest = dict(text_only_config=copy.deepcopy(I.TEXT_ONLY_CONFIG))
        argv = ['--language-model-only']
        self.assertEqual(guard(argv, manifest,
            args=SimpleNamespace(**I.TEXT_ONLY_CONFIG), engine=SimpleNamespace(**I.TEXT_ONLY_CONFIG)),
            I.TEXT_ONLY_CONFIG)
        for flag in ('--skip-mm-profiling', '--enable-mm-embeds', '--limit-mm-per-prompt',
                     '--no-language-model-only', '--language-model-only=true', '--language-model-only'):
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                guard(argv+[flag], manifest)
        for field, bad in [('language_model_only', 1), ('language_model_only', False),
                           ('skip_mm_profiling', True), ('enable_mm_embeds', True),
                           ('limit_mm_per_prompt', {'image': 0})]:
            invalid = dict(I.TEXT_ONLY_CONFIG, **{field: bad})
            with self.subTest(manifest_field=field), self.assertRaises(ValueError):
                guard(argv, dict(text_only_config=invalid))
            with self.subTest(parser_field=field), self.assertRaises(ValueError):
                guard(argv, manifest, args=SimpleNamespace(**invalid))
            with self.subTest(engine_field=field), self.assertRaises(ValueError):
                guard(argv, manifest, engine=SimpleNamespace(**invalid))
        with self.assertRaises(ValueError):
            guard(argv, manifest, args=SimpleNamespace())
        # The old memory checker/return remains exact after removing its one join.
        old_memory = next(n for n in ast.parse(self.old_contract).body
                         if isinstance(n, ast.FunctionDef) and n.name == 'cache_memory_config')
        new_memory = next(n for n in ast.parse(contract).body
                         if isinstance(n, ast.FunctionDef) and n.name == 'cache_memory_config')
        new_memory.body = [n for n in new_memory.body if not (isinstance(n, ast.Expr)
            and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name)
            and n.value.func.id == 'text_only_config')]
        self.assertEqual(ast.dump(old_memory), ast.dump(new_memory))

    def test_exact_delta_and_validator_pins_reject_modified_baselines(self):
        with self.assertRaises(ValueError):
            I.render_short_delta(self.old_delta+'\n')
        with self.assertRaises(ValueError):
            I.render_validator(self.old_validator.replace('expected=D.runtime(originals)', 'expected={}'), self.pins)
        with self.assertRaises(ValueError):
            I.render_current_software_coordinator(self.old_coordinator+'\n')

    def test_runtime_extends_exact_three_and_has_complete_keys(self):
        text = I.render_short_delta(self.old_delta)
        node = next(node for node in ast.parse(text).body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'RUNTIME' for target in node.targets))
        self.assertEqual(ast.literal_eval(node.value), I.OLD_RUNTIME + I.EXTRA_RUNTIME)
        self.assertEqual(len(ast.literal_eval(node.value)), 10)
        self.assertIn('set(old)==set(RUNTIME)', text)
        self.assertIn('set(out)==set(RUNTIME)', text)

    def test_reviewed_pins_cannot_omit_or_add_a_helper(self):
        missing = copy.deepcopy(self.pins);missing.pop('boundary_delta.py')
        extra = dict(self.pins, arbitrary_runtime=dict(bytes=1, sha256='b'*64))
        for value in (missing, extra):
            with self.assertRaises(ValueError):
                I.render_validator(self.old_validator, value)

    def test_reviewed_pins_require_exact_typed_finite_shape(self):
        variants = [dict(bytes=True, sha256='a'*64), dict(bytes=2**22+1, sha256='a'*64),
                    dict(bytes=10, sha256='X'*64), dict(bytes=10, sha256='a'*63),
                    dict(bytes=10, sha256='a'*64, ignored=True)]
        for malformed in variants:
            pins = copy.deepcopy(self.pins);pins['boundary_probe_v1.py'] = malformed
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                I.normalize_reviewed_helpers(pins)

    def test_pin_order_is_canonical(self):
        reversed_pins = dict(reversed(list(self.pins.items())))
        self.assertEqual(I.render_validator(self.old_validator, self.pins),
                         I.render_validator(self.old_validator, reversed_pins))

    def test_original_gate_function_and_test_list_stay_present(self):
        old = ast.parse(self.old_validator)
        child = ast.parse(I.render_validator(self.old_validator, self.pins))
        get_test_list = lambda tree: next(ast.literal_eval(node.value) for node in tree.body
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'TEST_FILES' for t in node.targets))
        self.assertEqual(get_test_list(old), get_test_list(child))
        for function in ('enumerate_tests', 'clock', 'dependency_contract'):
            old_node = next(node for node in old.body if isinstance(node, ast.FunctionDef) and node.name == function)
            new_node = next(node for node in child.body if isinstance(node, ast.FunctionDef) and node.name == function)
            self.assertEqual(ast.dump(old_node), ast.dump(new_node))
        text = I.render_validator(self.old_validator, self.pins)
        for retained in ("expected=D.runtime(originals)",
                         "for name,text in expected.items():C.need(C.checked(m['files'][name]).read_text()==text",
                         "base=bind_model.readset(sr)+command_contract.validate(C,sr,m)",
                         "authority['cutoff_epoch']==1792710600"):
            self.assertIn(retained, text)
        self.assertNotIn(I.ORIGINAL_VALIDATOR_AUTHORITY_GATE, text)
        self.assertIn(I.CONTINUATION_VALIDATOR_AUTHORITY_GATE, text)
        authority = copy.deepcopy(self.old_authority)
        prior_ref = dict(path=I.PARENT_ROOT+'/SHORT_AUTHORITY.json', bytes=886,
            sha256='04bf2cd30b4d6fb7de4831450ba8cc89ab3df72b90b50fcf6b648e9142498eb9')
        new = I.continuation_authority(authority, prior_ref)
        self.assertEqual(authority, self.old_authority)
        self.assertEqual(new['historical_authority_ref'], prior_ref)
        self.assertEqual(new['user_authorization_ref'], I.AUTHORIZATION_REF)
        self.assertEqual((new['start_epoch'], new['cutoff_epoch'], new['phase_seconds'], new['cleanup_seconds']),
                         (1792689000, 1792710600, 3600, 180))
        for key, bad in [('phase_seconds', 3599), ('cleanup_seconds', 179), ('cutoff_epoch', 1792710600)]:
            malformed = dict(authority, **{key: bad})
            with self.subTest(authority_key=key), self.assertRaises(ValueError):
                I.continuation_authority(malformed, prior_ref)
        auth_path = Path(__file__).with_name('AUTHORIZATION_CONTINUATION.json')
        payload = json.loads(I.pinned_text(auth_path.read_text(), I.AUTHORIZATION_REF))
        self.assertIs(I.check_continuation_payload(payload), payload)
        for key, bad in [('old_window_extended', True), ('phase_seconds', 3599),
                         ('cleanup_seconds', 179), ('physical_npus', [0, 1, 2, 3]),
                         ('formal_performance_admitted', True), ('internal_batch_cutoff_epoch', 1792710601)]:
            malformed = dict(payload, **{key: bad})
            with self.subTest(ticket_key=key), self.assertRaises(ValueError):
                I.check_continuation_payload(malformed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--original-root', type=Path, default=ORIGINAL_ROOT)
    args, remaining = parser.parse_known_args()
    ORIGINAL_ROOT = args.original_root
    unittest.main(argv=[__file__, *remaining], verbosity=2)
