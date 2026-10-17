import importlib.util,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
s=importlib.util.spec_from_file_location('_r22_exact_test',P/'test_readonly_binder_guard.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
r=unittest.TextTestRunner().run(unittest.TestSuite([m.GuardControls('test_exact_program_exe_and_stable_process_identity')]))
raise SystemExit(0 if r.wasSuccessful()and r.testsRun==1 else 3)
