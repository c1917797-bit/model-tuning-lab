import tempfile,threading,unittest
from types import SimpleNamespace
from pathlib import Path
import torch
from independent_c1_stage_probe import C1StageProbe,make_probe,observe_chunk_norm
from audit_c1_stage_capture import audit_capture

class StageProbeTests(unittest.TestCase):
    def test_actual_normalization_observer_and_restore(self):
        calls=[];seen=[];module=SimpleNamespace(l2norm_fwd=lambda x:(calls.append(x),x+1)[1])
        original=module.l2norm_fwd
        with observe_chunk_norm(module,lambda q,k:seen.append((q,k))):
            self.assertEqual(module.l2norm_fwd(1),2)
            self.assertEqual(module.l2norm_fwd(2),3)
            self.assertEqual(seen,[(2,3)])
        self.assertIs(module.l2norm_fwd,original)
        with self.assertRaises(RuntimeError):
            with observe_chunk_norm(module,lambda *x:None):
                raise RuntimeError("kernel failure")
        self.assertIs(module.l2norm_fwd,original)
        with self.assertRaises(ValueError):
            with observe_chunk_norm(module,lambda *x:None):module.l2norm_fwd(1)
        self.assertIs(module.l2norm_fwd,original)
    def test_normalization_callback_failure_and_nested_ownership(self):
        module=SimpleNamespace(l2norm_fwd=lambda x:x);original=module.l2norm_fwd
        def fail(*x):raise ValueError("capture failure")
        with self.assertRaises(ValueError):
            with observe_chunk_norm(module,fail):
                module.l2norm_fwd(1);module.l2norm_fwd(2)
        self.assertIs(module.l2norm_fwd,original)
        with observe_chunk_norm(module,lambda *x:None):
            with self.assertRaises(RuntimeError):
                with observe_chunk_norm(module,lambda *x:None):pass
            module.l2norm_fwd(1);module.l2norm_fwd(2)
        self.assertIs(module.l2norm_fwd,original)
    def fixture(self):
        windows=tuple(SimpleNamespace(request_id=rid,request_row=row,
            source_start=row*5+lo,source_end=row*5+hi,packed_start=row*5+lo,packed_end=row*5+hi)
            for row,rid in enumerate(("a","b")) for lo,hi in ((0,2),(2,5)))
        layout=SimpleNamespace(rank=0,step=9,request_ids=("a","b"),state_slots=(3,4),
            has_initial=(True,True),windows=windows,packed_tokens=10,
            chains=((("live",0),("cached","body"),("live",1)),
                    (("live",2),("cached","body"),("live",3))))
        plans=[SimpleNamespace(request_id=rid,tokens_sha256="body",body_start=10,body_end=22)
               for rid in ("a","b")]
        affine=SimpleNamespace(transition=torch.eye(128).expand(12,128,128).clone(),
                               zero_state=torch.zeros(12,128,128))
        body=SimpleNamespace(affine=affine)
        leased={rid:(None,3,body) for rid in ("a","b")}
        return layout,plans,leased,body
    def test_real_128_head0_packed_and_serial_pair(self):
        layout,plans,leased,body=self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            probe=C1StageProbe(layout,plans,leased,manifest_sha256="a"*64,root=Path(temp)/"capture")
            shared=SimpleNamespace(q=torch.ones(1,4,10,128,dtype=torch.bfloat16),
                                   k=torch.ones(1,4,10,128,dtype=torch.bfloat16))
            v=torch.ones(1,10,12,128,dtype=torch.bfloat16)
            g=torch.zeros(1,10,12);beta=torch.ones_like(g)
            states=torch.zeros(4,12,128,128)
            before=states.clone()
            probe.packed_inputs(shared,v,g,beta,states,states)
            probe.packed_states(states,states,{"body":body})
            result=(torch.zeros(5,12,128),states[1],torch.zeros(3,2560))
            probe.final("packed","a",result)
            for j,lo,hi in ((0,0,2),(1,2,5)):
                span=slice(lo,hi)
                probe.serial_inputs("a",lo,hi,shared.q[:,:,span].transpose(1,2),
                    shared.k[:,:,span].transpose(1,2),v[:,span],g[:,span],beta[:,span],
                    states[j:j+1],"official_chunk64")
                probe.serial_terminal("a",lo,hi,states[j])
            probe.serial_state("a","cached_composition",states[1],body)
            probe.serial_state("a","suffix_seed",states[1],body)
            probe.final("serial","a",result)
            identity=probe.capture.identity.copy();receipt=probe.seal("a")
            audited=audit_capture(receipt["root"],expected_identity=identity,
                                  manifest_sha256=receipt["capture_manifest_sha256"])
            self.assertIsNone(audited["first_observed_divergence"])
            self.assertEqual(identity["requests"],["a"])
            self.assertTrue(torch.equal(states,before))
            self.assertEqual(len(receipt["branches"]),4)
            probe.discard()
    def test_ineligible_selection_and_outside_failed_request(self):
        layout,plans,leased,body=self.fixture();layer=SimpleNamespace(prefix="other")
        self.assertIsNone(make_probe(layer,layout,plans,leased,None))
        layer.prefix="language_model.model.layers.0.linear_attn";layout.packed_tokens=12001
        self.assertIsNone(make_probe(layer,layout,plans,leased,None))
        layout.packed_tokens=10
        with self.assertRaises(ValueError):make_probe(layer,layout,plans,leased,lambda e:None)
        with tempfile.TemporaryDirectory() as temp:
            p=C1StageProbe(layout,plans,leased,manifest_sha256="a"*64,root=Path(temp)/"capture")
            self.assertFalse(p.seal("b")["complete"])
            self.assertFalse((Path(temp)/"capture").exists())
    def test_other_thread_not_captured(self):
        module=SimpleNamespace(l2norm_fwd=lambda x:x);seen=[]
        with observe_chunk_norm(module,lambda *x:seen.append(x)):
            thread=threading.Thread(target=lambda:[module.l2norm_fwd(i) for i in range(3)])
            thread.start();thread.join()
            module.l2norm_fwd(4);module.l2norm_fwd(5)
        self.assertEqual(seen,[(4,5)])

if __name__=="__main__":unittest.main()
