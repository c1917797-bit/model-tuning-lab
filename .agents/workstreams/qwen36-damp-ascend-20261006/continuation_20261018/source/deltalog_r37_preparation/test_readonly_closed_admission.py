"""Arithmetic and real frozen storage061 check controls; no historical raw.

The real source modules are declared own files in the complete model bundle.
Temporary roots below are empty control fixtures, never the experiment root.
"""
import copy
import inspect
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import historical_capture_closed2 as HISTORICAL
import model_snapshot_budget as B
import original_storage061 as ORIGINAL
import readonly_closed_admission as A

G = 2**30
ACTUAL = 45898518779
OLD_COMMITTED = 111049091756
NEW_COMMITTED = 84552810402


def fixture():
    phases = [dict(leaf='/fixture/n16', frozen_bytes=1131358910),
              dict(leaf='/fixture/n160', frozen_bytes=8879581752)]
    rows = [dict(leaf=row['leaf'], stage='numeric', budget_bytes=33 * G) for row in phases]
    return phases, rows


def real_checker(root, ledger, *, actual=ACTUAL, committed=OLD_COMMITTED, overlap=False):
    result = types.ModuleType('_readonly_admission_real061_fixture')
    result.__dict__.update(ORIGINAL.__dict__)
    result.ROOT = Path(root)
    result.check = types.FunctionType(ORIGINAL.check.__code__, result.__dict__, 'check',
                                     ORIGINAL.check.__defaults__, ORIGINAL.check.__closure__)
    result.check.__kwdefaults__ = dict(ORIGINAL.check.__kwdefaults__)
    closed = [dict(leaf='/old-closed/' + str(index)) for index in range(13)]
    if overlap:
        closed[0]['leaf'] = '/fixture/n16'

    def commitment(current_root, current_ledger):
        if len(closed) != 13 or current_ledger != ledger:
            raise ValueError('original fixture closure/ledger')
        return actual, committed

    result.commitment = commitment
    return result


