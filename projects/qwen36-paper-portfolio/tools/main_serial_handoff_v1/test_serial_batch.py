"""Control-flow fixtures/local child processes only; no Docker/NPU/AW calls."""
import ast
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import serial_batch as B
import skvq010_adapter as A

SKVQ_LOCAL = Path("C:/Users/Huawei/AppData/Local/Temp/skvq-preprojection-current72h-20261010-010") if os.name == "nt" else A.PROFILE_ROOT


class FixtureBackend:
    def __init__(self, exits=(0, 0), unknown=False, release_error=False, wrong_source=False, reused=False):
        self.exits = iter(exits)
        self.calls = []
        self.unknown = unknown
        self.release_error = release_error
        self.wrong_source = wrong_source
        self.reused = reused
        self.clock = 100
        self.first = "worker original ValueError"

    def now(self):
        return self.clock

    def self_guard(self):
        return None

    def run_adapter(self, t, action, ticket_ref, terminal_ref, output):
        self.calls.append((action, t["id"]))
        if action == "prepare":
            value = dict(schema="main.serial-fresh-readonly/v1", source_ref=t["source_ref"], owner=t["owner"],
                         physical_idle=[4, 5, 6, 7], ordinary_batch_overhead_bytes=B.SELF_RSS,
                         original_host_admission_unchanged=True, fixture_only=True)
        else:
            if self.release_error:
                raise ValueError("permission or owner identity failure")
            value = dict(schema="main.serial-exact-owned-release/v1", source_ref=t["source_ref"], owner=t["owner"],
                         child_terminal_ref=terminal_ref, original_result_ref=B.reference(Path(t["output_root"]) / t["result_name"]),
                         exact_owned_release=True, physical_idle=[4, 5, 6, 7], external_stopped=False,
                         original_failed=B.obj(B.reference(Path(t["output_root"]) / t["result_name"]))["status"] == "FAILED",
                         first_fault=self.first, AW_terminal_claimed=False, fixture_only=True)
            if self.wrong_source:
                value["source_ref"] = dict(t["source_ref"], sha256="0" * 64)
        B.publish(output, value)
        return value

    def launch(self, t, output):
        self.calls.append(("launch", t["id"]))
        if self.reused:
            raise ValueError("PID still present/reused after actual wait")
        if self.unknown:
            return dict(schema="main.serial-child-unknown/v1", AW_terminal_claimed=False,
                        reason="AW lookup not_found is not a completion")
        exit_code = next(self.exits)
        Path(t["output_root"]).mkdir()
        B.publish(Path(t["output_root"]) / t["result_name"], {"status": "FAILED" if exit_code else "complete",
                  "primary": self.first if exit_code else None, "fixture_only": True})
        return dict(schema="main.serial-child-terminal/v1", argv=t["argv"], source_ref=t["source_ref"],
                    exit_code=exit_code, reaped=True, AW_terminal_claimed=False, fixture_only=True)


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="serial-handoff-fixture-")
        self.root = Path(self.temp.name).resolve()
        self.pin = B.publish(self.root / "source.json", {"fixture_only": True})
        self.entry = B.publish(self.root / "entry.py", {"fixture_only": True, "kind": "entry"})
        self.adapter = B.publish(self.root / "adapter.py", {"fixture_only": True, "kind": "adapter"})

    def tearDown(self):
        self.temp.cleanup()

    def ticket(self, name="one"):
        value = dict(id=name, source_ref=self.pin, entry_ref=self.entry, adapter_ref=self.adapter,
                     argv=[sys.executable, self.entry["path"], "--source", self.pin["sha256"]],
                     output_root=str(self.root / (name + "-experiment")), result_name="HOST_RESULT.json",
                     owner="fixture-owner-" + name, image="sha256:" + "6" * 64, physical=[4, 5, 6, 7],
                     protected=[0, 1, 2, 3], wall_seconds=10, cutoff_epoch=1000)
        review = dict(schema="main.reviewed-stage-admission/v1", reviewed_by="MAIN", ready_for_gate=True,
                      state="ACTUAL_PREREQUISITES_CONSUMED", gate="model-screen", ticket_id=name,
                      source_ref=self.pin, entry_ref=self.entry, adapter_ref=self.adapter, argv=value["argv"],
                      output_root=value["output_root"], owner=value["owner"], missing=[],
                      actual_prerequisites=[dict(artifact_ref=self.pin, consumer_ref=self.pin, acceptance_ref=self.pin)], fixture_only=True)
        review["stage_policy"] = {key: value[key] for key in ("image", "physical", "protected", "wall_seconds", "cutoff_epoch", "result_name")}
        value["review_ref"] = B.publish(self.root / (name + "-review.json"), review)
        return value

    def plan(self, *tickets):
        return dict(schema="main.finite-serial-stage-plan/v1", reviewed_by="MAIN", stages=list(tickets),
                    empty_reason="no MAIN-reviewed successor available", batch_resources=dict(host_cpu_shared=1,
                    max_rss_bytes=B.SELF_RSS, additional_ordinary_ram_bytes=B.SELF_RSS, fresh_ancestor_admission_required=True))

    def run_plan(self, plan, backend=None):
        return B.execute(plan, self.root / "batch", backend or FixtureBackend())

    def test_success_release_then_exact_next(self):
        backend = FixtureBackend()
        result = self.run_plan(self.plan(self.ticket("one"), self.ticket("two")), backend)
        self.assertEqual(result["state"], "FINITE_QUEUE_EXHAUSTED")
        self.assertEqual(backend.calls, [("prepare", "one"), ("launch", "one"), ("release", "one"),
                                         ("prepare", "two"), ("launch", "two"), ("release", "two")])
        self.assertFalse(result["AW_terminal_claimed"])
        self.assertFalse(result["actual_cross_paper_zero_idle_claimed"])

    def test_failed_worker_repair_without_same_retry(self):
        backend = FixtureBackend(exits=(1, 0))
        result = self.run_plan(self.plan(self.ticket("one"), self.ticket("two")), backend)
        self.assertEqual([x["state"] for x in result["stages"]], ["REPAIR", "STAGE_TERMINAL_RELEASED"])
        release = B.obj(result["stages"][0]["release_ref"])
        self.assertEqual(release["first_fault"], "worker original ValueError")
        self.assertEqual(sum(c == ("launch", "one") for c in backend.calls), 1)

    def test_release_owner_failure_blocks_next(self):
        backend = FixtureBackend(release_error=True)
        result = self.run_plan(self.plan(self.ticket("one"), self.ticket("two")), backend)
        self.assertEqual(result["state"], "UNKNOWN_OR_BLOCKED")
        self.assertNotIn(("prepare", "two"), backend.calls)
        self.assertIn("permission", result["stages"][0]["first_fault"])

    def test_lost_handle_cannot_promote_disk_result(self):
        backend = FixtureBackend(unknown=True)
        result = self.run_plan(self.plan(self.ticket("one"), self.ticket("two")), backend)
        self.assertEqual(result["state"], "UNKNOWN_OR_BLOCKED")
        self.assertNotIn(("release", "one"), backend.calls)
        self.assertNotIn(("launch", "two"), backend.calls)

    def test_reused_pid_stops_not_absence(self):
        backend = FixtureBackend(reused=True)
        result = self.run_plan(self.plan(self.ticket("one"), self.ticket("two")), backend)
        self.assertEqual(result["state"], "UNKNOWN_OR_BLOCKED")
        self.assertNotIn(("release", "one"), backend.calls)

    def test_release_wrong_source_blocks(self):
        result = self.run_plan(self.plan(self.ticket()), FixtureBackend(wrong_source=True))
        self.assertEqual(result["state"], "UNKNOWN_OR_BLOCKED")

    def test_empty_queue_records_real_reason_no_load(self):
        backend = FixtureBackend()
        result = self.run_plan(self.plan(), backend)
        self.assertEqual(result["state"], "NO_READY_TICKET")
        self.assertEqual(backend.calls, [])
        self.assertEqual(result["idle_reason"], "no MAIN-reviewed successor available")

    def test_software_prepared_is_not_ready(self):
        ticket = self.ticket()
        review = B.obj(ticket["review_ref"])
        review["state"] = "SOURCE_PREPARED"
        ticket["review_ref"] = B.publish(self.root / "only-software.json", review)
        result = self.run_plan(self.plan(ticket))
        self.assertEqual(result["stages"][0]["state"], "PREPARATION_MISSING")

    def test_missing_gate_dependency_blocked(self):
        ticket = self.ticket()
        review = B.obj(ticket["review_ref"])
        review["actual_prerequisites"] = []
        ticket["review_ref"] = B.publish(self.root / "no-dependencies.json", review)
        self.assertEqual(self.run_plan(self.plan(ticket))["stages"][0]["state"], "PREPARATION_MISSING")

    def test_predecessor_hash_drift_blocked(self):
        ticket = self.ticket()
        Path(self.pin["path"]).write_bytes(b"different\n")
        self.assertEqual(self.run_plan(self.plan(ticket))["stages"][0]["state"], "PREPARATION_MISSING")

    def test_existing_output_never_retried(self):
        ticket = self.ticket()
        Path(ticket["output_root"]).mkdir()
        self.assertEqual(self.run_plan(self.plan(ticket))["stages"][0]["state"], "PREPARATION_MISSING")

    def test_duplicate_ticket_rejected_before_dispatch(self):
        ticket = self.ticket()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.run_plan(self.plan(ticket, ticket))

    def test_fixed_deadline_no_shorter_stage(self):
        backend = FixtureBackend()
        backend.clock = 995
        result = self.run_plan(self.plan(self.ticket()), backend)
        self.assertEqual(result["stages"][0]["state"], "PREPARATION_MISSING")
        self.assertEqual(backend.calls, [])

    def test_time_spent_in_fresh_check_cannot_cross_fit(self):
        backend = FixtureBackend()
        original = backend.run_adapter
        def delay(*args):
            value = original(*args)
            backend.clock = 999
            return value
        backend.run_adapter = delay
        result = self.run_plan(self.plan(self.ticket()), backend)
        self.assertEqual(result["stages"][0]["state"], "PREPARATION_MISSING")
        self.assertNotIn(("launch", "one"), backend.calls)

    def test_no_pending_alias_after_successful_publication(self):
        self.assertEqual(list(self.root.glob("*.pending-*")), [])
        with self.assertRaisesRegex(ValueError, "overwrite"):
            B.publish(self.root / "source.json", {})

    def test_bool_bytes_not_a_valid_ref(self):
        with self.assertRaisesRegex(ValueError, "strict three"):
            B.checked(dict(self.pin, bytes=True))

    def test_default_off_real_cli_no_ticket_reads(self):
        process = subprocess.run([sys.executable, "-I", "-B", str(Path(B.__file__)), "--reviewed-plan", "MISSING"], capture_output=True, text=True, timeout=5)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout), dict(default_enabled=False, stage_dispatched=False))

    def test_optin_required_real_cli(self):
        env = dict(os.environ)
        env.pop("MAIN_FINITE_SERIAL_HANDOFF_ENABLE", None)
        process = subprocess.run([sys.executable, "-I", "-B", str(Path(B.__file__)), "--execute"], env=env, capture_output=True, text=True, timeout=5)
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("explicit MAIN opt-in", process.stderr)

    def test_real_local_child_wait_not_aw_envelope(self):
        process = subprocess.Popen([sys.executable, "-I", "-B", "-c", "raise SystemExit(7)"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 7)
        self.assertEqual((stdout, stderr), (b"", b""))
        # This real stdlib wait test supplies no device/owner/numerical verdict.

    def test_ticket_local_missing_does_not_starve_ready_successor(self):
        first = self.ticket("one")
        review = B.obj(first["review_ref"])
        review["missing"] = ["actual-new-software-source"]
        first["review_ref"] = B.publish(self.root / "missing-review.json", review)
        backend = FixtureBackend(exits=(0,))
        result = self.run_plan(self.plan(first, self.ticket("two")), backend)
        self.assertEqual([x["state"] for x in result["stages"]], ["PREPARATION_MISSING", "STAGE_TERMINAL_RELEASED"])
        self.assertEqual(backend.calls, [("prepare", "two"), ("launch", "two"), ("release", "two")])

    def test_unknown_global_fresh_resource_does_not_skip_to_next(self):
        backend = FixtureBackend()
        def refused(*args):
            raise ValueError("fresh common ancestor RAM unknown")
        backend.run_adapter = refused
        result = self.run_plan(self.plan(self.ticket("one"), self.ticket("two")), backend)
        self.assertEqual(result["state"], "UNKNOWN_OR_BLOCKED")
        self.assertEqual(len(result["stages"]), 1)

    @unittest.skipUnless(os.name == "posix", "Linux /proc LocalBackend.launch regression must run on MAIN; Windows is not process-identity proof")
    def test_actual_local_backend_launch_exit1_reaped_and_original_logs(self):
        script = self.root / "actual-child.py"
        script.write_text("import sys,time\nprint('fixture-only begin',flush=True)\ntime.sleep(.2)\nprint('fixture-only first fault',file=sys.stderr,flush=True)\nraise SystemExit(1)\n")
        directory = self.root / "real-launch"
        directory.mkdir()
        ticket = self.ticket("local-actual")
        ticket["argv"] = [sys.executable, "-I", "-B", str(script)]
        ticket["wall_seconds"] = 5
        terminal = B.LocalBackend().launch(ticket, directory)
        self.assertEqual(terminal["schema"], "main.serial-child-terminal/v1")
        self.assertEqual(terminal["exit_code"], 1)
        self.assertTrue(terminal["reaped"])
        self.assertFalse(Path("/proc/%d" % terminal["pid"]).exists())
        self.assertEqual(terminal["source_ref"], ticket["source_ref"])
        self.assertEqual(terminal["stdout_ref"], B.reference(directory / "stdout.raw"))
        self.assertEqual(terminal["stderr_ref"], B.reference(directory / "stderr.raw"))
        self.assertIn("fixture-only first fault", (directory / "stderr.raw").read_text())
        self.assertFalse(terminal["AW_terminal_claimed"])


def native_validator():
    """Execute the exact original pure method AST, not guessed validation logic."""
    path = SKVQ_LOCAL / "MAIN_HOST.py"
    tree = ast.parse(path.read_bytes())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Control")
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "validate")
    namespace = {"require": B.need, "IMAGE": A.IMAGE, "OWNER": A.OWNER, "GIB": 2 ** 30}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(path), "exec"), namespace)
    return namespace["validate"]


