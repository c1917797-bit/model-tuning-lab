import importlib.util,math,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('_actual_decision',P/'decision.py');D=importlib.util.module_from_spec(s);s.loader.exec_module(D)
class Controls(unittest.TestCase):
 def test01_repeated4percent_retained_not_accepted(self):
  v=D.retain_component([dict(dense=100.,candidate=104.)]*3,correctness_consumed=True,same_configuration=True);self.assertTrue(v['retain_for_composition']);self.assertFalse(v['standalone_10percent_observed']);self.assertFalse(v['final_accepted'])
 def test02_no_correctness(self):self.assertFalse(D.retain_component([dict(dense=100.,candidate=104.)]*3,same_configuration=True)['retain_for_composition'])
 def test03_unmatched_configuration(self):self.assertFalse(D.retain_component([dict(dense=100.,candidate=104.)]*3,correctness_consumed=True)['retain_for_composition'])
 def test04_one_pair_only(self):self.assertFalse(D.retain_component([dict(dense=100.,candidate=104.)],correctness_consumed=True,same_configuration=True)['retain_for_composition'])
 def test05_one_negative_round(self):self.assertFalse(D.retain_component([dict(dense=100.,candidate=v)for v in(104.,105.,99.)],correctness_consumed=True,same_configuration=True)['retain_for_composition'])
 def test06_invalid_measures_rejected(self):
  for x in(0.,-1.,float('nan'),float('inf'),True):
   with self.assertRaises(ValueError):D.retain_component([dict(dense=100.,candidate=x)])
 def test07_final_requires_actual_combination_three_pairs(self):
  v=D.final_measurement([dict(dense=100.,candidate=108.)]*3,correctness_consumed=True,same_configuration=True,all_three_tasks_consumed=True);self.assertFalse(v['final_measurement_requirements_observed'])
 def test08_missing_task_results(self):self.assertFalse(D.final_measurement([dict(dense=100.,candidate=111.)]*3,correctness_consumed=True,same_configuration=True)['final_measurement_requirements_observed'])
 def test09_even_full_observations_do_not_issue_acceptance(self):
  v=D.final_measurement([dict(dense=100.,candidate=111.)]*3,correctness_consumed=True,same_configuration=True,all_three_tasks_consumed=True);self.assertTrue(v['final_measurement_requirements_observed']);self.assertFalse(v['final_accepted']);self.assertFalse(v['run_authority'])
 def test10_unknown_actual_duration(self):
  v=D.deadline_budget(cutoff=1792002456,now=1791923600,stages=dict(model_startup=None,paired_smoke=None,full_tasks=None,HE_sandbox=None),cleanup_seconds=90,safety_seconds=900);self.assertEqual(v['status'],'no_finite_eta');self.assertFalse(v['ready'])
 def test11_missing_score_budget(self):self.assertEqual(D.deadline_budget(cutoff=10000,now=1,stages=dict(model=1000,score=None),cleanup_seconds=90,safety_seconds=900)['status'],'no_finite_eta')
 def test12_expired_budget_not_launched(self):
  v=D.deadline_budget(cutoff=10000,now=9500,stages=dict(model=5400,whole=900,score=900),cleanup_seconds=0,safety_seconds=900);self.assertEqual(v['status'],'budget_expired');self.assertFalse(v['full_start_admitted'])
if __name__=='__main__':unittest.main()
