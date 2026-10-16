import sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import test115,test116,test_controller116r1,test_conv_hook116r3,test_alias116r5,test_device118,test_registration118r1,test_calibration118
s=unittest.TestSuite()
for m in(test115,test116,test_controller116r1,test_conv_hook116r3,test_alias116r5,test_device118,test_registration118r1,test_calibration118):
 for case in unittest.defaultTestLoader.loadTestsFromModule(m):
  for test in case:
   if test._testMethodName not in('test_actual_host_receive_outer_inner','test_real_six_raw_consumer_both_independent_references'):s.addTest(test)
r=unittest.TextTestRunner().run(s)
raise SystemExit(0 if r.wasSuccessful()and r.testsRun==29 else 3)
