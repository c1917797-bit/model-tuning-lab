"""Mock-only launcher tests: no model loading, service launch or NPU operation."""
from contextlib import ExitStack
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

SPEC = importlib.util.spec_from_file_location(
    "gdn_teacher_launcher_under_test",
    Path(__file__).resolve().parents[1] / "tools/run_gdn_teacher_capture.py")
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


class TeacherLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.tools = self.repo / "tools"
        self.tools.mkdir(parents=True)
        self.worker = self.tools / "gdn_teacher_capture_worker.py"
        self.worker.write_text("# mock observer\n")
        self.wrapper = self.tools / "run_gdn_teacher_capture.py"
        self.wrapper.write_text("# mock launcher identity\n")
        self.results = self.root / "results"
        self.results.mkdir()
        self.out = self.results / "new-capture"
        self.capture = self.root / "capture.json"
        self.capture.write_text('{"schema":"mock-capture/v1"}\n')
        self.build = self.root / "build.json"
        self.build.write_text("{}\n")
        self.model = self.root / "model"
        self.model.mkdir()
        for name in GATE.MODEL_HASHES:
            (self.model / name).write_text("{}\n")
        self.model_hashes = {name: GATE.shared.digest(self.model / name)
                             for name in GATE.MODEL_HASHES}
        self.base_args = [
            "--build-manifest", str(self.build),
            "--build-manifest-sha256", GATE.shared.digest(self.build),
            "--reference-manifest-sha256", "2" * 64,
            "--worker-sha256", GATE.shared.digest(self.worker),
            "--capture-manifest", str(self.capture),
            "--capture-manifest-sha256", GATE.shared.digest(self.capture),
            "--output-dir", str(self.out),
        ]

    def tearDown(self):
        self.temp.cleanup()

    def args(self):
        return GATE.parse_args(self.base_args)[1]

    def invoke(self, extra=(), inherited=None, build_error=None, runtime_error=None,
               socket_error=None, model_mismatch=False):
        with ExitStack() as stack:
            stack.enter_context(patch.object(GATE, "ROOT", self.repo))
            stack.enter_context(patch.object(GATE, "RESULT_ROOT", self.results))
            stack.enter_context(patch.object(GATE, "WORKER", self.worker))
            stack.enter_context(patch.object(GATE, "MODEL", str(self.model)))
            if not model_mismatch:
                stack.enter_context(patch.object(GATE, "MODEL_HASHES", self.model_hashes))
            stack.enter_context(patch.object(GATE, "__file__", str(self.wrapper)))
            stack.enter_context(patch.dict(GATE.os.environ,
                {"ASCEND_RT_VISIBLE_DEVICES": "0,1,2,3", **(inherited or {})}, clear=True))
            self.verify_build = stack.enter_context(patch.object(
                GATE.shared, "verify_build", side_effect=build_error,
                return_value={"plugin_version": "0.1.11", "wheel_sha256": "3" * 64}))
            self.verify_runtime = stack.enter_context(patch.object(
                GATE.shared, "verify_runtime", side_effect=runtime_error,
                return_value={"source_sha256": {"mock-runtime": "4" * 64}}))
            fake_socket = MagicMock()
            fake_socket.__enter__.return_value.bind.side_effect = socket_error
            stack.enter_context(patch.object(GATE.socket, "socket", return_value=fake_socket))
            def run_service(command, env, output, maximum, grace):
                self.assertTrue((output / "teacher-capture").is_dir())
                self.assertTrue((output / "service-manifest.json").is_file())
                self.assertEqual(maximum, 1800)
                self.assertEqual(grace, 30)
                return 0
            self.run = stack.enter_context(patch.object(
                GATE.shared, "run_service", side_effect=run_service))
            return GATE.main([*self.base_args, *extra])

    def test_service_is_dense_eager_tp4_bounded_context(self):
        command = GATE.service_command("python")
        self.assertEqual(command[0], "python")
        for name, value in (("--model", GATE.MODEL), ("--tensor-parallel-size", "4"),
                            ("--max-num-seqs", "1"), ("--max-model-len", "4096"),
                            ("--max-num-batched-tokens", "4096"),
                            ("--worker-cls", GATE.WORKER_CLASS)):
            self.assertEqual(command[command.index(name) + 1], value)
        self.assertIn("--enforce-eager", command)
        self.assertIn("--no-enable-prefix-caching", command)
        for banned in ("--hf-overrides", "--profiler-config", "--compilation-config",
                       "--async-scheduling"):
            self.assertNotIn(banned, command)

    def test_success_reuses_shared_provenance_and_process_lifecycle(self):
        self.assertEqual(self.invoke(), 0)
        self.verify_build.assert_called_once()
        self.verify_runtime.assert_called_once_with("2" * 64)
        self.run.assert_called_once()
        record = json.loads((self.out / "service-manifest.json").read_text())
        self.assertEqual(record["variant"], "dense128")
        self.assertEqual(record["shared_hf_head_k_dim"], 128)
        self.assertTrue(record["calibration_only"])
        self.assertFalse(record["request_policy"]["enable_thinking"])
        self.assertEqual(record["capture_manifest_sha256"], GATE.shared.digest(self.capture))
        self.assertEqual(record["model_metadata_sha256"], self.model_hashes)
        self.assertEqual(record["stop_request_path"], str(self.out / "stop.request"))

    def test_environment_clears_stale_capture_and_disables_optimizations(self):
        args = self.args()
        env, disabled, observer, inherited = GATE.service_environment(args, self.out, {
            "ASCEND_RT_VISIBLE_DEVICES": "0,1,2,3",
            "VLLM_ASCEND_DRRQR_ENABLE": "1",
            "VLLM_ASCEND_DRRQR_CAPTURE_DIR": "/old",
            "VLLM_ASCEND_DRRQR_PLAN_PATH": "/old-plan",
            "DRRQR_LAYERWISE_PROBE_DIR": "/old-probe",
            "DRRQR_ANY_OTHER_CAPTURE": "1",
            "DRRQR_GDN_TEACHER_MANIFEST": "/old-manifest",
            "VLLM_ASCEND_ENABLE_NZ": "1",
        })
        self.assertEqual(env["VLLM_ASCEND_DRRQR_ENABLE"], "0")
        self.assertTrue(all(value == "0" for value in disabled.values()))
        for old in ("VLLM_ASCEND_DRRQR_CAPTURE_DIR", "VLLM_ASCEND_DRRQR_PLAN_PATH",
                    "DRRQR_LAYERWISE_PROBE_DIR", "DRRQR_ANY_OTHER_CAPTURE"):
            self.assertNotIn(old, env)
        self.assertEqual(observer["DRRQR_GDN_TEACHER_MANIFEST"], str(self.capture))
        self.assertEqual(observer["DRRQR_GDN_TEACHER_MANIFEST_SHA256"], GATE.shared.digest(self.capture))
        self.assertEqual(observer["DRRQR_GDN_TEACHER_DIR"], str(self.out / "teacher-capture"))
        self.assertEqual(inherited["VLLM_ASCEND_DRRQR_ENABLE"], "1")

    def test_wrong_device_namespace_rejected(self):
        with self.assertRaises(ValueError):
            GATE.service_environment(self.args(), self.out, {"ASCEND_RT_VISIBLE_DEVICES": "4,5,6,7"})

    def test_repository_pythonpath_rejected(self):
        with self.assertRaises(ValueError):
            GATE.service_environment(self.args(), self.out, {
                "ASCEND_RT_VISIBLE_DEVICES": "0,1,2,3", "PYTHONPATH": str(GATE.ROOT)})

    def test_native_determinism_overrides_are_removed_not_encoded_as_zero(self):
        for value in ("0", "1", "false", "true", "strict", "invalid"):
            with self.subTest(value=value):
                env, disabled, observer, inherited = GATE.service_environment(
                    self.args(), self.out, {
                        "ASCEND_RT_VISIBLE_DEVICES": "0,1,2,3",
                        "HCCL_DETERMINISTIC": value,
                        "LCCL_DETERMINISTIC": value,
                    })
                for key in GATE.UNSET_RUNTIME_FLAGS:
                    self.assertNotIn(key, env)
                    self.assertNotIn(key, disabled)
                    self.assertNotIn(key, observer)
                    self.assertEqual(inherited[key], value)

    def test_manifest_distinguishes_unset_native_flags_from_disabled_flags(self):
        self.assertEqual(self.invoke(inherited={
            "HCCL_DETERMINISTIC": "0", "LCCL_DETERMINISTIC": "1"}), 0)
        env = self.run.call_args.args[1]
        record = json.loads((self.out / "service-manifest.json").read_text())
        self.assertEqual(record["unset_runtime_flags"], {
            "HCCL_DETERMINISTIC": None, "LCCL_DETERMINISTIC": None})
        for key in GATE.UNSET_RUNTIME_FLAGS:
            self.assertNotIn(key, env)
            self.assertNotIn(key, record["disabled_optimization_flags"])
        self.assertEqual(record["inherited_runtime_environment"]["HCCL_DETERMINISTIC"], "0")
        self.assertEqual(record["inherited_runtime_environment"]["LCCL_DETERMINISTIC"], "1")
        self.assertIn("not explicit zero/false", record["native_determinism_policy"])

    def test_forbidden_diagnostic_determinism_configuration_rejected(self):
        with self.assertRaises(ValueError):
            GATE.service_environment(self.args(), self.out, {
                "ASCEND_RT_VISIBLE_DEVICES": "0,1,2,3", "DRRQR_DIAGNOSTIC_DETERMINISM": "1"})

    def test_service_budget_cannot_exceed_1800(self):
        with self.assertRaises(SystemExit):
            GATE.parse_args([*self.base_args, "--max-service-seconds", "1801"])

    def test_bad_hash_is_rejected(self):
        with self.assertRaises(SystemExit):
            GATE.parse_args([*self.base_args, "--worker-sha256", "not-a-sha"])

    def test_relative_manifest_is_rejected(self):
        with self.assertRaises(SystemExit):
            GATE.parse_args([*self.base_args, "--capture-manifest", "relative.json"])

    def test_existing_output_is_preserved_and_no_service_runs(self):
        self.out.mkdir()
        (self.out / "old.txt").write_text("preserve")
        with self.assertRaises(SystemExit):
            self.invoke()
        self.assertEqual((self.out / "old.txt").read_text(), "preserve")
        self.run.assert_not_called()

    def test_worker_hash_mismatch_prevents_service(self):
        with self.assertRaises(ValueError):
            self.invoke(extra=("--worker-sha256", "0" * 64))
        self.run.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_capture_manifest_hash_mismatch_prevents_service(self):
        with self.assertRaises(ValueError):
            self.invoke(extra=("--capture-manifest-sha256", "0" * 64))
        self.run.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_build_mismatch_prevents_service(self):
        with self.assertRaises(ValueError):
            self.invoke(build_error=ValueError("build mismatch"))
        self.run.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_runtime_mismatch_prevents_service(self):
        with self.assertRaises(ValueError):
            self.invoke(runtime_error=ValueError("runtime mismatch"))
        self.run.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_checkpoint_metadata_mismatch_prevents_service(self):
        with self.assertRaises(ValueError):
            self.invoke(model_mismatch=True)
        self.run.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_port_collision_does_not_replace_existing_owner(self):
        with self.assertRaises(OSError):
            self.invoke(socket_error=OSError("port occupied"))
        self.run.assert_not_called()
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