class OriginalReleaseValidatorTests(unittest.TestCase):
    def pair(self):
        row = dict(cid="a" * 64, name="fixture-capture", source="b" * 64, mem=64 * 2 ** 30,
                   cpuset="1,2,3,144", devices={"/dev/davinci4": "/dev/davinci0"},
                   mounts={"/adakv-results": ("/cache/fixture/candidate", True)}, env={"TEST": "1"})
        raw = dict(Id=row["cid"], Name="/" + row["name"], Image=A.IMAGE, ExecIDs=None,
                   State=dict(Running=False, Pid=0, OOMKilled=False),
                   Config=dict(Image=A.IMAGE, Entrypoint=["/bin/bash"], Cmd=["-c", "exec /bin/sleep infinity"],
                               Labels={"model-tuning-lab.owner": A.OWNER, "model-tuning-lab.source": row["source"]}, Env=["TEST=1"]),
                   HostConfig=dict(Privileged=False, Memory=row["mem"], MemorySwap=row["mem"], NanoCpus=4 * 10 ** 9,
                                   CpusetCpus=row["cpuset"], CgroupnsMode="host", NetworkMode="none", IpcMode="private",
                                   ShmSize=2 * 2 ** 30, PidsLimit=1024, CapDrop=["ALL"], SecurityOpt=["no-new-privileges"],
                                   DeviceRequests=None, DeviceCgroupRules=None, Devices=[dict(PathOnHost="/dev/davinci4", PathInContainer="/dev/davinci0", CgroupPermissions="rwm")]),
                   Mounts=[dict(Type="bind", Destination="/adakv-results", Source="/cache/fixture/candidate", RW=True)])
        return row, raw

    def test_exact_original_method_positive(self):
        row, raw = self.pair()
        self.assertIs(native_validator()(None, raw, row), raw)

    def test_foreign_owner_negative(self):
        row, raw = self.pair()
        raw["Config"]["Labels"]["model-tuning-lab.owner"] = "foreign"
        with self.assertRaisesRegex(ValueError, "exact owned"):
            native_validator()(None, raw, row)

    def test_source_drift_negative(self):
        row, raw = self.pair()
        raw["Config"]["Labels"]["model-tuning-lab.source"] = "c" * 64
        with self.assertRaises(ValueError):
            native_validator()(None, raw, row)

    def test_protected_device_negative(self):
        row, raw = self.pair()
        raw["HostConfig"]["Devices"][0]["PathOnHost"] = "/dev/davinci0"
        with self.assertRaisesRegex(ValueError, "exact Devices"):
            native_validator()(None, raw, row)

    def test_mount_or_memory_drift_negative(self):
        row, raw = self.pair()
        raw["HostConfig"]["Memory"] -= 1
        with self.assertRaises(ValueError):
            native_validator()(None, raw, row)

    def test_adapter_has_no_stop_create_exec(self):
        tree = ast.parse(Path(A.__file__).read_bytes())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "command")
        body = ast.get_source_segment(Path(A.__file__).read_text(), fn)
        self.assertNotIn('"stop"', body)
        self.assertNotIn('"create"', body)
        self.assertNotIn('"exec"', body)


