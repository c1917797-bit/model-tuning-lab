"""Small stdlib contracts for real two-operation KVBuffer correctness dispatch."""
from datetime import datetime, timezone
import hashlib
import ast
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys

ROOT = Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT = ROOT / "projects/kvbuffer-parallel-ascend"
BASE = PROJECT / "tools/split_dispatch_v1"
RESULT_ROOT = Path("/cache/cch/qwen36-kvbuffer-parallel-20261006")
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PYTHON = "/usr/local/python3.12.13/bin/python3"
RUNNER = str(PROJECT / "tools/split_gate_v1/run.py")
OWNER = "kvbuffer-split-dispatch-v1"
PARENT_OP = "exec-00000000000006a0"
PARENT_PEER = "lgw_a6109c51076a4a2c9d2674ca5a8704a0"
PARENT_IDS = (
 "644e483333a636130b1310c15f8f694187331391a3d8df0f40ab36051b9a21db",
 "d4abaa82dea94ba3132faf33e355de88157787d57d61611e6a28be335b1f30b4",
 "305f493062816e210a135c509b5cdebf7571074c898b18db319e2de99c6ff24f",
 "5deeeaa5aa9e78ba165ecf5250b8ee8b85b1feb4f30c58eb392e8c5758db7517")
CARDS = {1: 5, 16: 6}
GIB = 1024**3
MEMORY = 8 * GIB
JOINT_RAM = 24 * GIB
JOINT_CPU = 3
IDLE_SOURCE = ROOT/"projects/damp-ascend/tools/run_collector_smoke.py"
IDLE_SOURCE_SHA = "da541917ebd8764a81624a215a157b6d4e18fbaaa53d9310be54a104d2fbbf92"
NPU_SMI = "/usr/local/sbin/npu-smi"
NPU_SMI_SHA = "c9476b1bf1a2b1cb6b1def82e27889b6f89189a12e9ff4aee5bd2047a19a3cce"
PREFIX = "MAIN_KVBUFFER_SPLIT_CHILD "
OWN = ("controller.py", "contracts.py", "test_controller.py", "READY.md")
WAIT = ('set -e; source /usr/local/Ascend/ascend-toolkit/set_env.sh; '
 'source /usr/local/Ascend/cann-9.1.0/share/info/ascendnpu-ir/bin/set_env.sh; '
 'source /usr/local/Ascend/nnal/atb/set_env.sh --cxx_abi=1; '
 'export ASCEND_HOME_PATH=/usr/local/Ascend/cann-9.1.0; '
 'for i in $(seq 1 600); do if test -f "$1"; then shift; exec "$@"; fi; sleep 1; done; exit 73')

def require(ok, message):
    if not ok:
        raise ValueError(message)

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def ref(path):
    return dict(path=str(path), sha256=sha(path))

def read_ref(value, limit=16*1024*1024):
    require(type(value) is dict and set(value) == {"path", "sha256"}, "exact original Ref")
    p = Path(value["path"])
    require(p.is_absolute() and ".." not in p.parts and p.is_file() and not p.is_symlink(),
            "absolute ordinary evidence file")
    require(re.fullmatch("[0-9a-f]{64}", value["sha256"]) and sha(p) == value["sha256"],
            "raw evidence byte drift")
    require(p.stat().st_size <= limit, "bounded JSON evidence")
    return p.read_bytes()

def clean(data):
    def bad(x):
        raise ValueError("nonfinite JSON: " + x)
    value = json.loads(data, parse_constant=bad)
    def finite(x):
        if isinstance(x,float):
            require(math.isfinite(x),"nonfinite JSON float")
        elif isinstance(x,dict):
            for y in x.values():finite(y)
        elif isinstance(x,list):
            for y in x:finite(y)
    finite(value)
    return value

def write_new(path, value):
    with Path(path).open("xb") as stream:
        stream.write(canonical(value) + b"\n")
    return ref(path)

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    require("torch" not in sys.modules and "torch_npu" not in sys.modules,
            "host source audit must remain stdlib")
    return m

