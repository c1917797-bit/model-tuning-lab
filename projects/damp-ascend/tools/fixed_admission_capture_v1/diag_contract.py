"""Fixed-admission diagnostic contract. Importing this file never imports Torch."""
from __future__ import annotations
import ast
import hashlib
import os
import shlex
import sys
import json
import re
from pathlib import Path

ROOT = Path("/opt/host/vnf/austinov/model-tuning-lab")
RESULT_ROOT = Path("/cache/cch/qwen36-damp-20261006")
MODEL = "/cache/efim/Qwen3.6-27B"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PYTHON = "/usr/local/python3.12.13/bin/python3"
PACKAGE_ROOT = ROOT / "projects/damp-ascend/tools/fixed_admission_capture_v1"
COLLECTOR = ROOT / "projects/damp-ascend/collector"
TRAIN = RESULT_ROOT / "calibration-inputs/full-training-36x1024-v3.json"
TRAIN_SHA = "f348e0b0404e2f3a619b986f5c1152427c52f1a3550386ee1f894eafa6986b33"
ROW = "math-fit-02"
TOKEN_SHA = "3221d44cf06bc8c752a03a0c895d5a5fb82ef73ab7fe714efd67b29fe427522d"
LAYERS = tuple(i for i in range(64) if i % 4 != 3)
ARMS = ("off-a", "off-b", "on")
TURNS = 33
RAW_LIMIT = 20 * 1024**3
RANK_LIMIT = RAW_LIMIT // 12
SECONDS = 45 * 60
ORDINARY_FLOOR = 64 * 1024**3
HOST_RESERVE = 8 * 1024**3
GIB = 1024**3
FORMAL_CPUS = 6
PREFLIGHT_CPUS = 1
PREFLIGHT_MEMORY = 2 * GIB
ALLT_OWNER = "damp-allT-dispatch-v1"
ALLT_OPERATION = "exec-00000000000006a0"
MAIN_PEER = "lgw_a6109c51076a4a2c9d2674ca5a8704a0"
PRIOR_IDS = {
    4: "644e483333a636130b1310c15f8f694187331391a3d8df0f40ab36051b9a21db",
    5: "d4abaa82dea94ba3132faf33e355de88157787d57d61611e6a28be335b1f30b4",
    6: "305f493062816e210a135c509b5cdebf7571074c898b18db319e2de99c6ff24f",
    7: "5deeeaa5aa9e78ba165ecf5250b8ee8b85b1feb4f30c58eb392e8c5758db7517",
}
PRIOR_PROOF_SHAS = {
    4: "b0db314b7752614832cb7bb71682ef71f633082c3a646d891a6f96954ff499ca",
    5: "552659aec66716f4595bf20ffd90e281d9250e818165b085fd3bdf813b6d4aa1",
    6: "157ee02348d220e39b01983c4792859e8f7af3b071634a6eb9f9086288d2d337",
    7: "133b3e76cae53dee474222d81fec330aea202bab5ec454243327517fe078538e",
}
PROTECTED_ID = "eeb65fd29e054783ce8ba6f9165ea54d38a2575f170225ddf11b3e7584b9f12a"
PROTECTED_NAME = "/qwen36_hypic2048_quality41984_baseline_npu0_3_v1"
PROTECTED_PROCESS_NAMES = {"vllm","python3","VLLM::EngineCor","VLLM::Worker_TP"}
PROTECTED_GROWTH_LIMIT = 4 * GIB
BOOTSTRAP_SOURCE = ROOT / "projects/damp-ascend/tools/prefill_float_dispatch_v1/dispatch.py"
BOOTSTRAP_SHA = "094defb90bfc6d748d13069a48bd24297d01caaab1720ef5b8a3bc32ecf87c9e"
NATIVE_SO = "/vllm-workspace/vllm-ascend/vllm_ascend/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
NATIVE_SO_SHA = "eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a"
RUNTIME = {
    "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py": "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816",
    "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py": "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968",
    "/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_qwen3_5.py": "21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3",
    "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py": "885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0",
    "/vllm-workspace/vllm/vllm/forward_context.py": "1c6fa51e9a02a120fed5e7357afb1190516cbdfefd1c644dfcd860603f1527c5",
}
def require(value, message):
    if not value:
        raise ValueError(message)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False,
                      ensure_ascii=False).encode()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def load(path):
    return json.loads(Path(path).read_text())

def write_new(path, value):
    path = Path(path)
    with path.open("xb") as f:
        f.write(canonical(value)+b"\n")