class ReadonlyClosedAdmission(unittest.TestCase):
    def test_known_retained_bytes_and_new_full_cap(self):
        phases, rows = fixture()
        self.assertEqual(A.strict_accounting(B, ACTUAL, OLD_COMMITTED, phases, rows), NEW_COMMITTED)
        self.assertEqual(80 * G - NEW_COMMITTED, 1346535518)
        self.assertEqual(sum(33 * G - row['frozen_bytes'] for row in phases), 60856019722)

    def test_original_prior_policy_exact_inverse_and_check_retained(self):
        text = inspect.getsource(HISTORICAL.prior_policy)
        changed = A.prior_delta(text)
        self.assertEqual(changed.replace(A.NEW, A.OLD), text)
        self.assertEqual(changed.count('proof=S.check()'), 1)
        with self.assertRaises(ValueError):
            A.prior_delta(text.replace('proof=S.check()', 'proof={}'))

    def test_real_original_check_rejects_old_and_accepts_proved_adjustment(self):
        phases, rows = fixture()
        with tempfile.TemporaryDirectory() as root:
            ledger = dict(reservations=rows)
            (Path(root) / 'STORAGE_LEDGER061.23.json').write_text(__import__('json').dumps(ledger))
            storage = real_checker(root, ledger)
            original_check = storage.check
            with patch.object(storage.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=143 * G)):
                with self.assertRaises(ValueError):
                    storage.check(storage.ROOT)
                calls = []
                record, saved_check = A.wrap_commitment(storage, B, phases, ledger, lambda: calls.append('fenced'))
                proof = storage.check(storage.ROOT)
            self.assertIs(saved_check, original_check)
            self.assertIs(storage.check, original_check)
            self.assertEqual((proof['max_total_bytes'], proof['min_free_bytes']), (80 * G, 100 * G))
            self.assertEqual(proof['committed_bytes'], NEW_COMMITTED)
            self.assertEqual(record['calls'], 1)
            self.assertEqual(calls, ['fenced'])

    def test_real_original_check_still_rejects_free_below_100(self):
        phases, rows = fixture()
        with tempfile.TemporaryDirectory() as root:
            ledger = dict(reservations=rows)
            (Path(root) / 'STORAGE_LEDGER061.23.json').write_text(__import__('json').dumps(ledger))
            storage = real_checker(root, ledger)
            A.wrap_commitment(storage, B, phases, ledger, lambda: None)
            with patch.object(storage.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=100 * G - 1)):
                with self.assertRaisesRegex(ValueError, 'free100GiB'):
                    storage.check(storage.ROOT)

    def test_new_run_requires_fresh_full_132_not_old_remaining_capacity(self):
        proof = dict(filesystem_free_bytes=132 * G)
        A.require_fresh_free(B, proof, 132 * G)
        for old, live in ((132 * G - 1, 143 * G), (143 * G, 132 * G - 1)):
            with self.assertRaises(ValueError):
                A.require_fresh_free(B, dict(filesystem_free_bytes=old), live)

    def test_negative_bool_and_noninteger_total_rejected(self):
        phases, rows = fixture()
        for total, old in ((-1, OLD_COMMITTED), (True, OLD_COMMITTED), (1.0, OLD_COMMITTED),
                           (ACTUAL, ACTUAL - 1), (ACTUAL, float(OLD_COMMITTED))):
            with self.assertRaises(ValueError):
                A.strict_accounting(B, total, old, phases, rows)

    def test_duplicate_missing_or_extra_closed_leaves_rejected(self):
        phases, rows = fixture()
        for bad in ([phases[0], phases[0]], phases[:1], phases + [dict(leaf='/fixture/third', frozen_bytes=0)]):
            with self.assertRaises(ValueError):
                A.strict_accounting(B, ACTUAL, OLD_COMMITTED, bad, rows)

    def test_only_original_unique_numeric33_rows_are_reduced(self):
        phases, rows = fixture()
        candidates = []
        for field, value in (('stage', 'cpu'), ('budget_bytes', 32 * G)):
            changed = copy.deepcopy(rows)
            changed[0][field] = value
            candidates.append(changed)
        candidates.extend([rows[:1], rows + [dict(rows[0])]])
        for bad in candidates:
            with self.assertRaises(ValueError):
                A.strict_accounting(B, ACTUAL, OLD_COMMITTED, phases, bad)

    def test_frozen_byte_domain_is_strict(self):
        phases, rows = fixture()
        for value in (-1, True, 33 * G + 1, 1.0):
            changed = copy.deepcopy(phases)
            changed[0]['frozen_bytes'] = value
            with self.assertRaises(ValueError):
                A.strict_accounting(B, ACTUAL, OLD_COMMITTED, changed, rows)

    def test_80_cap_actual_and_commitment_remain_fail_closed(self):
        phases, rows = fixture()
        for total, old in ((80 * G + 1, 160 * G), (ACTUAL, OLD_COMMITTED + 2 * G)):
            with self.assertRaises(ValueError):
                A.strict_accounting(B, total, old, phases, rows)

    def test_already_closed_leaf_cannot_be_discounted_twice(self):
        phases, rows = fixture()
        with tempfile.TemporaryDirectory() as root:
            storage = real_checker(root, dict(reservations=rows), overlap=True)
            with self.assertRaisesRegex(ValueError, 'already discounted'):
                A.wrap_commitment(storage, B, phases, dict(reservations=rows), lambda: None)

    def test_fence_error_and_changed_checker_are_not_swallowed(self):
        phases, rows = fixture()
        ledger = dict(reservations=rows)
        with tempfile.TemporaryDirectory() as root:
            storage = real_checker(root, ledger)

            def reject():
                raise ValueError('changed full closed2 metadata')

            A.wrap_commitment(storage, B, phases, ledger, reject)
            with self.assertRaisesRegex(ValueError, 'changed full closed2'):
                storage.commitment(storage.ROOT, ledger)
            storage = real_checker(root, ledger)
            A.wrap_commitment(storage, B, phases, ledger, lambda: None)
            storage.check = lambda: dict(passed=True)
            with self.assertRaisesRegex(ValueError, 'never replaced'):
                storage.commitment(storage.ROOT, ledger)


if __name__ == '__main__':
    unittest.main()