def sources(packet_sha):
    packet = clean(read_ref(dict(path=str(BASE/"PACKET.json"), sha256=packet_sha)))
    require(packet.get("schema") == "kvbp.split-dispatch-sources/v1" and
            packet.get("default_enabled") is False and set(packet["sources"]) == set(OWN),
            "NEW exact default-OFF packet")
    pins = {str(BASE/name): value for name, value in packet["sources"].items()}
    pins.update(packet["frozen_dependencies"])
    for path, wanted in pins.items():
        require(sha(path) == wanted, "immutable source drift: " + path)
    for value in packet["artifacts"].values():
        p = Path(value["path"])
        require(p.is_file() and not p.is_symlink() and sha(p) == value["sha256"], "actual artifact drift")
    executable = packet.get("host_executable")
    require(executable == dict(path=NPU_SMI,sha256=NPU_SMI_SHA,resolved_path=NPU_SMI),
            "verified exact host npu-smi identity")
    p = Path(NPU_SMI)
    require(p.is_file() and not p.is_symlink() and str(p.resolve()) == NPU_SMI and
            sha(p) == NPU_SMI_SHA and os.access(p,os.X_OK),
            "actual npu-smi bytes/executable path; no guessed driver/tools/PATH")
    bridge = load(PROJECT/"tools/split_service_authority_v1/validator.py", "kvbp_dispatch_bridge")
    bridge.frozen(packet["bridge_manifest"], lambda p: Path(p).read_bytes())
    split = load(PROJECT/"tools/split_gate_v1/contract.py", "kvbp_dispatch_split")
    host = load(ROOT/"projects/damp-ascend/tools/allT_dispatch_controller_v1/controller.py",
                "kvbp_dispatch_host")
    float_helper = load(ROOT/"projects/damp-ascend/tools/prefill_float_dispatch_v1/dispatch.py",
                        "kvbp_dispatch_canary")
    return packet, pins, bridge, split, host, float_helper

def parent_terminal(raw, expected):
    d = raw.get("structuredContent", raw)
    op = d.get("operation", {})
    result = op.get("result", {})
    r = result.get("record", {})
    require(d.get("operationId") == PARENT_OP and d.get("terminal") is True and
            op.get("targetPeerId") == PARENT_PEER and op.get("routeDecision") == "peer_direct",
            "original MA06a0 terminal peer/operation")
    require(result.get("found") is True and result.get("lane") == "job" and
            result.get("state") == "completed" and r.get("lane") == "job" and
            r.get("state") == "completed" and r.get("id") == PARENT_OP and
            r.get("cancelled") is False and r.get("timedOut") is False and type(r.get("exitCode")) is int,
            "true completed parent; no cancel/timeout/running")
    require(expected.get("command") == "/usr/bin/python3" and expected.get("cwd") == str(ROOT) and
            type(expected.get("args")) is list and bool(expected["args"]) and
            all(r.get(k) == expected[k] for k in ("command", "args", "cwd")),
            "MAIN independently supplied exact original parent argv/cwd")
    code = r["exitCode"]
    require((code == 0 and r.get("error") is None) or
            (code != 0 and r.get("error") == "exit code"),
            "parent error must agree with actual completed exit")
    return dict(operation_id=PARENT_OP, peer_id=PARENT_PEER, exit_code=code,
                scope="resource release only; failed capture/allT is not PASS")

def bounds(inputs, now=None):
    require(type(inputs) is dict and set(inputs) == {
        "parent_operation", "parent_expected", "run_slug", "phase_seconds",
        "formal_start_utc", "deadline_utc", "main_approved", "forbid_other_owned_jobs"},
        "MAIN complete exact joint inputs")
    require(inputs["main_approved"] is True and inputs["forbid_other_owned_jobs"] is True,
            "explicit MAIN approval/exclusive correctness ownership")
    slug = inputs["run_slug"]
    require(type(slug) is str and re.fullmatch("[a-z0-9][a-z0-9-]{0,48}", slug), "bounded new run slug")
    budgets = inputs["phase_seconds"]
    require(type(budgets) is dict and set(budgets) == {"1", "16"} and
            all(type(x) is int and 1800 <= x <= 10800 for x in budgets.values()),
            "MAIN measured/conservative phase budgets required, no implicit3600")
    start, deadline = [datetime.fromisoformat(inputs[k].replace("Z", "+00:00"))
                       for k in ("formal_start_utc", "deadline_utc")]
    now = now or datetime.now(timezone.utc)
    require(start.tzinfo is not None and deadline.tzinfo is not None and
            start <= now and 0 < (deadline-start).total_seconds() <= 86400,
            "MAIN real formal clock, never invent or reset24h")
    require(now.timestamp() + 600 + max(budgets.values()) + 180 <= deadline.timestamp(),
            "joint remaining window includes setup and cleanup; deadline never extended")
    return dict(root=str(RESULT_ROOT/("split-dispatch-"+slug)), phase_seconds=budgets,
                deadline_utc=inputs["deadline_utc"], formal_start_utc=inputs["formal_start_utc"],
                ordinary_ram_bytes=JOINT_RAM, joint_cpu=JOINT_CPU,
                performance=False, service_ready=False)

