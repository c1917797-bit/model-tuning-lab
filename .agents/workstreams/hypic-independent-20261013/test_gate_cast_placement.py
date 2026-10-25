"""Focused gate-placement equality/source/rollback controls, CPU only."""
from contextvars import ContextVar
import hashlib
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest import mock
import torch
import independent_recurrent_boundary as boundary
import independent_c1_short_prefix as prefix
import independent_c1_short_suffix as suffix
import independent_gate_cast_delivery as delivery

torch.set_num_threads(1)
ROOT=Path(__file__).resolve().parent
OLD=subprocess.check_output(["git","show",
    "880c325f463a016828d23a3e2a24c025b7918a55:.agents/workstreams/hypic-independent-20261013/independent_recurrent_boundary.py"],
    cwd=ROOT,text=True)
scope={};exec(compile(OLD,"<frozen-original-boundary>","exec"),scope)
original=scope["recurrent_boundary"]

def inputs(length,dtype,*,noncontiguous=False,actual_shape=False):
    torch.manual_seed(3300+length)
    hk,hv,dk,dv=(4,12,128,128)if actual_shape else(2,4,8,7)
    def random(shape):
        if noncontiguous:
            return(torch.randn(*shape[:-1],shape[-1]*2,dtype=dtype)*.1)[...,::2]
        return torch.randn(*shape,dtype=dtype)*.1
    q=random((1,length,hk,dk));k=random(q.shape)
    v=random((1,length,hv,dv))
    g=-torch.rand(1,length,hv,dtype=torch.float64 if dtype==torch.float64 else torch.float32)*.2
    beta=torch.sigmoid(random((1,length,hv)))
    initial=random((1,hv,dk,dv)).to(torch.float64 if dtype==torch.float64 else torch.float32)
    return q,k,v,g,beta,initial

def bindings():
    return{m.__name__:hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()
           for m in(boundary,prefix,suffix,delivery)}

class NumericGatePlacement(unittest.TestCase):
    def test_default_exactly_matches_frozen_original(self):
        for dtype in(torch.float64,torch.float32,torch.bfloat16):
            with self.subTest(dtype=dtype):
                args=inputs(8,dtype)
                for x,y in zip(original(*args),boundary.recurrent_boundary(*args)):
                    self.assertTrue(torch.equal(x,y))
    def test_hoisted_exact_values_lengths_dtypes_and_strides(self):
        for length in(1,8,64):
            for dtype in(torch.float64,torch.float32,torch.bfloat16):
                with self.subTest(length=length,dtype=dtype):
                    args=inputs(length,dtype,noncontiguous=True)
                    before=[x.clone()for x in args]
                    a=[];b=[]
                    expected=boundary.recurrent_boundary(*args,gate_cast_observer=a.append)
                    actual=boundary.recurrent_boundary(*args,hoist_gate_casts=True,gate_cast_observer=b.append)
                    for x,y in zip(expected,actual):self.assertTrue(torch.equal(x,y))
                    for x,y in zip(args,before):self.assertTrue(torch.equal(x,y))
                    self.assertEqual(a[0]["gate_conversion_dispatch_sites"],2*length)
                    self.assertEqual(b[0]["gate_conversion_dispatch_sites"],2)
                    self.assertEqual(a[0]["gate_conversion_elements"],b[0]["gate_conversion_elements"])
    def test_actual_state_shape_bf16(self):
        args=inputs(64,torch.bfloat16,actual_shape=True)
        for x,y in zip(boundary.recurrent_boundary(*args),
                       boundary.recurrent_boundary(*args,hoist_gate_casts=True)):
            self.assertTrue(torch.equal(x,y))
    def test_independent_tensor_to_invocation_count(self):
        args=inputs(8,torch.bfloat16);old=torch.Tensor.to;counts=[]
        for hoist in(False,True):
            calls=[]
            def tracked(t,*a,**kw):
                calls.append((tuple(t.shape),t.dtype))
                return old(t,*a,**kw)
            with mock.patch.object(torch.Tensor,"to",new=tracked):
                boundary.recurrent_boundary(*args,hoist_gate_casts=hoist)
            counts.append(len(calls))
        self.assertEqual(counts[0]-counts[1],14)
    def test_input_observer_preserved(self):
        args=inputs(8,torch.bfloat16);a=[];b=[]
        boundary.recurrent_boundary(*args,input_observer=lambda **v:a.append(v))
        boundary.recurrent_boundary(*args,hoist_gate_casts=True,input_observer=lambda **v:b.append(v))
        self.assertEqual(set(a[0]),set(b[0]))
        for key in a[0]:
            if isinstance(a[0][key],torch.Tensor):self.assertTrue(torch.equal(a[0][key],b[0][key]))
            else:self.assertEqual(a[0][key],b[0][key])
    def test_invalid_controls(self):
        args=inputs(1,torch.float32)
        with self.assertRaises(ValueError):boundary.recurrent_boundary(*args,hoist_gate_casts=1)
        with self.assertRaises(ValueError):boundary.recurrent_boundary(*args,gate_cast_observer=1)

