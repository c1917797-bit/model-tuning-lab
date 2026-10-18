"""Offline source/plan and resource contracts; never Docker or original raw I/O."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

import owner as C
import plan as P


class Contracts(unittest.TestCase):
    def fixture(self):
        plan = copy.deepcopy(P.expected())
        previous_rows = dict(tree=[], native_own_inputs=[], layer=43)
        for case in P.CASES:
            group = 'tree' if case['kind'] == 'tree' else 'native_own_inputs'
            previous_rows[group].append(dict(label=case['label'], elements=1536,
                                            failed=case['original_failed_elements'],
                                            compensated_failed=case['original_failed_elements'],
                                            failed_set_changed=False))
        database = {
            'plan': plan,
            P.SOURCE['path']: dict(prepared_only=False, whole_numerical_qualification=False),
            P.RANK_REPORT['path']: dict(source=P.SOURCE, receipt=P.RECEIPT, raw=P.RAW,
                                       report=dict(component_checks_pass=False,
                                                   whole_numerical_qualified=False)),
            P.RECEIPT['path']: dict(source=P.SOURCE, rank=1, primary=None, raw=P.RAW),
            P.PREVIOUS['path']: dict(schema='bole.saved-fa-compensated-rounding-diagnostic/v1',
                                    rank=1, original_source=P.SOURCE, original_raw=P.RAW,
                                    rank_report=P.RANK_REPORT, qualified=False, NPU=False,
                                    original_failures_preserved=True, rows=[previous_rows]),
        }

        class Reader:
            need = staticmethod(C.need)

            @staticmethod
            def obj(reference):
                return database[reference['path']]

            @staticmethod
            def checked(reference):
                return Path(reference['path'])

        return Reader, database, plan

    def test_default_off(self):
        root = Path(__file__).resolve().parent
        for name in ('owner.py', 'recover.py', 'bind.py'):
            result = subprocess.run([sys.executable, '-I', '-B', str(root/name)],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), dict(enabled=False, NPU=False))

    def test_exact_plan_readset(self):
        reader, _, _ = self.fixture()
        result = P.consume(reader, dict(path='plan'))
        self.assertEqual(result['readset'], [dict(path='plan'), P.SOURCE,
                                           P.RANK_REPORT, P.RECEIPT, P.RAW, P.PREVIOUS])
        self.assertFalse(result['qualified'])

    def test_changed_preregistered_case_rejected(self):
        reader, _, plan = self.fixture()
        plan['cases'][0]['node'] = 1
        with self.assertRaisesRegex(ValueError, 'exact fixed'):
            P.consume(reader, dict(path='plan'))

    def test_promoted_old_report_rejected(self):
        reader, database, _ = self.fixture()
        database[P.RANK_REPORT['path']]['report']['component_checks_pass'] = True
        with self.assertRaisesRegex(ValueError, 'preserve original failed'):
            P.consume(reader, dict(path='plan'))

    def test_other_rank_producer_rejected(self):
        reader, database, _ = self.fixture()
        database[P.RECEIPT['path']]['rank'] = 0
        with self.assertRaisesRegex(ValueError, 'producer/raw join'):
            P.consume(reader, dict(path='plan'))

    def test_changed_previous_failure_rejected(self):
        reader, database, _ = self.fixture()
        database[P.PREVIOUS['path']]['rows'][0]['tree'][0]['failed'] = 0
        with self.assertRaisesRegex(ValueError, '1/1/0'):
            P.consume(reader, dict(path='plan'))

    def test_cpu_container_arguments(self):
        argv = C.create_argv(1, {'/input': ('/input', False), '/output': ('/output', True)},
                             {'TORCH_DEVICE_BACKEND_AUTOLOAD': '0'}, 'test-only',
                             ['-I', '-B', '/recover.py'])
        self.assertNotIn('--device', argv)
        self.assertNotIn('--privileged', argv)
        for key, value in [('--memory', str(8*2**30)), ('--memory-swap', str(8*2**30)),
                           ('--cpus', '1'), ('--network', 'none'), ('--ipc', 'private')]:
            self.assertEqual(argv[argv.index(key)+1], value)
        self.assertIn('--read-only', argv)
        self.assertIn('type=bind,src=/input,dst=/input,readonly', argv)
        self.assertEqual((C.START, C.CUT), (1792226600, 1792313000))


if __name__ == '__main__':
    unittest.main()
