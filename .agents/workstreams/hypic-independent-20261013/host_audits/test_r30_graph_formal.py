"""HOST controls: actual retained base argv path, timed policy and real INFO logs."""
from contextlib import redirect_stdout
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from host_audits import r30_graph_formal_controller as driver
from host_audits import r30_graph_formal_audit as audit

WS = Path(__file__).resolve().parent.parent


def timed_case(on=True):
    c=json.loads((WS/("FORMAL_R25_G3_R1_20261025_CONTRACT.json" if on else
                     "FORMAL_R25_G1_R1_20261025_CONTRACT.json")).read_text())
    cfg=json.loads((WS/"GRAPH_R29_G3_CONFIG_20261025.json").read_text())
    cfg.update(c1_performance_mode=True,c1_layer_shadow_validation=False,
               c1_first_divergence=False,c1_first_divergence_head_policy="head0",
               prompt_snapshot_probe_batches=0)
    if not on:
        cfg.update(c1_partitioned_render=False,c1_async_material_transfer=False,
                   c1_lazy_initial_snapshot=False)
    c.update(enforce_eager=False,base_controller_sha256=audit.BASE_SHA,
             graph_runtime=dict(audit.GRAPH,candidate_enabled=on))
    return c,cfg


class PolicyTests(unittest.TestCase):
    def test_actual_full40_group_policies(self):
        for on in (False,True):
            c,cfg=timed_case(on)
            self.assertEqual(audit.validate_policy(c,cfg)["algorithm_on"],on)

    def test_old_eager_profile_cannot_be_relabelled(self):
        c,cfg=timed_case();c["enforce_eager"]=True
        with self.assertRaises(ValueError):audit.validate_policy(c,cfg)

    def test_other_image_is_rejected(self):
        c,cfg=timed_case();c["image"]="other"
        with self.assertRaises(ValueError):audit.validate_policy(c,cfg)

    def test_real_base_identity_is_not_aliased_to_host(self):
        c,cfg=timed_case();c["controller_sha256"]="a"*64
        with self.assertRaises(ValueError):audit.validate_policy(c,cfg)

    def test_canary_probe_policy_cannot_enter_timing(self):
        c,cfg=timed_case();cfg["prompt_snapshot_probe_batches"]=2
        with self.assertRaises(ValueError):audit.validate_policy(c,cfg)

    def test_disabled_probe_requires_valid_head_policy(self):
        c,cfg=timed_case();cfg["c1_first_divergence_head_policy"]="max_state_residual"
        with self.assertRaises(ValueError):audit.validate_policy(c,cfg)

    def test_pdc_groups_need_real_observer_successor(self):
        for group in ("G2","G4"):
            c,cfg=timed_case();c["performance_group"]=group
            with self.assertRaises(ValueError):audit.validate_policy(c,cfg)

    def test_safety_checks_cannot_silently_disappear(self):
        c,cfg=timed_case();cfg["c2_layer_finite_gate"]=False
        with self.assertRaises(ValueError):audit.validate_policy(c,cfg)


