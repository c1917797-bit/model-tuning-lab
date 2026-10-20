"""Exception integrity checks; no host scan, container or device operation."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

P = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_fd_diag_test', P / 'fd_inventory_diagnostic.py')
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)


class Controls(unittest.TestCase):
    def test_success_returns_original_observation_without_scan(self):
        result = object()
        calls = []
        ctl = SimpleNamespace(observe=lambda label: (calls.append(label), result)[1])
        with patch.object(F, 'capture') as scan:
            self.assertIs(F.observe(None, ctl, 'x', {}, P), result)
            scan.assert_not_called()
        self.assertEqual(calls, ['x'])

    def test_limit_error_is_same_object_and_original_called_once(self):
        original = ValueError('bounded actual FD inventory')
        calls = []
        def reject(label):
            calls.append(label)
            raise original
        summary = {}
        with patch.object(F, 'capture', return_value={'path': '/actual/diagnostic'}) as scan:
            with self.assertRaises(ValueError) as raised:
                F.observe(None, SimpleNamespace(observe=reject), 'x', summary, P)
            self.assertIs(raised.exception, original)
            scan.assert_called_once()
        self.assertEqual(calls, ['x'])
        self.assertEqual(len(summary['FD_inventory_failure_diagnostics']), 1)

    def test_diagnostic_failure_preserves_original_rejection(self):
        original = ValueError('bounded actual FD inventory')
        def reject(label):
            raise original
        summary = {}
        with patch.object(F, 'capture', side_effect=OSError('test diagnostic unavailable')):
            with self.assertRaises(ValueError) as raised:
                F.observe(None, SimpleNamespace(observe=reject), 'x', summary, P)
        self.assertIs(raised.exception, original)
        self.assertTrue(summary['FD_inventory_diagnostic_errors'])

    def test_unrelated_guard_rejection_does_not_scan(self):
        original = ValueError('actual protected device exclusion')
        def reject(label):
            raise original
        with patch.object(F, 'capture') as scan:
            with self.assertRaises(ValueError) as raised:
                F.observe(None, SimpleNamespace(observe=reject), 'x', {}, P)
            self.assertIs(raised.exception, original)
            scan.assert_not_called()


if __name__ == '__main__':
    unittest.main()
