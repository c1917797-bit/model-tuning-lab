"""Focused CPU wiring controls; mocked owner/argv records are not device proof."""
import copy
import hashlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

WORKSTREAM = Path(__file__).resolve().parent.parent
if str(WORKSTREAM) not in sys.path:
    sys.path.insert(0, str(WORKSTREAM))
from host_audits import r27_graph_controller as target


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Controls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hypic-r27-cpu-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "host_audits").mkdir()
        (self.root / target.ENTRY).write_bytes(Path(target.__file__).read_bytes())
        (self.root / target.BASE_ENTRY).write_bytes((WORKSTREAM / target.BASE_ENTRY).read_bytes())
        self.saved = []
        self.operations = []
        def original_write(root, name, data):
            self.operations.append("write:" + name)
            self.saved.append((root, name, copy.deepcopy(data), data))
        self.original_write = original_write
        self.owner = types.SimpleNamespace(
            __file__=str(self.root / target.BASE_ENTRY), write=original_write)
        self.owner.run_contract = self.owner_run
        self.contract = {
            "controller_sha256": digest(self.root / target.ENTRY),
            "base_controller_sha256": target.BASE_SHA256,
            "host_controller_source_sha256": {
                target.ENTRY: digest(self.root / target.ENTRY),
                target.BASE_ENTRY: target.BASE_SHA256},
            "baseline_host_source_sha256": {target.BASE_ENTRY: target.BASE_SHA256},
            "physical_npus": [0, 1, 2, 3], "tp": 4, "enforce_eager": False,
            "image": target.IMAGE, "performance_group": "G1",
            "raw_root": str(self.root / "new-immutable-raw"),
            "absolute_stop_utc": "2099-01-01T00:00:00Z",
            "graph_runtime": {
                "profile": target.PROFILE, "candidate_enabled": False,
                "compilation_mode": 3, "cudagraph_mode": "FULL_DECODE_ONLY",
                "capture_sizes": list(target.CAPTURE_SIZES),
                "official_debug_logging": True,
                "official_compilation_source_sha256": target.ENUM_SOURCE_SHA256}}
        self.native_args = [
            "docker", "run", "-e", "ASCEND_RT_VISIBLE_DEVICES=0,1,2,3",
            target.IMAGE, "serve", "/model", "--compilation-config",
            json.dumps({"cudagraph_mode": "FULL_DECODE_ONLY",
                        "cudagraph_capture_sizes": target.CAPTURE_SIZES})]
        self.argv = list(self.native_args)
        self.after_launch = None

    def owner_run(self, contract):
        self.assertIs(contract, self.contract)
        self.owner.write(Path(contract["raw_root"]), "preflight.json", {"unchanged": True})
        data = {"argv": self.argv, "controller_sha256": target.BASE_SHA256,
                "diagnostic_sources": contract.get("cache_diagnostic"),
                "git_commit": "synthetic-owner-control"}
        self.owner.write(Path(contract["raw_root"]), "launch.json", data)
        # This is the exact order in the fixed base source: write then command(args).
        self.operations.append("command")
        self.executed_argv = self.argv
        if self.after_launch:
            self.after_launch()
        return "mock-owner-result"

    def enable(self):
        self.contract["performance_group"] = "G3"
        self.contract["graph_runtime"]["candidate_enabled"] = True
        for name in (*target.GRAPH_RUNTIME_SOURCES, "graph-config.json"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# synthetic CPU source fixture\n")
        self.manifest = {
            "graph_profile": target.PROFILE, "config": "graph-config.json",
            "source_sha256": {name: digest(self.root / name) for name in (
                *target.GRAPH_RUNTIME_SOURCES, "graph-config.json")}}
        self.manifest_path = self.root / "graph-manifest.json"
        self.refresh_manifest()
        self.argv = self.native_args[:2] + [
            "-v", "/synthetic/workstream:/probe:ro",
            "-e", "PYTHONPATH=/probe/compact_bootstrap:/probe:/pinned/inherited",
            "-e", "INDEPENDENT_CACHE_DIAGNOSTIC=1",
            "-e", "INDEPENDENT_DIAGNOSTIC_ROOT=/scratch/diagnostics",
            "-e", "INDEPENDENT_DIAGNOSTIC_BATCHES=2",
            "-e", "INDEPENDENT_COMPACT_HYPIC=1",
            "-e", "INDEPENDENT_COMPACT_MANIFEST=/probe/graph-manifest.json",
            "-e", "INDEPENDENT_COMPACT_RAW=/scratch/diagnostics"] + self.native_args[2:]

    def refresh_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest))
        self.contract["cache_diagnostic"] = {
            "compact_manifest": "graph-manifest.json",
            "source_sha256": dict(self.manifest["source_sha256"],
                                  **{"graph-manifest.json": digest(self.manifest_path)})}

    def check(self):
        return target.check_contract(self.contract, source_root=self.root, base_module=self.owner)

    def run_owner(self):
        return target.run_contract(self.contract, source_root=self.root, base_module=self.owner)

    def launch(self):
        return next(row for row in self.saved if row[1] == "launch.json")

    def test_check_only_never_calls_owner_or_writes(self):
        self.owner.run_contract = mock.Mock(side_effect=AssertionError("device path"))
        checked = self.check()
        self.assertFalse(checked["device_run"])
        self.assertFalse(checked["device_admission_performed"])
        self.assertEqual(checked["host_controller_source_bindings"], 2)
        self.assertEqual(self.saved, [])
        self.owner.run_contract.assert_not_called()

    def test_cli_defaults_to_check_without_run(self):
        cp = self.root / "contract.json"
        cp.write_text(json.dumps(self.contract))
        with mock.patch.object(target, "check_contract", return_value={"device_run": False}) as checked, \
             mock.patch.object(target, "run_contract") as run, mock.patch("builtins.print"):
            target.main(["--contract", str(cp)])
        checked.assert_called_once()
        run.assert_not_called()

    def test_native_g1_is_real_native_graph_without_probe(self):
        self.assertEqual(self.run_owner(), "mock-owner-result")
        logged = self.launch()[2]
        actual = self.launch()[3]
        self.assertIs(actual["argv"], self.executed_argv)
        self.assertEqual(logged["argv"], self.executed_argv)
        self.assertFalse(any("/probe" in value or "INDEPENDENT_" in value
                             for value in self.executed_argv))
        self.assertNotIn("--enforce-eager", self.executed_argv)
        self.assertIn("VLLM_LOGGING_LEVEL=DEBUG", self.executed_argv)
        self.assertLess(self.executed_argv.index("VLLM_LOGGING_LEVEL=DEBUG"),
                        self.executed_argv.index(target.IMAGE))
        self.assertEqual(logged["graph_runtime"]["common_environment_added"],
                         ["VLLM_LOGGING_LEVEL=DEBUG"])
        config = json.loads(self.executed_argv[self.executed_argv.index("--compilation-config")+1])
        self.assertEqual(config["mode"], 3)
        self.assertEqual(config["cudagraph_mode"], "FULL_DECODE_ONLY")
        self.assertIsNone(logged["graph_runtime"]["bootstrap"])
        self.assertIs(self.owner.write, self.original_write)

    def test_graph_g3_log_and_command_share_same_mutated_argv(self):
        self.enable()
        before = copy.deepcopy(self.contract)
        self.run_owner()
        logged, actual = self.launch()[2:]
        self.assertIs(actual["argv"], self.executed_argv)
        self.assertEqual(logged["argv"], self.executed_argv)
        self.assertEqual(self.operations, ["write:preflight.json", "write:launch.json", "command"])
        self.assertIn("PYTHONPATH=/probe/graph_candidate/bootstrap:/probe:/pinned/inherited",
                      self.executed_argv)
        for value in ("INDEPENDENT_GRAPH_HYPIC=1",
                      "INDEPENDENT_GRAPH_MANIFEST=/probe/graph-manifest.json",
                      "INDEPENDENT_GRAPH_RAW=/scratch/diagnostics",
                      "INDEPENDENT_CACHE_DIAGNOSTIC=1", "VLLM_LOGGING_LEVEL=DEBUG"):
            self.assertIn(value, self.executed_argv)
        self.assertFalse(any(x.startswith("INDEPENDENT_COMPACT_") for x in self.executed_argv))
        self.assertEqual(len(logged["graph_runtime"]["environment_removed"]), 3)
        self.assertEqual(len(logged["graph_runtime"]["environment_added"]), 3)
        self.assertEqual(self.contract, before)

    def test_wrapper_and_real_base_identity_are_distinct(self):
        self.run_owner()
        logged = self.launch()[2]
        self.assertEqual(logged["controller_sha256"], target.BASE_SHA256)
        self.assertEqual(logged["base_controller_sha256"], target.BASE_SHA256)
        self.assertEqual(logged["host_controller_sha256"], self.contract["controller_sha256"])
        self.assertNotEqual(logged["controller_sha256"], logged["host_controller_sha256"])

    def test_non_launch_writes_are_passed_through(self):
        self.run_owner()
        self.assertEqual(self.saved[0][2], {"unchanged": True})
        self.assertNotIn("graph_runtime", self.saved[0][2])

    def test_exception_restores_only_owned_write(self):
        self.after_launch = lambda: (_ for _ in ()).throw(RuntimeError("mock failure"))
        with self.assertRaisesRegex(RuntimeError, "mock failure"):
            self.run_owner()
        self.assertIs(self.owner.write, self.original_write)
        self.assertFalse(target._OWNED_RUN.locked())

    def test_foreign_replacement_is_not_clobbered_on_failure(self):
        foreign = lambda *a: None
        def change():
            self.owner.write = foreign
            raise RuntimeError("mock foreign replacement")
        self.after_launch = change
        with self.assertRaises(RuntimeError):
            self.run_owner()
        self.assertIs(self.owner.write, foreign)
        self.assertFalse(target._OWNED_RUN.locked())

    def reject_check(self, change):
        change()
        with self.assertRaises((ValueError, OSError)):
            self.check()
        self.assertEqual(self.saved, [])

    def test_false_flag_cannot_carry_algorithm_manifest(self):
        self.enable()
        self.contract["graph_runtime"]["candidate_enabled"] = False
        self.contract["performance_group"] = "G1"
        self.reject_check(lambda: None)

    def test_true_flag_requires_algorithm_manifest(self):
        self.contract["graph_runtime"]["candidate_enabled"] = True
        self.contract["performance_group"] = "G3"
        self.reject_check(lambda: None)

    def test_graph_flag_is_strict_bool(self):
        self.reject_check(lambda: self.contract["graph_runtime"].update(candidate_enabled=1))

    def test_graph_canary_group_without_formal_performance_label(self):
        self.contract["graph_canary_group"] = self.contract.pop("performance_group")
        self.assertTrue(self.check()["configuration_valid"])

    def test_conflicting_canary_and_performance_groups_are_rejected(self):
        self.contract["graph_canary_group"] = "G3"
        self.reject_check(lambda: None)

    def test_eager_true_is_rejected(self):
        self.reject_check(lambda: self.contract.update(enforce_eager=True))

    def test_none_compile_profile_is_rejected(self):
        self.reject_check(lambda: self.contract["graph_runtime"].update(compilation_mode=0))

    def test_enum_source_drift_is_rejected(self):
        self.reject_check(lambda: self.contract["graph_runtime"].update(
            official_compilation_source_sha256="0"*64))

    def test_canary_requires_explicit_common_debug_profile(self):
        self.reject_check(lambda: self.contract["graph_runtime"].update(
            official_debug_logging=False))

    def test_preexisting_logging_override_is_not_silently_replaced(self):
        self.argv[2:2] = ["-e", "VLLM_LOGGING_LEVEL=INFO"]
        with self.assertRaises(ValueError):
            self.run_owner()
        self.assertIs(self.owner.write, self.original_write)

    def test_wrapper_source_binding_is_required(self):
        self.reject_check(lambda: self.contract["host_controller_source_sha256"].update(
            {target.ENTRY: target.BASE_SHA256}))

    def test_base_identity_is_not_faked_with_host_hash(self):
        self.reject_check(lambda: self.contract.update(
            base_controller_sha256=self.contract["controller_sha256"]))

    def test_source_drift_is_rejected(self):
        self.reject_check(lambda: (self.root / target.BASE_ENTRY).write_bytes(b"changed"))

    def test_wrong_graph_manifest_profile_is_rejected(self):
        self.enable()
        self.manifest["graph_profile"] = "wrong"
        self.refresh_manifest()
        self.reject_check(lambda: None)

    def test_missing_graph_loader_binding_is_rejected(self):
        self.enable()
        del self.manifest["source_sha256"]["graph_candidate/worker_loader.py"]
        self.refresh_manifest()
        self.reject_check(lambda: None)

    def test_missing_graph_activation_binding_is_rejected(self):
        self.enable()
        del self.manifest["source_sha256"]["graph_candidate/activation.py"]
        self.refresh_manifest()
        self.reject_check(lambda: None)

    def test_native_g1_probe_argv_is_rejected_before_launch_write(self):
        self.argv[2:2] = ["-e", "INDEPENDENT_CACHE_DIAGNOSTIC=1"]
        with self.assertRaises(ValueError):
            self.run_owner()
        self.assertFalse(any(row[1] == "launch.json" for row in self.saved))
        self.assertIs(self.owner.write, self.original_write)

    def test_eager_argv_is_rejected_even_when_contract_is_false(self):
        self.argv.append("--enforce-eager")
        with self.assertRaises(ValueError):
            self.run_owner()
        self.assertIs(self.owner.write, self.original_write)

    def test_missing_old_namespace_flag_fails_closed(self):
        self.enable()
        i = self.argv.index("INDEPENDENT_COMPACT_HYPIC=1")
        del self.argv[i-1:i+1]
        with self.assertRaises(ValueError):
            self.run_owner()
        self.assertIs(self.owner.write, self.original_write)

    def test_immutable_existing_raw_root_is_rejected(self):
        self.reject_check(lambda: Path(self.contract["raw_root"]).mkdir())

    def test_nested_or_concurrent_controller_is_rejected(self):
        target._OWNED_RUN.acquire()
        try:
            with self.assertRaises(RuntimeError):
                self.run_owner()
        finally:
            target._OWNED_RUN.release()


if __name__ == "__main__":
    unittest.main()
