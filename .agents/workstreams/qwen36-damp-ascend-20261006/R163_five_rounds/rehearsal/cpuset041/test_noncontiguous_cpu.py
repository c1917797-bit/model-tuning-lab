"""Replay MAIN's actual reported CPU-ID seam through the frozen policy.
No CPU affinity, Docker, NPU, admission, reservation or live observation here.
"""
import copy,hashlib,importlib.util,unittest
from pathlib import Path
P=Path('C:/Users/Huawei/AppData/Local/Temp/kivi-continuous-prefix-r156-20261013-002/cohort_policy.py')
b=P.read_bytes()
if len(b)!=10024 or hashlib.sha256(b).hexdigest()!='3b11b2eee79b2da97cc9f2204826a3cb4a1b349b29ed2a8e86d6ea0786c43476':raise ValueError('whole current policy source')
s=importlib.util.spec_from_file_location('_mxr_actual_noncontiguous_policy',P);M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
class CPUIds(unittest.TestCase):
 def test01_actual_ID_set_rejects_physical_ID_reserve(self):
  ids=[0,1,2,3,144,145,166];host=dict(effective_capacity=7,effective_cpus=ids,ancestor_cpuset=ids,quota_ancestors=[dict(key='q',capacity=7)]);daemon=dict(effective_capacity=7,effective_cpus=ids,quota_ancestors=[dict(key='q',capacity=7)])
  plan=dict(members=[dict(run_id='a',host_cpu=0,guest_cpus=[1]),dict(run_id='b',host_cpu=2,guest_cpus=[3])],reserve_cpus=[4,5])
  for name in('a','b'):
   with self.assertRaisesRegex(ValueError,'daemon aggregate'):M.cpu_plan(plan,name,host,daemon)
 def test02_actual_noncontiguous_reserve_both_members_pass(self):
  ids=[0,1,2,3,144,145,166];host=dict(effective_capacity=7,effective_cpus=ids,ancestor_cpuset=ids,quota_ancestors=[dict(key='q',capacity=7)]);daemon=dict(effective_capacity=7,effective_cpus=ids,quota_ancestors=[dict(key='q',capacity=7)])
  plan=dict(members=[dict(run_id='a',host_cpu=0,guest_cpus=[1]),dict(run_id='b',host_cpu=2,guest_cpus=[3])],reserve_cpus=[144,145])
  rows=[M.cpu_plan(plan,n,host,daemon)for n in('a','b')];self.assertEqual([(r['host_cpu'],r['guest_cpu'])for r in rows],[(0,1),(2,3)]);self.assertEqual(rows[0]['reserve_cpus'],[144,145])
  weaker=copy.deepcopy(daemon);weaker['quota_ancestors'][0]['capacity']=5
  with self.assertRaisesRegex(ValueError,'summed CPU budget'):M.cpu_plan(plan,'a',host,weaker)
if __name__=='__main__':unittest.main(verbosity=2)
