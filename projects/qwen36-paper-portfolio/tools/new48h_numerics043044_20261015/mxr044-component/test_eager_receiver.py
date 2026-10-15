import unittest
from eager_receiver import make_receiver
class Tests(unittest.TestCase):
 def build(self,enabled,scope=True,graph=False):
  calls=[]
  def native(A,cu_seqlens=None,chunk_indices_bt=None,output_dtype=None):
   calls.append(A);return 'native'
  def forbidden(*a):raise AssertionError('unqualified candidate callback')
  solve,counts=make_receiver(native,None,forbidden,forbidden,forbidden,
    lambda:scope,forbidden,lambda:graph,enabled=enabled)
  return solve,counts,calls
 def test_default_off_preserves_native_arguments(self):
  solve,counts,calls=self.build(False);x=object()
  self.assertEqual(solve(x),'native');self.assertEqual(calls,[x])
  self.assertEqual(counts,{'native':1,'candidate':0})
 def test_graph_and_outside_gdn_never_enter_candidate(self):
  for scope,graph in ((True,True),(False,False)):
   solve,counts,calls=self.build(True,scope,graph)
   self.assertEqual(solve(object()),'native');self.assertEqual(counts['candidate'],0)
if __name__=='__main__':unittest.main()
