import copy,tempfile,unittest
from pathlib import Path
import torch
from independent_c1_stage_capture import FirstDivergenceCapture
from audit_c1_stage_runtime import audit_runtime_capture

class RuntimeStageAuditTests(unittest.TestCase):
    def fixture(self,temp):
        raw=Path(temp);(raw/"diagnostics").mkdir()
        identity=dict(rank=0,pid=123,step=9,layer="language_model.model.layers.0.linear_attn",
            manifest_sha256="a"*64,requests=["r"],generations={"r":3},
            tokens_sha256={"r":"b"*64},head_indices=dict(query=0,key=0,value=0),
            key_width=128,value_width=128)
        capture=FirstDivergenceCapture(identity)
        for side in ("packed","serial"):
            for window,lo,hi in (("prefix",0,2),("suffix",2,5)):
                n=hi-lo
                tensors=dict(q=torch.zeros(n,128),k=torch.zeros(n,128),v=torch.zeros(n,128),
                    g=torch.zeros(n),beta=torch.ones(n),initial=torch.zeros(128,128))
                capture.add(side=side,request_id="r",stage="inputs",window=window,
                    source_start=lo,source_end=hi,tensors=tensors)
            for stage,window,lo,hi in (("prefix_terminal","prefix",0,2),
                    ("cached_composition","body",10,16386),("suffix_seed","suffix",2,5),
                    ("final","suffix",2,5)):
                tensors={"state":torch.zeros(128,128)}
                if stage=="cached_composition":
                    tensors.update(transition=torch.zeros(128,128),zero_state=torch.zeros(128,128))
                if stage=="final":tensors.update(output=torch.zeros(3,128),conv=torch.zeros(3,2560))
                capture.add(side=side,request_id="r",stage=stage,window=window,
                    source_start=lo,source_end=hi,tensors=tensors)
        receipt=capture.seal_failure(raw/"diagnostics"/"c1-stage-rank0-step9",failed_request_id="r")
        receipt["capture_manifest_sha256"]=receipt.pop("manifest_sha256")
        receipt["root"]="/scratch/diagnostics/c1-stage-rank0-step9"
        common=dict(rank=0,pid=123,step=9,layer=identity["layer"],manifest_sha256="a"*64)
        installs=[dict(event="compact_hypic_hooks_installed",pid=123+i,
            manifest_sha256="a"*64,c1_first_divergence=True,c1_packed_wave=True) for i in range(4)]
        public=dict(common,event="compact_public_state_published",generation=3,tokens_sha256="b"*64)
        failure=dict(common,event="c1_packed_wave_shadow_checked",request_id="r",passed=False,
            private_buffers=True,actual_slot_commit="not_started",atol=.01,rtol=.003,
            group_requests=["r","other"],metrics=[dict(tensor=name,passed=name!="state",
                max_scaled=2 if name=="state" else 0) for name in ("output","state","conv")])
        branches=[dict(side=side,request_id="r",window=window,
            branch="official_chunk64" if side=="packed" else "independent_recurrent_le64")
            for side in ("packed","serial") for window in ("prefix","suffix")]
        coordinates={rid:dict(slot=i,has_initial=True,body_start=10,body_end=16386)
                     for i,rid in enumerate(("r","other"))}
        event=dict(receipt,**common,event="c1_first_divergence_capture",request_id="r",
                   actual_slot_commit="not_started",branches=branches,coordinates=coordinates)
        return installs+[public,failure,event],raw
    def test_complete_link_and_independent_head_oracle(self):
        with tempfile.TemporaryDirectory() as temp:
            events,raw=self.fixture(temp)
            report=audit_runtime_capture(events,raw,manifest_sha256="a"*64)
            self.assertTrue(report["capture_link_verified"])
            self.assertEqual(len(report['fp64_captured_input_references']),4)
            self.assertTrue(all(x['within_frozen_tolerance'] for x in report['internal_state_checks']))
            self.assertIsNone(report["tensor_audit"]["first_observed_divergence"])
    def test_identity_and_generation_mutations(self):
        changes=[lambda e:e[-1].update(pid=999),lambda e:e[-1].update(step=10),
            lambda e:e[-1].update(manifest_sha256="c"*64),
            lambda e:e[-1].update(capture_manifest_sha256="c"*64),
            lambda e:e[4].update(generation=4),lambda e:e[4].update(tokens_sha256="c"*64),
            lambda e:e[0].update(c1_first_divergence=False),
            lambda e:e[-1].update(actual_slot_commit="completed"),
            lambda e:e[-1].update(root="/scratch/../escape"),
            lambda e:e[-1].update(complete=False)]
        for mutate in changes:
            with tempfile.TemporaryDirectory() as temp:
                events,raw=self.fixture(temp);mutate(events)
                with self.assertRaises(ValueError):audit_runtime_capture(events,raw,manifest_sha256="a"*64)
    def test_missing_failure_branch_and_coordinates(self):
        changes=[lambda e:e.pop(5),lambda e:e[-1]["branches"].pop(),
            lambda e:e[-1]["branches"][2].update(branch="official_chunk64"),
            lambda e:e[-1]["coordinates"]["r"].update(has_initial=False),
            lambda e:e[-1]["coordinates"]["r"].update(body_end=16385),
            lambda e:e[-1]["coordinates"]["r"].update(slot=-1),
            lambda e:e[-1]["coordinates"].pop("other")]
        for mutate in changes:
            with tempfile.TemporaryDirectory() as temp:
                events,raw=self.fixture(temp);mutate(events)
                with self.assertRaises(ValueError):audit_runtime_capture(events,raw,manifest_sha256="a"*64)
    def test_commit_and_duplicate_capture_reject(self):
        for kind in ("compact_gdn_body_composed","c1_layer_precommit_validated","duplicate"):
            with tempfile.TemporaryDirectory() as temp:
                events,raw=self.fixture(temp)
                if kind=="duplicate":events.append(copy.deepcopy(events[-1]))
                else:events.append(dict(events[-1],event=kind))
                with self.assertRaises(ValueError):audit_runtime_capture(events,raw,manifest_sha256="a"*64)

if __name__=="__main__":unittest.main()
