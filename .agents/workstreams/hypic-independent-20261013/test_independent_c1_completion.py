import sys,types,hashlib,unittest
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import ExitStack
import torch
from independent_compact_activation import c1_install_route
from independent_compact_linear import execute_compact_linear
from independent_layer_finite_guard import LayerFiniteGuard
from independent_c1_completion_shadow import verify_completion_shadow
import test_independent_compact_linear as compact_fixture


class CompletionControls(unittest.TestCase):
    def test_route_default_off_explicit_and_ambiguous(self):
        calls=[]
        def install(stage,**kw):calls.append(kw);return lambda:None
        with patch("independent_compact_gdn_hook.install_compact_gdn",install):
            cfg,fn,on=c1_install_route({"x":1});fn(None)
            self.assertFalse(calls[-1]["layer_completion"])
            cfg,fn,on=c1_install_route({"x":1,"c1_layer_completion_barrier":True,
                                      "c1_layer_shadow_validation":True})
            self.assertEqual(cfg,{"x":1});fn(None)
            self.assertTrue(calls[-1]["layer_completion"]);self.assertTrue(calls[-1]["layer_shadow"])
            for key in ("c1_layer_completion_barrier","c1_layer_shadow_validation"):
                for value in (None,1,0,"true"):
                    with self.assertRaises(ValueError):c1_install_route({key:value})
            with self.assertRaises(ValueError):c1_install_route({"c1_layer_shadow_validation":True})

    def test_same_compact_math_deferred_finite(self):
        f=compact_fixture.CompactLinearTests().fixture()
        k,v,b,g,state,plan,identity,material,calls,live=f
        expected=execute_compact_linear(material,identity,plan,state,torch.zeros(3,6,dtype=state.dtype),run_live=live)
        gate=LayerFiniteGuard()
        actual=execute_compact_linear(material,identity,plan,state,torch.zeros(3,6,dtype=state.dtype),
                                      run_live=live,finite_check=gate.collect)
        self.assertEqual(gate.validate(),3)
        events=[];verify_completion_shadow(actual,expected,plan,"layer",events.append)
        self.assertTrue(events[0]["passed"])
        for x,y in zip(actual,expected):torch.testing.assert_close(x,y)

    def test_shadow_failure_not_accepted(self):
        p=SimpleNamespace(request_id="r",rank=0,step=1)
        for actual in ((torch.zeros(2),)*3,(torch.full((2,),float("nan")),)*3):
            events=[]
            with self.assertRaises(ValueError):
                verify_completion_shadow(actual,(torch.ones(2),)*3,p,"layer",events.append)
            self.assertFalse(events and events[-1]["passed"])

    def hook_case(self,completion=True,fail_second=False,nonfinite=False,packed=False,
                  fail_shadow=False,fail_preparation=False,probe=False,fail_capture=False,
                  residual_policy=False):
        from independent_compact_gdn_hook import install_compact_gdn
        from independent_compact_material_pool import CompactLinearMaterialPool
        from independent_compact_model_hook import CURRENT_COMPACT_MODEL
        from independent_runner_context import CURRENT_REQUEST_SLICES
        from independent_mixed_query_plan import NativeQueryPlan
        class Layer:
            def _forward_core(self,*args):return "original"
        layer=Layer();layer.prefix="l"
        layer.kv_cache=(torch.zeros(2,3,6),torch.zeros(2,2,3,5))
        stage=SimpleNamespace(compact_store=CompactLinearMaterialPool(1024),boundary=8)
        plans=tuple(NativeQueryPlan(str(i),0,4,i*2,0,2,"prefill") for i in range(2))
        requests=tuple(SimpleNamespace(request_id=p.request_id,rank=p.rank,step=p.step,
            token_start=p.token_start,scheduled_tokens=p.scheduled_tokens) for p in plans)
        assoc=tuple(SimpleNamespace(state_slot=i,has_initial_state=True) for i in range(2))
        events=[];sync=[];spans=[];core=torch.zeros(4,2,3);probe_closed=[]
        class FakeProbe:
            def discard(self):probe_closed.append(True)
            def serial_inputs(self,*args,**kw):pass
            def serial_terminal(self,*args,**kw):pass
            def serial_state(self,*args,**kw):pass
            def final(self,*args,**kw):pass
            def seal(self,rid,**values):
                if residual_policy:
                    if set(values)!={"actual_state","reference_state","reported_max"}:
                        raise AssertionError("actual failed state/max not passed to observer")
                    if values["actual_state"].shape!=values["reference_state"].shape:
                        raise AssertionError("state pair shape drift")
                if fail_capture:raise ValueError("capture write failure")
                return {"complete":True}
        def emit(event):
            if event["event"]=="c1_layer_precommit_validated":
                self.assertEqual(float(layer.kv_cache[1].abs().sum()),0)
                self.assertEqual(float(core.abs().sum()),0)
            events.append(event)
        def boundary(layer,projected,b,a,conv,**kw):
            spans.append(kw["synchronize"])
            def run(state):
                if fail_second and len(spans)==2:raise RuntimeError("late request failure")
                out=torch.ones(projected.shape[0],2,3)
                if nonfinite and len(spans)==2:out[0,0,0]=float("nan")
                return out,torch.ones_like(state),torch.ones_like(conv)
            return run
        def packed_prepare(layer,stage,plans,associations,mixed_qkv,b,a,leases,backend_state,**kw):
            if fail_preparation:raise RuntimeError('packed preparation failure')
            if probe:
                backend_state['probe']=FakeProbe()
                leases.callback(backend_state['probe'].discard)
            results={}
            for row,plan in enumerate(plans):
                out=torch.ones(2,2,3)*(2 if fail_shadow and row==1 else 1)
                state=torch.ones(2,5,3);tail=torch.ones(3,6)
                kw['finite_check'](out,state,tail)
                results[plan.request_id]=(out,state,tail)
            return results,{},SimpleNamespace(windows=(1,2),packed_tokens=4)
        module=types.ModuleType("fake");module.QwenGatedDeltaNetAttention=Layer
        context=types.ModuleType("vllm.forward_context")
        context.get_forward_context=lambda:SimpleNamespace(attn_metadata={"l":object()})
        original=Layer._forward_core
        with ExitStack() as stack:
            stack.enter_context(patch.dict(sys.modules,{
                "vllm.forward_context":context,
                "vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn":module}))
            stack.enter_context(patch("independent_compact_gdn_hook.hashlib.sha256",
                return_value=SimpleNamespace(hexdigest=lambda:"d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816")))
            stack.enter_context(patch("independent_runtime_adapter.associate_native_mixed_linear",return_value=assoc))
            stack.enter_context(patch("independent_linear_map.validate_linear_plan_associations",side_effect=lambda p,a:a))
            stack.enter_context(patch("independent_native_boundary.make_boundary_runner",boundary))
            stack.enter_context(patch("independent_native_decode_prepare.prepare_native_decode",return_value={}))
            stack.enter_context(patch("independent_c1_packed_prepare.prepare_packed_layer",packed_prepare))
            stack.enter_context(patch.object(torch,"npu",SimpleNamespace(synchronize=lambda:sync.append("commit")),create=True))
            stop=install_compact_gdn(stage,enabled=True,emit=emit,layer_completion=completion,
                native_decode_batch=packed,layer_shadow=packed,packed_wave=packed,
                first_divergence=probe,
                first_divergence_head_policy="max_state_residual" if residual_policy else "head0")
            token=CURRENT_COMPACT_MODEL.set(SimpleNamespace(plans=plans))
            token2=CURRENT_REQUEST_SLICES.set(requests)
            try:
                if fail_second or nonfinite or fail_shadow or fail_preparation:
                    with self.assertRaises((RuntimeError,ValueError)):
                        layer._forward_core(torch.ones(4,6),torch.ones(4,2),torch.ones(4,2),core)
                    self.assertEqual(float(core.abs().sum()),0)
                    self.assertEqual(float(layer.kv_cache[0].abs().sum()),0)
                    self.assertEqual(float(layer.kv_cache[1].abs().sum()),0)
                    self.assertFalse(sync)
                    self.assertFalse(any(e["event"].endswith("completed") for e in events))
                else:
                    layer._forward_core(torch.ones(4,6),torch.ones(4,2),torch.ones(4,2),core)
                    self.assertTrue(torch.equal(core,torch.ones_like(core)))
                    self.assertEqual(sync,["commit"])
                    self.assertEqual(spans,[True]*2 if packed else [not completion]*2)
                    self.assertEqual(sum(e["event"]=="c1_layer_precommit_validated" for e in events),int(completion))
            finally:
                CURRENT_REQUEST_SLICES.reset(token2);CURRENT_COMPACT_MODEL.reset(token);stop()
            self.assertIs(Layer._forward_core,original)
            if probe:self.assertTrue(probe_closed)

    def test_hook_collects_all_then_commit_and_uninstall(self):self.hook_case()
    def test_hook_late_failure_no_actual_writes(self):self.hook_case(fail_second=True)
    def test_hook_nonfinite_no_actual_writes(self):self.hook_case(nonfinite=True)
    def test_hook_default_serial_path_unchanged(self):self.hook_case(completion=False)
    def test_packed_hook_shadow_all_then_commit(self):self.hook_case(packed=True)
    def test_packed_hook_late_shadow_failure_zero_writes(self):self.hook_case(packed=True,fail_shadow=True)
    def test_packed_hook_preparation_failure_zero_writes(self):self.hook_case(packed=True,fail_preparation=True)
    def test_probe_shadow_failure_no_writes_and_closed(self):
        self.hook_case(packed=True,fail_shadow=True,probe=True)
    def test_probe_write_failure_no_writes_and_closed(self):
        self.hook_case(packed=True,fail_shadow=True,probe=True,fail_capture=True)
    def test_residual_observer_gets_actual_pair_before_zero_writes(self):
        self.hook_case(packed=True,fail_shadow=True,probe=True,residual_policy=True)
    def test_residual_observer_seal_failure_releases_without_writes(self):
        self.hook_case(packed=True,fail_shadow=True,probe=True,residual_policy=True,fail_capture=True)
    def test_probe_route_default_and_strict(self):
        _,install,_=c1_install_route({})
        self.assertFalse(install.c1_first_divergence)
        config=dict(c1_packed_wave=True,native_decode_batch=True,
            c1_layer_completion_barrier=True,c1_layer_shadow_validation=True,
            c1_first_divergence=True)
        remaining,install,_=c1_install_route(config)
        self.assertEqual(remaining,{})
        self.assertTrue(install.c1_first_divergence)
        for invalid in (1,None,"true"):
            with self.assertRaises(ValueError):c1_install_route({**config,"c1_first_divergence":invalid})
        with self.assertRaises(ValueError):c1_install_route({"c1_first_divergence":True})

    def test_packed_route_requires_explicit_controls(self):
        cfg,install,_=c1_install_route({'c1_packed_wave':True,'native_decode_batch':True,
            'c1_layer_completion_barrier':True,'c1_layer_shadow_validation':True})
        self.assertTrue(install.c1_packed_wave);self.assertEqual(cfg,{})
        for config in ({'c1_packed_wave':True},{'c1_packed_wave':1},
                       {'c1_packed_wave':'true'},{'c1_packed_wave':None}):
            with self.assertRaises(ValueError):c1_install_route(config)


if __name__=="__main__":unittest.main()
