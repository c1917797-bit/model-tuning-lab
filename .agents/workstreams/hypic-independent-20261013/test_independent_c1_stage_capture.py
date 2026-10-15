import copy,hashlib,json,tempfile,unittest
from pathlib import Path
import torch
from independent_c1_stage_capture import FirstDivergenceCapture,selected_capture,REQUIRED
from audit_c1_stage_capture import audit_capture

class StageCaptureTests(unittest.TestCase):
    def identity(self):
        return dict(rank=0,pid=123,layer="language_model.model.layers.0.linear_attn",
            step=9,manifest_sha256="a"*64,requests=["r1"],generations={"r1":3})
    def fill(self,c,*,delta=False):
        for side in ("packed","serial"):
            for stage in ("inputs","prefix_terminal","cached_composition","suffix_seed","final"):
                tensors={k:torch.ones(2,2) for k in REQUIRED[stage]}
                if delta and side=="packed" and stage=="prefix_terminal":tensors["state"]+=.1
                c.add(side=side,request_id="r1",stage=stage,window="prefix",
                      source_start=2,source_end=4,tensors=tensors)
    def seal(self,parent,*,delta=False):
        c=FirstDivergenceCapture(self.identity());self.fill(c,delta=delta)
        return c,c.seal_failure(Path(parent)/"capture",failed_request_id="r1")
    def audit(self,receipt,identity=None):
        return audit_capture(receipt["root"],expected_identity=identity or self.identity(),
                             manifest_sha256=receipt["manifest_sha256"])
    def test_independent_fp64_recurrence(self):
        import numpy as np
        from audit_c1_stage_capture import sampled_head_fp64_recurrence
        k=np.eye(2);v=np.array([[2.,0.],[0.,4.]])
        out,state=sampled_head_fp64_recurrence(k,k,v,np.zeros(2),np.array([.5,.25]),np.zeros((2,2)))
        np.testing.assert_allclose(state,np.eye(2))
        np.testing.assert_allclose(out,np.eye(2)*2**-.5)
        with self.assertRaises(ValueError):
            sampled_head_fp64_recurrence(k,k,v,np.zeros(1),np.ones(2),np.zeros((2,2)))

    def test_default_disabled_no_identity_or_io(self):
        self.assertIsNone(selected_capture(None))
        with self.assertRaises(ValueError):selected_capture(None,enabled=1)
    def test_cpu_snapshot_independent_from_input_mutation(self):
        c=FirstDivergenceCapture(self.identity());x=torch.ones(2,2,requires_grad=True)
        c.add(side="packed",request_id="r1",stage="prefix_terminal",window="prefix",
              source_start=2,source_end=4,tensors={"state":x})
        with torch.no_grad():x.zero_()
        self.assertEqual(c.records[0]["tensors"]["state"].sum(),4)
        c.discard();self.assertFalse(c.records)
        with self.assertRaises(ValueError):c.seal_failure(Path("/tmp/absent"),failed_request_id="r1")
    def test_all_stages_and_first_observed_divergence(self):
        with tempfile.TemporaryDirectory() as temp:
            c,r=self.seal(temp,delta=True);a=self.audit(r)
            self.assertEqual(a["first_observed_divergence"]["stage"],"prefix_terminal")
            self.assertEqual(a["first_observed_divergence"]["tensor"],"state")
            self.assertTrue(c.closed);self.assertFalse(c.records)
            with self.assertRaises(ValueError):self.audit(r,{**self.identity(),"step":10})
    def test_identical_samples_not_full_equivalence(self):
        with tempfile.TemporaryDirectory() as temp:
            _,r=self.seal(temp);a=self.audit(r)
            self.assertIsNone(a["first_observed_divergence"])
            self.assertIn("not full tensors",a["scope"])
    def test_identity_rejects(self):
        i=self.identity()
        for change in (dict(rank=1),dict(rank=False),dict(step=-1),dict(pid=0),
                       dict(layer="other"),dict(manifest_sha256="bad"),
                       dict(requests=["r1","r1"]),dict(generations={"r1":0}),
                       dict(requests=["a","b","c"])):
            with self.assertRaises(ValueError):FirstDivergenceCapture({**i,**change})
    def test_bounds_and_failure_atomic_add(self):
        c=FirstDivergenceCapture(self.identity(),max_bytes=8)
        with self.assertRaises(ValueError):
            c.add(side="packed",request_id="r1",stage="prefix_terminal",window="prefix",
                  source_start=2,source_end=4,tensors={"state":torch.ones(2,2)})
        self.assertEqual(c.bytes,0);self.assertFalse(c.records)
        c=FirstDivergenceCapture(self.identity(),max_records=1)
        kw=dict(side="packed",request_id="r1",stage="prefix_terminal",window="prefix",
                source_start=2,source_end=4,tensors={"state":torch.ones(2,2)})
        c.add(**kw)
        with self.assertRaises(ValueError):c.add(**{**kw,"side":"serial"})
        with self.assertRaises(ValueError):c.add(**kw)
    def test_nan_wrong_stage_and_request_reject(self):
        for change in (dict(stage="unknown"),dict(request_id="unknown"),
                       dict(source_end=1),dict(source_start=True),
                       dict(tensors={"state":torch.full((2,2),float("nan"))})):
            c=FirstDivergenceCapture(self.identity())
            kw=dict(side="packed",request_id="r1",stage="prefix_terminal",window="prefix",
                    source_start=2,source_end=4,tensors={"state":torch.ones(2,2)})
            with self.assertRaises(ValueError):c.add(**{**kw,**change})
    def test_tamper_missing_extra_and_symlink(self):
        for mutation in ("tamper","missing","extra","symlink"):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temp:
                _,r=self.seal(temp);root=Path(r["root"]);p=next(root.glob("*.npy"))
                if mutation=="tamper":p.write_bytes(p.read_bytes()[:-1]+b"X")
                elif mutation=="missing":p.unlink()
                elif mutation=="extra":(root/"extra").write_text("extra")
                else:
                    saved=root.parent/"saved.npy";p.rename(saved);p.symlink_to(saved)
                with self.assertRaises(ValueError):self.audit(r)
    def test_missing_pair_and_coordinate_drift(self):
        for mutation in ("missingpair","coordinate","stage","generation"):
            with tempfile.TemporaryDirectory() as temp:
                _,r=self.seal(temp);root=Path(r["root"]);mp=root/"manifest.json"
                m=json.loads(mp.read_text())
                if mutation=="missingpair":
                    e=m["records"].pop()
                    for d in e["tensors"].values():(root/d["file"]).unlink()
                    m["payload_bytes"]-=sum(d["nbytes"] for d in e["tensors"].values())
                elif mutation=="coordinate":m["records"][5]["source_end"]+=1
                elif mutation=="stage":m["records"][5]["stage"]="final"
                else:m["identity"]["generations"]["r1"]+=1
                raw=json.dumps(m).encode();mp.write_bytes(raw)
                r["manifest_sha256"]=hashlib.sha256(raw).hexdigest()
                with self.assertRaises(ValueError):self.audit(r)
    def test_exclusive_seal_and_passed_discard(self):
        with tempfile.TemporaryDirectory() as temp:
            c,r=self.seal(temp);second=FirstDivergenceCapture(self.identity());self.fill(second)
            with self.assertRaises(FileExistsError):second.seal_failure(r["root"],failed_request_id="r1")
            c=FirstDivergenceCapture(self.identity());self.fill(c);c.discard()
            self.assertFalse((Path(temp)/"passed").exists())

if __name__=="__main__":unittest.main()