class GateDelivery(unittest.TestCase):
    def setUp(self):
        self.original=boundary.recurrent_boundary
        self.context=ContextVar("test-selected-wave",default=None)
        self.helper=SimpleNamespace(CURRENT_COMPACT_MODEL=self.context)
    def tearDown(self):
        prefix.recurrent_boundary=self.original;suffix.recurrent_boundary=self.original
    def install(self,hoisted=False):
        events=[]
        stop=delivery.install_gate_cast_placement(enabled=True,hoisted=hoisted,
                                                 emit=events.append,source_bindings=bindings())
        return stop,events
    def test_disabled_no_import_or_alias_change(self):
        with mock.patch.object(delivery.importlib,"import_module",side_effect=AssertionError("disabled import")):
            delivery.install_gate_cast_placement()()
        self.assertIs(prefix.recurrent_boundary,self.original)
        with self.assertRaises(ValueError):delivery.install_gate_cast_placement(hoisted=True)
    def test_real_alias_dispatch_evidence_and_rollback(self):
        args=inputs(8,torch.bfloat16)
        for hoisted in(False,True):
            stop,events=self.install(hoisted)
            selection=SimpleNamespace(plans=[SimpleNamespace(rank=2,step=9,request_id="one")])
            with mock.patch.dict(sys.modules,{"independent_compact_model_hook":self.helper}):
                token=self.context.set(selection)
                try:
                    for module in(prefix,suffix):
                        for x,y in zip(module.recurrent_boundary(*args),self.original(*args)):
                            self.assertTrue(torch.equal(x,y))
                finally:self.context.reset(token)
            receipts=[e for e in events if e["event"]=="c1_gate_cast_placement_observed"]
            self.assertEqual([e["phase"]for e in receipts],["prefix","suffix"])
            self.assertTrue(all(e["gate_conversion_dispatch_sites"]==(2 if hoisted else 16)for e in receipts))
            self.assertTrue(all((e["rank"],e["step"],e["request_ids"])==(2,9,["one"])for e in receipts))
            stop()
            self.assertIs(prefix.recurrent_boundary,self.original)
            self.assertIs(suffix.recurrent_boundary,self.original)
    def test_bad_source_or_duplicate_install_fail_closed(self):
        b=bindings();b[boundary.__name__]="0"*64
        with self.assertRaises(ValueError):delivery.install_gate_cast_placement(enabled=True,emit=lambda e:None,source_bindings=b)
        self.assertIs(prefix.recurrent_boundary,self.original)
        stop,events=self.install()
        try:
            with self.assertRaises(RuntimeError):self.install()
        finally:stop()
    def test_foreign_alias_not_overwritten(self):
        stop,events=self.install()
        foreign=lambda:None;prefix.recurrent_boundary=foreign
        with self.assertRaises(ValueError):stop()
        self.assertIs(prefix.recurrent_boundary,foreign)
    def test_install_emission_failure_unwinds(self):
        def fail(e):raise OSError("evidence unavailable")
        with self.assertRaises(OSError):delivery.install_gate_cast_placement(enabled=True,emit=fail,source_bindings=bindings())
        self.assertIs(prefix.recurrent_boundary,self.original)
        self.assertIs(suffix.recurrent_boundary,self.original)
    def test_no_selected_context_fails(self):
        stop,events=self.install()
        try:
            with mock.patch.dict(sys.modules,{"independent_compact_model_hook":self.helper}):
                with self.assertRaises(ValueError):prefix.recurrent_boundary(*inputs(1,torch.float32))
        finally:stop()

    def test_failed_private_shape_check_rejects_before_return(self):
        stop,events=self.install(True)
        selection=SimpleNamespace(plans=[SimpleNamespace(rank=0,step=1,request_id="one")])
        try:
            with mock.patch.dict(sys.modules,{"independent_compact_model_hook":self.helper}):
                token=self.context.set(selection)
                try:
                    with mock.patch.object(torch,"equal",return_value=False):
                        with self.assertRaises(ValueError):prefix.recurrent_boundary(*inputs(1,torch.float32))
                finally:self.context.reset(token)
            self.assertTrue(any(e.get("event")=="c1_gate_cast_first_shape_checked"and not e["passed"]for e in events))
        finally:stop()

if __name__=="__main__":unittest.main()