class ActualBaseArgvTests(unittest.TestCase):
    def exercise(self,on):
        c,cfg=timed_case(on)
        with tempfile.TemporaryDirectory(prefix="hypic-r30-base-")as tmp:
            tmp=Path(tmp);model=tmp/"model";model.mkdir()
            config=model/"config.json";config.write_text("{}")
            c.update(raw_root=str(tmp/"attempt"),model=str(model),
                     model_config_sha256=hashlib.sha256(config.read_bytes()).hexdigest())
            if on:
                c["cache_diagnostic"]={"compact_manifest":"test-bound.json","source_sha256":{}}
            else:
                c.pop("cache_diagnostic",None)
            checked={"controller_sha256":hashlib.sha256(Path(driver.__file__).read_bytes()).hexdigest(),
                     "graph_runtime":c["graph_runtime"]}
            captured=[];original_write=driver.base.write
            def write(root,name,data):
                if name=="launch.json":driver.rewrite_launch(data,c,checked)
                return original_write(root,name,data)
            def command(argv,timeout=30):
                if argv[:3]==["docker","image","inspect"]:
                    return json.dumps([{"Config":{"Env":[]}}])
                if argv[:3]==["git","rev-parse","HEAD"]:return "cpu-only-test"
                if argv[:2]==["docker","run"]:
                    captured.append(list(argv))
                    raise RuntimeError("CPU test intentionally stops before Docker allocation")
                if argv[:2]==["ss","-H"]:return ""
                raise AssertionError("unexpected external command: "+repr(argv))
            with patch.object(driver.base,"command",command),patch.object(driver.base,"write",write),\
                 patch.object(driver.base,"snapshot",lambda *a,**k:{"foreign":[],"processes":[]}),\
                 patch.object(driver.base,"port_free",lambda p:None),redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):driver.base.run_contract(c)
            self.assertEqual(len(captured),1)
            launch=json.loads((tmp/"attempt/launch.json").read_text())
            self.assertEqual(captured[0],launch["argv"])
            self.assertEqual(launch["controller_sha256"],audit.BASE_SHA)
            self.assertEqual(launch["base_controller_sha256"],audit.BASE_SHA)
            self.assertEqual(launch["host_controller_sha256"],checked["controller_sha256"])
            argv=captured[0]
            self.assertIn("VLLM_LOGGING_LEVEL=INFO",argv)
            self.assertNotIn("VLLM_LOGGING_LEVEL=DEBUG",argv)
            self.assertEqual(json.loads(audit.native._option(argv,"--compilation-config")),
                             audit.native.COMPILATION)
            self.assertNotIn("--enforce-eager",argv)
            if on:
                self.assertIn("INDEPENDENT_GRAPH_HYPIC=1",argv)
                self.assertFalse(any(x.startswith("INDEPENDENT_COMPACT_")for x in argv))
            else:
                self.assertFalse(any(":/probe"in x for x in argv))
                self.assertFalse(any(x.startswith("INDEPENDENT_")for x in argv))

    def test_actual_native_base_passes_same_mutated_argv_to_owner(self):
        self.exercise(False)

    def test_actual_hypic_base_passes_same_mutated_argv_to_owner(self):
        self.exercise(True)


class ActualInfoLogTests(unittest.TestCase):
    def logs(self,label):
        names={"native":("graph-r27-g1-canary-r1-20261025",
            "bba1a77583d4bcd041234204ac418d48b084de46e8a18d3b9e98988d1fa8f78b"),
            "hypic":("graph-r29-g3-warmup-r1-20261025",
            "9af7c9fe93f8050029135da5f53708c7e710bcbb29b9c36df0e6fdfa2efbc957")}
        name,want=names[label]
        raw=(Path("/cache/cch/hypic-independent-20261013")/name/"service.log").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),want)
        return [x for x in raw.decode().splitlines()if " DEBUG "not in x]

    def test_actual_native_info_without_debug_capture_is_valid(self):
        p=audit.parse_info_graph(("\n".join(self.logs("native"))+"\n").encode())
        self.assertEqual(set(p["workers"]),set(range(4)))
        self.assertEqual(p["replay_directly_observed_rank"],0)

    def test_actual_hypic_info_without_debug_capture_is_valid(self):
        p=audit.parse_info_graph(("\n".join(self.logs("hypic"))+"\n").encode())
        self.assertEqual(p["workers"],{0:59,1:60,2:61,3:62})

    def test_install_markers_cannot_prove_real_graph(self):
        with self.assertRaises(ValueError):
            audit.parse_info_graph(b"graph_candidate_hooks_installed\n")

    def test_missing_actual_replay_rejected(self):
        rows=[x for x in self.logs("native")if "Replaying aclgraph"not in x]
        with self.assertRaises(ValueError):audit.parse_info_graph("\n".join(rows).encode())

    def test_foreign_replay_pid_rejected(self):
        rows=[x.replace("pid=58","pid=999")if "Replaying aclgraph"in x else x
              for x in self.logs("native")]
        with self.assertRaises(ValueError):audit.parse_info_graph("\n".join(rows).encode())

    def test_missing_worker_model_load_rejected(self):
        rows=[x for x in self.logs("native")if not
              ("Worker_TP3"in x and "Starting to load model"in x)]
        with self.assertRaises(ValueError):audit.parse_info_graph("\n".join(rows).encode())


if __name__=="__main__":
    unittest.main()
