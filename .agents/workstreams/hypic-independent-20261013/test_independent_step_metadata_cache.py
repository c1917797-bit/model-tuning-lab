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
