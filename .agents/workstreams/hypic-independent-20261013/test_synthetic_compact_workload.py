import unittest
from synthetic_compact_workload import expand_payloads


class WorkloadTests(unittest.TestCase):
    def test_full_long_shapes_and_unique_segment(self):
        recipe={'start':1000,'length':16384}
        specs=[{'kind':'public','max_tokens':1}]+[
            {'kind':'private','relocation':r,'input_tokens':32768,'max_tokens':1024} for r in (4096,7168)]
        payloads=expand_payloads(specs,recipe);public=payloads[0]['prompt']
        self.assertEqual(len(public),16384)
        for payload,r in zip(payloads[1:],(4096,7168)):
            self.assertEqual(len(payload['prompt']),32768)
            self.assertEqual(payload['prompt'][r:r+16384],public)
            self.assertEqual(payload['max_tokens'],1024)
            self.assertTrue(payload['ignore_eos'])
    def test_empty_suffix_and_ambiguous_recipe_rejected(self):
        with self.assertRaises(ValueError):
            expand_payloads([{'kind':'private','relocation':7168,'input_tokens':20000,'max_tokens':1024}],{'start':1000,'length':16384})


if __name__=='__main__':unittest.main()
