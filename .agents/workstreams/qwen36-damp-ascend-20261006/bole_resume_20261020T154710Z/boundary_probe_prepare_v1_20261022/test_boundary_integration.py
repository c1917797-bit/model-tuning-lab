"""Focused source-only controls; never added to the original twenty tests."""
import argparse
import ast
import copy
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import boundary_integration as I

ORIGINAL_ROOT = Path(I.PARENT_ROOT)


class BoundaryIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_delta = (ORIGINAL_ROOT/'short_binding_delta.py').read_text()
        cls.old_validator = (ORIGINAL_ROOT/'performance_validate.py').read_text()
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
        self.assertEqual(text, self.old_validator)

    def test_exact_delta_and_validator_pins_reject_modified_baselines(self):
        with self.assertRaises(ValueError):
            I.render_short_delta(self.old_delta+'\n')
        with self.assertRaises(ValueError):
            I.render_validator(self.old_validator.replace('expected=D.runtime(originals)', 'expected={}'), self.pins)

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
                         "authority['cutoff_epoch']==1792672721"):
            self.assertIn(retained, text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--original-root', type=Path, default=ORIGINAL_ROOT)
    args, remaining = parser.parse_known_args()
    ORIGINAL_ROOT = args.original_root
    unittest.main(argv=[__file__, *remaining], verbosity=2)
