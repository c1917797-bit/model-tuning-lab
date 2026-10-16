"""Affected inherited + new source/entry regression; no backend or math rerun."""
import sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def main():
 names=['test088r1','test088r2','test088r3','test_typed_readset088r4','test_storage088r5','test_handshake088r6','test_overlay088r6','test_declared_baselines088r6r1','test_cleanup_stop088r6r2'];suite=unittest.defaultTestLoader.loadTestsFromNames(names);r=unittest.TextTestRunner(verbosity=2).run(suite);return 0 if r.wasSuccessful()else 1
if __name__=='__main__':raise SystemExit(main())
