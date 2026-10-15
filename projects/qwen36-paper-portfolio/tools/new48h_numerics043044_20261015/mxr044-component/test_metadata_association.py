import unittest
from metadata_association import Associations
from metadata_certificate import certificate,consume,version
class Tensor:
 def __init__(self,shape,ptr=1,version=0):
  self.shape=shape;self.ndim=len(shape);self.ptr=ptr;self._version=version;self.device='npu:0'
 def is_contiguous(self):return True
 def __len__(self):return self.shape[0]
 def data_ptr(self):return self.ptr
class Meta:pass
class Inference(Tensor):
 @property
 def _version(self):raise RuntimeError('Inference tensors do not track version counter.')
 @_version.setter
 def _version(self,value):pass
class Tests(unittest.TestCase):
 def setup_values(self,kind=Tensor):
  meta=Meta();meta.cu_seqlens_host=(0,129);meta.chunk_indices_chunk64_host=(0,0,0,1,0,2)
  cu=kind((2,),2);indices=kind((3,2),3);meta.chunk_indices_chunk64=indices
  return meta,cu,indices
 def test_source_association_and_exact_pointer_certificate(self):
  meta,cu,indices=self.setup_values();a=Associations();a.produced(meta);a.attach(meta,cu);self.assertTrue(a.verified(meta,cu))
  c=certificate(meta,cu,129,'layer', [129]);A=Tensor((1,129,12,64),4)
  proof=consume(c,A,cu,indices,None);self.assertEqual(proof['chunks'],3)
  self.assertIsNone(consume(c,A,Tensor((2,),2),indices,None))
  cu._version+=1;self.assertFalse(a.verified(meta,cu));self.assertIsNone(consume(c,A,cu,indices,None))
 def test_inference_host_and_identity_guards_remain(self):
  meta,cu,indices=self.setup_values(Inference);a=Associations();a.produced(meta);a.attach(meta,cu);self.assertTrue(a.verified(meta,cu))
  self.assertIsNone(version(cu));meta.cu_seqlens_host=(0,128);self.assertFalse(a.verified(meta,cu))
 def test_unregistered_and_wrong_length_fallback(self):
  meta,cu,indices=self.setup_values();self.assertFalse(Associations().verified(meta,cu))
  self.assertIsNone(certificate(meta,cu,32768,'layer',[129]))
 def test_inference_same_object_unannounced_reuse_refused(self):
  meta,cu,indices=self.setup_values(Inference);a=Associations();a.produced(meta);a.attach(meta,cu)
  self.assertTrue(a.verified(meta,cu,'layer0'));self.assertFalse(a.verified(meta,cu,'layer0'))
  with self.assertRaises(ValueError):a.attach(meta,cu)
  with self.assertRaises(ValueError):a.produced(meta)
  # A genuinely new source-produced object can be attached even if framework
  # deliberately reuses its tensor storage; this is a new metadata epoch.
  new,unused,unused_index=self.setup_values(Inference);new.chunk_indices_chunk64=indices
  a.produced(new);a.attach(new,cu);self.assertTrue(a.verified(new,cu,'layer0'))
