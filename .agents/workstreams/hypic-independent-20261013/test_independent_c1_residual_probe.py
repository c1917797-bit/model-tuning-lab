import tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
import torch
import test_independent_c1_stage_probe as fixture_module
from independent_c1_stage_probe import C1StageProbe
from independent_native_decode_prepare import shadow_metrics
from independent_compact_activation import c1_install_route
from audit_c1_stage_capture import audit_capture

class ResidualProbeTests(unittest.TestCase):
    def fill(self,p):
        layout,plans,leased,body=fixture_module.StageProbeTests().fixture()
        q=torch.arange(4,dtype=torch.bfloat16).reshape(1,4,1,1).expand(1,4,10,128).clone()
        shared=SimpleNamespace(q=q,k=q.clone())
        v=torch.ones(1,10,12,128,dtype=torch.bfloat16)
        g=torch.zeros(1,10,12);beta=torch.ones_like(g);states=torch.zeros(4,12,128,128)
        p.packed_inputs(shared,v,g,beta,states,states)
        p.packed_states(states,states,{"body":body})
        reference=(torch.zeros(5,12,128),states[1].clone(),torch.zeros(3,2560))
        actual=tuple(x.clone() for x in reference);actual[1][8,3,7]=.25
        p.final("packed","a",actual)
        # Serialized short recurrence has already expanded Q/K to12 heads.
        expanded=shared.q.transpose(1,2).repeat_interleave(3,dim=2)
        for j,lo,hi in ((0,0,2),(1,2,5)):
            span=slice(lo,hi)
            p.serial_inputs("a",lo,hi,expanded[:,span],expanded[:,span],v[:,span],
                g[:,span],beta[:,span],states[j:j+1],"independent_recurrent_le64")
            p.serial_terminal("a",lo,hi,states[j])
        p.serial_state("a","cached_composition",states[1],body)
        p.serial_state("a","suffix_seed",states[1],body)
        p.final("serial","a",reference)
        # Mutate original after every stage; independent clones must retain zeros.
        states.add_(100)
        return actual,reference

    def probe(self,temp):
        layout,plans,leased,body=fixture_module.StageProbeTests().fixture()
        return C1StageProbe(layout,plans,leased,manifest_sha256="a"*64,
            root=Path(temp)/"capture",head_policy="max_state_residual")

    def test_actual_nonzero_head_failure_selected_and_sealed(self):
        with tempfile.TemporaryDirectory() as temp:
            p=self.probe(temp);actual,reference=self.fill(p)
            self.assertFalse(p.capture.records);self.assertGreater(p.deferred.bytes,0)
            metric=shadow_metrics(actual[1],reference[1])
            receipt=p.seal("a",actual_state=actual[1],reference_state=reference[1],
                           reported_max=metric["max_scaled"])
            identity=p.capture.identity
            self.assertEqual(identity["head_indices"],dict(query=2,key=2,value=8))
            self.assertEqual(identity["head_selection"]["key_coordinate"],3)
            report=audit_capture(receipt["root"],expected_identity=identity,
                                 manifest_sha256=receipt["capture_manifest_sha256"])
            self.assertEqual(report["first_observed_divergence"]["stage"],"final")
            self.assertEqual(receipt["records"],12)
            self.assertTrue(p.deferred.closed);self.assertEqual(p.deferred.bytes,0)

    def test_passed_call_discard_no_files(self):
        with tempfile.TemporaryDirectory() as temp:
            p=self.probe(temp);self.fill(p);p.discard()
            self.assertTrue(p.deferred.closed);self.assertTrue(p.capture.closed)
            self.assertFalse(list(Path(temp).iterdir()))

    def test_bad_report_clears_all_without_files(self):
        with tempfile.TemporaryDirectory() as temp:
            p=self.probe(temp);actual,reference=self.fill(p)
            with self.assertRaises(ValueError):
                p.seal("a",actual_state=actual[1],reference_state=reference[1],reported_max=1.)
            self.assertTrue(p.deferred.closed);self.assertTrue(p.capture.closed)
            self.assertFalse(list(Path(temp).iterdir()))

    def test_defaultoff_route_and_strict_policy(self):
        _,fn,_=c1_install_route({})
        self.assertEqual(fn.c1_first_divergence_head_policy,"head0")
        config=dict(native_decode_batch=True,c1_layer_completion_barrier=True,
            c1_layer_shadow_validation=True,c1_packed_wave=True,c1_first_divergence=True,
            c1_first_divergence_head_policy="max_state_residual")
        rest,fn,_=c1_install_route(config)
        self.assertEqual(rest,{});self.assertEqual(fn.c1_first_divergence_head_policy,"max_state_residual")
        for value in (None,1,"other"):
            with self.assertRaises(ValueError):
                c1_install_route({**config,"c1_first_divergence_head_policy":value})
        with self.assertRaises(ValueError):
            c1_install_route({"c1_first_divergence_head_policy":"max_state_residual"})

if __name__=="__main__":unittest.main()