class OriginalAWTerminalTests(unittest.TestCase):
    def original(self, code=1):
        argv = ["/usr/bin/env", "MAIN_SKVQ_HOST_ENABLE=1", "fixture-only"]
        value = dict(schema="agentweb.operation/v1", terminal=True, status="completed", succeeded=code == 0,
                     error=None if code == 0 else "exit code", operation=dict(ok=True, routeDecision="peer_direct",
                     targetPeerId="lgw_a6109c51076a4a2c9d2674ca5a8704a0", result=dict(state="completed",
                     record=dict(state="completed", command=argv[0], args=argv[1:], exitCode=code, error=None, timedOut=False, cancelled=False))))
        return value, argv

    def test_original_exit1_not_numerical_pass(self):
        value, argv = self.original()
        self.assertEqual(A.actual_aw_terminal(value, argv)["exitCode"], 1)

    def test_original_exit0(self):
        value, argv = self.original(0)
        self.assertEqual(A.actual_aw_terminal(value, argv)["exitCode"], 0)

    def test_not_found_cannot_be_terminal(self):
        value, argv = self.original()
        value["terminal"] = False
        with self.assertRaisesRegex(ValueError, "real completed"):
            A.actual_aw_terminal(value, argv)

    def test_original_transport_failure_not_exit1(self):
        value, argv = self.original()
        value["error"] = "target_unavailable"
        with self.assertRaisesRegex(ValueError, "actual exit1"):
            A.actual_aw_terminal(value, argv)

    def test_original_cancelled_not_completed(self):
        value, argv = self.original()
        value["operation"]["result"]["record"]["cancelled"] = True
        with self.assertRaises(ValueError):
            A.actual_aw_terminal(value, argv)

    def test_original_foreign_argv_refused(self):
        value, argv = self.original()
        with self.assertRaisesRegex(ValueError, "exact completed"):
            A.actual_aw_terminal(value, argv + ["retry"])

    def test_unknown_exit_code_refused(self):
        value, argv = self.original()
        value["operation"]["result"]["record"]["exitCode"] = None
        with self.assertRaises(ValueError):
            A.actual_aw_terminal(value, argv)

    def test_actual_052b_original_exact_failure_contract(self):
        if os.name != "nt":
            path = Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN_SKVQ010_FAILED_052B_ORIGINAL_20261010.json")
        else:
            path = Path("C:/Users/Huawei/AppData/Local/Temp/c160-skvq010-actual-failure/MAIN_ORIGINAL_052B.json")
        value = json.loads(path.read_bytes())
        record = value["operation"]["result"]["record"]
        actual = A.actual_aw_terminal(value, [record["command"]] + record["args"])
        self.assertEqual(actual["exitCode"], 1)
        marker = json.loads(actual["stdout"].strip())
        self.assertEqual(marker["status"], "FAILED")
        self.assertEqual(marker["host_result"]["sha256"], "3ff3f90f8717df1ed65828141af501cbf6f52fc233e335639af593f18390b718")


if __name__ == "__main__":
    unittest.main(verbosity=2)