def plan(inputs, now=None):
    b = bounds(inputs, now)
    root = Path(b["root"])
    jobs = []
    for batch, card in CARDS.items():
        name = "kvbuffer_split_b%d_%s" % (batch, inputs["run_slug"].replace("-", "_"))
        job_root = root / ("b%d" % batch)
        launch = job_root/"launch"
        output = job_root/"results"
        mounts = [(str(ROOT), str(ROOT), True),
                  (str(RESULT_ROOT/"build-p1-v1"), "/kvbuffer-results/build-p1-v1", True),
                  (str(RESULT_ROOT/"meta-p1-v1"), "/kvbuffer-results/meta-p1-v1", True),
                  (str(output), "/kvbuffer-results", False),
                  (str(launch), "/kvbuffer-launch", True),
                  ("/usr/local/Ascend/driver", "/usr/local/Ascend/driver", True)]
        create = ["/usr/bin/docker", "create", "--name", name,
                  "--label", "model-tuning-lab.owner="+OWNER,
                  "--label", "model-tuning-lab.joint="+inputs["run_slug"],
                  "--label", "model-tuning-lab.batch="+str(batch), "--network", "none",
                  "--memory", "8g", "--memory-swap", "8g", "--cpus", "1",
                  "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                  "--device", "/dev/davinci%d:/dev/davinci0" % card]
        for node in ("davinci_manager", "devmm_svm", "hisi_hdc"):
            create += ["--device", "/dev/"+node+":/dev/"+node]
        for source, target, ro in mounts:
            create += ["--mount", "type=bind,source=%s,target=%s%s" %
                       (source, target, ",readonly" if ro else "")]
        create += ["-e", "ASCEND_RT_VISIBLE_DEVICES=0", "-e", "PYTHONDONTWRITEBYTECODE=1",
                   "-e", "OMP_NUM_THREADS=1", "-w", str(ROOT), "--entrypoint", "/bin/bash",
                   IMAGE, "-c", "exec sleep infinity"]
        jobs.append(dict(batch=batch, physical_card=card, container_name=name,
                         job_root=str(job_root), launch_root=str(launch), output_root=str(output),
                         create_argv=create, phase_timeout_seconds=b["phase_seconds"][str(batch)],
                         image_identity="/kvbuffer-launch/identity.json",
                         image_output="/kvbuffer-results/gate"))
    return dict(schema="kvbp.split-joint-plan/v1", **b, jobs=jobs,
                parent_operation_pending=True, actual_device_proof_pending=True, npu_executed=False)

def gate_argv(job, cid):
    return ["/usr/bin/docker", "exec", cid, "/bin/bash", "-c", WAIT,
            "kvbuffer-await-b"+str(job["batch"]), "/kvbuffer-launch/RELEASE",
            PYTHON, "-B", RUNNER, "--batch", str(job["batch"]), "--physical-device",
            str(job["physical_card"]), "--identity", job["image_identity"],
            "--output-dir", job["image_output"]]

def inspect_proof(entry, job, cid):
    require(entry.get("Id") == cid and re.fullmatch("[0-9a-f]{64}", cid) and
            entry.get("Name") == "/"+job["container_name"] and entry.get("Image") == IMAGE,
            "exact owned prepared container/image")
    host, config = entry["HostConfig"], entry["Config"]
    require(host.get("Privileged") is False and host.get("Memory") == MEMORY and
            host.get("MemorySwap") == MEMORY and host.get("NanoCpus") == 10**9 and
            host.get("NetworkMode") == "none" and host.get("IpcMode") != "host" and
            not host.get("DeviceRequests") and set(host.get("CapDrop", [])) == {"ALL"} and
            any(x in ("no-new-privileges", "no-new-privileges=true") for x in host.get("SecurityOpt", [])),
            "single1CPU8GiB/no-swap/nonprivileged/no-network")
    labels = config.get("Labels") or {}
    require(labels.get("model-tuning-lab.owner") == OWNER and
            labels.get("model-tuning-lab.batch") == str(job["batch"]), "exact ownership label")
    wanted = {"/dev/davinci%d"%job["physical_card"]:"/dev/davinci0",
              **{"/dev/"+n:"/dev/"+n for n in ("davinci_manager", "devmm_svm", "hisi_hdc")}}
    require(len(host.get("Devices", [])) == 4 and
            {d["PathOnHost"]:d["PathInContainer"] for d in host["Devices"]} == wanted,
            "only5/6 card+control devices, never0-3")
    expected = {}
    argv = job["create_argv"]
    for i, x in enumerate(argv):
        if x == "--mount":
            pieces = argv[i+1].split(",")
            fields = dict(x.split("=",1) for x in pieces if "=" in x)
            expected[fields["target"]] = (fields["source"], "readonly" not in pieces)
    require(len(entry["Mounts"]) == len(expected), "no hidden/missing mounts")
    for mount in entry["Mounts"]:
        require(mount["Destination"] in expected, "unexpected mount")
        src, rw = expected[mount["Destination"]]
        require(mount.get("Type") == "bind" and mount["RW"] is rw and
                Path(mount["Source"]).resolve() == Path(src).resolve(), "real mount RO/RW source binding")
    require(config.get("WorkingDir") == str(ROOT) and config.get("Entrypoint") == ["/bin/bash"] and
            config.get("Cmd") == ["-c", "exec sleep infinity"], "exact starter/cwd")
    env = dict(x.split("=",1) for x in config.get("Env",[]) if "=" in x)
    require(env.get("ASCEND_RT_VISIBLE_DEVICES") == "0" and env.get("PYTHONDONTWRITEBYTECODE") == "1" and
            env.get("OMP_NUM_THREADS") == "1", "actual visible/bytecode/thread constraints")
    return cid

def gate_process(pid, cid, batch, host, *, require_python):
    row = host.owner_pid(pid, cid)
    ns = Path("/proc", str(pid), "status").read_text()
    m = re.search(r"^NSpid:\s+([0-9 \t]+)$", ns, re.M)
    require(m is not None, "actual NSpid absent")
    row["namespace_pids"] = list(map(int, m[1].split()))
    require(row["namespace_pids"] and row["namespace_pids"][0] == pid, "host/namespace PID chain")
    argv = Path("/proc", str(pid), "cmdline").read_bytes().split(b"\0")
    argv = [x.decode() for x in argv if x]
    row["argv"] = argv
    if require_python:
        require(len(argv) >= 3 and argv[0] == PYTHON and argv[1] == "-B" and argv[2] == RUNNER,
                "same real exec PID must be old imagePython/-B/RUNNER, not waiting bash")
        expected = [PYTHON,"-B",RUNNER,"--batch",str(batch),"--physical-device",str(CARDS[batch]),
                    "--identity","/kvbuffer-launch/identity.json","--output-dir","/kvbuffer-results/gate"]
        require(argv == expected, "actual exact true batch/card/identity/output gate PID")
    else:
        require("kvbuffer-await-b"+str(batch) in argv and WAIT in argv and RUNNER in argv,
                "unique prelaunch wait bash, explicitly not NPU native process")
    row["observed_role"] = "actual_gate_python" if require_python else "prelaunch_wait_bash_not_native"
    return row

def stage_report(report, identity, batch, bridge, split, manifest, meta):
    require(report.get("schema") == "kvbp.split-native-gate/v1" and
            report.get("status") == "single_batch_kernel_native_eager_graph_pass" and
            report.get("claim") == "kernel-only" and "error" not in report,
            "raw failed/missing split report is not PASS")
    require(report.get("protocol") == split.protocol(batch, CARDS[batch]) and
            report.get("launch_identity") == identity and
            report.get("launch_identity_sha256") == digest(canonical(identity)+b"\n"),
            "unchanged real protocol/identity")
    drivers = {p.rsplit("/",1)[1]:v for p,v in manifest["frozen_dependencies"].items()
               if "/tools/split_gate_v1/" in p}
    require(report["driver_sources"] == identity["driver_sources"] == drivers and
            report["native_sources"] == identity["native_sources"] == manifest["native_pins"] and
            identity["repo_sources"] == manifest["repo_pins"], "frozen driver/native source receipt")
    require(report["candidate_schema"] == meta["schema"] and
            report["frozen_receipts"] == dict(build_receipt_sha256=bridge.BUILD,
               meta_receipt_sha256=bridge.META,library_sha256=bridge.LIBRARY,
               repo_sources=manifest["repo_pins"],meta_is_not_npu_proof=True), "actual build/Meta/schema")
    require(report["loaded_libraries"].get(bridge.NATIVE_PATH) == bridge.NATIVE_SHA and
            any("kvbuffer" in p and h == bridge.LIBRARY for p,h in report["loaded_libraries"].items()),
            "real mapped libraries, not source bytes alone")
    return bridge.validate_cases(report, batch)

def raw_step_ceiling(batch):
    require(batch in CARDS,"real B1/B16 only")
    # Frozen oracle's four state/guard copies, two native states and cloned I/O;
    # output <=FP32. Serializer16MiB is conservative policy, not measured ABI bound.
    payload = 5195776*(batch+3) + 22688*batch + 5640
    return ((payload + 16*1024**2 + 4095)//4096)*4096

def phase_disk_need(remaining_seconds):
    require(type(remaining_seconds) in (int,float) and math.isfinite(remaining_seconds) and
            0 <= remaining_seconds <= 10800,"bounded remaining phase seconds")
    # Passed raw checkpoints are deleted; cumulative73GiB is not retained storage.
    # Two simultaneous raw ceilings + remaining30s two-source4MiB audit snapshots
    # above an unchanged8GiB reserve. Unknown peer time uses its full phase budget.
    return 8*GIB + sum(raw_step_ceiling(b) for b in CARDS) + \
           math.ceil(remaining_seconds/30)*2*4*1024**2

def runtime_budget(mem_available,free_disk,remaining_seconds,cgroups):
    require(type(mem_available) is int and mem_available >= 8*GIB,"live ordinaryRAM8GiB reserve")
    need = phase_disk_need(remaining_seconds)
    require(type(free_disk) is int and free_disk >= need,"live remaining-phase disk headroom")
    require(set(cgroups) == {1,16},"both exact owned cgroups/statuses required")
    for batch,row in cgroups.items():
        require(row.get("memory_limit_bytes") == MEMORY and row.get("cpu_quota") == 1,
                "both actual cgroup8GiB/1CPU caps")
        if row.get("running"):
            current,peak = row.get("memory_current_bytes"),row.get("memory_peak_bytes")
            require(type(current) is int and type(peak) is int and 0 <= current <= peak <= MEMORY,
                    "actual live cgroup current/peak missing, nonfinite or over cap")
        else:
            require(row.get("pid") == 0 and row.get("stopped_verified") is True,
                    "peer not running needs exact stopped proof, not absent peak fabrication")
    growth = sum(row["memory_limit_bytes"]-row["memory_current_bytes"]
                 for row in cgroups.values() if row.get("running"))
    require(mem_available >= 8*GIB + growth,
            "live ordinaryRAM reserve plus uncommitted growth to both owned caps")
    return dict(ordinary_mem_available_bytes=mem_available,ordinary_ram_reserve_bytes=8*GIB,
                uncommitted_owned_cap_growth_bytes=growth,
                live_ram_required_bytes=8*GIB+growth,
                free_disk_bytes=free_disk,remaining_phase_seconds=remaining_seconds,
                remaining_phase_disk_required_bytes=need,
                raw_step_ceiling_bytes={str(b):raw_step_ceiling(b) for b in CARDS},
                cgroups=cgroups,scope="actual sampled resource budget; no numerical/performance PASS")

def idle_hbm_ceiling():
    """Read the exact existing environment envelope, not a guessed zero-HBM rule."""
    require(sha(IDLE_SOURCE)==IDLE_SOURCE_SHA,"actual frozen idle_snapshot source")
    tree=ast.parse(IDLE_SOURCE.read_text())
    functions=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="idle_snapshot"]
    require(len(functions)==1,"actual idle_snapshot body")
    bounds=[]
    for node in ast.walk(functions[0]):
        if (isinstance(node,ast.Compare) and len(node.ops)==1 and isinstance(node.ops[0],ast.LtE) and
            isinstance(node.left,ast.Subscript) and isinstance(node.left.slice,ast.Constant) and
            node.left.slice.value=="hbm_mib" and len(node.comparators)==1 and
            isinstance(node.comparators[0],ast.Constant)):
            bounds.append(node.comparators[0].value)
    require(bounds==[3165],"source-proven exact3165 envelope, no arbitrary widening")
    return bounds[0]

def idle_card(telemetry):
    require(type(telemetry) is dict and telemetry.get("aicore")==0 and
            type(telemetry.get("hbm_mib")) is int and 0<=telemetry["hbm_mib"]<=idle_hbm_ceiling(),
            "actual zero-AICore + source-bound idle HBM envelope")
    return True
