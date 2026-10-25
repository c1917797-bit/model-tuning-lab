"""Focused HOST-only R27 controls; synthetic logs are never NPU proof."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

WORKSTREAM = Path(__file__).resolve().parent.parent
if str(WORKSTREAM) not in sys.path:
    sys.path.insert(0, str(WORKSTREAM))
from host_audits import r27_graph_canary_audit as target


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AuditControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hypic-r27-audit-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.raw = self.base / "raw"
        self.raw.mkdir()
        self.cp = self.base / "contract.json"
        host = self.base / target.HOST_CONTROLLER
        host.parent.mkdir()
        host.write_text("# synthetic HOST controller fixture; not executable proof\n")
        (self.base / target.BASE_CONTROLLER).write_bytes(
            (WORKSTREAM / target.BASE_CONTROLLER).read_bytes())
        auditor = self.base / target.HOST_AUDITOR
        auditor.write_bytes(Path(target.__file__).read_bytes())
        (self.base/"baseline-bound.py").write_text("# synthetic baseline dependency\n")
        self.own = digest(host)
        native, public = [21] * 8192, [31] * 16384
        rows = []
        for i in range(2):
            start = 9216 + i * 512
            end = start + len(public)
            rows.append({"token_ids": native + [41+i] * (start-8192) + public
                         + [51+i] * (32768-end), "segment_start": start, "segment_end": end})
        self.artifact = {"native_prefix": native, "public_segment": public, "requests": rows}
        tokens = self.base / "tokens.json"
        dump(tokens, self.artifact)
        runtime = {"profile": target.PROFILE, "candidate_enabled": False,
                   "compilation_mode": 3, "cudagraph_mode": "FULL_DECODE_ONLY",
                   "capture_sizes": target.CAPTURE_SIZES,
                   "official_compilation_source_sha256": target.COMPILATION_SHA256,
                   "official_debug_logging": True}
        self.contract = {"physical_npus": [0,1,2,3], "tp": 4,
            "formal_performance": False, "formal_quality": False,
            "enable_prefix_caching": False, "enforce_eager": False,
            "graph_canary_group": "G1", "controller_sha256": self.own,
            "base_controller_sha256": target.BASE_SHA256,
            "r27_host_audit": {"source_sha256": {target.HOST_AUDITOR:digest(auditor)}},
            "host_controller_source_sha256": {
                target.HOST_CONTROLLER: self.own, target.BASE_CONTROLLER: target.BASE_SHA256},
            "graph_runtime": runtime, "raw_root": str(self.raw), "image": "synthetic-pinned-image",
            "formal_token_artifact": {"path": str(tokens), "sha256": digest(tokens)}}
        self.contract["baseline_host_source_sha256"] = dict(
            self.contract["host_controller_source_sha256"],
            **{"baseline-bound.py":digest(self.base/"baseline-bound.py")})
        self.contract["port"] = 8233
        self.launch = {"controller_sha256": target.BASE_SHA256,
            "host_controller_sha256": self.own, "base_controller_sha256": target.BASE_SHA256,
            "graph_runtime": dict(runtime, compilation_config=target.COMPILATION, bootstrap=None),
            "argv": ["docker", "run", "-e", "VLLM_LOGGING_LEVEL=DEBUG", "image", "serve", "/model",
                     "--tensor-parallel-size", "4", "--data-parallel-size", "1",
                     "--no-enable-prefix-caching", "--compilation-config", json.dumps(target.COMPILATION)]}
        first = rows[0]
        prompts = [public + first["token_ids"][first["segment_end"]:first["segment_end"]+256],
                   rows[0]["token_ids"], rows[1]["token_ids"]]
        self.records = [{"index": i, "payload": {"prompt": prompt, "max_tokens": 1 if i==0 else 1024,
            "temperature": 0, "seed": 0, "ignore_eos": True},
            "response": {"id": "api-"+str(i), "usage": {"prompt_tokens": len(prompt),
                "completion_tokens": 1 if i==0 else 1024}}} for i,prompt in enumerate(prompts)]
        self.cid = "a" * 64
        self.samples = [{"foreign": [], "owners": [{"pid":1000+r,"npu":r,"nspid":[1000+r,100+r],
            "owned":True,"cgroup":"/"+self.cid} for r in range(4)]}]
        self.start = {"container_id": self.cid, "image": self.contract["image"],
                      "devices": ["/dev/davinci"+str(i) for i in range(4)]}
        self.release = {"owned_container":self.cid,"removed":True,"port_free":True,
                        "final_physical_processes":[]}
        self.result = {"valid":True,"error":None,"guard_errors":[],"responses":3,
                       "isolation_samples":1,"release":self.release}
        self.events = {}
        self.flush()

    def flush(self):
        for name,value in (("launch.json",self.launch),("result.json",self.result),
                           ("responses.json",self.records),("isolation.json",self.samples),
                           ("service-start.json",self.start),("release.json",self.release)):
            dump(self.raw/name,value)
        journal = ([{"event":"isolation","snapshot":s} for s in self.samples]
                   + [dict(r,event="response") for r in self.records]
                   + [{"event":"terminal","result":self.result}])
        (self.raw/"events.jsonl").write_text("".join(json.dumps(e)+"\n" for e in journal))
        for rank,events in self.events.items():
            directory=self.raw/"diagnostics";directory.mkdir(exist_ok=True)
            (directory/("compact-worker-"+str(100+rank)+".jsonl")).write_text(
                "".join(json.dumps(e)+"\n" for e in events))
        dump(self.cp,self.contract)

    def treatment(self):
        self.contract["graph_canary_group"]="G3"
        self.contract["graph_runtime"]["candidate_enabled"]=True
        self.launch["graph_runtime"].update(candidate_enabled=True,bootstrap="graph_candidate/bootstrap")
        cfg = {k:True for k in ("prefill_prompt_snapshot","c1_layer_shadow_validation",
               "c1_first_divergence","c1_partitioned_render","c1_lazy_initial_snapshot",
               "forward_metadata_snapshot","c2_layer_completion_barrier","c2_layer_finite_gate",
               "c2_block_table_snapshot","c2_block_table_diagnostic")}
        cfg.update(prompt_snapshot_probe_batches=2,c1_performance_mode=False)
        config="graph-config.json";dump(self.base/config,cfg)
        sources={config:digest(self.base/config)}
        for name in target.GRAPH_FILES:
            p=self.base/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text("# synthetic source binding "+name+"\n");sources[name]=digest(p)
        manifest="graph-manifest.json"
        dump(self.base/manifest,{"graph_profile":target.PROFILE,"config":config,"source_sha256":sources})
        mh=digest(self.base/manifest)
        self.contract["cache_diagnostic"]={"source_sha256":sources,"compact_manifest":manifest}
        self.contract["c2_snapshot_acceptance"]={"enabled":True,
            "group_source":"verified-native-full-attention-spec","layers":["kv"+str(i) for i in range(16)]}
        self.launch["argv"][2:2]=[
            "-e","INDEPENDENT_GRAPH_HYPIC=1","-e","INDEPENDENT_GRAPH_MANIFEST=/probe/"+manifest,
            "-e","INDEPENDENT_GRAPH_RAW=/scratch/diagnostics",
            "-e","PYTHONPATH=/probe/graph_candidate/bootstrap:/probe:official"]
        for rank in range(4):
            common={"rank":rank,"pid":100+rank,"manifest_sha256":mh}
            events=[dict(common,event="compact_hypic_hooks_installed",**cfg),
                    dict(common,event="graph_candidate_hooks_installed",profile=target.PROFILE),
                    dict(common,event="graph_native_worker_import_verified",graph_profile=target.PROFILE,
                         native_source_sha256=target.NATIVE_RUNNER_SHA256,
                         original_importer_executed=True,native_dummy_metadata_policy_verified=True)]
            for count,kind,prefix in ((48,"compact_public_state_published","linear"),
                                      (16,"compact_public_kv_published","kv")):
                events.extend(dict(common,event=kind,layer=prefix+str(i)) for i in range(count))
            for ordinal in range(2):
                step=ordinal+2;rid="api-"+str(ordinal+1)+"-runtime"
                events.extend([
                    dict(common,event="native_request_progress",request_id=rid,step=step,
                         scheduled_tokens=32768,computed_tokens=0),
                    dict(common,event="compact_native_attention_groups_captured",step=step,
                         request_ids=[rid],source="verified-native-full-attention-spec",
                         attention_groups=[{"group":0,"layers":["kv"+str(i) for i in range(16)]}])])
                for i in range(48):
                    layer="linear"+str(i)
                    events.append(dict(common,event="c1_packed_wave_prepared",step=step,layer=layer,
                        state_schedule="partitioned",state_passes=1,actual_slot_commit="not_started",
                        windows=1,packed_tokens=16392,state_window_visits=1,state_token_visits=16392,
                        requests=[rid]))
                    if ordinal==0:
                        events.append(dict(common,event="c1_packed_wave_shadow_checked",step=step,
                            layer=layer,request_id=rid,passed=True,private_buffers=True,
                            actual_slot_commit="not_started",atol=.01,rtol=.003,
                            metrics=[{"tensor":k,"passed":True,"max_abs":0.0,"rms":0.0,"max_scaled":0.0}
                                     for k in ("output","state","conv")]))
                    events.append(dict(common,event="compact_gdn_body_composed",step=step,
                        request_id=rid,layer=layer,finite=True,skipped_body_tokens=16376,
                        retained_rows=16392,initial_snapshot_skipped=ordinal==1))
                for i in range(16):
                    layer="kv"+str(i)
                    events.extend([
                        dict(common,event="c2_layer_precommit_validated",step=step,layer=layer,
                             requests=[rid],tensors=2,finite=True,actual_slot_commit="not_started"),
                        dict(common,event="compact_c2_queries_completed",step=step,layer=layer,
                             request_id=rid,skipped_body_queries=16376,retained_rows=16392,
                             query_windows=1,group=0),
                        dict(common,event="c2_block_table_snapshot_layer_checked",step=step,layer=layer,
                             group=0,request_ids=[rid],reads_delta=1 if i==0 else 0,
                             hits_delta=0 if i==0 else 1)])
                events.append(dict(common,event="compact_model_rows_completed",step=step,
                    request_ids=[rid],original_rows=32768,retained_rows=16392,
                    forward_metadata_snapshot=True,metadata_snapshot_reads=3,metadata_snapshot_hits=141,
                    c2_block_table_snapshot=True,c2_block_table_snapshot_reads=1,
                    c2_block_table_snapshot_hits=15,c2_snapshot_scope_owner="graph_candidate.prefill_bridge",
                    inner_helper_c2_snapshot=False))
                events.append(dict(common,event="prompt_snapshot_opportunity",step=100+ordinal,
                    request_ids=[rid],computed_tokens=[32768],scheduled_tokens=[1],
                    omitted_decode_ids=[rid],retained_prefill_ids=[],omitted_prompt_tokens=32768,
                    order=["original","prefill_only"] if ordinal==0 else ["prefill_only","original"],
                    measurements={k:{"wall_ns":1,"thread_cpu_ns":1} for k in ("original","prefill_only")}))
            self.events[rank]=events
        self.flush()

    def reject(self, mutate):
        mutate();self.flush()
        with self.assertRaises((ValueError,OSError,KeyError)):
            target.audit_mechanism(self.cp)

    def test_native_report_is_partial_not_graph_proof(self):
        out=target.audit_mechanism(self.cp)
        self.assertEqual(out["arm"],"G1")
        self.assertTrue(out["bounded_mechanism_audited"])
        self.assertFalse(out["valid"]);self.assertFalse(out["graph_execution_verified"])
        self.assertFalse(out["live_release_verified"])

    def test_whole_audit_rejects_absent_and_caller_asserted_graph_proof(self):
        for evidence in (None,{"graph_execution_verified":True}):
            with self.assertRaises(target.GraphEvidencePending) as raised:
                target.audit(self.cp,graph_evidence=evidence)
            self.assertFalse(raised.exception.partial_report["valid"])

    def test_real_base_identity_cannot_be_aliased_to_host(self):
        self.reject(lambda:self.launch.update(controller_sha256=self.own))

    def test_contract_cannot_alias_host_identity_to_base(self):
        self.reject(lambda:self.contract.update(controller_sha256=target.BASE_SHA256))

    def test_host_source_drift_rejected(self):
        self.reject(lambda:(self.base/target.HOST_CONTROLLER).write_text("drift"))

    def test_actual_compilation_mode_not_just_contract_flag(self):
        def mutate():
            self.launch["argv"][-1]=json.dumps(dict(target.COMPILATION,mode=0))
        self.reject(mutate)

    def test_enforce_eager_rejected(self):
        self.reject(lambda:self.launch["argv"].append("--enforce-eager"))

    def test_debug_off_rejected(self):
        self.reject(lambda:self.launch["argv"].__setitem__(3,"VLLM_LOGGING_LEVEL=INFO"))

    def test_native_cannot_load_graph_or_compact_package(self):
        self.reject(lambda:self.launch["argv"].__setitem__(slice(2,2),["-e","INDEPENDENT_GRAPH_HYPIC=1"]))

    def test_mislabelled_group_rejected(self):
        self.reject(lambda:self.contract.update(graph_canary_group="G3"))

    def test_actual_payload_and_output_denominator_preserved(self):
        self.reject(lambda:self.records[2]["response"]["usage"].update(completion_tokens=32))

    def test_failed_terminal_preserved(self):
        self.reject(lambda:self.result.update(valid=False))

    def test_external_process_rejected(self):
        self.reject(lambda:self.samples[0].update(foreign=[{"pid":9999}]))

    def test_exact_release_required(self):
        self.reject(lambda:self.release.update(removed=False))

    def test_source_bound_treatment_keeps_all_existing_pure_joins(self):
        self.treatment();out=target.audit_mechanism(self.cp)
        self.assertEqual(out["hot"]["denominator"],2)
        self.assertTrue(out["hot"]["accepted_hot_coverage"])
        self.assertEqual(out["c2_snapshot"]["reads"],8)
        self.assertEqual(out["c2_snapshot"]["hits"],120)
        self.assertEqual(out["partition"]["numeric_shadows"],192)
        self.assertFalse(out["valid"])

    def test_treatment_rejects_double_old_loader_activation(self):
        self.treatment()
        self.reject(lambda:self.launch["argv"].__setitem__(slice(2,2),["-e","INDEPENDENT_COMPACT_HYPIC=1"]))

    def test_outer_snapshot_provenance_not_renamed_old_inner_scope(self):
        self.treatment()
        def mutate():
            for e in self.events[0]:
                if e["event"]=="compact_model_rows_completed":
                    e["inner_helper_c2_snapshot"]=True
        self.reject(mutate)

    def test_fourrank_hot_denominator_not_relaxed(self):
        self.treatment()
        self.reject(lambda:self.events[0].pop(next(i for i,e in enumerate(self.events[0])
            if e["event"]=="compact_c2_queries_completed")))

    def test_failed_numeric_shadow_rejected(self):
        self.treatment()
        self.reject(lambda:next(e for e in self.events[0]
            if e["event"]=="c1_packed_wave_shadow_checked").update(passed=False))

    def test_stale_source_manifest_rejected(self):
        self.treatment()
        self.reject(lambda:(self.base/"graph_candidate/entry_router.py").write_text("drift"))


    def test_complete_native_source_map_is_checked_at_terminal(self):
        self.reject(lambda:(self.base/"baseline-bound.py").write_text("drift"))

    def test_independent_auditor_actual_source_is_bound(self):
        self.reject(lambda:(self.base/target.HOST_AUDITOR).write_text("drift"))

    def test_live_release_uses_exact_base_helpers_without_device_execution(self):
        import formal_r15_tp4 as base
        absent=SimpleNamespace(returncode=1,stdout="[]\n",stderr="Error: No such object: "+self.cid)
        with patch.object(target.subprocess,"run",return_value=absent) as inspect, \
             patch.object(base,"snapshot",return_value={"processes":[]}) as snapshot, \
             patch.object(base,"port_free") as port:
            out=target.audit_mechanism(self.cp,live_release=True)
        self.assertTrue(out["live_release_verified"])
        inspect.assert_called_once_with(["docker","inspect",self.cid],capture_output=True,text=True)
        snapshot.assert_called_once_with()
        port.assert_called_once_with(8233)

    def test_live_release_rejects_still_existing_exact_container(self):
        import formal_r15_tp4 as base
        with patch.object(target.subprocess,"run",return_value=SimpleNamespace(
                returncode=0,stdout="[{}]",stderr="")), \
             patch.object(base,"snapshot") as snapshot:
            with self.assertRaisesRegex(ValueError,"container absence"):
                target.audit_mechanism(self.cp,live_release=True)
        snapshot.assert_not_called()

    def test_live_release_rejects_current_physical_process(self):
        import formal_r15_tp4 as base
        absent=SimpleNamespace(returncode=1,stdout="[]",stderr="No such container")
        with patch.object(target.subprocess,"run",return_value=absent), \
             patch.object(base,"snapshot",return_value={"processes":[[0,9999]]}), \
             patch.object(base,"port_free") as port:
            with self.assertRaisesRegex(ValueError,"physical0-3"):
                target.audit_mechanism(self.cp,live_release=True)
        port.assert_not_called()


    def official_log(self):
        lines=[]
        for rank in range(4):
            prefix="(Worker_TP"+str(rank)+" pid="+str(100+rank)+") "
            lines.extend([
                prefix+"DEBUG 10-25 12:00:00 [acl_graph.py:164] Capturing a aclgraph on (FULL,BatchDescriptor(num_tokens=4, num_reqs=4, uniform=True, has_lora=False, num_active_loras=0))",
                *([prefix+"INFO 10-25 12:00:01 [acl_graph.py:243] Replaying aclgraph"] if rank==0 else [])])
        return "\n".join(lines)+"\n"

    def test_official_native_graph_lines_join_exact_own_namespace_pids(self):
        (self.raw/"service.log").write_text(self.official_log())
        out=target.audit(self.cp)
        self.assertTrue(out["valid"])
        self.assertEqual(out["graph"]["worker_pids"],{r:100+r for r in range(4)})
        self.assertEqual(out["graph"]["per_rank"][0]["capture_sizes_observed"],[4])

    def test_treatment_graph_requires_official_log_not_installation_event(self):
        self.treatment()
        with self.assertRaises(target.GraphEvidencePending):
            target.audit(self.cp)
        (self.raw/"service.log").write_text(self.official_log())
        out=target.audit(self.cp)
        self.assertTrue(out["valid"]);self.assertEqual(out["hot"]["denominator"],2)

    def test_ansi_official_format_is_supported_without_relaxing_content(self):
        text=self.official_log().replace("(Worker", "\x1b[36m(Worker").replace(") DEBUG", ")\x1b[0m DEBUG")
        (self.raw/"service.log").write_text(text)
        self.assertTrue(target.audit(self.cp)["graph_execution_verified"])

    def test_wrong_source_line_and_candidate_self_report_do_not_pass(self):
        for text in (self.official_log().replace("[acl_graph.py:164]","[entry_router.py:164]"),
                     '{"event":"graph_candidate_hooks_installed","graph_execution_verified":true}\n'):
            (self.raw/"service.log").write_text(text)
            with self.assertRaises(ValueError):
                target.audit(self.cp)

    def test_missing_rank_or_wrong_pid_cannot_borrow_other_worker_proof(self):
        for text in ("\n".join(self.official_log().splitlines()[:-2]),
                     self.official_log().replace("TP2 pid=102","TP2 pid=9999")):
            (self.raw/"service.log").write_text(text)
            with self.assertRaises(ValueError):
                target.audit(self.cp)

    def test_actual2_padded4_is_accepted_but_descriptor4_vs2_rejected(self):
        text=self.official_log().replace("num_reqs=4","num_reqs=2")
        (self.raw/"service.log").write_text(text)
        with self.assertRaises(ValueError):
            target.audit(self.cp)

    def test_ordinary_worker_diagnostic_does_not_invent_a_new_gate(self):
        (self.raw/"service.log").write_text(self.official_log()+
            "(Worker_TP0 pid=100) Traceback (most recent call last):\n")
        out=target.audit(self.cp)
        self.assertTrue(out["valid"])
        self.assertTrue(out["graph"]["ordinary_worker_diagnostic_lines"])

    def test_replay_before_capture_rejected(self):
        lines=self.official_log().splitlines()
        lines[0],lines[1]=lines[1],lines[0]
        (self.raw/"service.log").write_text("\n".join(lines))
        with self.assertRaises(ValueError):
            target.audit(self.cp)

if __name__=="__main__":
    unittest.main()