def source_contract():
    m = load(PACKAGE_ROOT / "SOURCE_MANIFEST.json")
    require(m["schema"] == "damp-fixed-admission-sources/v1", "wrong source manifest")
    for name, digest in m["files"].items():
        require(file_sha(PACKAGE_ROOT/name) == digest, "new packet drift: "+name)
    for name, digest in m["external_repo_files"].items():
        require(file_sha(ROOT/name) == digest, "frozen dependency drift: "+name)
    require(m["runtime_sources"] == RUNTIME, "runtime pins changed")
    require(set(m["source_audit"]) == {"md","json"}, "both source audits required")
    for ref in m["source_audit"].values():
        path = (ROOT/ref["path"]).resolve()
        require(path.is_relative_to(ROOT) and file_sha(path) == ref["sha256"],
                "source audit reference drift: "+ref["path"])
    return {"path": str(PACKAGE_ROOT/"SOURCE_MANIFEST.json"),
            "sha256": file_sha(PACKAGE_ROOT/"SOURCE_MANIFEST.json")}

def make_manifest():
    require(file_sha(TRAIN) == TRAIN_SHA, "TRAIN bytes changed; no fallback")
    m = load(TRAIN)
    found = [r for r in m["rows"] if r["id"] == ROW]
    require(len(found) == 1 and len(found[0]["input_ids"]) == 1024, "TRAIN row not unique1024")
    row = dict(found[0])
    require(row["input_ids_sha256"] == TOKEN_SHA and sha(canonical(row["input_ids"])) == TOKEN_SHA,
            "TRAIN token identity changed")
    require(row["source"]["split"] == "train", "not publisher TRAIN")
    row["split"] = "diagnostic"  # Original source and full target/context selection remain intact.
    m.update(mode="smoke", rows=[row], anchors=[24], horizon=2,
             provenance="project-smoke-not-calibration")
    m["generation"] = dict(m["generation"], min_tokens=33, max_tokens=33)
    m["diagnostic"] = {"schema": "damp-fixed-admission/v1", "source_manifest_file_sha256": TRAIN_SHA,
                       "source_row_id": ROW, "calibration_admitted": False,
                       "fixed_single_request": True}
    return m

def overlay_inventory(entries):
    found = [e for e in entries if e.group == "vllm.general_plugins" and e.name == "damp_capture"]
    require(len(found) == 1 and found[0].value == "damp_admission_diagnostic:register",
            "duplicate/wrong damp_capture entrypoint; collector dist-info must not be on PYTHONPATH")
    return {"name": found[0].name, "value": found[0].value, "group": found[0].group}

def validated_path(root):
    p = Path(root).resolve()
    require(p.is_relative_to(RESULT_ROOT) and p != RESULT_ROOT, "result root out of scope")
    require(not p.exists(), "new output already exists; no overwrite")
    return p

def budget(mem_available, free_disk):
    require(mem_available >= ORDINARY_FLOOR+HOST_RESERVE, "64GiB ordinary floor +8GiB reserve")
    require(free_disk >= 40*1024**3, "free disk below40GiB")
    return {"ordinary_floor": ORDINARY_FLOOR, "host_reserve": HOST_RESERVE,
            "raw_limit": RAW_LIMIT, "seconds": SECONDS}

def canonical_event(event):
    """Stable cross-arm attributes; absolute pointers/UUIDs are separately checked within each arm."""
    return {k: event[k] for k in ("turn", "layer", "prefix", "metadata", "parameters", "slot",
                                  "ssm_geometry", "conv_geometry")}

def snapshot_signature(value):
    return {k: value[k] for k in ("sha256", "shape", "dtype", "finite", "num_bytes")}

