import copy,tempfile,unittest
from pathlib import Path
import torch
from independent_c1_stage_capture import FirstDivergenceCapture
from audit_c1_stage_runtime import audit_runtime_capture

class RuntimeStageAuditTests(unittest.TestCase):
    def fixture(self,temp,*,residual=False,key_head=2,point=(3,7),claimed_max=5.,final_value=.05):
        raw=Path(temp);(raw/"diagnostics").mkdir()
        identity=dict(rank=0,pid=123,step=9,layer="language_model.model.layers.0.linear_attn",
            manifest_sha256="a"*64,requests=["r"],generations={"r":3},
            tokens_sha256={"r":"b"*64},head_indices=dict(query=0,key=0,value=0),
            key_width=128,value_width=128)
        selected=dict(value_head=8,key_coordinate=point[0],value_coordinate=point[1],
            reported_max_scaled=claimed_max,selected_max_scaled=claimed_max,atol=.01,rtol=.003,
            selection="runtime full-state FP32 argmax; exported head is sampled")
        if residual:identity.update(head_policy="max_state_residual",
            head_indices=dict(query=key_head,key=key_head,value=8),head_selection=selected)
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
                if stage=="final":
                    tensors.update(output=torch.zeros(3,128),conv=torch.zeros(3,2560))
                    if residual and side=="packed":tensors["state"][3,7]=final_value
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
        selection=dict(common,event="c1_first_divergence_selection",eligible=True,reason=None,
            total_entries=2,hot_request_ids=["r","other"],excluded_native_one=[],
            active_windows=4,packed_tokens=10,selected_request_id="r",actual_slot_commit="not_started")
        if residual:
            for install in installs:install["c1_first_divergence_head_policy"]="max_state_residual"
            event.update(head_policy="max_state_residual",head_selection=selected)
            failure["metrics"][1]["max_scaled"]=claimed_max
        return installs+[public,selection,failure,event],raw
    def test_selected_failed_head_point_independent_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            events,raw=self.fixture(temp,residual=True)
            report=audit_runtime_capture(events,raw,manifest_sha256="a"*64)
            self.assertEqual(report["selected_failed_point"]["value_head"],8)
            self.assertGreater(report["selected_failed_point"]["independently_recomputed_scaled_residual"],1)
    def test_selected_head_mapping_point_and_maximum_mutations(self):
        for kwargs in (dict(key_head=1),dict(point=(4,7)),dict(claimed_max=6.),
                       dict(final_value=.005)):
            with tempfile.TemporaryDirectory() as temp:
                events,raw=self.fixture(temp,residual=True,**kwargs)
                with self.assertRaises(ValueError):
                    audit_runtime_capture(events,raw,manifest_sha256="a"*64)
        with tempfile.TemporaryDirectory() as temp:
            events,raw=self.fixture(temp,residual=True)
            events[0].pop("c1_first_divergence_head_policy")
            with self.assertRaises(ValueError):
                audit_runtime_capture(events,raw,manifest_sha256="a"*64)

    def test_complete_link_and_independent_head_oracle(self):
        with tempfile.TemporaryDirectory() as temp:
            events,raw=self.fixture(temp)
            report=audit_runtime_capture(events,raw,manifest_sha256="a"*64)
            self.assertTrue(report["capture_link_verified"])
            self.assertEqual(len(report['fp64_captured_input_references']),4)
            self.assertTrue(all(x['within_frozen_tolerance'] for x in report['internal_state_checks']))
            self.assertIsNone(report["tensor_audit"]["first_observed_divergence"])

    def test_canonical_prefix_capture_requires_actual_producing_route(self):
        with tempfile.TemporaryDirectory() as temp:
            events,raw=self.fixture(temp,residual=True)
            for install in events[:4]:
                install["c1_short_prefix_terminal_policy"]="canonical_recurrent_le64"
            events[-1]["branches"][0]["branch"]="independent_recurrent_le64"
            common={k:events[-1][k] for k in ("rank","pid","step","layer","manifest_sha256")}
            routes=[dict(common,event="c1_prefix_terminal_route",request_id=rid,job=j,
                window="prefix",source_start=0,source_end=2,packed_start=10*j,packed_end=10*j+2,
                rows=2,branch="independent_recurrent_le64",policy="canonical_recurrent_le64",
                actual_slot_commit="not_started") for rid,j in (("r",0),("other",2))]
            events[6:6]=routes
            report=audit_runtime_capture(events,raw,manifest_sha256="a"*64)
            self.assertTrue(report["prefix_route_audit"]["verified"])
            routes[0].update(source_end=3,packed_end=3,rows=3)
            with self.assertRaises(ValueError):
                audit_runtime_capture(events,raw,manifest_sha256="a"*64)
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
        changes=[lambda e:e.pop(6),lambda e:e[-1]["branches"].pop(),
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

    def test_five_native1_entries_joined_and_not_sampled(self):
        with tempfile.TemporaryDirectory() as temp:
            events,raw=self.fixture(temp);selection=events[5]
            names=["n"+str(i) for i in range(5)]
            selection.update(total_entries=7,excluded_native_one=names)
            native=dict(selection,event="native_decode_batch_completed",requests=names,
                rows=5,slots=[5,6,7,8,9],private_buffers=True,actual_slot_commit="deferred")
            events.insert(5,native)
            self.assertTrue(audit_runtime_capture(events,raw,manifest_sha256="a"*64)["capture_link_verified"])
            native["rows"]=4
            with self.assertRaises(ValueError):audit_runtime_capture(events,raw,manifest_sha256="a"*64)

    def test_selection_mutations_reject(self):
        changes=[lambda e:e.pop(5),lambda e:e[5].update(eligible=False),
            lambda e:e[5].update(total_entries=7),lambda e:e[5].update(selected_request_id="other"),
            lambda e:e[5].update(hot_request_ids=["r"]),lambda e:e[5].update(active_windows=3),
            lambda e:e[5].update(packed_tokens=12001)]
        for mutate in changes:
            with tempfile.TemporaryDirectory() as temp:
                events,raw=self.fixture(temp);mutate(events)
                with self.assertRaises(ValueError):audit_runtime_capture(events,raw,manifest_sha256="a"*64)

if __name__=="__main__":unittest.main()
