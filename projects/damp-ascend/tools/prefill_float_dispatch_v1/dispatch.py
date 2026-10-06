"""MAIN-only one-shot DAMP FP32 SR divide dispatcher; default dry, no Torch/NPU."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
REPO = BASE.parents[3]
PROJECT = REPO / "projects/damp-ascend"
ROOT = Path("/cache/cch/qwen36-damp-20261006")
PROBE = PROJECT / "operator/prefill_pack_v1/probe"
FIXED = PROBE / "fixed_buffers_v1"
BUILD = ROOT / "prefill-float-build-v1"
SO = BUILD / "build/libqwen36_damp_prefill_float_probe_ops.so"
SO_SHA = "80a06b48be444fbef9a37f7c9857c95518b8181cb8b5ba5ac6a1a21002cb85c0"
RECEIPT = BUILD / "build-receipt.json"
RECEIPT_SHA = "7696732308c3dc7c9565cb91b471cf3df268cc94f59cde292c46dfaad60a6baf"
SOURCE_SHA = "e8e1bd5f29b219b68351834da02c5385925ce51d86edfd27be304c1ef140817c"
RUNTIME_SHA = "bfc7d359ad444ad22dc99915f9372b543beef8d3ac568c2e96bb48c22554f1f1"
FIXED_SHA = "44b4bb5056c8fb6695725fcd6058a72e45d67023ebf0c206c3c106d9bdfd860d"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PYTHON = "/usr/local/python3.12.13/bin/python3"
HELPER = PROJECT / "tools/allT_dispatch_controller_v1/controller.py"
HELPER_SHA = "c44412ffbfffa5b8e1630694343044d874c87ab72e3ad76875c2e69bc6c6e1ff"
FULL = PROJECT / "tools/run_full_capture.py"
FULL_SHA = "9ad5e359766578a24f06e127a990ab93d1e86555baa15d1abb7bb2b3ffc51122"
SMOKE = PROJECT / "tools/run_collector_smoke.py"
SMOKE_SHA = "da541917ebd8764a81624a215a157b6d4e18fbaaa53d9310be54a104d2fbbf92"
DEADLINE = "2026-10-07T08:48:03Z"
GIB = 1024**3
MEMORY = 8 * GIB
RESERVE = 8 * GIB
DISK = 8 * GIB
PHASE_TIMEOUT = 3600
OWNER = "damp-prefill-float-dispatch-v1"
OWN = ("dispatch.py", "test_dispatch.py", "READY.md")
BOOTSTRAP = ('set -e; source /usr/local/Ascend/ascend-toolkit/set_env.sh; '
 'source /usr/local/Ascend/cann-9.1.0/share/info/ascendnpu-ir/bin/set_env.sh; '
 'source /usr/local/Ascend/nnal/atb/set_env.sh --cxx_abi=1; '
 'export ASCEND_HOME_PATH=/usr/local/Ascend/cann-9.1.0; exec "$@"')
CANARY_CODE = '''import json,os,sys,time
import torch,torch_npu
assert os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0"
assert torch.__version__=="2.10.0+cpu" and torch_npu.__version__=="2.10.0.post4"
torch_npu.npu.set_compile_mode(jit_compile=False)
torch.npu.set_device(0)
assert torch.npu.device_count()==1
assert torch.npu.get_device_name("npu:0")=="Ascend910B4"
x=torch.tensor([1.,2.,3.],dtype=torch.float32,device="npu:0")
y=x*x
torch.npu.synchronize()
value=y.cpu().tolist()
assert value==[1.,4.,9.]
print(json.dumps({"schema":"damp-prefill-float-canary/v1","status":"actual_canary_pass",
 "npu_executed":True,"expected_physical_card":int(sys.argv[1]),"logical_device":0,
 "runtime_soc":torch.npu.get_device_name("npu:0"),"result":value,
 "create_argv_sha256":sys.argv[2],"canary_program_sha256":sys.argv[3],
 "completed_at_unix_ns":time.time_ns(),
 "scope":"tiny NPU mul only; physical authority is actual MAIN inspect"}))
'''
CANARY_SHA = hashlib.sha256(CANARY_CODE.encode()).hexdigest()

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def checked(path, digest):
    p = Path(path)
    require(p.is_absolute() and p.is_file() and not p.is_symlink(), "ordinary absolute file: " + str(p))
    require(isinstance(digest, str) and re.fullmatch("[0-9a-f]{64}", digest), "full SHA256")
    require(sha(p) == digest, "source/artifact drift: " + str(p))
    return p

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def read(path, limit=64 * 1024 * 1024):
    p = Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size <= limit, "bounded ordinary JSON")
    def reject(value):
        raise ValueError("nonfinite JSON: " + value)
    return json.loads(p.read_text(), parse_constant=reject)

def write(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")

def arguments():
    return SimpleNamespace(source_manifest=str(PROBE / "source_manifest.json"),
        source_manifest_sha256=SOURCE_SHA, runtime_manifest=str(PROBE / "runtime_manifest.json"),
        runtime_manifest_sha256=RUNTIME_SHA, library=str(SO), library_sha256=SO_SHA,
        build_receipt=str(RECEIPT), build_receipt_sha256=RECEIPT_SHA,
        fixed_manifest_sha256=FIXED_SHA)

def closure():
    checked(PROBE / "source_manifest.json", SOURCE_SHA)
    checked(PROBE / "runtime_manifest.json", RUNTIME_SHA)
    checked(FIXED / "runtime_manifest.json", FIXED_SHA)
    source, runtime, fixed = (read(p) for p in (PROBE / "source_manifest.json",
                              PROBE / "runtime_manifest.json", FIXED / "runtime_manifest.json"))
    require(source.get("namespace") == "qwen36_damp_prefill_float_probe" and
            source.get("schema") == "damp-prefill-float-compiled-source/v1" and
            len(source["compiled_sources"]) == 9 and len(runtime["sources"]) == 15, "old compiled9/runtime15")
    table = {}
    for rows in (source["compiled_sources"], runtime["sources"], fixed["frozen_dependencies"], fixed["sources"]):
        for name, digest in rows.items():
            p = (REPO / name).resolve()
            require(p.is_relative_to(PROJECT.resolve()), "source escaped project")
            require(name not in table or table[name] == digest, "conflicting source pin")
            checked(p, digest)
            table[name] = digest
    require(fixed.get("schema") == "damp-prefill-fixed-buffers-runtime/v1" and
            fixed.get("counts") == [64, 896] and fixed.get("turns") == 20 and
            fixed.get("identical_repeats") == 8 and fixed.get("prepare_per_case") == 1 and
            fixed.get("default_execute") is False and fixed.get("npu_executed") is False,
            "frozen fixed-buffer protocol")
    for p, digest in ((HELPER, HELPER_SHA), (FULL, FULL_SHA), (SMOKE, SMOKE_SHA),
                      (SO, SO_SHA), (RECEIPT, RECEIPT_SHA)):
        checked(p, digest)
    receipt = read(RECEIPT)
    require(receipt.get("schema") == "damp-prefill-float-build/v1" and
            receipt.get("status") == "compiled_no_device" and receipt.get("npu_executed") is False and
            receipt.get("image_id") == IMAGE and receipt.get("npu_arch") == "dav-2201" and
            receipt.get("namespace") == source["namespace"] and
            receipt.get("source_manifest_sha256") == SOURCE_SHA and
            receipt.get("library_sha256") == SO_SHA and receipt.get("sources") == source["compiled_sources"],
            "actual exact float build receipt")
    for command in receipt.get("commands", []):
        require(command.get("exit_code") == 0 and command.get("command"), "actual successful command")
        checked(command["log_path"], command["log_sha256"])
    require(len(receipt.get("commands", [])) >= 2, "actual build command logs")
    exported = receipt.get("exported_kernel", {})
    require(exported.get("name") == "qwen36_damp_prefill_float_div_bits_kernel" and
            exported.get("defined") is True and exported.get("type") in ("T", "W"), "non-UND exported kernel")
    checked(exported["audit_path"], exported["audit_sha256"])
    original = load("float_dispatch_original", PROBE / "run_float_gate.py")
    require(receipt.get("cann_version_info_sha256") == original.OPP_SHA, "actual archived OPP identity")
    fixed_runner = load("float_dispatch_fixed", FIXED / "run_fixed_buffers.py")
    h = load("float_dispatch_host_helper", HELPER)
    full = load("float_dispatch_parent_proof", FULL)
    require("torch" not in sys.modules and "torch_npu" not in sys.modules, "source preparation is stdlib only")
    return dict(compiled_sources=9, runtime_sources=15, fixed_source_files=4,
        files=table, library_sha256=SO_SHA, build_receipt_sha256=RECEIPT_SHA,
        image_local_OPP_admission="pending original.source_bindings in same immutable image before Torch"), original, fixed_runner, h, full

def packet(path, digest):
    checked(path, digest)
    require(Path(path).resolve() == BASE / "PACKET.json", "this NEW packet only")
    p = read(path)
    require(p.get("schema") == "damp-prefill-float-dispatch-source/v1" and
            set(p.get("sources", {})) == set(OWN), "exact NEW source packet")
    for name, pin in p["sources"].items():
        checked(BASE / name, pin)
    return p

def source_check():
    info, original, fixed, _, _ = closure()
    args = arguments()
    bindings = original.source_bindings(args)
    before = fixed.source_snapshot(args)
    require(fixed.bind_sources(args, before) == bindings, "original/fixed actual source_bindings mismatch")
    require(before["all_match"] and "torch" not in sys.modules and "torch_npu" not in sys.modules,
            "image-local admission must be actual and no Torch")
    return dict(schema="damp-prefill-float-image-source/v1", status="actual_source_bindings_pass",
        source=info, bindings=bindings, fixed_manifest_sha256=FIXED_SHA,
        OPP=dict(path=str(original.OPP_PATH), sha256=sha(original.OPP_PATH)),
        npu_executed=False, torch_imported=False)

def deadline(seconds=0, now=None):
    now = now or datetime.now(timezone.utc)
    remaining = (datetime.fromisoformat(DEADLINE.replace("Z", "+00:00")) - now).total_seconds()
    require(remaining > seconds, "fixed DAMP cutoff/phase budget; never extend")
    return remaining

def terminal(raw, helper):
    d = raw.get("structuredContent", raw)
    require(d.get("operationId") == helper.PARENT_OPERATION and d.get("terminal") is True, "actual MA0455 terminal")
    op = d.get("operation", {})
    require(op.get("routeDecision") == "peer_direct" and op.get("targetPeerId") == helper.PARENT_PEER,
            "original actual MA peer/direct route")
    result = op.get("result", {})
    record = result.get("record", {})
    require(result.get("found") is True and result.get("ok") is True and result.get("lane") == "job" and
            result.get("state") == "completed" and record.get("id") == helper.PARENT_OPERATION and
            record.get("lane") == "job" and record.get("state") == "completed" and
            type(record.get("exitCode")) is int and record.get("cancelled") is False and
            record.get("timedOut") is False and record.get("error") is None and
            record.get("command") == "/usr/bin/python3" and record.get("cwd") == str(REPO),
            "authoritative actual completed exit; no outer-ok inference")
    return dict(operation_id=helper.PARENT_OPERATION, exit_code=record["exitCode"],
        capture_success=record["exitCode"] == 0, raw_terminal_preserved=True,
        scope="terminal releases scheduling only; a nonzero capture remains failed")

def plan(run_id, physical):
    require(type(physical) is int and physical in (4, 5, 6, 7), "one authorized card")
    require(isinstance(run_id, str) and re.fullmatch("[a-z][a-z0-9_-]{0,31}", run_id), "safe new run ID")
    root = ROOT / ("prefill-float-dispatch-" + run_id)
    name = "qwen36_damp_prefill_float_npu%d_20261006_%s" % (physical, run_id)
    argv = ["docker", "create", "--name", name, "--label", "model-tuning-lab.owner=" + OWNER,
        "--label", "model-tuning-lab.run=" + run_id, "--network", "none", "--cpus", "1",
        "--memory", "8g", "--memory-swap", "8g", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--device", "/dev/davinci%d:/dev/davinci0" % physical]
    for node in ("davinci_manager", "devmm_svm", "hisi_hdc"):
        argv += ["--device", "/dev/" + node]
    for p, writable in ((REPO, False), (BUILD, False), (Path("/usr/local/Ascend/driver"), False),
                        (root, True), (root / "launch", False)):
        argv += ["--mount", "type=bind,source=%s,target=%s%s" % (p, p, "" if writable else ",readonly")]
    argv += ["-e", "ASCEND_RT_VISIBLE_DEVICES=0", "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-e", "OMP_NUM_THREADS=1", "-e", "TOKENIZERS_PARALLELISM=false", "-w", str(REPO),
        "--entrypoint", "/bin/bash", IMAGE, "-c", BOOTSTRAP, "damp-float-bootstrap", "/bin/sleep", "infinity"]
    return dict(schema="damp-prefill-float-dispatch-plan/v1", status="dry-plan-not-executed",
        launchable=False, run_id=run_id, physical_card=physical, logical_card=0,
        root=str(root), container_name=name, docker_create_argv=argv,
        create_argv_sha256=hashlib.sha256(json.dumps(argv, separators=(",", ":")).encode()).hexdigest(),
        scope=dict(graph=False, packing=False, serving=False, performance=False, task_accuracy=False),
        deadline=DEADLINE, sequence=["actual image-local source_bindings(no Torch)", "fresh canary",
                                   "old full eager matrix", "fresh canary", "fixed-buffer eager matrix"],
        pending=["actual MA0455 terminal/stopped parent", "MAIN explicit opt-in", "fresh resources/mapping/canary"])

def inspect_owned(actual, entry, cid):
    require(re.fullmatch("[0-9a-f]{64}", cid) and actual.get("Id") == cid and
            actual.get("Name") == "/" + entry["container_name"] and actual.get("Image") == IMAGE, "exact owned name/ID/image")
    host, config = actual["HostConfig"], actual["Config"]
    labels = config.get("Labels") or {}
    require(labels.get("model-tuning-lab.owner") == OWNER and labels.get("model-tuning-lab.run") == entry["run_id"], "actual owned labels")
    require(host.get("Privileged") is False and host.get("NetworkMode") == "none" and
            host.get("IpcMode") != "host" and not host.get("DeviceRequests") and
            host.get("Memory") == MEMORY and host.get("MemorySwap") == MEMORY and
            host.get("NanoCpus") == 10**9 and set(host.get("CapDrop", [])) == {"ALL"} and
            any(x in ("no-new-privileges", "no-new-privileges=true") for x in host.get("SecurityOpt", [])), "actual cgroup/security scope")
    wanted = {"/dev/davinci%d" % entry["physical_card"]: "/dev/davinci0",
              **{"/dev/" + x: "/dev/" + x for x in ("davinci_manager", "devmm_svm", "hisi_hdc")}}
    devices = host.get("Devices", [])
    require(len(devices) == 4 and {r["PathOnHost"]: r["PathInContainer"] for r in devices} == wanted, "one authorized physical mapping")
    mounts = actual["Mounts"]
    expected = {str(REPO): False, str(BUILD): False, "/usr/local/Ascend/driver": False,
                entry["root"]: True, str(Path(entry["root"])/"launch"): False}
    require(len(mounts) == 5 and {r["Destination"] for r in mounts} == set(expected), "exact mounts only")
    for r in mounts:
        require(r["Type"] == "bind" and r["RW"] is expected[r["Destination"]] and
                Path(r["Source"]).resolve() == Path(r["Destination"]).resolve(), "actual RO sources/RW new root")
    env = dict(x.split("=", 1) for x in config.get("Env", []) if "=" in x)
    argv = entry["docker_create_argv"]
    for i, x in enumerate(argv):
        if x == "-e":
            key, value = argv[i+1].split("=", 1)
            require(env.get(key) == value, "actual environment drift")
    after = argv[argv.index("--entrypoint")+2:]
    require(config.get("Entrypoint") == ["/bin/bash"] and config.get("Cmd") == after[1:] and
            config.get("WorkingDir") == str(REPO), "actual startup command")
    return actual

def telemetry(raw):
    result, current = {}, None
    for line in raw.splitlines():
        head = re.match(r"^\|\s*(\d+)\s+910B4\s*\|", line)
        if head:
            current = int(head[1])
            continue
        fields = line.split("|")
        row = (re.fullmatch(r"\s*(\d+)\s+\d+\s*/\s*\d+\s+(\d+)\s*/\s*(\d+)\s*", fields[3])
               if len(fields) == 5 and re.fullmatch(r"\s*[0-9A-Fa-f:.]+\s*", fields[2]) else None)
        if row and current is not None:
            result[current] = dict(aicore=int(row[1]), hbm_mib=int(row[2]), capacity_mib=int(row[3]))
    return result

def resources(cmd, h, card, protected=None, owned=None, idle=True):
    raw, _ = cmd.run("npu-smi", ["npu-smi", "info"])
    rows = h.parse_processes(raw)
    p = h.protected_fingerprint(rows)
    require(protected is None or p == protected, "protected0-3 identities changed; never signal them")
    data = telemetry(raw)
    require(card in data, "actual target 910B4 telemetry")
    if idle:
        require(not rows[card] and data[card]["aicore"] == 0 and data[card]["hbm_mib"] <= 3165, "selected card outside actual idle envelope")
    else:
        for row in rows[card]:
            h.owner_pid(row["pid"], owned)
    # Record declarations/node holders; idle declarations do not trigger stop.
    cmd.run("docker-ps", ["docker", "ps", "--no-trunc"])
    cmd.run("target-node-holders", ["fuser", "-v", "/dev/davinci" + str(card)], allowed=(0, 1))
    uda = Path("/proc/uda/namespace_node").read_text()
    engine = cmd.json("docker-info", ["docker", "info", "--format", "{{json .}}"])
    require(type(engine.get("NCPU")) is int and engine["NCPU"] >= 1, "actual Docker CPU capacity")
    mem = Path("/proc/meminfo").read_text()
    match = re.search(r"^MemAvailable:\s*(\d+)\s+kB", mem, re.M)
    require(match, "actual ordinary MemAvailable")
    available = int(match[1]) * 1024
    running, _ = cmd.run("running-IDs", ["docker", "ps", "--quiet", "--no-trunc"])
    joint_cpu, joint_memory, leases = 1, MEMORY, []
    # Conservative full caps for identifiable existing MAIN correctness/selector jobs.
    # Unknown authorized-card compute blocks joint scheduling, but is never stopped.
    all_known = set()
    for cid in running.split():
        actual = h.inspect(cmd, cid, "joint-inspect")
        if cid == owned:
            continue
        labels = actual["Config"].get("Labels") or {}
        host = actual["HostConfig"]
        is_numeric = labels.get("model-tuning-lab.owner") in ("damp-allT-dispatch-v1", OWNER)
        is_selector = labels.get("model-tuning-lab.cpu-selector-owner") == "main-cpu-selector-v1"
        if is_numeric or is_selector:
            quota, cap = (1, MEMORY) if is_numeric else (2, 4 * GIB)
            require(host.get("Privileged") is False and actual["Image"] == IMAGE and
                    host.get("NanoCpus") == quota * 10**9 and host.get("Memory") == cap and
                    host.get("MemorySwap") == cap, "actual joint MAIN cgroup/quota bounds")
            if is_selector:
                require(not host.get("Devices") and not host.get("DeviceRequests"), "CPU selector has devices")
            else:
                nodes = [d["PathOnHost"] for d in host.get("Devices", []) if re.fullmatch("/dev/davinci[0-7]", d["PathOnHost"])]
                require(len(nodes) == 1 and nodes[0] in ["/dev/davinci"+str(i) for i in range(4,8)] and
                        nodes[0] != "/dev/davinci" + str(card), "joint single disjoint correctness card")
                for c in range(4, 8):
                    for row in rows[c]:
                        identity = h.proc_identity(row["pid"])
                        if any(cid == component or component == "docker-" + cid + ".scope"
                               for line in identity["cgroup"].splitlines() for component in line.split(":", 2)[-1].split("/")):
                            all_known.add((c, row["pid"]))
            leases.append(dict(container_id=cid, cpu_quota=quota, memory_limit_bytes=cap,
                               cgroup=h.cgroup_record(actual, cid, cap, quota)))
            joint_cpu += quota
            joint_memory += cap
    for c in range(4, 8):
        if c == card:
            continue
        require(all((c, r["pid"]) in all_known for r in rows[c]), "unknown real authorized-card job; MAIN must serialize")
    require(engine["NCPU"] >= joint_cpu, "fresh aggregate CPU quotas exceed Docker NCPU")
    require(available >= (RESERVE if owned else joint_memory + RESERVE), "fresh ordinary RAM budget; no HugeTLB reclamation")
    require(shutil.disk_usage(ROOT).free >= (GIB if owned else DISK), "fresh result disk headroom")
    mounting = h.mount_budget(cmd)
    return dict(observed_at_unix_ns=time.time_ns(), npu_smi=raw, rows=rows, protected=p,
        telemetry=data, uda_namespace=uda, meminfo=mem, ordinary_mem_available_bytes=available,
        ram_admission_bytes=joint_memory+RESERVE, joint_cpu_quota=joint_cpu, docker_info=engine,
        joint_correctness_leases=leases, mount_headroom=mounting)

def parent_stopped(cmd, h, full, args):
    raw = read(checked(args.parent_operation_receipt, args.parent_operation_sha256))
    record = terminal(raw, h)
    create = read(h.PARENT_AUDIT / "create-command.json")["argv"]
    require(create[create.index("--name")+1] == h.PARENT_NAME, "actual parent create name")
    label = next(x for x in create if x.startswith(full.LABEL + "="))
    owner = label.split("=", 1)[1]
    require(owner, "actual parent ownership nonce")
    full.NAME = h.PARENT_NAME  # configure fresh imported proof object; never edit frozen source
    actual = h.inspect(cmd, h.PARENT_ID, "parent-stopped-inspect")
    full.container_proof(actual, h.PARENT_ID, owner)
    require(actual["State"].get("Running") is False and actual["State"].get("Status") == "exited", "TP4 parent must already be stopped")
    return dict(terminal=record, raw_operation=raw, operation_sha256=args.parent_operation_sha256,
                stopped_inspect=actual, create_command_sha256=sha(h.PARENT_AUDIT / "create-command.json"),
                source_lock_required=False)

def container_exec(cid, *args):
    return ["docker", "exec", cid, "/bin/bash", "-c", BOOTSTRAP, "damp-float-exec", PYTHON, "-B", *args]

def gate_argv(kind, entry, cid, proof):
    common = ["--execute", "--library", str(SO), "--library-sha256", SO_SHA,
        "--build-receipt", str(RECEIPT), "--build-receipt-sha256", RECEIPT_SHA,
        "--preflight", str(proof), "--preflight-sha256", sha(proof),
        "--physical-card", str(entry["physical_card"]), "--output-dir", str(Path(entry["root"]) / kind)]
    if kind == "old-matrix":
        program = PROBE / "run_float_gate.py"
        common += ["--mode", "npu", "--source-manifest", str(PROBE / "source_manifest.json"),
            "--source-manifest-sha256", SOURCE_SHA, "--runtime-manifest", str(PROBE / "runtime_manifest.json"),
            "--runtime-manifest-sha256", RUNTIME_SHA]
    else:
        require(kind == "fixed-buffers", "known frozen phase only")
        program = FIXED / "run_fixed_buffers.py"
        common += ["--fixed-manifest-sha256", FIXED_SHA]
    return container_exec(cid, str(BASE / "dispatch.py"), "--run-frozen-gate", kind, *common)

def canary(cmd, h, entry, cid, protected, phase, audit):
    before = resources(cmd, h, entry["physical_card"], protected, cid)
    write(audit / (phase + "-precanary.json"), before)
    inspect_owned(h.inspect(cmd, cid), entry, cid)
    argv = container_exec(cid, "-c", CANARY_CODE, str(entry["physical_card"]),
                          entry["create_argv_sha256"], CANARY_SHA)
    output, _ = cmd.run(phase + "-canary", argv, timeout=90)
    rows = []
    for line in output.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get("schema") == "damp-prefill-float-canary/v1":
            rows.append(row)
    require(len(rows) == 1, "one actual canary result")
    row = rows[0]
    require(row.get("status") == "actual_canary_pass" and row.get("npu_executed") is True and
            row.get("expected_physical_card") == entry["physical_card"] and row.get("logical_device") == 0 and
            row.get("runtime_soc") == "Ascend910B4" and row.get("result") == [1., 4., 9.] and
            row.get("create_argv_sha256") == entry["create_argv_sha256"] and
            row.get("canary_program_sha256") == CANARY_SHA and
            type(row.get("completed_at_unix_ns")) is int and
            0 <= time.time_ns()-row["completed_at_unix_ns"] <= 300*10**9, "actual fresh canary identity")
    write(audit / (phase + "-canary.json"), row)
    after = resources(cmd, h, entry["physical_card"], protected, cid)
    write(audit / (phase + "-postcanary.json"), after)
    actual = inspect_owned(h.inspect(cmd, cid), entry, cid)
    proof = dict(physical_npu_ids=[entry["physical_card"]],
        logical_to_physical={"0":entry["physical_card"]}, privileged=False,
        exclusive_resource_check_passed=True, observed_at_unix_ns=time.time_ns(), container_id=cid,
        container_inspect=actual, canary=dict(path=str(audit / (phase + "-canary.json")),
        sha256=sha(audit / (phase + "-canary.json"))), fresh_resource_audit=str(audit / (phase + "-postcanary.json")))
    path = audit / (phase + "-device-proof.json")
    write(path, proof)
    return path

def run_frozen_gate(kind, argv):
    """Same-image wrapper preserves the frozen gate arithmetic and its primary error."""
    require(kind in ("old-matrix", "fixed-buffers"), "exact frozen child phase")
    _, old, fixed, _, _ = closure()
    runner = old if kind == "old-matrix" else fixed
    args = runner.parse(argv)
    require(args.execute and (kind != "old-matrix" or args.mode == "npu"),
            "real frozen NPU child only, no Meta substitution")
    require(Path(args.output_dir).parent.parent == ROOT and
            Path(args.output_dir).parent.name.startswith("prefill-float-dispatch-") and
            Path(args.output_dir).name == kind, "exact fresh child output")
    audit = Path(args.output_dir).parent / "launch"
    require(audit.is_dir(), "MAIN-created current audit root")
    source_check()
    error, secondary, maps = None, [], []
    old_path = list(sys.path)
    try:
        sys.path.insert(0, str(PROBE))
        runner.main(argv)
    except BaseException as e:
        error = e
    finally:
        sys.path[:] = old_path
        try:
            lines = Path("/proc/self/maps").read_text().splitlines()
            paths = sorted({line.split()[-1] for line in lines if "/" in line and
                (line.split()[-1] == str(SO.resolve()) or Path(line.split()[-1]).name == "libtorch_npu.so")})
            maps = [dict(path=p, sha256=sha(p)) for p in paths]
            require(any(r["path"] == str(SO.resolve()) and r["sha256"] == SO_SHA for r in maps) and
                    any(Path(r["path"]).name == "libtorch_npu.so" for r in maps), "actual child loaded SO/libtorch_npu maps")
        except BaseException as e:
            secondary.append(repr(e))
        evidence_path = Path(args.output_dir) / "LOADED_LIBRARIES.json"
        try:
            write(evidence_path, dict(schema="damp-prefill-float-child-libraries/v1",
                original_error=None if error is None else repr(error), secondary_errors=secondary, maps=maps,
                source_unchanged_numerics=True, serving_ready=False, performance_claim=False))
        except BaseException as evidence_error:
            secondary.append("loaded-library evidence write failed: " + repr(evidence_error))
            # A frozen gate can fail before mkdir. Never create or retry its output
            # here, nor let this secondary evidence error replace its exception.
            try:
                print(json.dumps(dict(schema="damp-prefill-float-child-secondary-error/v1",
                    status="failed", original_error=None if error is None else repr(error),
                    secondary_errors=secondary, evidence_path=str(evidence_path),
                    evidence_written=False, serving_ready=False, performance_claim=False),
                    allow_nan=False), file=sys.stderr, flush=True)
            except BaseException as stderr_error:
                # The outer process exit/traceback remains authoritative even when
                # its diagnostic stream is unavailable.
                secondary.append("secondary stderr emission failed: " + repr(stderr_error))
    if error is not None:
        raise error
    require(not secondary, "child loaded-library evidence failed")
    return 0

def validate_loaded(directory):
    p = directory / "LOADED_LIBRARIES.json"
    row = read(p)
    require(row.get("schema") == "damp-prefill-float-child-libraries/v1" and
            row.get("original_error") is None and row.get("secondary_errors") == [] and
            any(r.get("path") == str(SO.resolve()) and r.get("sha256") == SO_SHA for r in row.get("maps", [])) and
            any(Path(r["path"]).name == "libtorch_npu.so" and re.fullmatch("[0-9a-f]{64}",r["sha256"])
                for r in row.get("maps", [])), "actual exact child loaded-library identity")
    for r in row["maps"]:
        # libtorch_npu is image-local; its actual hash is retained, not faked as a host path.
        if r["path"] == str(SO.resolve()):
            checked(r["path"], r["sha256"])
    return dict(path=str(p), sha256=sha(p), candidate_library_sha256=SO_SHA)

def phase_run(cmd, h, argv, entry, cid, protected, label, audit):
    deadline(PHASE_TIMEOUT + 120)
    out, err = audit / (label + ".stdout"), audit / (label + ".stderr")
    process = None
    original_error = None
    cleanup_errors = []
    started = time.monotonic()
    with out.open("xb") as stdout, err.open("xb") as stderr:
        try:
            process = subprocess.Popen(argv, stdout=stdout, stderr=stderr)
            turn = 0
            while process.poll() is None:
                deadline()
                require(time.monotonic()-started <= PHASE_TIMEOUT, "fixed one-shot phase timeout")
                if turn % 4 == 0:
                    actual = inspect_owned(h.inspect(cmd, cid, label + "-runtime-inspect"), entry, cid)
                    require(not actual["State"].get("OOMKilled"), "owned OOM")
                    h.cgroup_record(actual, cid, MEMORY, 1)
                    record = resources(cmd, h, entry["physical_card"], protected, cid, idle=False)
                    write(audit / (label + "-monitor-%d.json" % turn), record)
                turn += 1
                time.sleep(3)
            require(process.returncode == 0, "real frozen gate nonzero exit; no retry")
        except BaseException as error:
            original_error = repr(error)
        finally:
            if process is not None and process.poll() is None:
                try:
                    process.terminate()  # local owned docker-exec client only
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
                except BaseException as secondary:
                    cleanup_errors.append(repr(secondary))
                    if original_error is None:
                        original_error = "local owned exec client cleanup failed"
    write(audit / (label + "-command.json"), dict(argv=argv, container_id=cid,
        exit_code=None if process is None else process.returncode, error=original_error,
        cleanup_errors=cleanup_errors, stdout=str(out), stdout_sha256=sha(out), stderr=str(err), stderr_sha256=sha(err),
        automatic_retry=False, performance_claim=False))
    require(original_error is None, original_error or "phase failed")

def report_identity(report):
    bindings = report.get("bindings", {})
    require(bindings.get("source_manifest_sha256") == SOURCE_SHA and
            bindings.get("runtime_manifest_sha256") == RUNTIME_SHA and
            bindings.get("library_sha256") == SO_SHA and
            bindings.get("build_receipt_sha256") == RECEIPT_SHA and
            report.get("namespace") == "qwen36_damp_prefill_float_probe" and
            report.get("actual_runtime_soc") == "Ascend910B4" and report.get("npu_executed") is True and
            report.get("graph_supported") is False and report.get("packing_supported") is False and
            report.get("serving_ready") is False, "actual report immutable identity/scope")

def artifact(path, digest, directory):
    p = Path(path)
    require(p.parent.resolve() == directory.resolve(), "raw artifact outside this frozen gate output")
    checked(p, digest)
    require(p.stat().st_size > 0, "empty raw artifact")
    return p

def validate_old(directory):
    p = directory / "report.json"
    report = read(p)
    report_identity(report)
    require(report.get("schema") == "damp-prefill-exact-float-gate/v1" and
            report.get("status") == "exact_float_numerical_pass" and report.get("mode") == "npu" and
            report.get("error") is None, "old matrix terminal pass")
    cases = load("float_dispatch_registered_cases", PROBE / "cases.py")
    expected = []
    for name, rows in cases.matrix_chunks(896):
        for enabled in (False, True):
            expected.append((name+("-certificate" if enabled else "-exact"), len(rows), enabled))
    for n in (64, 896):
        for turn in range(20):
            for enabled in (False, True):
                expected.append(("changing-%d-%d-%d" % (n, turn, enabled), n, enabled))
    actual = report.get("cases", [])
    require(len(actual) == len(expected), "old entire registered matrix required")
    for row, (name, count, enabled) in zip(actual, expected):
        require(row.get("name") == name and row.get("count") == count and
                row.get("use_candidate") is enabled and row.get("status") == "passed" and
                row.get("identical_repeats") == 8, "old exact fixture/order/repeat coverage")
        raw = artifact(row["artifact"], row["artifact_sha256"], directory)
        require((directory / (name + ".before.pt")).is_file() and raw.name == name + ".pt", "old raw-before retained")
    names = ["N0", "N63", "N65", "N897", "N1792", "wrongdtype", "noncontiguous", "offset", "alias", "cpu"]
    require([r.get("name") for r in report["negative"]] == names and
            all(r.get("passed") is True for r in report["negative"]), "old all ten actual negative rejections")
    for name in names:
        require((directory / ("reject-"+name+".before.pt")).is_file() and
                (directory / ("reject-"+name+".pt")).is_file(), "negative raw-before/after retained")
    return dict(path=str(p), sha256=sha(p), actual_cases=len(actual), actual_negative_cases=10)

def validate_fixed(directory):
    p = directory / "report.json"
    report = read(p)
    report_identity(report)
    require(report.get("schema") == "damp-prefill-fixed-buffers-gate/v1" and
            report.get("status") == "fixed_buffers_exact_float_pass" and report.get("error") is None and
            report.get("performance_supported") is False and report.get("npu_dispatch_attempted") is True,
            "fixed-buffer real terminal pass")
    require(len(report.get("cases", [])) == 4, "all four fixed-buffer cases")
    for row, (count, enabled) in zip(report["cases"], ((64, False), (64, True), (896, False), (896, True))):
        name = str(count) + ("-certificate" if enabled else "-exact")
        require(row.get("name") == name and row.get("count") == count and row.get("use_candidate") is enabled and
                row.get("status") == "passed" and row.get("prepares") == 1 and
                row.get("changed_turns") == 20 and row.get("identical_repeats") == 8 and
                len(row.get("turns", [])) == 20, "registered20 changes/8 repeats/1prepare")
        for key in ("input_pointers", "view_pointers"):
            require(len(row.get(key, [])) == 3 and all(type(r.get("pointer")) is int and
                    r["pointer"] % 32 == 0 for r in row[key]), "actual stable ND32B pointer records")
        require((directory / (name+"-prepare.before.pt")).is_file() and
                (directory / (name+"-prepare.pt")).is_file(), "prepare raw-before/after retained")
        previous = None
        for index, turn in enumerate(row["turns"]):
            require(turn.get("turn") == index and turn.get("status") == "passed" and
                    turn.get("identical_repeats") == 8 and len(turn.get("input_fingerprints", [])) == 3,
                    "fixed turn coverage/fingerprints")
            fingerprints = turn["input_fingerprints"]
            require(all(re.fullmatch("[0-9a-f]{64}", x) for x in fingerprints) and
                    (previous is None or all(a != b for a, b in zip(previous, fingerprints))), "actual three changed inputs")
            previous = fingerprints
            raw = artifact(turn["artifact"], turn["artifact_sha256"], directory)
            require(raw.name == name+"-turn-"+str(index)+".pt" and
                    (directory / (name+"-turn-"+str(index)+".before.pt")).is_file() and
                    (directory / (name+"-turn-"+str(index)+".rows.before.json")).is_file(), "turn raw-before/after retained")
    before = read(checked(report["source_before"]["path"], report["source_before"]["sha256"]))
    after = read(checked(report["source_after"]["path"], report["source_after"]["sha256"]))
    require(before.get("all_match") is True and after.get("all_match") is True and
            [(r["path"], r["actual_sha256"]) for r in before["files"]] ==
            [(r["path"], r["actual_sha256"]) for r in after["files"]], "fixed source before/after unchanged")
    require(any(r.get("path") == str(SO) and r.get("sha256") == SO_SHA for r in report.get("loaded_libraries", [])),
            "fixed actual loaded candidate SO maps")
    return dict(path=str(p), sha256=sha(p), actual_cases=4, changed_turns=80, identical_replays=640)

def execute(args, prepared):
    require(os.environ.get("DAMP_PREFILL_FLOAT_DISPATCH_EXECUTE") == "1", "MAIN explicit environment opt-in")
    require(Path.cwd().resolve() == REPO, "canonical host cwd")
    info, _, _, h, full = prepared
    packet(args.packet_manifest, args.packet_sha256)
    terminal(read(checked(args.parent_operation_receipt, args.parent_operation_sha256)), h)
    deadline(2*PHASE_TIMEOUT + 600)
    entry = plan(args.run_id, args.physical_card)
    root, audit = Path(entry["root"]), Path(entry["root"]) / "launch"
    require(not root.exists() and not root.is_symlink(), "NEW non-overwrite root")
    root.mkdir(exist_ok=False)
    audit.mkdir()
    cmd, cid, protected, failed = h.Commands(audit), None, None, None
    results, stops = [], []
    try:
        write(audit / "SOURCE_BEFORE.json", dict(source=info, packet_sha256=args.packet_sha256,
                                               packet=packet(args.packet_manifest, args.packet_sha256), plan=entry))
        write(audit / "PARENT_TERMINAL.json", parent_stopped(cmd, h, full, args))
        images = cmd.json("image-inspect", ["docker", "image", "inspect", IMAGE])
        require(len(images) == 1 and images[0]["Id"] == IMAGE and images[0]["Architecture"] == "arm64", "actual immutable image")
        fresh = resources(cmd, h, entry["physical_card"])
        protected = fresh["protected"]
        write(audit / "PRELAUNCH.json", fresh)
        h.absent_names(cmd, [entry])
        closure(); packet(args.packet_manifest, args.packet_sha256)
        output, _ = cmd.run("create", entry["docker_create_argv"])
        cid = output.strip()
        require(re.fullmatch("[0-9a-f]{64}", cid), "unknown create outcome; never guess/retry/reclaim")
        inspect_owned(h.inspect(cmd, cid, "created-inspect"), entry, cid)
        cmd.run("start", ["docker", "start", cid])
        inspect_owned(h.inspect(cmd, cid, "started-inspect"), entry, cid)
        h.cgroup_record(h.inspect(cmd, cid), cid, MEMORY, 1)
        # Only original no-Torch source_bindings runs before the canary; no substitute OPP proof.
        out, _ = cmd.run("image-source-check", container_exec(cid, str(BASE / "dispatch.py"), "--source-check"), timeout=120)
        actual = [json.loads(x) for x in out.splitlines() if x.startswith("{")]
        require(len(actual) == 1 and actual[0].get("status") == "actual_source_bindings_pass" and
                actual[0].get("npu_executed") is False and actual[0].get("torch_imported") is False and
                actual[0]["bindings"]["library_sha256"] == SO_SHA, "actual same-image noTorch source admission")
        write(audit / "IMAGE_SOURCE_BINDINGS.json", actual[0])
        for kind in ("old-matrix", "fixed-buffers"):
            closure(); packet(args.packet_manifest, args.packet_sha256)
            deadline(PHASE_TIMEOUT+240)
            require(not (root / kind).exists(), "new phase output only")
            proof = canary(cmd, h, entry, cid, protected, kind, audit)
            phase_run(cmd, h, gate_argv(kind, entry, cid, proof), entry, cid, protected, kind, audit)
            report = validate_old(root / kind) if kind == "old-matrix" else validate_fixed(root / kind)
            report["actual_loaded_libraries"] = validate_loaded(root / kind)
            actual_report = read(root / kind / "report.json")
            require(actual_report["physical_card"] == entry["physical_card"] and
                    actual_report.get("device_proof", {}).get("path") == str(proof) and
                    actual_report["device_proof"].get("sha256") == sha(proof),
                    "report must bind the actual phase-specific physical proof")
            write(audit / (kind+"-VALIDATION.json"), report)
            results.append(report)
    except BaseException as error:
        failed = repr(error)
        retained = []
        for kind in ("old-matrix", "fixed-buffers"):
            p = root / kind / "report.json"
            try:
                retained.append(dict(phase=kind, path=str(p), sha256=sha(p) if p.is_file() else None,
                                     report=read(p) if p.is_file() else None))
            except BaseException as copy_error:
                retained.append(dict(phase=kind, copy_error=repr(copy_error)))
        write(audit / "FAILURE.json", dict(original_error=failed, nullable_reports=retained,
            automatic_retry=False, unknown_create_not_reclaimed=True,
            scope="resource/interface/implementation/numerical failure, not paper-wide no-go"))
    finally:
        try:
            after = closure()[0]
            write(audit / "SOURCE_AFTER.json", dict(source=after, packet=packet(args.packet_manifest, args.packet_sha256)))
            require(after == info, "host source closure drift")
        except BaseException as secondary:
            write(audit / "SOURCE_AFTER_FAILURE.json", dict(error=repr(secondary), original_error=failed))
            if failed is None:
                failed = "source-after admission failed"
        if cid is not None and re.fullmatch("[0-9a-f]{64}", cid):
            try:
                actual = inspect_owned(h.inspect(cmd, cid, "stop-preinspect"), entry, cid)
                if actual["State"]["Running"]:
                    cmd.run("stop-owned", ["docker", "stop", "--time", "30", cid], timeout=45)
                actual = inspect_owned(h.inspect(cmd, cid, "stop-postinspect"), entry, cid)
                require(not actual["State"]["Running"] and actual["State"]["Status"] in ("exited", "created"), "owned stop retained")
                stops.append(dict(container_id=cid, deleted=False, status=actual["State"]["Status"]))
            except BaseException as secondary:
                stops.append(dict(container_id=cid, stop_error=repr(secondary), deleted=False))
                if failed is None:
                    failed = "exact owned stop failed; MAIN attention"
            try:
                released = resources(cmd, h, entry["physical_card"], protected)
                write(audit / "POST_RELEASE.json", released)
            except BaseException as secondary:
                write(audit / "RELEASE_FAILURE.json", dict(error=repr(secondary), original_error=failed, no_external_signals=True))
                if failed is None:
                    failed = "release proof failed; MAIN attention"
        write(audit / "STOP_RETAIN.json", stops)
    require(failed is None, "one-shot failed; raw evidence retained: " + str(audit))
    result = dict(schema="damp-prefill-float-dispatch-result/v1", status="isolated_eager_float_dispatch_pass",
        reports=results, exact_owned_container_stopped_and_retained=True,
        graph_supported=False, packing_supported=False, serving_ready=False, performance_claim=False,
        task_accuracy_claim=False, deadline=DEADLINE)
    write(audit / "RESULT.json", result)
    return result

def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] == "--run-frozen-gate":
        require(len(argv) > 2, "exact frozen child phase and arguments")
        return run_frozen_gate(argv[1], argv[2:])
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--source-check", action="store_true", help="same-image noTorch admission only; no output or device")
    p.add_argument("--run-id", default="v1")
    p.add_argument("--physical-card", type=int, choices=(4, 5, 6, 7), default=4)
    for name in ("packet-manifest", "packet-sha256", "parent-operation-receipt", "parent-operation-sha256"):
        p.add_argument("--" + name)
    args = p.parse_args(argv)
    require(not (args.execute and args.source_check), "separate source-check/execute modes")
    if args.execute:
        require(os.environ.get("DAMP_PREFILL_FLOAT_DISPATCH_EXECUTE") == "1", "MAIN explicit opt-in before admission")
        require(all(getattr(args, name) for name in ("packet_manifest", "packet_sha256",
                "parent_operation_receipt", "parent_operation_sha256")), "actual MAIN source/terminal proofs")
    if args.source_check:
        print(json.dumps(source_check(), allow_nan=False))
        return 0
    prepared = closure()
    if not args.execute:
        result = plan(args.run_id, args.physical_card)
        result["source"] = prepared[0]
        result["no_docker_or_npu"] = True
        print(json.dumps(result, allow_nan=False))
        return 0
    print(json.dumps(execute(args, prepared), allow_nan=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
