import unittest
from independent_step_metadata_cache import metadata_scope, cpu_list

class Tensor:
    def __init__(self, values):
        self.values = values
        self._version = 0
        self.reads = 0
    def detach(self): return self
    def cpu(self): self.reads += 1; return self
    def tolist(self): return list(self.values)

class Tests(unittest.TestCase):
    def test_disabled(self):
        x=Tensor([1])
        with metadata_scope():
            cpu_list(x);cpu_list(x)
        self.assertEqual(x.reads,2)
    def test_same_identity(self):
        x=Tensor([1])
        with metadata_scope(enabled=True):
            a=cpu_list(x);a[0]=9
            self.assertEqual(cpu_list(x),[1])
        self.assertEqual(x.reads,1)
    def test_mutation(self):
        x=Tensor([1])
        with metadata_scope(enabled=True):
            cpu_list(x);x.values=[2];x._version+=1
            self.assertEqual(cpu_list(x),[2])
        self.assertEqual(x.reads,2)
    def test_identity_and_new_scope(self):
        x=Tensor([1]);y=Tensor([2])
        with metadata_scope(enabled=True):
            self.assertEqual(cpu_list(x),[1])
            self.assertEqual(cpu_list(y),[2])
        with metadata_scope(enabled=True):cpu_list(x)
        self.assertEqual(x.reads,2)
    def test_exception_releases(self):
        x=Tensor([1])
        with self.assertRaises(RuntimeError):
            with metadata_scope(enabled=True):
                cpu_list(x);raise RuntimeError()
        cpu_list(x)
        self.assertEqual(x.reads,2)
    def test_nested(self):
        x=Tensor([1])
        with metadata_scope(enabled=True):
            cpu_list(x)
            with metadata_scope(enabled=True):cpu_list(x)
            cpu_list(x)
        self.assertEqual(x.reads,2)
    def test_missing_version_falls_back(self):
        x=Tensor([1]);del x._version
        with metadata_scope(enabled=True):cpu_list(x);cpu_list(x)
        self.assertEqual(x.reads,2)
    def test_invalid(self):
        with self.assertRaises(ValueError):
            with metadata_scope(enabled=1):pass
        with self.assertRaises(ValueError):cpu_list(None)

class SnapshotTests(unittest.TestCase):
    def make(self):
        from independent_step_metadata_cache import ForwardMetadataSnapshot
        from types import SimpleNamespace
        return ForwardMetadataSnapshot((("r",0,7),),source_verified_immutable=True), SimpleNamespace(indices=Tensor([1,2]))
    def test_explicit_contract(self):
        from independent_step_metadata_cache import ForwardMetadataSnapshot
        with self.assertRaises(ValueError):ForwardMetadataSnapshot((1,))
    def test_single_read(self):
        s,m=self.make()
        a=s.read(m,"indices",s.requests);a[0]=99
        self.assertEqual(s.read(m,"indices",s.requests),[1,2])
        self.assertEqual(m.indices.reads,1)
        self.assertEqual(s.reads,1)
    def test_new_tensor_rejected(self):
        s,m=self.make();s.read(m,"indices",s.requests);m.indices=Tensor([3])
        with self.assertRaises(ValueError):s.read(m,"indices",s.requests)
    def test_version_change_rejected(self):
        s,m=self.make();s.read(m,"indices",s.requests);m.indices._version+=1
        with self.assertRaises(ValueError):s.read(m,"indices",s.requests)
    def test_other_step_rejected(self):
        s,m=self.make()
        with self.assertRaises(ValueError):s.read(m,"indices",(("r",0,8),))
    def test_close(self):
        s,m=self.make();s.read(m,"indices",s.requests);s.close()
        self.assertFalse(s._entries)
        with self.assertRaises(ValueError):s.read(m,"indices",s.requests)
    def test_distinct_group(self):
        from types import SimpleNamespace
        s,m=self.make();n=SimpleNamespace(indices=Tensor([3]))
        self.assertEqual(s.read(m,"indices",s.requests),[1,2])
        self.assertEqual(s.read(n,"indices",s.requests),[3])
        self.assertEqual(s.reads,2)

class ForwardScopeTests(unittest.TestCase):
    def test_route(self):
        from independent_compact_activation import metadata_snapshot_install_route
        self.assertEqual(metadata_snapshot_install_route({}),({},False))
        self.assertEqual(metadata_snapshot_install_route({"forward_metadata_snapshot":True,"x":2}),({"x":2},True))
        with self.assertRaises(ValueError):metadata_snapshot_install_route({"forward_metadata_snapshot":1})
    def test_association_scope(self):
        from types import SimpleNamespace
        from independent_step_metadata_cache import association_cpu_list,forward_snapshot_scope
        req=(SimpleNamespace(request_id="r",rank=0,step=1),)
        m=SimpleNamespace(indices=Tensor([3]))
        with forward_snapshot_scope((("r",0,1),),enabled=True) as snapshot:
            self.assertEqual(association_cpu_list(m,"indices",req),[3])
            self.assertEqual(association_cpu_list(m,"indices",req),[3])
            self.assertEqual(snapshot.reads,1)
            self.assertEqual(snapshot.hits,1)
            with self.assertRaises(RuntimeError):
                with forward_snapshot_scope((("r",0,1),),enabled=True):pass
        association_cpu_list(m,"indices",req)
        self.assertEqual(m.indices.reads,2)
    def test_actual_inference_tensor_snapshot(self):
        import torch
        from types import SimpleNamespace
        from independent_step_metadata_cache import association_cpu_list,forward_snapshot_scope
        req=(SimpleNamespace(request_id="r",rank=0,step=1),)
        with torch.inference_mode():
            m=SimpleNamespace(indices=torch.tensor([3,4]))
            with forward_snapshot_scope((("r",0,1),),enabled=True) as snapshot:
                self.assertEqual(association_cpu_list(m,"indices",req),[3,4])
                self.assertEqual(association_cpu_list(m,"indices",req),[3,4])
                self.assertEqual(snapshot.reads,1)
