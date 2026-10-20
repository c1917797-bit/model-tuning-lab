"""Actual retained authority content, not measured task evidence."""
import copy
import json
from pathlib import Path
import unittest
import consume_formal as C

P = Path(__file__).resolve().parent / 'authority'


class TaskScopeTests(unittest.TestCase):
    def setUp(self):
        self.replacement = json.loads((P / 'R115_TASK_ACCURACY_CONTRACT_20261013.json').read_bytes())
        self.renewal = json.loads((P / 'R118_NEW12H_AUTHORITY_20261013.json').read_bytes())

    def test_retained_exact_latest_authority(self):
        C.validate_task_scope(list(C.TASKS), self.replacement, self.renewal)

    def test_union_with_superseded_list_is_rejected(self):
        with self.assertRaises(ValueError):
            C.validate_task_scope(list(C.TASKS) + ['LongBench-v2'], self.replacement, self.renewal)

    def test_omission_and_missing_supersession_are_rejected(self):
        with self.assertRaises(ValueError):
            C.validate_task_scope(['GSM8K', 'MMLU'], self.replacement, self.renewal)
        bad = copy.deepcopy(self.replacement)
        bad['supersedes_for_new_experiments'] = []
        with self.assertRaises(ValueError):
            C.validate_task_scope(list(C.TASKS), bad, self.renewal)

    def test_normal_eos_and_task_cap_still_required(self):
        for key, value in [('normal_eos', False), ('max_tokens', 1024), ('enable_thinking', True)]:
            bad = copy.deepcopy(self.renewal)
            bad['acceptance']['task_accuracy'][key] = value
            with self.assertRaises(ValueError):
                C.validate_task_scope(list(C.TASKS), self.replacement, bad)


if __name__ == '__main__':
    unittest.main()