def events(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

def resource_budget(ncpu, mem_available, free_disk, *, preflight, allt_running):
    """Only our known allT caps, this new cap and reserve; not external declarations."""
    require(type(ncpu) is int and ncpu >= 6, "invalid actual Docker NCPU")
    require(type(allt_running) is int and 0 <= allt_running <= 4, "unknown allT cardinality")
    require(preflight or allt_running == 0, "formal diagnostic requires allT actual release")
    numeric_cpu = 4 if allt_running else 0
    numeric_memory = 32*GIB if allt_running else 0
    new_cpu = PREFLIGHT_CPUS if preflight else FORMAL_CPUS
    new_memory = PREFLIGHT_MEMORY if preflight else ORDINARY_FLOOR
    require(ncpu >= numeric_cpu+new_cpu+1, "Docker CPU quota capacity +1CPU reserve exceeded")
    required = numeric_memory+new_memory+HOST_RESERVE
    require(mem_available >= required, "our conservative combined caps +8GiB reserve exceeded")
    require(free_disk >= 40*GIB, "free disk below40GiB")
    return {"engine_ncpu": ncpu, "numeric_caps_cpus": numeric_cpu,
            "numeric_caps_memory": numeric_memory, "new_cpus": new_cpu,
            "new_memory": new_memory, "reserve_cpus": 1, "reserve_memory": HOST_RESERVE,
            "mem_available": mem_available, "required_mem_available": required,
            "cpu_scope": "schedulable quota, not external future CPU guarantee",
            "external_declaration_caps_summed": False}

def expected_mounts(root):
    return {str(ROOT):(str(ROOT),False), MODEL:(MODEL,False),
            str(root):(str(root),True), str(TRAIN.parent):(str(TRAIN.parent),False),
            "/usr/local/Ascend/driver":("/usr/local/Ascend/driver",False)}

def inspect_contract(value, name, nonce, root, devices, *, preflight):
    require(value is not None and value["Image"] == IMAGE and
            value["Config"]["Labels"].get("damp.fixed-admission.owner") == nonce and
            value["Name"] == "/"+name, "not exact owned diagnostic container")
    require(re.fullmatch("[a-f0-9]{64}",value["Id"]) is not None, "invalid container ID")
    h = value["HostConfig"]
    memory = PREFLIGHT_MEMORY if preflight else ORDINARY_FLOOR
    cpus = PREFLIGHT_CPUS if preflight else FORMAL_CPUS
    require(h["Privileged"] is False and h["AutoRemove"] is False and
            h["Memory"] == h["MemorySwap"] == memory and h["NanoCpus"] == cpus*10**9 and
            h["ShmSize"] == (GIB if preflight else 8*GIB) and h["PidsLimit"] == 2048,
            "owned cgroup/quota/retain contract differs")
    require(set(h["CapDrop"] or []) == {"ALL"} and not h.get("CapAdd") and
            h["SecurityOpt"] in (["no-new-privileges"],["no-new-privileges:true"]) and
            h["NetworkMode"] == ("none" if preflight else "host") and
            h["IpcMode"] == "private" and not h.get("PidMode") and
            not h.get("DeviceRequests"), "owned security/network namespace differs")
    actual_devices = h.get("Devices") or []
    require(len(actual_devices) == len(devices) and
            {d["PathOnHost"]:d["PathInContainer"] for d in actual_devices} == devices and
            all(d["CgroupPermissions"] == "rwm" for d in actual_devices),
            "device map includes unapproved card or duplicate")
    mounts = value["Mounts"]
    expected = expected_mounts(root)
    require(len(mounts) == len(expected) and
            {m["Destination"] for m in mounts} == set(expected), "extra/missing mount")
    for m in mounts:
        source,rw = expected[m["Destination"]]
        require(m["Type"] == "bind" and m["Source"] == source and m["RW"] is rw,
                "mount source/mutability mismatch")
    return value

def bootstrap_command(root, command):
    require(file_sha(BOOTSTRAP_SOURCE) == BOOTSTRAP_SHA, "reviewed environment source drift")
    tree = ast.parse(BOOTSTRAP_SOURCE.read_text())
    assignments = [n for n in tree.body if isinstance(n,ast.Assign) and
                   any(isinstance(t,ast.Name) and t.id == "BOOTSTRAP" for t in n.targets)]
    require(len(assignments) == 1, "environment literal not unique")
    shell = ast.literal_eval(assignments[0].value)
    expected = ('set -e; source /usr/local/Ascend/ascend-toolkit/set_env.sh; '
                'source /usr/local/Ascend/cann-9.1.0/share/info/ascendnpu-ir/bin/set_env.sh; '
                'source /usr/local/Ascend/nnal/atb/set_env.sh --cxx_abi=1; '
                'export ASCEND_HOME_PATH=/usr/local/Ascend/cann-9.1.0; exec "$@"')
    require(shell == expected, "reviewed bootstrap literal changed")
    prefix = str(Path(root)/"overlay")+":"+str(PACKAGE_ROOT)
    shell = shell[:-len('exec "$@"')] + 'export PYTHONPATH='+shlex.quote(prefix)+':"${PYTHONPATH:-}"; exec "$@"'
    return ["/bin/bash","-c",shell,"damp-fixed-env"]+list(command)

def runtime_environment(root):
    """Whitelist only; never dump all env, tokens, or credentials."""
    keys = ("ASCEND_HOME_PATH","LD_LIBRARY_PATH","PYTHONPATH","ASCEND_OPP_PATH",
            "ASCEND_CUSTOM_OPP_PATH","PATH")
    values = {k:os.environ.get(k) for k in keys}
    require(sys.version_info[:2] == (3,12) and sys.executable == PYTHON, "actual Python3.12 path mismatch")
    require(values["ASCEND_HOME_PATH"] == "/usr/local/Ascend/cann-9.1.0" and
            bool(values["LD_LIBRARY_PATH"]), "CANN shell environment not initialized")
    paths = (values["PYTHONPATH"] or "").split(":")
    require(paths[:2] == [str(Path(root)/"overlay"),str(PACKAGE_ROOT)] and
            str(COLLECTOR) not in paths, "module-only overlay/CANN path contract differs")
    refs = []
    for name in ("/usr/local/Ascend/ascend-toolkit/set_env.sh",
                 "/usr/local/Ascend/cann-9.1.0/share/info/ascendnpu-ir/bin/set_env.sh",
                 "/usr/local/Ascend/nnal/atb/set_env.sh"):
        refs.append({"path":name,"realpath":str(Path(name).resolve()),"sha256":file_sha(name)})
    return {"schema":"damp-fixed-environment/v1","python":sys.executable,
            "python_version":list(sys.version_info[:3]),"env_whitelist":values,
            "bootstrap_source":{"path":str(BOOTSTRAP_SOURCE),"sha256":BOOTSTRAP_SHA},
            "actual_shell_sources":refs,"native_frame_verified":False}

def prior_terminal(payload):
    """Original MAIN operation bytes are SHA-checked by caller; nonzero is release, not PASS."""
    record_root = payload.get("structuredContent",payload)
    op = record_root["operation"]
    record = op["result"]["record"]
    require(record_root["schema"] == "agentweb.operation/v1" and
            record_root["operationId"] == ALLT_OPERATION and record_root["terminal"] is True and
            record_root["phase"] == record_root["status"] == "completed" and
            op["routeDecision"] == "peer_direct" and op["targetPeerId"] == MAIN_PEER and
            op["fallbackUsed"] is False and record["id"] == ALLT_OPERATION and
            record["state"] == "completed" and record["cancelled"] is False and
            record["timedOut"] is False and type(record["exitCode"]) is int and
            record["cwd"] == str(ROOT), "prior actual MAIN terminal/source/route not admissible")
    return {"operation_id":ALLT_OPERATION,"peer":MAIN_PEER,"exit_code":record["exitCode"],
            "scheduling_terminal_only":True,"numerical_pass_claimed":False}

def prior_owned_contract(proofs, read_inspect):
    require(len(proofs) == 4, "four original actual allT device proofs required")
    actual = []
    for card,proof in zip((4,5,6,7),proofs):
        previous = proof["container_inspect"]
        ident = PRIOR_IDS[card]
        name = "/qwen36_damp_allt_npu"+str(card)+"_20261006_independent_v1"
        expected_devices = {"/dev/davinci"+str(card):"/dev/davinci0",
                            "/dev/davinci_manager":"/dev/davinci_manager",
                            "/dev/devmm_svm":"/dev/devmm_svm","/dev/hisi_hdc":"/dev/hisi_hdc"}
        require(proof["container_id"] == previous["Id"] == ident and
                proof["logical_to_physical"] == {"0":card} and proof["physical_npu_ids"] == [card] and
                proof["privileged"] is False and previous["Name"] == name and
                previous["Image"] == IMAGE and
                previous["Config"]["Labels"].get("model-tuning-lab.owner") == ALLT_OWNER,
                "original allT device proof identity/source differs")
        current = read_inspect(ident)
        for value in (previous,current):
            require(value is not None and value["Id"] == ident and value["Name"] == name and
                    value["Image"] == IMAGE and value["HostConfig"]["Privileged"] is False and
                    value["Config"]["Labels"].get("model-tuning-lab.owner") == ALLT_OWNER,
                    "prior allT exact stopped identity differs")
            devices = value["HostConfig"].get("Devices") or []
            require(len(devices) == 4 and
                    {x["PathOnHost"]:x["PathInContainer"] for x in devices} == expected_devices and
                    all(x["CgroupPermissions"] == "rwm" for x in devices),
                    "original/current allT device map differs")
        require(current["State"]["Running"] is False and current["State"]["Pid"] == 0,
                "prior allT not exact stopped/PID0/retained")
        # No Config.Env or full historical proof copied into a report/Git.
        actual.append({"id":ident,"name":name,"image":IMAGE,"owner":ALLT_OWNER,
                       "physical":card,"state":current["State"],
                       "devices":current["HostConfig"]["Devices"]})
    return actual

def prior_proof_refs(paths, digests):
    require(len(paths) == len(digests) == 4, "four original proof Ref inputs required")
    refs = [];proofs = []
    for card,path,digest in zip((4,5,6,7),paths,digests):
        expected = RESULT_ROOT/("allT-dispatch-independent_v1/physical"+str(card)+"/device-proof.json")
        require(Path(path).resolve() == expected and digest == PRIOR_PROOF_SHAS[card] and
                file_sha(path) == digest, "original MAIN device proof bytes/path differ")
        refs.append({"path":str(expected),"sha256":digest})
        proofs.append(load(path))
    return refs,proofs

def stats_usage(row):
    cpu = float(row["CPUPerc"].removesuffix("%"))
    match = re.fullmatch(r"\s*([0-9.]+)\s*(B|kB|KB|KiB|MB|MiB|GB|GiB|TB|TiB)\s*",
                         row["MemUsage"].split("/",1)[0])
    require(match is not None and cpu >= 0, "unknown actual Docker stats format")
    scale = {"B":1,"kB":1000,"KB":1000,"KiB":1024,"MB":1000**2,"MiB":1024**2,
             "GB":1000**3,"GiB":1024**3,"TB":1000**4,"TiB":1024**4}[match[2]]
    return cpu,float(match[1])*scale

def external_workload(inspect, stats, top, *, protected_baseline=None):
    lines = top.splitlines()
    processes = [{"pid":int(parts[0]),"name":parts[1]}
                 for line in lines[1:]
                 for parts in [re.split(r"\s+",line.strip(),maxsplit=1)]
                 if len(parts)==2 and parts[0].isdigit() and parts[1]]
    require(bool(processes) and len({x["pid"] for x in processes})==len(processes),
            "external process identity unavailable/ambiguous")
    processes.sort(key=lambda x:(x["pid"],x["name"]))
    commands = [x["name"] for x in processes]
    pure_sleep = all(x == "sleep" for x in commands)
    cpu,memory = stats_usage(stats)
    protected = inspect["Id"] == PROTECTED_ID
    if protected:
        h=inspect["HostConfig"]
        devices=h.get("Devices") or []
        expected={**{"/dev/davinci"+str(i):"/dev/davinci"+str(i) for i in range(4)},
                  "/dev/davinci_manager":"/dev/davinci_manager",
                  "/dev/devmm_svm":"/dev/devmm_svm","/dev/hisi_hdc":"/dev/hisi_hdc"}
        require(inspect["Name"]==PROTECTED_NAME and inspect["Image"]==IMAGE and
                h["Privileged"] is False and not h.get("DeviceRequests") and
                len(devices)==7 and {x["PathOnHost"]:x["PathInContainer"] for x in devices}==expected and
                all(x["CgroupPermissions"]=="rwm" for x in devices) and
                set(commands)==PROTECTED_PROCESS_NAMES,
                "known protected0-3 identity/map/process differs; stop only own diagnostic")
        require(cpu<=50,"known protected0-3 actual CPU high; stop only own diagnostic")
        if protected_baseline is not None:
            require(protected_baseline["id"]==PROTECTED_ID and
                    protected_baseline["actual_processes"]==processes,
                    "known protected0-3 process identity changed; stop only own diagnostic")
            require(memory-protected_baseline["memory_usage_bytes"]<=PROTECTED_GROWTH_LIMIT,
                    "known protected0-3 resident growth exceeds4GiB; stop only own diagnostic")
    else:
        require((pure_sleep and cpu<=2 and memory<=64*1024**2) or
                (not pure_sleep and cpu<=50 and memory<=2*GIB),
                "unknown non-sleep external CPU/RAM high; do not stop it")
    return {"id":inspect["Id"],"name":inspect["Name"],"image":inspect["Image"],
            "actual_commands":commands,"actual_processes":processes,"pure_sleep":bool(pure_sleep),
            "cpu_percent":cpu,"memory_usage_bytes":memory,"known_protected0_3":protected,
            "resident_already_accounted_in_mem_available":protected,
            "protected_growth_limit_bytes":PROTECTED_GROWTH_LIMIT if protected else None,
            "declaration_caps_not_summed":True,"external_hard_cap_guaranteed":False}
