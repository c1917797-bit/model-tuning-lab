import importlib.util,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def main():
    suite=unittest.TestSuite()
    for name in('test115.py','test116.py','test_controller116r1.py','test_conv_hook116r3.py','test_alias116r5.py'):
        spec=importlib.util.spec_from_file_location('actual_'+name[:-3],P/name);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(m))
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if result.testsRun!=21 or result.skipped:raise ValueError('exact six115 plus seven116 plus three real-controller whole suite, no skip')
    return 0 if result.wasSuccessful()else 1
if __name__=='__main__':raise SystemExit(main())
