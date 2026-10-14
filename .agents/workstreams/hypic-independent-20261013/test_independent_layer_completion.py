import unittest
from independent_layer_completion import complete_layer

class CompletionBarrier(unittest.TestCase):
    def test_order_and_single_barrier(self):
        seen=[]
        n=complete_layer(range(16),execute=lambda i:seen.append(("execute",i)),
            synchronize=lambda:seen.append(("sync",None)),
            receipt=lambda i:("receipt",i),emit=seen.append)
        self.assertEqual(n,16)
        self.assertEqual(seen[:16],[("execute",i) for i in range(16)])
        self.assertEqual(seen[16],("sync",None))
        self.assertEqual(seen[17:],[("receipt",i) for i in range(16)])
    def test_execution_failure_no_receipts(self):
        seen=[]
        def execute(i):
            if i==1:raise RuntimeError("kernel enqueue failed")
        with self.assertRaises(RuntimeError):
            complete_layer(range(3),execute=execute,synchronize=lambda:seen.append("sync"),
                receipt=lambda i:i,emit=seen.append)
        self.assertEqual(seen,[])
    def test_barrier_failure_no_receipts(self):
        seen=[]
        def sync():raise RuntimeError("device completion failed")
        with self.assertRaises(RuntimeError):
            complete_layer(range(3),execute=lambda i:None,synchronize=sync,
                receipt=lambda i:i,emit=seen.append)
        self.assertEqual(seen,[])
    def test_receipt_validation_failure_no_partial_receipts(self):
        seen=[]
        def receipt(i):
            if i==1:raise ValueError("invalid identity")
            return i
        with self.assertRaises(ValueError):
            complete_layer(range(3),execute=lambda i:None,synchronize=lambda:None,
                receipt=receipt,emit=seen.append)
        self.assertEqual(seen,[])
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            complete_layer([],execute=lambda i:None,synchronize=lambda:None,
                receipt=lambda i:i,emit=lambda x:None)

if __name__=="__main__":unittest.main()

