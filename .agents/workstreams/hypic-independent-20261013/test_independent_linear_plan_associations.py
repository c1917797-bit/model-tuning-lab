import unittest
from dataclasses import replace
from independent_linear_map import LinearSlice,validate_linear_plan_associations
from independent_mixed_query_plan import NativeQueryPlan

class AssociationTests(unittest.TestCase):
    def fixture(self):
        plans=(NativeQueryPlan('d',0,5,0,100,1,'decode'),
               NativeQueryPlan('p',0,5,1,0,12,'cold-material'))
        states=(LinearSlice('d',0,5,0,4,0,1,True),
                LinearSlice('p',0,5,1,9,1,13,False))
        return plans,states
    def test_complete_mapping(self):
        p,s=self.fixture();self.assertEqual(validate_linear_plan_associations(p,s),s)
    def test_missing_alias_wrong_step_and_initial_rejected(self):
        p,s=self.fixture()
        for bad in (s[:1],(s[0],replace(s[1],state_slot=4)),
                    (s[0],replace(s[1],step=6)),
                    (s[0],replace(s[1],has_initial_state=True)),
                    tuple(reversed(s))):
            with self.assertRaises(ValueError):validate_linear_plan_associations(p,bad)

if __name__=='__main__':unittest.main()
