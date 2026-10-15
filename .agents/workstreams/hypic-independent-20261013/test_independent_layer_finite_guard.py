import unittest
from unittest.mock import patch
import torch
from independent_layer_finite_guard import LayerFiniteGuard


class LayerFiniteGuardTests(unittest.TestCase):
    def test_finite_one_scalar_and_input_unchanged(self):
        tensors=[torch.randn(2,3) for _ in range(12)]
        originals=[t.clone() for t in tensors]
        gate=LayerFiniteGuard()
        for i in range(0,12,3):gate.collect(*tensors[i:i+3])
        original=torch.Tensor.item
        calls=[]
        def item(t,*args):
            calls.append(t.numel())
            return original(t,*args)
        with patch.object(torch.Tensor,"item",item):
            self.assertEqual(gate.validate(),12)
        self.assertEqual(calls,[1])
        for a,b in zip(tensors,originals):self.assertTrue(torch.equal(a,b))

    def test_nonfinite_blocks_commit_and_closes(self):
        for bad in (float("nan"),float("inf"),float("-inf")):
            gate=LayerFiniteGuard()
            output=torch.ones(2)
            state=torch.tensor([bad])
            target=torch.zeros(2)
            gate.collect(output,state)
            with self.assertRaises(ValueError):
                gate.validate()
                target.copy_(output)
            self.assertTrue(torch.equal(target,torch.zeros(2)))
            with self.assertRaises(RuntimeError):gate.validate()

    def test_collect_keeps_latest_private_values(self):
        x=torch.ones(3);gate=LayerFiniteGuard();gate.collect(x)
        x[1]=float("nan")
        with self.assertRaises(ValueError):gate.validate()

    def test_bounds_and_empty(self):
        for n in (0,513,True,1.5):
            with self.assertRaises(ValueError):LayerFiniteGuard(max_tensors=n)
        gate=LayerFiniteGuard(max_tensors=1);gate.collect(torch.ones(1))
        with self.assertRaises(ValueError):gate.collect(torch.ones(1))
        self.assertEqual(gate.validate(),1)
        with self.assertRaises(ValueError):LayerFiniteGuard().validate()

    def test_invalid_and_closed_collection(self):
        for x in (None,torch.empty(0),torch.empty(1,device="meta")):
            with self.assertRaises(ValueError):LayerFiniteGuard().collect(x)
        gate=LayerFiniteGuard();gate.collect(torch.ones(1));gate.validate()
        with self.assertRaises(RuntimeError):gate.collect(torch.ones(1))


if __name__=="__main__":unittest.main()
