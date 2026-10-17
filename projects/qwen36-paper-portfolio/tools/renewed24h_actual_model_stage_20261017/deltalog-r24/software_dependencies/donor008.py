"""Concrete MAIN-only R118 MXR capture ticket, default OFF.

Reuse pinned KIVI011 safety Controller, not its algorithm/main. No foreign stop,
delete, retries, deadline resets or generalized scheduler. Fresh output required.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import types
import shutil
import traceback

HERE = Path(__file__).resolve().parent
ROOT = Path("/opt/host/vnf/austinov/model-tuning-lab")
PREP = Path("/cache/cch/qwen36-paper-preparation-20261007")
UP = PREP / "lowbit/kivi-direct-d8-fp32-model-boundary-r87-v1-011"
SOURCE1 = PREP / "lowbit/mxr-r118-capture-20261013-001"
SOURCE3 = PREP / "lowbit/mxr-r118-capture-launch-20261013-003"
DEPLOY = PREP / "lowbit/mxr-r118-proc-snapshot-repair-20261013-008"
OUT = PREP / "lowbit/run-mxr-r118-native-capture-20261013-008"
AUTH = ROOT / ".agents/workstreams/qwen36-damp-ascend-20261006/R118_NEW12H_AUTHORITY_20261013.json"
AUTH_SHA = "32b3d57baa8f5f843d95675de57e0e8d5579dd8766c9d3d9bd320f834af05a72"
UP_CONTRACT_SHA = "529f2c017aca438c6f3638ebfdbd3ddae4d30ce9521b0da0146e83ee4fac74ee"
UP_SAFETY_SHA = "8c83e08318b530c4d022b91bbacd34b12121b3380e1a14d32262c9a3875f6fa7"
SOURCE3_SHA = "55e10903d731759b84d3cee3d54d4aa63a4c219aa1b30dd94e4ad923b2d5eacd"
START, CUTOFF = 1791879730, 1791922930
PHASE, CLEANUP_TOTAL = 2700, 270  # three distinct retained containers, <=90s each
POLICY = dict(path=str(PREP / "lowbit/_draft_adakv_current_prepare/R118/skvq-writer-native-v1-003/idle_policy.py"),
    bytes=6194, sha256="1988d3843b340a06b0c402b96886ea7a6feb8bab573f67fb8c74512bcca33616")
ROLES = {
    "protected_contract": dict(path=str(PREP / "sparse/adakv-native-serial-once-v1-016/once_contract.py"), sha256="a7e446d79c58672bb77cafaf3968ee4dbbdd70a2b86afcd350065b69338f45bb"),
    "protected_lifecycle": dict(path=str(PREP / "sparse/adakv-native-serial-once-v1-015/safety_lifecycle.py"), sha256="4bbd492809c9ba1922fd3885b101f8cc6fe187884703c21e4a2d44acd1444b75"),
    "output_scanner": dict(path=str(PREP / "recurrent/adakv030-fa-physical-layout-observation-v6-user72h-20261010/output_budget.py"), sha256="44e5ccfdad173e6b9eebc025260e489893d672c316c6aac3f8bf68a5e03c16ad"),
}


def need(value, why):
    if not value:
        raise ValueError(why)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def load(path, digest, name):
    path = Path(path)
    need(path.is_file() and not path.is_symlink() and sha(path) == digest, "exact source: " + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def frozen_directory(root, digest):
    need(root.is_dir() and not root.is_symlink() and sha(root / "SOURCE_MANIFEST.json") == digest, "deployed frozen source manifest")
    value = json.loads((root / "SOURCE_MANIFEST.json").read_text())
    for row in value["files"]:
        p = Path(row["path"])
        need(not p.is_absolute() and ".." not in p.parts, "bounded own package leaf")
        target = root / p
        need(not target.is_symlink() and target.stat().st_size == row["bytes"] and sha(target) == row["sha256"], "deployed complete source identity")
    return value


def guest_environment(cpu=False, arm="capture"):
    need(arm == "capture", "this host ticket only native observer; shadow is separate admission")
    return dict(ASCEND_RT_VISIBLE_DEVICES="" if cpu else "0,1,2,3", TORCH_DEVICE_BACKEND_AUTOLOAD="0",
        PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
        TMPDIR="/adakv-results", VLLM_DISABLE_REQUEST_ID_RANDOMIZATION="1",
        MST_MXR_CAPTURE_ENABLE="0", MST_MXR_SOLVE_ENABLE="0", MST_MXR_NATIVE_WORKER_RECEIPT="0")


def safety(source_ref, policy_ref, start):
    import resource
    base = load(UP / "model_contract.py", UP_CONTRACT_SHA, "_mxr_original_contract")
    base.configure(dict(runtime_roles=ROLES))
    # Private experiment facade: keep original infrastructure functions/source,
    # replace only explicit experiment time and source context in this process.
    facade = types.ModuleType("model_contract")
    facade.__dict__.update(base.__dict__)
    facade.CUT = "2026-10-13T20:22:10+00:00"
    facade.CUTOFF = CUTOFF
    need("model_contract" not in sys.modules, "fresh private host namespace")
    sys.modules["model_contract"] = facade
    S = load(UP / "safety_host.py", UP_SAFETY_SHA, "_mxr_original_safety")
    S.PHASE = PHASE
    S.OWNER = "mxr-r118-native-capture008"
    S.environment = guest_environment
    old_labels = S.labels
    def labels(expected):
        value = old_labels(expected)
        value["model-tuning-lab.mxr-host-sha256"] = sha(HERE / "host_ticket.py")
        return value
    S.labels = labels
    # Shared native003 was deployed/read back by MAIN; still verify this Ref at
    # every execution. No historical idle snapshot is reused as admission.
    policy = load(policy_ref["path"], policy_ref["sha256"], "_mxr_shared_idle_policy")
    install_idle_policy(policy, S)
    snapshot_policy = load(HERE / "protected_snapshot_policy.py", sha(HERE / "protected_snapshot_policy.py"), "_mxr_snapshot_policy008")
    frozen_path = ROOT / "projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py"
    snapshot_policy.install(S, (UP / "safety_host.py").read_bytes(), str(UP / "safety_host.py"), frozen_path.read_bytes(), str(frozen_path))
    state = dict(cleanup_spent=0., start=start, end=start + PHASE)
    class Owned(S.Controller):
        def __init__(self, leaf):
            super().__init__(argparse.Namespace(output_dir=leaf), start)
            self.name = "mxr-r118-capture008-" + leaf.name
        def rss(self):
            own = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            child = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
            need(own + child <= 512 * 1024, "source-original host plus CLI cumulative512MiB")
            return dict(host_peak_rss_kib=own, child_peak_rss_kib=child, aggregate_peak_rss_kib=own + child)
        def remaining(self, cleanup=False, cap=30):
            now = time.monotonic()
            if cleanup:
                if self.cleanup_deadline is None:
                    self.cleanup_deadline = min(now + 90, state["end"], now + CUTOFF - time.time())
                value = self.cleanup_deadline - now
            else:
                value = min(state["end"] - now, CUTOFF - time.time()) - (CLEANUP_TOTAL - state["cleanup_spent"])
            need(value > 0, "fixed current phase/window including exact-owned cleanup; no reset")
            return min(cap, value)
        def cleanup(self):
            before = time.monotonic()
            try:
                return super().cleanup()
            finally:
                state["cleanup_spent"] += time.monotonic() - before
        def resources(self, initial=False):
            value = super().resources(initial)
            engine = json.loads(base.obj(value["engine"])["stdout"])
            need(engine["DockerRootDir"] == "/cache/docker", "fresh observed Docker storage, not full rootfs assumption")
            free = shutil.disk_usage(engine["DockerRootDir"]).free
            need(free >= S.RESERVE + (S.WORKSPACE if initial else 0), "actual Docker root storage reserve")
            need(len(Path("/proc/1/mountinfo").read_text().splitlines()) < 95000, "unchanged safe mount reserve")
            value["docker_storage"] = dict(path=engine["DockerRootDir"], available_bytes=free,
                host_rootfs_available_bytes=shutil.disk_usage("/").free, rootfs_cleanup_authorized=False)
            return value
        def create_native(self, model, cpu):
            mounts = {str(ROOT):(str(ROOT),False), str(SOURCE1):(str(SOURCE1),False),
                str(SOURCE3):(str(SOURCE3),False), str(DEPLOY):(str(DEPLOY),False), str(UP):(str(UP),False),
                "/usr/local/Ascend/driver":("/usr/local/Ascend/driver",False),
                "/models/Qwen3.6-27B":(model["host_model_root"],False),
                str(OUT):(str(OUT),False), str(self.out):(str(self.out),True),
                "/adakv-results":(str(self.out),True), str(AUTH):(str(AUTH),False),
                base.MODEL_REF["path"]:(base.MODEL_REF["path"],False)}
            self.expected = dict(cid=None, name=self.name, image=base.IMAGE,
                arm="cpu-preflight" if cpu else "candidate", algorithm_arm="capture", source=source_ref,
                host_sha256=UP_SAFETY_SHA, guest_cpus=self.cpu["guest_cpus"][:1] if cpu else self.cpu["guest_cpus"], mounts=mounts)
            old, _ = self.call("unique-name", [S.DOCKER, "ps", "-a", "--filter", "name=^/" + self.name + "$", "--format", "{{.ID}}"])
            need(not old["stdout"].strip(), "new exact owned name; no reuse")
            for path, rw in mounts.values():
                need(Path(path).exists() and not Path(path).is_symlink(), "actual exact mount absent/alias")
            for path in ({} if cpu else S.device_map()):
                need(Path(path).exists(), "actual authorized device node")
            self.create_owned({"safety_host.py":UP_SAFETY_SHA})
            inspected, _ = self.inspect()
            need(not inspected["State"]["Running"] and inspected["State"]["Pid"] == 0, "fresh owned container")
            self.call("start", [S.DOCKER, "start", self.cid], cap=60)
            inspected, _ = self.inspect()
            need(inspected["State"]["Running"] and not inspected["State"].get("OOMKilled"), "native init running")
            cpu_view = S.H.cpu_view(inspected["State"]["Pid"])
            need(cpu_view["effective_capacity"] == (1 if cpu else 4) and cpu_view["effective_cpus"] == self.expected["guest_cpus"], "actual cgroup CPU quotas")
            base.write(self.out / "GUEST-CPU.json", cpu_view)
    return base, S, Owned, state


def install_idle_policy(policy, S):
    return policy.install(S.H, dict(path=str(ROOT / "projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py"),
        bytes=33743, sha256="ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86"))


def child(ctl, c, label, argv, seconds, observe=True):
    if ctl.server is None:
        ctl.server_started = datetime.datetime.now(datetime.timezone.utc)
    command = c.docker_argv(ctl.cid, argv)
    before = time.monotonic()
    with (ctl.out / (label + ".stdout")).open("x") as stdout, (ctl.out / (label + ".stderr")).open("x") as stderr:
        process = subprocess.Popen(ctl.wrapper(command), stdout=stdout, stderr=stderr, cwd=ROOT)
        ctl.client = process
        while process.poll() is None:
            need(time.monotonic() - before < seconds, "bounded one-shot child")
            need(ctl.server is None or ctl.server.poll() is None, "model server failed during child")
            ctl.remaining()
            if observe:
                ctl.observe(label)
            time.sleep(1)
    need(process.returncode == 0, "original child failure retained: " + label)
    return c.write(ctl.out / (label + "-CHILD.json"), dict(argv=command, host_pid=process.pid, exit_code=process.returncode,
        stdout=c.ref(ctl.out / (label + ".stdout")), stderr=c.ref(ctl.out / (label + ".stderr"))))


def close_owned(ctl, c, primary=None):
    """Exactly one cleanup attempt; never turn cleanup into a compute retry."""
    need(not getattr(ctl, "_mxr_done", False), "cleanup already attempted")
    ctl._mxr_done = True
    ctl.primary = primary
    try:
        value = ctl.cleanup()
        report = c.obj(value)
        need(report["stopped"] is True and report["retained"] is True and not report["deleted"]
             and not report["errors"] and not ctl.secondary, "exact owned stop-retain and true release")
        return value
    except BaseException as exc:
        ctl.secondary.append("MXR cleanup: " + repr(exc))
        if primary is None:
            raise
        # The original computation exception is re-raised by the caller. The
        # complete controller cleanup record/secondary error remains retained.
        return None


def worker_bindings(ctl, c, root, run_id):
    rows = []
    for rank in range(4):
        receipt = root / ("NATIVE-WORKER-r%d.json" % rank)
        value = c.obj(c.ref(receipt))
        need(value["schema"] == "mxr.actual-native-loaded-worker/v1" and value["run_id"] == run_id
             and value["rank"] == rank and value["worker_class"] == "vllm_ascend.worker.worker.NPUWorker"
             and value["worker_sha256"] == "c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3"
             and value["original_load_completed"] is True and value["visible_devices"] == "0,1,2,3",
             "actual original loaded worker receipt")
        ticks = int(value["stat"][value["stat"].rfind(")") + 2:].split()[19])
        device = value["logical_device"]
        need(type(device) is int and device in range(4), "actual worker logical device")
        matches = [row for row in ctl.process_proofs if row["namespace_pids"][-1] == value["pid"]
                   and row["physical"] == device + 4 and row["start_ticks"] == ticks and ctl.cid in row["cgroup"]]
        need(matches and len({(row["pid"], row["start_ticks"]) for row in matches}) == 1,
             "native worker namespace PID/start/cgroup bound to actual owned physical card")
        rows.append(dict(rank=rank, namespace_pid=value["pid"], logical=device, physical=device + 4,
                         loaded_receipt=c.ref(receipt), actual_host_process=matches[-1]))
    need({row["physical"] for row in rows} == {4,5,6,7} and len({row["namespace_pid"] for row in rows}) == 4,
         "four distinct actual TP4 worker identities")
    return rows


def run(source_ref, start):
    import resource
    c, S, Owned, state = safety(source_ref, POLICY, start)
    own = []
    primary, result, capture_rows = None, {}, []
    failure_detail = None
    def make(name):
        leaf = OUT / name
        leaf.mkdir(mode=0o700)
        ctl = Owned(leaf)
        if own:
            ctl.protected = own[0].protected
        own.append(ctl)
        return ctl
    try:
        cpu = make("cpu-preflight")
        initial = cpu.observe("initial-native-admission", initial=True)
        host = S.H.cpu_view(os.getpid())
        os.sched_setaffinity(0, {min(host["effective_cpus"])})
        _, hard = resource.getrlimit(resource.RLIMIT_AS)
        need(hard == resource.RLIM_INFINITY, "same safe Docker child AS hard-limit restore")
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, hard))
        model = c.model(c.MODEL_REF)  # all29 files and15 actual shards; no historical label shortcut
        cpu.remaining()
        cpu.create_native(model, True)
        child(cpu, c, "cold-off", [str(SOURCE1 / "cold_entry.py"), "--source-root", str(SOURCE1),
            "--installed-ascend-root", "/vllm-workspace/vllm-ascend/vllm_ascend"], 120, observe=False)
        child(cpu, c, "native-parser", [str(DEPLOY / "guest_probe.py"), "--execute", "--mode", "cpu",
            "--source3", str(SOURCE3), "--upstream", str(UP), "--output", str(cpu.out / "CPU.json")], 150, observe=False)
        cpu_report = c.obj(c.ref(cpu.out / "CPU.json"))
        need(cpu_report["pass_preflight"] is True and cpu_report["mode"] == "cpu" and not cpu_report["canaries"], "actual Devices[] precheck")
        result["cpu"] = dict(initial=initial, report=c.ref(cpu.out / "CPU.json"), cleanup=close_owned(cpu, c))

        ctl = make("candidate")
        result["fresh_tp4_admission"] = ctl.observe("TP4-admission", initial=True)
        ctl.create_native(model, False)
        child(ctl, c, "all4-canary", [str(DEPLOY / "guest_probe.py"), "--execute", "--mode", "n1",
            "--source3", str(SOURCE3), "--upstream", str(UP), "--output", str(ctl.out / "CANARY.json")], 180)
        canary = c.obj(c.ref(ctl.out / "CANARY.json"))
        need(canary["mode"] == "n1" and canary["pass_preflight"] and len(canary["canaries"]) == 4, "all4 actual tiny prerequisite")
        receipt_root = ctl.out / "worker-receipts"
        receipt_root.mkdir()
        run_id = "mxr-r118-native-capture008"
        args = [str(DEPLOY / "server_boot.py"), "--execute", "--mode", "capture", "--capture-source", str(SOURCE1),
            "--upstream-source", str(UP), "--output", str(ctl.out / "model"), "--run-id", run_id,
            "--authority", str(AUTH), "--model-manifest", c.MODEL_REF["path"], "--port", "8252"]
        original_command = c.docker_argv(ctl.cid, args)
        command = original_command[:2] + ["-e", "MST_MXR_NATIVE_WORKER_RECEIPT=1", "-e", "MST_MXR_NATIVE_WORKER_ROOT=" + str(receipt_root),
            "-e", "MST_MXR_NATIVE_WORKER_RUN_ID=" + run_id] + original_command[2:]
        ctl.server_started = datetime.datetime.now(datetime.timezone.utc)
        stdout = (ctl.out / "server.stdout").open("x")
        stderr = (ctl.out / "server.stderr").open("x")
        model_error = None
        try:
            ctl.server = subprocess.Popen(ctl.wrapper(command), stdout=stdout, stderr=stderr, cwd=ROOT)
            deadline = time.monotonic() + min(1500, ctl.remaining(cap=1500))
            while True:
                need(ctl.server.poll() is None and time.monotonic() < deadline, "native server startup bounded/failed")
                ctl.observe("native-model-startup")
                health = [c.PY, "-I", "-B", "-c", "import urllib.request; assert urllib.request.urlopen('http://127.0.0.1:8252/health',timeout=2).status==200"]
                observation = ctl.h.run(ctl.wrapper([S.DOCKER, "exec", ctl.cid, *health]), min(4, ctl.remaining(cap=4)))
                c.write(ctl.out / ("HEALTH-%d.json" % time.time_ns()), observation)
                if observation["exit_code"] == 0:
                    break
                time.sleep(2)
            bindings = worker_bindings(ctl, c, receipt_root, run_id)
            result["actual_loaded_workers"] = c.write(ctl.out / "ALL4-LOADED.json", dict(schema="mxr.actual-all4-loaded/v1", rows=bindings))
            child(ctl, c, "warmup-arm-capture", [str(SOURCE3 / "capture_client.py"), "--execute", "--model-config",
                "/models/Qwen3.6-27B/config.json", "--server-output", str(ctl.out / "model"),
                "--output", str(ctl.out / "client"), "--run-id", run_id, "--port", "8252"], 300)
            ctl.observe("actual-frame-produced")
            for row in bindings:
                worker = ctl.out / "model/capture" / ("worker-%d" % row["namespace_pid"])
                runtime = c.obj(c.ref(worker / "RUNTIME.json"))
                case = c.obj(c.ref(worker / "case-000/CASE.json"))
                need(runtime["pid"] == row["namespace_pid"] and runtime["run_id"] == case["run_id"] == run_id
                     and not (worker / "case-000/FAILURE.json").exists(), "actual native TP frame, not frontend directory")
                capture_rows.append(dict(**row, worker_root=str(worker), case=c.ref(worker / "case-000/CASE.json")))
            result["canary"] = c.ref(ctl.out / "CANARY.json")
            result["capture"] = capture_rows
        except BaseException as exc:
            model_error = exc
            raise
        finally:
            try:
                result["TP4_cleanup"] = close_owned(ctl, c, model_error)
            finally:
                stdout.close()
                stderr.close()

        cpu2 = make("cpu-consumer")
        cpu2.observe("post-release-CPU-consumption", initial=True)
        cpu2.create_native(model, True)
        reports = []
        for row in capture_rows:
            output = cpu2.out / ("rank-%d" % row["rank"])
            child(cpu2, c, "consume-r%d" % row["rank"], [str(SOURCE1 / "consume_capture.py"), "--worker-root", row["worker_root"],
                "--out-root", str(output), "--run-id", run_id, "--expected-cases", "1"], 120, observe=False)
            report_ref = c.ref(output / "RESULT.json")
            report = c.obj(report_ref)
            need(report["schema"] == "mxr.capture.independent-consumer/v1" and report["run_id"] == run_id
                 and report["original_native_gate_pass"] is True and report["cases"] == 1
                 and report["mxr_qualified"] is False and report["performance_ready"] is False,
                 "actual independent native FP64 consumer, not candidate/E2E qualification")
            reports.append(dict(rank=row["rank"], output=str(output), result=report_ref))
        result["independent_FP64_original_solve_consumers"] = reports
        result["consumer_cleanup"] = close_owned(cpu2, c)
    except BaseException as exc:
        primary = exc
        failure_detail = dict(type=type(exc).__name__, errno=getattr(exc,"errno",None), filename=getattr(exc,"filename",None), traceback="".join(traceback.format_exception(type(exc),exc,exc.__traceback__)))
    finally:
        secondary = []
        for ctl in reversed(own):
            if ctl.cid and not getattr(ctl, "_mxr_done", False):
                ctl.primary = primary
                try:
                    close_owned(ctl, c, primary)
                except BaseException as exc:
                    secondary.append(repr(exc))
            secondary.extend(ctl.secondary)
        if state["cleanup_spent"] > CLEANUP_TOTAL:
            secondary.append("shared current270s cleanup budget exceeded")
        if time.monotonic() > state["end"] or time.time() >= CUTOFF:
            secondary.append("fixed current phase/window expired")
        owned_state = []
        for ctl in own:
            release = False
            if ctl.cid and (ctl.out / "cleanup.json").is_file():
                try:
                    note = c.obj(c.ref(ctl.out / "cleanup.json"))
                    release = note["stopped"] is True and note["retained"] is True and not note["errors"]
                except BaseException:
                    release = False
            owned_state.append(dict(stage=str(ctl.out), cid=ctl.cid,
                exact_owned_release_verified=release if ctl.cid else None))
        try:
            frozen_directory(HERE, source_ref["sha256"])
            frozen_directory(SOURCE1, "f88e44fe7f7fa6b61ef6d5043a3a335a565dc59a6dac57acf5d24ff18779fc4e")
            frozen_directory(SOURCE3, SOURCE3_SHA)
            need(sha(AUTH) == AUTH_SHA and sha(UP / "safety_host.py") == UP_SAFETY_SHA
                 and sha(UP / "model_contract.py") == UP_CONTRACT_SHA and sha(POLICY["path"]) == POLICY["sha256"],
                 "source/authority identity unchanged after stage")
        except BaseException as exc:
            secondary.append("source-after: " + repr(exc))
        result.update(schema="mxr.actual-native-capture-host/v1", source=source_ref, primary=repr(primary) if primary else None, primary_detail=failure_detail,
            secondary=secondary, elapsed=time.monotonic() - start, cleanup_seconds=state["cleanup_spent"],
            owned_containers=owned_state,
            all_created_containers_release_verified=all(r["exact_owned_release_verified"] for r in owned_state if r["cid"]),
            status="NATIVE_FRAMES_AND_FP64_CONSUMED" if primary is None and not secondary else "failed",
            matrix_MXR_qualified=False, full_model_qualified=False, performance_ready=False, task_accuracy=False)
        c.write(OUT / "RESULT.json", result)
    if primary:
        raise primary
    need(not result["secondary"], "cleanup/time/source secondary failure")
    print(json.dumps(dict(result=str(OUT / "RESULT.json"), status=result["status"])))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--source-sha256")
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps(dict(enabled=False, npu_started=False, hardware_ready=False)))
        return 0
    start = time.monotonic()
    need(START <= time.time() and time.time() + PHASE <= CUTOFF, "current R118 whole45min incl cleanup")
    need(HERE == DEPLOY and not HERE.is_symlink() and sha(AUTH) == AUTH_SHA, "actual intended deployed source/current authority")
    source = frozen_directory(HERE, args.source_sha256)
    need(source["authority_sha256"] == AUTH_SHA and source["cutoff_epoch"] == CUTOFF, "same source-frozen current window")
    for row in source["dependencies"]:
        path = Path(row["path"])
        need(path.is_absolute() and not path.is_symlink() and path.stat().st_size == row["bytes"]
             and sha(path) == row["sha256"], "full observed shared source dependency before admission")
    frozen_directory(SOURCE1, "f88e44fe7f7fa6b61ef6d5043a3a335a565dc59a6dac57acf5d24ff18779fc4e")
    frozen_directory(SOURCE3, SOURCE3_SHA)
    need(not OUT.exists() and OUT.parent.is_dir() and not OUT.is_symlink(), "one immutable new output; no retry/reuse")
    need(Path(POLICY["path"]).stat().st_size == POLICY["bytes"] and sha(POLICY["path"]) == POLICY["sha256"], "shared native003 policy actually deployed by MAIN")
    OUT.mkdir(mode=0o700)
    os.environ["TMPDIR"] = str(OUT)
    source_ref = dict(path=str(HERE / "SOURCE_MANIFEST.json"), bytes=(HERE / "SOURCE_MANIFEST.json").stat().st_size, sha256=args.source_sha256)
    return run(source_ref, start)


if __name__ == "__main__":
    raise SystemExit(main())
