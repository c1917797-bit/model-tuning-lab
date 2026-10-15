import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from input_contract import require,EXPECTED
class RequiredInputs(unittest.TestCase):
 def test_missing_before_any_read(self):
  called=[]
  with self.assertRaises(ValueError):require({'files':{}},lambda r:called.append(r))
  self.assertEqual(called,[])
 def test_exact_read(self):
  called=[];self.assertEqual(require({'files':{'REGRESSION_INPUTS.json':EXPECTED}},lambda r:called.append(r)),EXPECTED);self.assertEqual(called,[EXPECTED])
 def test_bad_ref(self):
  with self.assertRaises(ValueError):require({'files':{'REGRESSION_INPUTS.json':dict(EXPECTED,bytes=0)}},lambda r:None)
if __name__=='__main__':unittest.main()
