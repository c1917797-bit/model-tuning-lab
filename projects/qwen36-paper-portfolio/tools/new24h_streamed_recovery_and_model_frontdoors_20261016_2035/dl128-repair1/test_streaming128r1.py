"""Actual replayable-index ABI controls; receipt/data bodies remain explicit software fixtures."""
import copy,json,unittest
from unittest.mock import patch
import test_frontdoor128 as F
R=F.R

class StreamedRecoveryControls(unittest.TestCase):
 def test_old_R2_source_and_missing_wrong_index_reject(self):
  for change in ('old','missing','sha','count','parents'):
   C,m,p,s,docs,rs,stage,inspect=F.fixture();key=lambda r:json.dumps(r,sort_keys=True)
   reader=docs[key(rs)];d=reader['recovery_readset_index']
   if change=='old':reader['prepared_template']=dict(R.R2_TEMPLATE,path=R.R2_TEMPLATE['path'].replace('repair3','repair2'))
   elif change=='missing':__import__('pathlib').Path(d['index_ref']['path']).unlink()
   elif change=='sha':d['index_ref']['sha256']='0'*64
   elif change=='count':d['entries']+=1
   else:d['parents']=[];d['parent_count']=0
   with patch.object(R,'streamed',C.streamed),self.assertRaises((ValueError,FileNotFoundError)):
    R.load_recovery(C,m,p,s)
 def test_real_export_is_replayable_and_small_recording_not_blob_array(self):
  C,m,p,s,docs,rs,stage,inspect=F.fixture();key=lambda r:json.dumps(r,sort_keys=True)
  planref=dict(path='/SOFTWARE_ONLY128/current-model-plan.json',bytes=1,sha256='1'*64);docs[key(planref)]=p
  def actual_recovery_frontdoor(reader,context,pr,sr):
   return R.load_recovery(reader,context,reader.obj(pr),sr)
  with patch.object(R,'streamed',C.streamed),patch.object(R,'admit',actual_recovery_frontdoor):
   refs=R.readset(C,m,planref,s)
   descriptor=docs[key(rs)]['recovery_readset_index']
   self.assertEqual(refs.descriptor,descriptor)
   first=list(refs);self.assertEqual(first,list(refs));self.assertEqual(len(refs),len(first))
   self.assertIsInstance(refs.parents,tuple);self.assertLess(len(refs.base),100)
   self.assertGreater(descriptor['entries'],600)
   with self.assertRaises(ValueError):refs.extend([])
 def test_routing_MODE_preserved(self):
  import split_qualification128 as Q
  self.assertEqual(Q.MODE,'actual052-split-scale-diagnostic-only')

if __name__=='__main__':unittest.main()
