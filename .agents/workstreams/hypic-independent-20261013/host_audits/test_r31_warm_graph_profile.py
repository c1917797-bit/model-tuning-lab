"""Host controls execute the genuine retained profile base up to Docker allocation."""
import copy
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch,Mock
from host_audits import r31_warm_graph_profile as driver
W=driver.WORKSTREAM

def contract(group):
    return json.loads((W/f"WARM_GRAPH_COST_R31_{group}_R1_20261025_CONTRACT.json").read_bytes())

class RealProfileBoundaryTests(unittest.TestCase):
    def check_only(self,group):
        c=contract(group)
        with patch.object(driver.base,"command") as command:
            checked=driver.check_contract(c)
        command.assert_not_called()
        self.assertFalse(checked["device_run"])
        return checked

    def test_default_checks_both_actual_contracts_without_device(self):
        for g in("G1","G3"):
            with self.subTest(group=g):self.check_only(g)

    def test_foreign_device_and_oversized_profile_rejected(self):
        for key,value in(("physical_npus",[4,5,6,7]),("profile_byte_limit",3*1024**3)):
            c=contract("G3");c[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):driver.check_contract(c)
        c=contract("G3");c["profile_diagnostic"]["max_iterations"]=17
        with self.assertRaises(ValueError):driver.check_contract(c)

    def test_wrong_real_controller_identity_rejected(self):
        c=contract("G3");c["controller_sha256"]="0"*64
        with self.assertRaises(ValueError):driver.check_contract(c)

    def actual_launch(self,group,*,space_failure=False):
        with tempfile.TemporaryDirectory(prefix="r31-host-",dir="/cache/cch")as tmp:
            c=contract(group);c["raw_root"]=str(Path(tmp)/"new-raw")
            captured=[];stopped=Mock()
            def command(args,timeout=30):
                if args[:3]==["docker","image","inspect"]:
                    return json.dumps([{"Config":{"Env":[]}}])
                if args[:2]==["docker","run"]:
                    captured.append(list(args))
                    if space_failure:driver.base.snapshot("a"*64)
                    raise RuntimeError("HOST_STOP_BEFORE_DOCKER_ALLOCATION")
                if args and args[0]=="git":return "HOST_FIXTURE_NOT_DEVICE_PROOF\n"
                if args and args[0]=="ss":return ""
                raise AssertionError(args)
            snap=lambda cid=None:{"utc":"HOST_FIXTURE","processes":[],"owners":[],"foreign":[],"raw":"HOST_FIXTURE"}
            original_write=driver.base.write;original_snapshot=driver.base.snapshot
            with ExitStack()as stack:
                stack.enter_context(patch.object(driver.base,"command",side_effect=command))
                stack.enter_context(patch.object(driver.base,"snapshot",side_effect=snap))
                stack.enter_context(patch.object(driver.base,"port_free"))
                stack.enter_context(patch.object(driver.base,"stop_owned_on_foreign",stopped))
                if space_failure:
                    stack.enter_context(patch.object(driver.os,"statvfs",return_value=Mock(f_bavail=1,f_frsize=1)))
                fixture_snapshot=driver.base.snapshot
                with self.assertRaises(SystemExit):driver.run_contract(c)
                self.assertIs(driver.base.write,original_write)
                self.assertIs(driver.base.snapshot,fixture_snapshot)
            self.assertIs(driver.base.snapshot,original_snapshot)
            self.assertEqual(len(captured),1)
            launch=json.loads((Path(c["raw_root"])/"launch.json").read_bytes())
            self.assertEqual(launch["argv"],captured[0])
            self.assertEqual(launch["controller_sha256"],driver.BASE_SHA)
            self.assertEqual(launch["base_controller_sha256"],driver.BASE_SHA)
            self.assertEqual(launch["host_controller_sha256"],c["host_controller_sha256"])
            self.assertEqual(launch["r31_profile"]["profile"],c["profile_diagnostic"])
            self.assertEqual(json.loads(driver.retained.native._option(captured[0],"--profiler-config")),
                driver.profiler_config(c["profile_diagnostic"]))
            self.assertEqual(json.loads(driver.retained.native._option(captured[0],"--compilation-config")),
                driver.retained.native.COMPILATION)
            env=driver.retained.native._environment(captured[0])
            self.assertEqual(env["VLLM_LOGGING_LEVEL"],"INFO")
            self.assertEqual(env["TRITON_CACHE_DIR"],"/scratch/compiled-cache")
            self.assertTrue((Path(c["raw_root"])/"compiled-cache").is_dir())
            self.assertEqual(launch["profile_cache_environment"],{"TRITON_CACHE_DIR":"/scratch/compiled-cache"})
            self.assertNotIn("--enforce-eager",captured[0])
            self.assertIn("--no-enable-prefix-caching",captured[0])
            if group=="G3":
                self.assertEqual(env["INDEPENDENT_GRAPH_HYPIC"],"1")
                self.assertTrue(env["PYTHONPATH"].startswith("/probe/graph_candidate/bootstrap:/probe:"))
                self.assertNotIn("INDEPENDENT_COMPACT_HYPIC",env)
            else:
                self.assertFalse(any(x.startswith("INDEPENDENT_")for x in env))
                self.assertFalse(any(":/probe"in x for x in captured[0]))
            if space_failure:stopped.assert_called_once_with("a"*64,image=c["image"])
            else:stopped.assert_not_called()

    def test_actual_native_base_consumes_graph_and_profiler_argv(self):
        self.actual_launch("G1")
    def test_actual_candidate_base_consumes_graph_and_profiler_argv(self):
        self.actual_launch("G3")
    def test_storage_guard_targets_only_exact_owned_cid(self):
        self.actual_launch("G3",space_failure=True)

if __name__=="__main__":unittest.main()
