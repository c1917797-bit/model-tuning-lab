"""CPU controls for deferred actual-head capture; not NPU acceptance."""
import unittest
from unittest.mock import patch
import torch
from independent_c1_deferred_capture import (
    DeferredHeadCapture,sampled_head,residual_selection,selected_deferred_capture)
from independent_native_decode_prepare import shadow_metrics

def inputs(expanded=False):
    h=12 if expanded else 4
    return dict(q=torch.arange(2*h*3,dtype=torch.float32).reshape(2,h,3),
        k=torch.arange(2*h*3,dtype=torch.float32).reshape(2,h,3)+100,
        v=torch.arange(2*12*3,dtype=torch.float32).reshape(2,12,3),
        g=torch.zeros(2,12),beta=torch.ones(2,12),initial=torch.zeros(12,3,3))

def add(buffer,**overrides):
    args=dict(side="packed",request_id="request",stage="inputs",window="prefix",
              source_start=0,source_end=2,tensors=inputs())
    args.update(overrides);buffer.add(**args)

class DeferredTests(unittest.TestCase):
    def test_default_disabled(self):
        self.assertIsNone(selected_deferred_capture())
        with self.assertRaises(ValueError):selected_deferred_capture(enabled=1)

    def test_grouped_native_nonzero_head(self):
        x=inputs();y=sampled_head("inputs",x,8)
        self.assertTrue(torch.equal(y["q"],x["q"][:,2]))
        self.assertTrue(torch.equal(y["v"],x["v"][:,8]))

    def test_expanded_recurrent_nonzero_head(self):
        x=inputs(True);y=sampled_head("inputs",x,8)
        self.assertTrue(torch.equal(y["q"],x["q"][:,8]))

    def test_state_and_full_conv(self):
        x=dict(state=torch.arange(108.).reshape(12,3,3),
               output=torch.arange(72.).reshape(2,12,3),conv=torch.ones(3,2560))
        y=sampled_head("final",x,11)
        self.assertTrue(torch.equal(y["state"],x["state"][11]))
        self.assertIs(y["conv"],x["conv"])

    def test_clone_no_alias(self):
        b=DeferredHeadCapture();x=inputs();original=x["q"].clone();add(b,tensors=x)
        x["q"].add_(1000)
        self.assertTrue(torch.equal(b.records[0]["tensors"]["q"],original))
        self.assertFalse(b.records[0]["tensors"]["q"].requires_grad)
        b.discard();self.assertEqual((b.bytes,len(b.records)),(0,0));self.assertTrue(b.closed)

    def test_all_bytes_checked_before_any_clone(self):
        b=DeferredHeadCapture(max_bytes=1)
        with patch.object(torch.Tensor,"clone",side_effect=AssertionError("allocation occurred")):
            with self.assertRaisesRegex(ValueError,"before allocation"):add(b)
        self.assertEqual(b.records,[])

    def test_record_and_duplicate_bounds(self):
        b=DeferredHeadCapture(max_records=1);add(b)
        with self.assertRaisesRegex(ValueError,"duplicate"):add(b)
        self.assertTrue(b.closed);self.assertEqual(b.records,[])
        b=DeferredHeadCapture(max_records=1);add(b)
        with self.assertRaisesRegex(ValueError,"record bound"):add(b,window="suffix")
        self.assertTrue(b.closed);self.assertEqual(b.bytes,0)

    def test_exact_guard_argmax(self):
        reference=torch.full((12,3,5),2.);actual=reference.clone();actual[8,2,4]+=0.25
        metric=shadow_metrics(actual,reference)
        s=residual_selection(actual,reference,metric["max_scaled"])
        self.assertEqual((s["value_head"],s["key_coordinate"],s["value_coordinate"]),(8,2,4))
        with self.assertRaises(ValueError):residual_selection(actual,reference,1.)
        with self.assertRaises(ValueError):residual_selection(reference,reference,0.)

    def test_nonfinite_rejected(self):
        x=torch.zeros(12,3,3);x[0,0,0]=float("nan")
        with self.assertRaises(ValueError):residual_selection(x,torch.zeros_like(x),2.)

    def test_flush_selected_and_cleanup(self):
        b=DeferredHeadCapture();x=inputs();add(b,tensors=x)
        class Sink:
            def add(self,**kw):self.kw=kw
        sink=Sink();b.flush_to(sink,8)
        self.assertTrue(torch.equal(sink.kw["tensors"]["q"],x["q"][:,2]))
        self.assertTrue(b.closed);self.assertEqual(b.bytes,0)

    def test_sink_exception_cleanup(self):
        b=DeferredHeadCapture();add(b)
        class Sink:
            def add(self,**kw):raise RuntimeError("injected sink failure")
        with self.assertRaises(RuntimeError):b.flush_to(Sink(),8)
        self.assertTrue(b.closed);self.assertEqual(b.records,[])

    def test_allocation_exception_cleanup(self):
        b=DeferredHeadCapture()
        with patch.object(torch.Tensor,"clone",side_effect=RuntimeError("injected allocation")):
            with self.assertRaises(RuntimeError):add(b)
        self.assertTrue(b.closed);self.assertEqual(b.bytes,0)

    def test_bad_geometry_rejected(self):
        x=inputs();x["q"]=torch.zeros(2,5,3)
        with self.assertRaises(ValueError):sampled_head("inputs",x,8)
        with self.assertRaises(ValueError):sampled_head("inputs",inputs(),12)

if __name__=="__main__":unittest.main()
