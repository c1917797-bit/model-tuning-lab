"""MAIN one-stage selected-prefill dispatcher; stdlib/default OFF, not service."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
REPO = BASE.parents[3]
PROJECT = REPO / "projects/damp-ascend"
ROOT = Path("/cache/cch/qwen36-damp-20261006")
GATE = PROJECT / "operator/prefill_pack_v1/selected_slot_v1/gate_v1"
BUILD = ROOT / "selected-prefill-build-v1"
SO = BUILD / "build/libqwen36_damp_selected_prefill_v1_ops.so"
SO_SHA = "28684cb4f502ead28fd9974a54f420d0ec027de19ccc6728ba3942209fc910d7"
RECEIPT_SHA = "50f161e606a7faa567b7588300f526f3294c7ecfbf69a88edaa8898b09d1825f"
RUNTIME_SHA = "7ea60a45ea46f28811c16455885eab46dbd78bce5586a8914f06a701dbcd4ed1"
SELECTED_MANIFEST_SHA = "5670a88c77fde9fd81abadcb7c88d2b3f6bb684928e24f445a3a1d3a67f0a8bf"
DECODE_BUILD = ROOT / "all-batch-wrapper-v3-build-v1"
DECODE = DECODE_BUILD / "cmake/libqwen36_gdn_damp_all_batch_v3_decode_ops.so"
DECODE_SHA = "a802d2584f6342acd198406a94c4a4cb3dd0e9cd6cc360569e58f3f117ac0ade"
DECODE_RECEIPT_SHA = "a9c8a6824f3f0948d4395eabcc731a0b4e0da6a7f94d6053d3159cf008e23d36"
REFERENCE = ROOT / "native-sr-reference-build-v1/libqwen36_damp_native_reference_ops.so"
REFERENCE_SHA = "853f655c45c11cb5de5a1b0810c9a8850c0b66aea4c9aa049e01ac89f1aeccc8"
ANCHOR = ROOT / "production-integer-compaction-general-v1/gate/report.json"
ANCHOR_SHA = "d4d71a45ae75c36a6ed9f5dc02c23272a1fef44e18f0a62226b4fcb3b35423d8"
NATIVE = Path("/vllm-workspace/vllm-ascend/vllm_ascend/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so")
NATIVE_SHA = "eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PYTHON = "/usr/local/python3.12.13/bin/python3"
OPP = Path("/usr/local/Ascend/cann-9.1.0/opp/version.info")
OPP_SHA = "841279757459d4eabc1c8cfea69d3e1dc0fc9db3eb0c18100294cd5c1301b9e6"
OWNER = "damp-selected-prefill-dispatch-v1"
DEADLINE = "2026-10-07T08:48:03Z"
TIMEOUT = 3600
MEMORY = 8 * 1024**3
OWN = ("controller.py", "child_shim.py", "test_dispatch.py", "READY.md")
REUSED = {
 "projects/damp-ascend/tools/prefill_float_dispatch_v1/dispatch.py":
 "094defb90bfc6d748d13069a48bd24297d01caaab1720ef5b8a3bc32ecf87c9e",
 "projects/damp-ascend/tools/allT_dispatch_controller_v1/controller.py":
 "c44412ffbfffa5b8e1630694343044d874c87ab72e3ad76875c2e69bc6c6e1ff",
 "projects/damp-ascend/tools/run_full_capture.py":
 "9ad5e359766578a24f06e127a990ab93d1e86555baa15d1abb7bb2b3ffc51122",
 "projects/damp-ascend/tools/run_collector_smoke.py":
 "da541917ebd8764a81624a215a157b6d4e18fbaaa53d9310be54a104d2fbbf92"}
ADMISSION = GATE / "admission_v1"
ADMISSION_SHA = "3c47ea050cb519b3e4ced87bd13f32b817a8cd74e9305502b429eab871b93db8"

def require(ok, message):
    if not ok: raise RuntimeError(message)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for piece in iter(lambda: f.read(1024*1024), b""): h.update(piece)
    return h.hexdigest()

def checked(path, digest):
    p = Path(path)
    require(p.is_absolute() and p.is_file() and not p.is_symlink(), "ordinary absolute file: " + str(p))
    require(type(digest) is str and re.fullmatch("[0-9a-f]{64}", digest), "full SHA256")
    require(sha(p) == digest, "source/artifact drift: " + str(p))
    return p

def read(path, limit=64*1024*1024):
    p = Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size <= limit, "bounded ordinary JSON")
    def pairs(rows):
        out = {}
        for k,v in rows:
            require(k not in out, "duplicate JSON key")
            out[k] = v
        return out
    def reject(value): raise ValueError("nonfinite JSON: " + value)
    return json.loads(p.read_text(), object_pairs_hook=pairs, parse_constant=reject)

def write(path, value):
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False); f.write("\n")

def ref(path):
    return {"path": str(path), "sha256": sha(path)}

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def deadline(seconds=0, now=None):
    now = now or datetime.now(timezone.utc)
    left = (datetime.fromisoformat(DEADLINE.replace("Z","+00:00"))-now).total_seconds()
    require(left > seconds, "unchanged DAMP cutoff/phase budget; no extension")
    return left

def packet(digest=None):
    path = BASE / "PACKET.json"
    if digest is not None: checked(path, digest)
    row = read(path)
    require(row.get("schema") == "damp-selected-prefill-dispatch-source/v1" and
            set(row.get("sources",{})) == set(OWN) and row.get("reused_sources") == REUSED and
            row.get("deadline_utc") == DEADLINE and row.get("default_enabled") is False,
            "exact MAIN-reviewed source packet")
    for name, pin in row["sources"].items(): checked(BASE / name, pin)
    return row

def closure():
    checked(GATE/"RUNTIME_MANIFEST.json", RUNTIME_SHA)
    runtime = read(GATE/"RUNTIME_MANIFEST.json")
    require(runtime.get("schema") == "damp-selected-prefill-gate-runtime/v1" and
            runtime.get("default_enabled") is False and len(runtime["sources"]) == 9 and
            len(runtime["dependencies"]) == 50 and len(runtime["actual_image_sources"]) == 23,
            "frozen gate9/dependencies50/actual-image23")
    files = dict(REUSED)
    for table in (runtime["sources"], runtime["dependencies"]):
        for path, pin in table.items():
            target = (REPO / path).resolve()
            require(target.is_relative_to(PROJECT.resolve()), "source escaped project")
            require(path not in files or files[path] == pin, "conflicting source identity")
            files[path] = pin
    checked(ADMISSION/"SOURCE_MANIFEST.json", ADMISSION_SHA)
    admission_manifest = read(ADMISSION/"SOURCE_MANIFEST.json")
    files.update(admission_manifest["sources"])
    for path, pin in files.items(): checked(REPO/path, pin)
    for row in runtime["actual_snapshot_manifests"]: checked(row["path"],row["sha256"])
    # The source-bound original stdlib contract; never load an operator here.
    c = load("_selected_dispatch_frozen_contract", GATE/"selected_contract.py")
    a = load("_selected_dispatch_component_admission", ADMISSION/"contract.py")
    source = read(checked(GATE.parent/"source_manifest.json", SELECTED_MANIFEST_SHA))
    require(source["compiled_sources"] == c.COMPILED, "actual selected11 compiled source identity")
    for path, pin in source["compiled_sources"].items(): checked(REPO/path, pin)
    b = c.validate_build(read(checked(BUILD/"build-receipt.json", RECEIPT_SHA)))
    dm = read(checked(PROJECT/"operator/all_batch_wrapper_v3/source_manifest.json", c.ALL_BATCH_MANIFEST_SHA))
    db = read(checked(DECODE_BUILD/"build-receipt.json", DECODE_RECEIPT_SHA))
    c.require_decode_admission(db, dm, DECODE_SHA)
    for build in (b, db):
        for row in build["commands"]: checked(row["log_path"], row["log_sha256"])
        ex = build["exported_kernel"]; checked(ex["audit_path"],ex["audit_sha256"])
    for path,pin in ((SO,SO_SHA),(DECODE,DECODE_SHA),(REFERENCE,REFERENCE_SHA)):
        checked(path,pin)
    c.validate_anchor(read(checked(ANCHOR,ANCHOR_SHA)))
    f = load("_selected_dispatch_float_safety", REPO/next(iter(REUSED)))
    h = load("_selected_dispatch_host_helper", REPO/"projects/damp-ascend/tools/allT_dispatch_controller_v1/controller.py")
    full = load("_selected_dispatch_parent_proof", REPO/"projects/damp-ascend/tools/run_full_capture.py")
    # Configure a NEW private module instance's owner, never alter old source.
    f.OWNER = OWNER
    require("torch" not in sys.modules and "torch_npu" not in sys.modules, "CPU preflight is stdlib only")
    return runtime, c, a, f, h, full, files

def expected_libraries(stage):
    require(stage in ("isolated","native_feedback"), "known stage")
    result = {str(SO): SO_SHA}
    if stage == "native_feedback":
        result.update({str(DECODE):DECODE_SHA,str(REFERENCE):REFERENCE_SHA,str(NATIVE):NATIVE_SHA})
    return result

def gate_args(entry, proof):
    args = [str(GATE/"run.py"), "--execute", "--stage", entry["stage"],
      "--physical-card",str(entry["physical_card"]), "--preflight",str(proof),
      "--build-receipt",str(BUILD/"build-receipt.json"), "--library",str(SO),
      "--out",entry["gate_out"], "--runtime-manifest",str(GATE/"RUNTIME_MANIFEST.json"),
      "--runtime-manifest-sha256",RUNTIME_SHA, "--batches","1","16"]
    if entry["stage"] == "native_feedback":
        args += ["--decode-build-receipt",str(DECODE_BUILD/"build-receipt.json"),
          "--decode-library",str(DECODE), "--decode-library-sha256",DECODE_SHA,
          "--native-anchor-report",str(ANCHOR), "--reference-library",str(REFERENCE),
          "--reference-library-sha256",REFERENCE_SHA]
    return args

def plan(run_id, stage, card, runtime, bootstrap):
    require(stage in ("isolated","native_feedback") and type(card) is int and card in (4,5,6,7), "one permitted stage/card")
    require(type(run_id) is str and re.fullmatch("[a-z][a-z0-9_-]{0,31}",run_id), "safe fresh run ID")
    root = ROOT / ("selected-prefill-dispatch-"+run_id+"-"+stage)
    audit, output = root/"launch", root/"stage-output"
    mounts = {str(REPO):False, str(BUILD):False, str(DECODE_BUILD):False,
      str(REFERENCE.parent):False, str(ANCHOR.parent):False, "/usr/local/Ascend/driver":False,
      str(audit):False, str(output):True}
    for row in runtime["actual_snapshot_manifests"]: mounts[str(Path(row["path"]).parent)] = False
    name = "qwen36_damp_selected_%s_npu%d_20261006_%s" % (stage,card,run_id)
    argv = ["docker","create","--name",name,"--label","model-tuning-lab.owner="+OWNER,
      "--label","model-tuning-lab.run="+run_id,"--label","model-tuning-lab.stage="+stage,
      "--network","none","--cpus","1","--memory","8g","--memory-swap","8g",
      "--cap-drop","ALL","--security-opt","no-new-privileges",
      "--device","/dev/davinci%d:/dev/davinci0"%card]
    for node in ("davinci_manager","devmm_svm","hisi_hdc"): argv += ["--device","/dev/"+node]
    for p, rw in mounts.items():
        argv += ["--mount","type=bind,source=%s,target=%s%s"%(p,p,"" if rw else ",readonly")]
    argv += ["-e","ASCEND_RT_VISIBLE_DEVICES=0","-e","PYTHONDONTWRITEBYTECODE=1",
      "-e","TORCH_DEVICE_BACKEND_AUTOLOAD=0","-e","OMP_NUM_THREADS=1","-e","TOKENIZERS_PARALLELISM=false",
      "-w",str(REPO),"--entrypoint","/bin/bash",IMAGE,"-c",bootstrap,"selected-prefill-bootstrap","/bin/sleep","infinity"]
    return {"schema":"damp-selected-prefill-plan/v1","launchable":False,"run_id":run_id,"stage":stage,
      "physical_card":card,"container_name":name,"root":str(root),"audit":str(audit),
      "stage_output":str(output),"gate_out":str(output/stage),"observation":str(output/"same-process-observation.json"),
      "mounts":mounts,"docker_create_argv":argv,
      "create_argv_sha256":hashlib.sha256(json.dumps(argv,separators=(",",":")).encode()).hexdigest(),
      "batches":[1,16],"steps":160,"deadline":DEADLINE,"serving_ready":False,"performance_measurement_admitted":False}

def inspect_owned(actual, entry, cid):
    require(type(cid) is str and re.fullmatch("[0-9a-f]{64}",cid) and actual.get("Id") == cid and
            actual.get("Name") == "/"+entry["container_name"] and actual.get("Image") == IMAGE,
            "exact owned ID/name/image; no guessed cleanup")
    host, config = actual["HostConfig"], actual["Config"]
    labels = config.get("Labels") or {}
    require(labels.get("model-tuning-lab.owner") == OWNER and labels.get("model-tuning-lab.run") == entry["run_id"] and
            labels.get("model-tuning-lab.stage") == entry["stage"], "actual owner/run/stage")
    require(host.get("Privileged") is False and host.get("NetworkMode") == "none" and
            host.get("IpcMode") != "host" and not host.get("DeviceRequests") and
            host.get("Memory") == MEMORY and host.get("MemorySwap") == MEMORY and
            host.get("NanoCpus") == 10**9 and set(host.get("CapDrop",[])) == {"ALL"} and
            any(x in ("no-new-privileges","no-new-privileges=true") for x in host.get("SecurityOpt",[])),
            "actual memory/CPU/no-swap/security bounds")
    wanted = {"/dev/davinci%d"%entry["physical_card"]:"/dev/davinci0",
      **{"/dev/"+n:"/dev/"+n for n in ("davinci_manager","devmm_svm","hisi_hdc")}}
    require(len(host.get("Devices",[])) == 4 and
            {r["PathOnHost"]:r["PathInContainer"] for r in host["Devices"]} == wanted, "single physical4..7 mapping only")
    mounts = actual["Mounts"]
    require(len(mounts) == len(entry["mounts"]) and
            {r["Destination"] for r in mounts} == set(entry["mounts"]), "exact mount set only")
    for r in mounts:
        require(r["Type"] == "bind" and r["RW"] is entry["mounts"][r["Destination"]] and
                Path(r["Source"]).resolve() == Path(r["Destination"]).resolve(), "actual RO evidence/only stage-output RW")
    require([r["Destination"] for r in mounts if r["RW"]] == [entry["stage_output"]], "child cannot write MAIN launch/proof")
    env = dict(x.split("=",1) for x in config.get("Env",[]) if "=" in x)
    argv = entry["docker_create_argv"]
    for i,x in enumerate(argv):
        if x == "-e":
            k,v = argv[i+1].split("=",1); require(env.get(k) == v, "actual env drift")
    tail = argv[argv.index("--entrypoint")+2:]
    require(config.get("Entrypoint") == ["/bin/bash"] and config.get("Cmd") == tail[1:] and
            config.get("WorkingDir") == str(REPO), "actual bootstrap/workdir")
    return actual

def exec_argv(entry, cid, bootstrap, *program):
    args = ["docker","exec"]
    if entry["stage"] == "native_feedback": args += ["-e","DAMP_ENABLE_NATIVE_REFERENCE=1"]
    return args+[cid,"/bin/bash","-c",bootstrap,"selected-prefill-exec",PYTHON,"-B",*program]

def shim_argv(entry, cid, bootstrap, proof, packet_sha, preflight=False):
    args = [str(BASE/"child_shim.py"),"--packet-sha256",packet_sha,"--observation",entry["observation"]]
    if preflight: args += ["--preflight-only"]
    return exec_argv(entry,cid,bootstrap,*args,"--",*gate_args(entry,proof))

def canary(cmd, h, f, entry, cid, protected, audit):
    before = f.resources(cmd,h,entry["physical_card"],protected,cid)
    write(audit/"canary-before.json",before)
    inspect_owned(h.inspect(cmd,cid,"canary-inspect"),entry,cid)
    argv = exec_argv(entry,cid,f.BOOTSTRAP,"-c",f.CANARY_CODE,str(entry["physical_card"]),
                     entry["create_argv_sha256"],f.CANARY_SHA)
    raw,_ = cmd.run("canary",argv,timeout=90)
    rows = []
    for line in raw.splitlines():
        try: row=json.loads(line)
        except ValueError: continue
        if isinstance(row,dict) and row.get("schema") == "damp-prefill-float-canary/v1": rows.append(row)
    require(len(rows) == 1, "one actual reused mul canary result")
    row = rows[0]
    require(row.get("status") == "actual_canary_pass" and row.get("npu_executed") is True and
      row.get("runtime_soc") == "Ascend910B4" and row.get("expected_physical_card") == entry["physical_card"] and
      row.get("logical_device") == 0 and row.get("result") == [1.,4.,9.] and
      row.get("create_argv_sha256") == entry["create_argv_sha256"] and row.get("canary_program_sha256") == f.CANARY_SHA and
      type(row.get("completed_at_unix_ns")) is int and 0 <= time.time_ns()-row["completed_at_unix_ns"] <= 300*10**9,
      "fresh actual canary/runtime mapping authority")
    write(audit/"canary.json",row)
    after = f.resources(cmd,h,entry["physical_card"],protected,cid)
    write(audit/"canary-after.json",after)
    actual=inspect_owned(h.inspect(cmd,cid,"postcanary-inspect"),entry,cid)
    return proof(audit/"device-proof.json",entry,cid,actual,after,ref(audit/"canary.json"))

def proof(path, entry, cid, actual, resource, canary_ref=None):
    row={"physical_npu_ids":[entry["physical_card"]],"logical_to_physical":{"0":entry["physical_card"]},
      "privileged":False,"exclusive_resource_check_passed":True,"observed_at_unix_ns":time.time_ns(),
      "container_id":cid,"container_inspect":actual,"fresh_resource_observation":resource}
    if canary_ref is not None: row["canary"] = canary_ref
    write(path,row);return path

class CancelledRun(RuntimeError): pass

def phase(argv, audit, monitor, timeout=TIMEOUT):
    """Actual local exec-client Popen; signal only this owned client, not NPU PIDs."""
    stdout_path, stderr_path = audit/"child.stdout", audit/"child.stderr"
    started, start = time.time_ns(), time.monotonic()
    proc, cause, error, secondary, signal_number = None, "not_started", None, [], None
    old_handlers={}
    def cancel(signum, frame):
        nonlocal signal_number
        signal_number=signum;raise CancelledRun("actual controller received signal "+str(signum))
    try:
        for s in (signal.SIGINT,signal.SIGTERM):
            old_handlers[s]=signal.signal(s,cancel)
        with stdout_path.open("xb") as out, stderr_path.open("xb") as err:
            proc=subprocess.Popen(argv,stdout=out,stderr=err,cwd=REPO,stdin=subprocess.DEVNULL)
            cause="running";next_monitor=0
            while proc.poll() is None:
                elapsed=time.monotonic()-start
                if elapsed >= timeout:
                    cause="timeout";raise TimeoutError("actual one-shot child phase timeout")
                deadline()
                if elapsed >= next_monitor:
                    monitor();next_monitor=elapsed+10
                time.sleep(.25)
            cause="completed"
    except BaseException as failure:
        error=repr(failure)
        if isinstance(failure,CancelledRun) or isinstance(failure,KeyboardInterrupt): cause="cancelled"
        elif cause != "timeout": cause="failed"
    finally:
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill();proc.wait(timeout=5) # local controller-owned docker-exec client only
            except BaseException as failure: secondary.append(repr(failure))
        for s,handler in old_handlers.items(): signal.signal(s,handler)
    completed=time.time_ns()
    def raw(path):
        try:return path.read_text(errors="replace")
        except BaseException as failure:
            secondary.append(repr(failure));return None
    result={"command":argv[0],"args":argv[1:],"cwd":str(REPO),"state":cause,
      "returncode":None if proc is None else proc.poll(),"error":error,
      "cancelled":cause=="cancelled","timed_out":cause=="timeout","signal":signal_number,
      "stdout":raw(stdout_path),"stderr":raw(stderr_path),"started_ns":started,"completed_ns":completed,
      "duration_ms":(completed-started)/1e6,"secondary_errors":secondary}
    write(audit/"EXECUTION.json",result)
    return result

def child_receipt(entry, cid, execution, observation, report, proof_path, packet_row):
    # Values are raw real subprocess/inspect/same-process observations, not defaults
    # filled to meet a success schema. Failed observations may remain nullable.
    artifact_refs=[];copy_errors=[]
    def nullable_ref(path,label):
        try:return ref(path)
        except BaseException as error:
            copy_errors.append({"copy":label,"error":repr(error)});return None
    if isinstance(report,dict):
        for row in report.get("artifacts",[]):
            try:
                p=Path(row["path"])
                require(p.parent.resolve() == Path(entry["gate_out"]).resolve(), "artifact escaped this stage")
                artifact_refs.append(ref(p))
            except BaseException as error:copy_errors.append({"copy":"artifact","error":repr(error)})
    report_ref=nullable_ref(Path(entry["gate_out"])/"report.json","report") if isinstance(report,dict) else None
    observation_ref=nullable_ref(entry["observation"],"observation") if Path(entry["observation"]).is_file() else None
    return {"schema":"damp-selected-prefill-child/v1","stage":entry["stage"],
      "report":report_ref,
      "execution":execution,"container":{"id":cid,"image_id":IMAGE,
        "physical_npu_ids":[entry["physical_card"]],"logical_to_physical":{"0":entry["physical_card"]},
        "privileged":False},"owner_proof":ref(proof_path),
      "controller_sources":{str(BASE/name):pin for name,pin in packet_row["sources"].items()},
      "runtime_manifest":{"path":str(GATE/"RUNTIME_MANIFEST.json"),"sha256":RUNTIME_SHA},
      "runtime":observation.get("runtime"),"runtime_image_sources":observation.get("runtime_image_sources"),
      "loaded_libraries":observation.get("loaded_libraries"),"artifacts":artifact_refs,
      "same_process_observation":observation_ref,"receipt_copy_errors":copy_errors,
      "serving_ready":False,"performance_measurement_admitted":False}

def validate_stage(report, observation, execution, entry, runtime, c, a, started, completed):
    require(execution["state"] == "completed" and type(execution["returncode"]) is int and
      execution["returncode"] == 0 and execution["error"] is None and
      execution["cancelled"] is False and execution["timed_out"] is False and not execution["secondary_errors"],
      "actual child complete0, no timeout/cancellation/secondary error")
    require(observation.get("gate_returncode") == 0 and observation.get("primary_error") is None and
      observation.get("secondary_errors") == [] and observation.get("stage") == entry["stage"] and
      observation.get("pid") and observation.get("runtime") == {"soc":"Ascend910B4",
      "torch":"2.10.0+cpu","torch_npu":"2.10.0.post4","opp_version_info_sha256":OPP_SHA},
      "same-process actual runtime without error")
    require(observation.get("loaded_libraries") == expected_libraries(entry["stage"]) and
      observation.get("runtime_image_sources") == (runtime["actual_image_sources"] if entry["stage"]=="native_feedback" else {}),
      "actual mapped binaries/23 source bytes, not snapshot as loaded proof")
    require(report.get("schema") == "damp-selected-prefill-npu-gate/v1" and
      report.get("status") == ("isolated_selected_packing_pass" if entry["stage"]=="isolated" else "native_chunk_selected_pack_feedback_pass") and
      report.get("stage") == entry["stage"] and report.get("npu_executed") is True and
      report.get("schemas") == a.schemas() and report.get("steps") == 160 and report.get("limits") == c.LIMITS and
      report.get("general_sr") is True and report.get("actual_runtime_soc") == "Ascend910B4" and
      all(report.get(k) is False for k in ("serving_ready","performance_measurement_admitted","graph_supported","float_candidate_enabled")) and
      not any(k in report for k in ("error","traceback","failure_save_error")) and
      type(report.get("completed_ns")) is int and started <= report["completed_ns"] <= completed,
      "actual frozen numerical report scope/full completion")
    binding=report["bindings"]
    require(binding["sources"] == runtime["sources"] and binding["dependencies"] == runtime["dependencies"] and
      binding["compiled_sources"] == c.COMPILED and binding["library"] == {"path":str(SO),"sha256":SO_SHA} and
      binding["build_receipt"] == {"path":str(BUILD/"build-receipt.json"),"sha256":RECEIPT_SHA} and
      binding["runtime_manifest"] == {"path":str(GATE/"RUNTIME_MANIFEST.json"),"sha256":RUNTIME_SHA} and
      binding["image_id"] == IMAGE and binding["opp_version_info_sha256"] == OPP_SHA,
      "complete actual binding; final pair authority remains MAIN admission")
    expected = a.isolated(report,c) if entry["stage"]=="isolated" else a.native_feedback(report,c)
    artifacts=report.get("artifacts",[])
    require(len(artifacts) == len(expected) and {Path(r["path"]).name for r in artifacts} == expected and
      all(r.get("copy_errors") == [] for r in artifacts), "complete artifact/no-poison evidence")
    for row in artifacts:
        p=Path(row["path"]);require(p.parent.resolve() == Path(entry["gate_out"]).resolve() and p.is_file() and not p.is_symlink(),
                                   "ordinary retained stage artifact")

def failure_record(error, execution, report, observation, secondary):
    """Preserve the observed primary error before nullable-copy/cleanup errors."""
    original=None
    if isinstance(execution,dict) and isinstance(execution.get("error"),str):
        original=execution["error"]
    if original is None and isinstance(observation,dict):
        primary=observation.get("primary_error")
        if isinstance(primary,dict) and isinstance(primary.get("error"),str):
            original=primary["error"]
    if original is None and isinstance(report,dict) and isinstance(report.get("error"),str):
        original=report["error"]
    return {"original_error":original if original is not None else repr(error),
      "controller_error":repr(error),"secondary_errors":secondary,"execution":execution,
      "partial_report":report,"nullable_observation":observation,"automatic_retry":False,
      "whole_selected_call_must_retire":True,
      "scope":"component/resource/implementation failure; not paper-wide no-go"}

def execute(args, prepared, packet_row):
    require(os.environ.get("DAMP_SELECTED_PREFILL_DISPATCH_EXECUTE") == "1" and Path.cwd().resolve() == REPO,
            "MAIN explicit opt-in/canonical host")
    runtime,c,a,f,h,full,files = prepared
    deadline(TIMEOUT+180)
    entry=plan(args.run_id,args.stage,args.physical_card,runtime,f.BOOTSTRAP)
    root,audit,output = (Path(entry[k]) for k in ("root","audit","stage_output"))
    require(not root.exists() and not root.is_symlink(), "new non-overwriting root")
    checked(args.parent_operation_receipt,args.parent_operation_sha256)
    f.terminal(read(args.parent_operation_receipt),h) # completion may nonzero, not calibration success
    root.mkdir(exist_ok=False);audit.mkdir();output.mkdir()
    cmd=h.Commands(audit);cid=None;protected=None;failed=None;secondary=[];execution=None
    proof_path=None;observation={};report=None;child=None;cleanup=[]
    try:
        write(audit/"SOURCE.json",{"packet_sha256":args.packet_sha256,"packet":packet_row,"files":files,
                                "runtime_manifest":ref(GATE/"RUNTIME_MANIFEST.json"),"plan":entry})
        write(audit/"PARENT_TERMINAL.json",f.parent_stopped(cmd,h,full,args))
        image=cmd.json("immutable-image",["docker","image","inspect",IMAGE])
        require(len(image)==1 and image[0]["Id"]==IMAGE and image[0]["Architecture"]=="arm64", "actual immutable image")
        before=f.resources(cmd,h,entry["physical_card"]);protected=before["protected"]
        write(audit/"PRELAUNCH.json",before)
        h.absent_names(cmd,[entry]);closure();packet(args.packet_sha256);deadline(TIMEOUT+120)
        raw,_=cmd.run("create",entry["docker_create_argv"])
        created=raw.strip()
        require(re.fullmatch("[0-9a-f]{64}",created), "unknown create outcome; never guess/retry")
        cid=created
        inspect_owned(h.inspect(cmd,cid,"created-inspect"),entry,cid)
        cmd.run("start",["docker","start",cid])
        actual=inspect_owned(h.inspect(cmd,cid,"started-inspect"),entry,cid)
        h.cgroup_record(actual,cid,MEMORY,1)
        resource=f.resources(cmd,h,entry["physical_card"],protected,cid)
        preflight_proof=proof(audit/"image-preflight-proof.json",entry,cid,actual,resource)
        # Frozen gate actual source/ABI/OPP/image23 admission BEFORE Torch.
        cmd.run("actual-image-source",shim_argv(entry,cid,f.BOOTSTRAP,preflight_proof,args.packet_sha256,True),timeout=120)
        proof_path=canary(cmd,h,f,entry,cid,protected,audit)
        closure();packet(args.packet_sha256);deadline(TIMEOUT)
        def monitor():
            state=inspect_owned(h.inspect(cmd,cid,"phase-inspect"),entry,cid)
            require(state["State"].get("Running") is True and not state["State"].get("OOMKilled"), "owned cgroup stopped/OOM")
            group=h.cgroup_record(state,cid,MEMORY,1)
            require(group["memory_current_bytes"] < MEMORY, "owned cgroup at cap")
            snapshot=f.resources(cmd,h,entry["physical_card"],protected,cid,idle=False)
            write(audit/("runtime-%d.json"%time.time_ns()),{"cgroup":group,"resources":snapshot})
        argv=shim_argv(entry,cid,f.BOOTSTRAP,proof_path,args.packet_sha256)
        write(audit/"CHILD_COMMAND.json",{"command":argv[0],"args":argv[1:],"cwd":str(REPO)})
        execution=phase(argv,audit,monitor)
        # Copies independently nullable; never replace the raw dispatch error.
        for label,p in (("observation",Path(entry["observation"])),("report",Path(entry["gate_out"])/"report.json")):
            try:
                value=read(p)
                if label=="observation":observation=value
                else:report=value
            except BaseException as error: secondary.append({"copy":label,"error":repr(error)})
        child=child_receipt(entry,cid,execution,observation,report,proof_path,packet_row)
        write(audit/"child-receipt.json",child) # MAIN host-owned RO audit, never writable by child
        require(not secondary and not child["receipt_copy_errors"],"nullable observation/report/artifact copy failed")
        validate_stage(report,observation,execution,entry,runtime,c,a,execution["started_ns"],execution["completed_ns"])
        closure();packet(args.packet_sha256)
    except BaseException as error:
        retained=failure_record(error,execution,report,observation,secondary)
        failed=retained["original_error"]
        write(audit/"FAILURE.json",retained)
    finally:
        if cid is not None:
            try:
                inspect_owned(h.inspect(cmd,cid,"prestop-inspect"),entry,cid)
                cmd.run("stop-owned",["docker","stop","--time","30",cid],timeout=90)
                stopped=inspect_owned(h.inspect(cmd,cid,"stopped-inspect"),entry,cid)
                require(stopped["State"].get("Running") is False and stopped["State"].get("Status")=="exited", "owned stop actual result")
                cleanup.append({"container_id":cid,"stopped_inspect":stopped,"deleted":False})
                after=f.resources(cmd,h,entry["physical_card"],protected,cid)
                write(audit/"POST_RELEASE.json",after)
            except BaseException as error:
                cleanup.append({"container_id":cid,"cleanup_error":repr(error),"deleted":False})
                if failed is None: failed="owned stop/release proof failed; MAIN attention required"
        write(audit/"STOP_RETAIN.json",cleanup)
        if any("cleanup_error" in r for r in cleanup):
            write(audit/"CLEANUP_FAILURE.json",{"records":cleanup,"original_error":failed,"no_external_signals":True})
    require(failed is None, "failed one-shot selected component; evidence retained: "+str(audit))
    require(child is not None and child["report"] is not None, "actual complete child/report required")
    write(audit/"RESULT.json",{"status":"actual_selected_stage_complete","stage":entry["stage"],
      "report":child["report"],"child":ref(audit/"child-receipt.json"),"container_id":cid,
      "owned_container_stopped_retained":True,"serving_ready":False,"performance_measurement_admitted":False,
      "outer_operation_authority":"pending MAIN original operation_get bytes after this command exits"})
    print("MAIN_SELECTED_PREFILL_CHILD "+json.dumps({"child":ref(audit/"child-receipt.json"),
      "report":child["report"],"stage":entry["stage"]},sort_keys=True),flush=True)
    return 0

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true")
    p.add_argument("--stage",choices=("isolated","native_feedback"),default="isolated")
    p.add_argument("--run-id",default="v1")
    p.add_argument("--physical-card",type=int,choices=(4,5,6,7),default=4)
    p.add_argument("--packet-sha256")
    p.add_argument("--parent-operation-receipt",type=Path)
    p.add_argument("--parent-operation-sha256")
    args=p.parse_args(argv)
    if args.execute:
        require(os.environ.get("DAMP_SELECTED_PREFILL_DISPATCH_EXECUTE")=="1", "default OFF; MAIN only")
        require(all(getattr(args,n) is not None for n in
          ("packet_sha256","parent_operation_receipt","parent_operation_sha256")), "explicit actual MAIN authorities")
    packet_row=packet(args.packet_sha256);prepared=closure()
    if not args.execute:
        entry=plan(args.run_id,args.stage,args.physical_card,prepared[0],prepared[3].BOOTSTRAP)
        print(json.dumps({"status":"dry-plan-not-executed","plan":entry,
          "pending":["genuine MA0455 terminal/stopped owned parent","fresh single-card mapping/resources/canary",
                     "MAIN-reviewed packet SHA/actual outer terminal after stage"],
          "npu_executed":False,"serving_ready":False,"performance_measurement_admitted":False},allow_nan=False))
        return 0
    return execute(args,prepared,packet_row)

if __name__=="__main__":raise SystemExit(main())
