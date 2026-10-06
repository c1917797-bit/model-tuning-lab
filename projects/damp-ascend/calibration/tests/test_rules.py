"""Synthetic CPU rule/receipt fixtures; never presented as actual calibration."""
import inspect
import json
import math
from pathlib import Path
import tempfile
import unittest
from damp_calibrate.rules import (ALPHAS, choose, joint_risk, partition_rows, protected,
                                   retention, sr_from_rms)
from damp_calibrate.evidence import report_receipt,lock_source,lines
from damp_capture.contract import file_digest,MODEL_HASHES

class RulesTests(unittest.TestCase):
    def test_joint_not_product_of_independent_means(self):
        errors = [[100.,1.],[0.,50.]]; weights = [1.,100.]
        score = joint_risk(errors,weights)
        self.assertEqual(score,[50.,2500.5])
        self.assertEqual(protected(score,1)[0],[1])
        naive = [50.*50.5,25.5*50.5]
        self.assertEqual(protected(naive,1)[0],[0])

    def test_next_future_and_identity_anchor_term(self):
        self.assertEqual(retention([[0.]*12 for _ in range(256)]),[257.]*12)
        self.assertAlmostEqual(retention([[math.log(.5)],[math.log(.5)]])[0],1.3125)

    def test_retention_invalid_rows_fail(self):
        for rows in ([],[[0.],[0.,0.]],[[float('nan')]],[[.1]]):
            with self.assertRaises(ValueError): retention(rows)

    def test_sr_general_positive_fp32_not_power2(self):
        sr,pv = sr_from_rms([0.,3.,10.,1.],.5)
        self.assertEqual(sr[0],1.)
        self.assertTrue(all(x > 0 and math.isfinite(x) for x in sr))
        self.assertFalse(math.log2(sr[1]).is_integer())
        self.assertEqual(pv,[0,3,1,2])
        self.assertEqual(ALPHAS,(0.,.25,.5,.75,1.))

    def test_pv_sorts_post_scaling_and_index_breaks_ties(self):
        sr,pv = sr_from_rms([4.,2.,0.,2.],1.)
        self.assertEqual(sr,[4.,2.,1.,2.]); self.assertEqual(pv,[2,0,1,3])

    def test_protected_regions_keep_native_order(self):
        high,pk = protected([4.,2.,9.,9.,0.],2)
        self.assertEqual(high,[2,3]); self.assertEqual(pk,[2,3,0,1,4])
        self.assertEqual(protected([1.]*128,16)[0],list(range(16)))

    def test_selection_tie_and_invalid_are_explicit(self):
        self.assertEqual(choose([None,2.,2.]),1)
        for scores in ([None,None],[float('nan')],[-1.]):
            with self.assertRaises(ValueError): choose(scores)

    def test_partition_balance_and_identity(self):
        rows = [dict(id=f'{s}-{d}-{n}',split=s,domain=d)
            for s in ('fit','tune','validation') for d in ('math','code','general') for n in range(4)]
        self.assertEqual({s:len(v) for s,v in partition_rows(rows).items()},dict(fit=12,tune=12,validation=12))
        rows[-1]['id'] = rows[0]['id']
        with self.assertRaises(ValueError): partition_rows(rows)

    def test_validation_is_not_a_selection_argument(self):
        from damp_calibrate.pipeline import select
        self.assertEqual(list(inspect.signature(select).parameters),['samples','torch'])
        self.assertIn('set(samples) == {"fit","tune"}',inspect.getsource(select))

    def test_parity_receipt_wrong_hash_rank_mode_requests_rejected(self):
        baseline = dict(status='pass',mode='full',ranks=4,layers=48,requests=36,
                        output_parity='all token IDs bitwise same-eager')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'synthetic-report.json'
            for key,value in (('status','failed'),('ranks',3),('mode','smoke'),('requests',35)):
                fake = dict(baseline); fake[key] = value; path.write_text(json.dumps(fake))
                with self.subTest(key=key),self.assertRaises(ValueError):
                    report_receipt(dict(path=str(path),sha256=file_digest(path)),'full',36)
            path.write_text(json.dumps(baseline))
            with self.assertRaises(ValueError): report_receipt(dict(path=str(path),sha256='0'*64),'full',36)

    def test_source_lock_requires_independent_schema_model_image(self):
        baseline = dict(schema='damp.source-lock/v1',created_by='parent-controller',
            model_config_sha256=MODEL_HASHES['config.json'],image_id='sha256:'+'a'*64)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'synthetic-invalid-lock.json'
            for key,value in (('schema','damp-calibration-input/v1'),('created_by','calibration-script'),
                              ('model_config_sha256','0'*64),('image_id','unknown'),
                              ('image_id','sha256:'+'x'*64)):
                fake = dict(baseline); fake[key] = value; path.write_text(json.dumps(fake))
                with self.subTest(key=key,value=value),self.assertRaisesRegex(ValueError,'independent source lock'):
                    lock_source(path,Path(tmp)/'nonexistent-input.json',{},Path(tmp))

    def test_audit_line_limit_is_bounded_and_full_b1_admissible(self):
        self.assertEqual(inspect.signature(lines).parameters['maximum_lines'].default,400000)
        required = 2*36*4096 + 2*36*48*6 + 12*48*6 + 36*48 + 36 + 2
        self.assertGreater(required,250000)
        self.assertLess(required,400000)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'synthetic-lines.jsonl'
            path.write_text('{}\n'*6)
            with self.assertRaises(ValueError): list(lines(path,maximum_lines=5))

if __name__ == '__main__': unittest.main()
