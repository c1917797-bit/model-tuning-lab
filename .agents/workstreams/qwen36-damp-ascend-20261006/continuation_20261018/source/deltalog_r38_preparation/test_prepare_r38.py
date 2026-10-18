"""Pure source/metadata controls, not actual early/model qualification."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SNAP = HERE.parent.parent / 'resume_packets'
spec = importlib.util.spec_from_file_location('_r38_preparation_control', HERE / 'prepare_r38.py')
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)


class IdentityControls(unittest.TestCase):
    def fixture(self):
        original_owner = (SNAP / 'deltalog_early/owner.py').read_bytes()
        original_recover = (SNAP / 'deltalog_early/recover.py').read_bytes()
        owner = G.identity_text(original_owner.decode()).encode()
        recover = G.replace_once(original_recover, G.MODEL_OLD, G.MODEL_NEW)
        early_tree = {'owner.py': owner, 'recover.py': recover}
        early = dict(root=G.EARLY_NEW, output_root=G.EARLY_OUT_NEW + '/software',
                     files=G.source_refs(G.EARLY_NEW, early_tree))
        early_ref = G.put(early_tree, G.EARLY_NEW, 'SOURCE_TEMPLATE.json', G.serialize(early))
        packet = G.identity_text((SNAP / 'deltalog36/packet_contract.py').read_text()).encode()
        packet = G.replace_once(packet, 'SOFTWARE_CASES=243', 'SOFTWARE_CASES=255')
        budget = (SNAP / 'deltalog36/model_snapshot_budget.py').read_bytes()
        budget = G.replace_once(G.replace_once(budget, G.P_OLD, G.P_NEW), G.J_OLD, G.J_NEW)
        model_tree = {'packet_contract.py': packet, 'model_snapshot_budget.py': budget,
                      'software_dependencies/early_scan_owner.py': owner,
                      'software_dependencies/early_scan_template.json': early_tree['SOURCE_TEMPLATE.json']}
        model = dict(root=G.MODEL_NEW, output_root=G.module_constant(packet, 'OUTPUT'),
                     runtime_identity=G.module_constant(packet, 'IDENTITY'), software_cases=255,
                     early_software_policy=dict(prepared_owner_source=early_ref,
                                                owner_output_root=early['output_root']))
        return model_tree, early_tree, model, early, early_ref

    def test_complete_current_model_owner_child_and_fixture_pair(self):
        value = G.active_identity_audit(*self.fixture())
        self.assertEqual(value['active_stale_identity_tokens'], {})
        self.assertEqual((value['model_cases'], value['early_cases'], value['payload_cases']), (255, 253, 26))
        self.assertEqual(value['actual_child_model_root'], G.MODEL_NEW)

    def test_recover_whole_source_inverse_and_original_execution_gates(self):
        original = (SNAP / 'deltalog_early/recover.py').read_bytes()
        changed = G.replace_once(original, G.MODEL_OLD, G.MODEL_NEW)
        self.assertEqual(changed.replace(G.MODEL_NEW.encode(), G.MODEL_OLD.encode()), original)
        self.assertEqual(G.module_constant(changed, 'MODEL_ROOT'), G.MODEL_NEW)
        original_ast = ast.parse(original)
        actual_ast = ast.parse(changed)
        matches = 0
        for node in ast.walk(actual_ast):
            if isinstance(node, ast.Constant) and node.value == G.MODEL_NEW:
                node.value = G.MODEL_OLD
                matches += 1
        self.assertEqual(matches, 1)
        self.assertEqual(ast.dump(actual_ast), ast.dump(original_ast))

    def test_actual_r37_recover_mismatch_is_rejected(self):
        values = self.fixture()
        values[1]['recover.py'] = (SNAP / 'deltalog_early/recover.py').read_bytes()
        with self.assertRaisesRegex(ValueError, 'actual early owner and actual child'):
            G.active_identity_audit(*values)

    def test_stale_identity_in_either_additional_python_file_is_rejected(self):
        for tree in (0, 1):
            for token in (G.MODEL_OLD, G.EARLY_OLD, G.P_OLD, G.R37_MODEL_ROOT, 'R37admission'):
                values = self.fixture()
                values[tree]['unexpected_active_child.py'] = ('ROOT = ' + repr(token) + '\n').encode()
                with self.subTest(tree=tree, token=token), self.assertRaisesRegex(ValueError, 'stale identity'):
                    G.active_identity_audit(*values)

    def test_owner_root_output_label_and_software_count_cannot_drift(self):
        for mode in ('owner-root', 'output', 'label', 'count'):
            values = self.fixture()
            if mode == 'owner-root':
                values[1]['owner.py'] = values[1]['owner.py'].replace(G.EARLY_NEW.encode(), G.EARLY_OLD.encode())
            elif mode == 'output':
                values[2]['output_root'] += '-other'
            elif mode == 'label':
                values[1]['owner.py'] = values[1]['owner.py'].replace(b'deltalog-R38identity-early-software', b'foreign-owner')
            else:
                values[2]['software_cases'] = 243
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                G.active_identity_audit(*values)

    def test_active_template_and_recover_ref_bytes_cannot_drift(self):
        for mode in ('mirror', 'recover-ref'):
            values = self.fixture()
            if mode == 'mirror':
                values[0]['software_dependencies/early_scan_template.json'] += b' '
            else:
                values[3]['files']['recover.py']['bytes'] += 1
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                G.active_identity_audit(*values)

    def test_historical_donor_exception_is_one_exact_filename(self):
        values = self.fixture()
        values[1]['DONOR_OWNER.py'] = ('ROOT = ' + repr(G.MODEL_OLD) + '\n').encode()
        G.active_identity_audit(*values)
        values[1]['OTHER_DONOR_OWNER.py'] = values[1]['DONOR_OWNER.py']
        with self.assertRaisesRegex(ValueError, 'stale identity'):
            G.active_identity_audit(*values)

    def test_failed_predecessor_is_real_released_failure_and_stale_child(self):
        original = (SNAP / 'deltalog_early/recover.py').read_bytes()
        early_template = dict(path=G.R37_EARLY_ROOT + '/SOURCE_TEMPLATE.json', bytes=1, sha256='1' * 64)
        recover_ref = dict(path=G.R37_EARLY_ROOT + '/recover.py', bytes=len(original), sha256='2' * 64)
        model = dict(root=G.R37_MODEL_ROOT, prepared_only=True, software_cases=255,
                     early_software_policy=dict(prepared_owner_source=early_template))
        early = dict(root=G.R37_EARLY_ROOT, prepared_only=False,
                     schema='deltalog.prebind-software-source/v22', prepared_template=early_template,
                     files={'recover.py': recover_ref})
        result = dict(schema='deltalog.prebind-software-owned/v22', source=G.R37_EARLY_REF,
                      primary="ValueError('actual child exit0')", secondary=[],
                      resource_release_verified=True, stopped_retained=True, stage_result=None,
                      stage_ref=None, numeric_owner=None, Devices=[], NPU=False, qualified=False)
        records = {G.R37_MODEL_REF['path']: model, G.R37_EARLY_REF['path']: early,
                   G.R37_RESULT_REF['path']: result}
        def checked(reference):
            if reference == recover_ref:
                return original
            if reference == early_template:
                return b'{}'
            return G.serialize(records[reference['path']])
        with patch.object(G, 'checked', side_effect=checked):
            value = G.failed_r37(original)
            self.assertIs(value['old_failures_preserved'], True)
            for key, bad in (('primary', None), ('resource_release_verified', False),
                             ('stage_result', {'future': True}), ('qualified', True)):
                before = result[key]
                result[key] = bad
                with self.subTest(key=key), self.assertRaises(ValueError):
                    G.failed_r37(original)
                result[key] = before


if __name__ == '__main__':
    unittest.main()
