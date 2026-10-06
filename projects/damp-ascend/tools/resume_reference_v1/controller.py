"""Explicit on-only reference recovery. Default mode is read-only --plan.

This controller never launches off, edits frozen collector source, frees HugeTLB,
or stops any external container. A full pair is still reference-only evidence.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

# Read-only preparation must not produce import caches in frozen source.
sys.dont_write_bytecode = True

REPO = Path("/opt/host/vnf/austinov/model-tuning-lab")
ROOT = Path("/cache/cch/qwen36-damp-20261006")
OLD_LAUNCH = ROOT / "full-capture-v1-launch"
OFF = ROOT / "full-capture-v1-off"
ORIGINAL = REPO / "projects/damp-ascend/tools/run_full_capture.py"
ORIGINAL_SHA = "9ad5e359766578a24f06e127a990ab93d1e86555baa15d1abb7bb2b3ffc51122"
OLD_ID = "4505fd9eb29e4079768a2b0ea49f2bacd198f77023672bbc297c3c2aa86dd8ff"
DEADLINE = "2026-10-07T08:48:03Z"
GiB = 1024 ** 3
OFF_FILES = ("CLIENT_COMPLETE.json", "RUN.json", "client.jsonl", "request-identities.jsonl")
EXCLUSIONS = ["compressed recurrence", "graph", "serving integration",
              "end-to-end speedup", "task accuracy", "full weight-byte identity"]

def require(value, message):
    if not value:
        raise RuntimeError(message)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def read_json(path):
    require(Path(path).is_file() and not Path(path).is_symlink(), "missing/symlink JSON: " + str(path))
    return json.loads(Path(path).read_text())

def frozen():
    require(ORIGINAL.resolve() == ORIGINAL and sha(ORIGINAL) == ORIGINAL_SHA,
            "original full controller source drift")
    spec = importlib.util.spec_from_file_location("damp_original_full_controller", ORIGINAL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def receipts(directory):
    directory = Path(directory)
    result = []
    for p in sorted(directory.rglob("*")):
        require(not p.is_symlink(), "original evidence contains symlink")
        if p.is_file():
            require(p.resolve().is_relative_to(directory.resolve()), "evidence escaped original root")
            result.append(dict(path=str(p), bytes=p.stat().st_size, sha256=sha(p)))
    return result

def assert_original_unchanged(before):
    for root, expected in before.items():
        require(receipts(root) == expected, "original off/failure evidence changed: " + root)

def imports():
    collector = str(REPO / "projects/damp-ascend/collector")
    calibration = str(REPO / "projects/damp-ascend/calibration")
    sys.path[:0] = [collector, calibration]
    from damp_capture.contract import load_manifest, token_digest
    from damp_capture.identity import live_identity
    return load_manifest, token_digest, live_identity

def off_lock(original):
    source = read_json(OLD_LAUNCH / "source.json")
    require(source["image"] == original.IMAGE and
        source["manifest_file_sha256"] == original.MANIFEST_SHA and
        source["manifest_semantic_sha256"] == original.MANIFEST_SEMANTIC_SHA,
        "original launcher image/manifest identity changed")
    actual = {str(p.relative_to(REPO)): sha(p) for p in sorted(
        (REPO / "projects/damp-ascend/collector").rglob("*")) if p.is_file()}
    require(not any("__pycache__" in p for p in actual), "generated collector file")
    actual[str(original.HELPER.relative_to(REPO))] = sha(original.HELPER)
    actual[str(ORIGINAL.relative_to(REPO))] = sha(ORIGINAL)
    require(len(actual) == 28 and actual == source["files"],
            "frozen collector26/helper/full-launcher28 identity changed")
    require(sha(original.MANIFEST) == original.MANIFEST_SHA, "manifest file bytes changed")
    load_manifest, token_digest, live_identity = imports()
    manifest = load_manifest(original.MANIFEST)
    original.shape(manifest)
    require(digest(manifest) == original.MANIFEST_SEMANTIC_SHA, "manifest semantic drift")
    # Explicitly admit only the observed pre-on RAM refusal, not arbitrary failures.
    failure = read_json(OLD_LAUNCH / "FAILURE.json")
    require(failure == dict(error_type="RuntimeError",
        detail="ordinary MemAvailable below64GiB; never reclaim HugeTLB",
        automatic_retry=False, partial_reference_not_accepted=True),
        "original failure is not the independently identified pre-on resource gate")
    require(not (ROOT / "full-capture-v1-on").exists(), "original on exists; independent recovery review required")
    done = read_json(OLD_LAUNCH / "stopped.json")
    require(done == dict(id=OLD_ID, status="exited", retained=True),
            "original owned container stop receipt differs")
    off_receipt = read_json(OLD_LAUNCH / "off.receipt.json")
    require(off_receipt["exit_code"] == 0 and
        off_receipt["argv"][-12:] == [
            "-m", "damp_capture.run", "--manifest", str(original.MANIFEST),
            "--output-dir", str(OFF), "--capture", "off",
            "--batch-size", "4", "--memory-utilization", "0.80"],
        "original off exact successful command not proven")
    require(sorted(p.name for p in OFF.iterdir()) == sorted(OFF_FILES),
            "off evidence file set changed/extra artifacts")
    run = read_json(OFF / "RUN.json")
    require(run["schema"] == "damp-live-run/v1" and run["mode"] == "full" and
        run["evidence_scope"] == "FP32-reference-calibration-only" and
        run["capture_enabled"] is False and run["generation"] == manifest["generation"] and
        run["batch_size"] == 4 and run["manifest_sha256"] == digest(manifest) and
        run["enforce_eager"] is True and run["prefix_cache"] is False and
        run["chunked_prefill"] is False and run["physical_devices"] == [4,5,6,7] and
        run["logical_devices"] == [0,1,2,3], "off protocol/config identity differs")
    complete = read_json(OFF / "CLIENT_COMPLETE.json")
    require(complete == dict(manifest_sha256=digest(manifest), mode="full", rows=36),
            "off full completion not proven")
    rows = [json.loads(line) for line in (OFF / "client.jsonl").read_text().splitlines() if line.strip()]
    clients = {}
    expected = {r["id"]: r for r in manifest["rows"]}
    for row in rows:
        rid = row["logical_id"]
        require(rid in expected and rid not in clients and
            row["prompt_token_sha256"] == expected[rid]["input_ids_sha256"] and
            row["output_tokens"] == len(row["output_token_ids"]) == 4096 and
            row["output_token_sha256"] == token_digest(row["output_token_ids"]),
            "off missing/duplicate/prompt/output/hash mismatch")
        clients[rid] = row
    require(set(clients) == set(expected) and len(rows) == 36, "off36 incomplete")
    identity = live_identity(OFF, manifest, clients)
    before = {str(p): receipts(p) for p in (OLD_LAUNCH, OFF)}
    return dict(schema="damp.off-reference-reuse/v1", off_root=str(OFF),
        source=source, native_request_identity=identity, original_evidence=before,
        reuse_scope="complete native-off36; not a full calibration pair",
        not_proven=EXCLUSIONS), manifest

def source_bound_smoke(report_path=None, report_sha=None):
    """Read-only reproduce accepted NEW legacy audit; never manufacture smoke."""
    audit_path = ROOT/"legacy-v4-identity-audit-v1/AUDIT.json"
    audit_sha = "f51cd439a576f44159f2d849b812747838dddeaf445429751966b70d70c8000e"
    sidecar = audit_path.with_name("VALIDATION.json")
    sidecar_sha = "1f78093b451b2ad943fb3d7c7166fcdb12ee5a5caf320377d6891daadd43a37e"
    require(Path(report_path or sidecar).resolve() == sidecar and
        (report_sha or sidecar_sha) == sidecar_sha,
        "only accepted NEW source-bound legacy smoke sidecar admitted")
    require(sha(audit_path) == audit_sha and sha(sidecar) == sidecar_sha,
            "accepted source-bound smoke audit/sidecar bytes changed")
    audit = read_json(audit_path); report = read_json(sidecar)
    require(audit["schema"] == "damp.legacy-v4-identity-audit/v1" and
        audit["status"] == "identity_and_capture_audit_pass" and
        audit["no_original_evidence_modified"] is True and audit["validation"] == report,
        "NEW smoke sidecar not exactly the accepted audit's validation")
    require(report["status"] == "pass" and report["mode"] == "smoke" and
        report["ranks"] == 4 and report["layers"] == 48 and report["requests"] == 2 and
        report["request_identity"]["mode"] == "explicit-readonly-legacy-v4-source-bound-recovery" and
        report["request_identity"]["original_failure_preserved"] is True,
        "legacy recovered hook gate cannot be replaced by failed/fresh/compressed report")
    require(digest(audit["raw_receipts"]) == audit["raw_receipts_sha256"],
            "accepted raw-receipt list digest changed")
    source = report["request_identity"]["source"]; source_path = Path(source["path"])
    require(source_path == ROOT/"legacy-v4-identity-preflight-v1/legacy-source.json" and
        sha(source_path) == source["sha256"], "legacy source receipt differs")
    legacy = read_json(source_path); on = ROOT/"smoke-hook-v4-on"; off = ROOT/"smoke-hook-v4-off"
    require(legacy["on_root"] == str(on) and legacy["off_root"] == str(off),
            "legacy recovered roots differ")
    before = receipts(on) + receipts(off)
    require(before == audit["raw_receipts"], "legacy raw files changed/extra/missing")
    old_failure = ROOT/"smoke-hook-v4-launch/FAILURE.json"
    old_receipt = ROOT/"smoke-hook-v4-launch/validate.receipt.json"
    old_log = ROOT/"smoke-hook-v4-launch/validate.log"
    require(read_json(old_failure) == dict(error_type="RuntimeError",
        error="validate failed; preserve log and do not rerun") and
        read_json(old_receipt)["exit_code"] == 1 and
        "ValueError: worker/client identity mismatch" in old_log.read_text(),
        "original failed validator evidence must remain failed/preserved")
    preserved_failure = [dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
                         for p in (old_failure,old_receipt,old_log)]
    imports()
    from damp_capture.contract import load_manifest
    from damp_capture.validate import validate
    manifest_path = Path(audit["manifest"]["path"])
    require(manifest_path == ROOT/"calibration-inputs/smoke-hook-v4.json" and
        sha(manifest_path) == audit["manifest"]["sha256"], "smoke manifest bytes changed")
    manifest = load_manifest(manifest_path)
    require(digest(manifest) == audit["manifest"]["semantic_sha256"], "smoke semantic identity changed")
    actual = validate(on,manifest,off,legacy_source_path=source_path)
    require(actual == report, "readonly source-bound smoke replay does not reproduce")
    require(receipts(on)+receipts(off) == before, "smoke oracle bytes mutated during audit")
    for item in preserved_failure:
        require(sha(item["path"]) == item["sha256"], "original failure evidence changed")
    return report, dict(schema="damp.legacy-source-bound-smoke-reuse/v1",
        audit=dict(path=str(audit_path),sha256=audit_sha),
        sidecar=dict(path=str(sidecar),sha256=sidecar_sha),
        read_only_validation_reproduced=True,original_failed_validator_preserved=preserved_failure,
        raw_receipts_sha256=audit["raw_receipts_sha256"],source=source,
        scope="legacy source-bound native hook parity; NOT a fresh compressed numerical gate",
        not_proven=EXCLUSIONS)

def memory_plan(manifest, float_bytes=24, row_tuple_bytes=136):
    # Each completed timeline holds all6 *256 rows. No collector changes.
    row_count = len(manifest["rows"]) * len(manifest["layers"]) * len(manifest["anchors"]) * manifest["horizon"]
    across = 4 * row_count
    primitive = across * (12 * float_bytes + row_tuple_bytes)
    # 1.5x allowance is a planning reserve, NOT an observed strict upper bound.
    timeline_reserve = (primitive * 3 + 1) // 2
    anchor_count = 4 * len(manifest["rows"]) * len(manifest["layers"]) * len(manifest["anchors"])
    disk = anchor_count * (12*128*128*4 + manifest["horizon"]*12*4)
    return dict(schema="damp.reference-memory-plan/v1",
        original_admission_gib=64, ordinary_memory_only=True,
        policy="retain original64GiB admission; no lower-threshold CLI override",
        rows_per_rank=row_count, ranks=4, primitive_python_bytes=primitive,
        timeline_planning_reserve_bytes=timeline_reserve,
        object_sizes=dict(float=float_bytes, tuple12=row_tuple_bytes),
        object_sizes_measured_in_this_image=False,
        binary_payload_disk_bytes=disk, minimum_disk_gib=40,
        model_loading_peak_measured=False, allocator_overhead_upper_bound_proven=False,
        runtime_abort_memavailable_gib=8, monitor_interval_seconds=5,
        monitor_is_not_a_burst_or_OOM_guarantee=True,
        forbidden=["HugeTLB reclamation", "external container/process stop", "protected NPU0-3"],
        unknowns=["model/load CPU private-memory peak", "allocator fragmentation",
                  "runtime/IPC peak", "validator JSON expansion peak"],
        not_proven=EXCLUSIONS)

def new_identity(run_id):
    require(re.fullmatch(r"v[1-9][0-9]*", run_id or "") is not None, "new v<number> required")
    stem = "full-reference-resume-" + run_id
    return ROOT / (stem + "-launch"), ROOT / (stem + "-on"), "qwen36_damp_full_reference_resume_20261006_" + run_id

def require_deadline():
    from datetime import datetime, timezone
    require(datetime.now(timezone.utc) < datetime.fromisoformat(DEADLINE.replace("Z","+00:00")),
            "original DAMP24h deadline passed; recovery cannot reset it")

def memory_record():
    from datetime import datetime, timezone
    raw = Path("/proc/meminfo").read_text()
    fields = {m[1]: int(m[2]) for m in re.finditer(r"^(\w+):\s*(\d+)\s+kB", raw, re.M)}
    require("MemAvailable" in fields, "ordinary MemAvailable missing")
    return dict(utc=datetime.now(timezone.utc).isoformat(), meminfo=raw,
                mem_available_kib=fields["MemAvailable"])

def monitored_on(original, safety, cid, owner, audit, argv):
    """Only observe ordinary RAM; abort ONLY the exact fresh owned container."""
    started = time.monotonic()
    aborted = None
    peak = {"min_mem_available_kib": None, "samples": 0}
    with (audit/"on.log").open("x") as log, (audit/"ordinary-memory.jsonl").open("x") as records:
        proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, text=True)
        try:
            while proc.poll() is None:
                sample = memory_record()
                peak["samples"] += 1
                x = sample["mem_available_kib"]
                peak["min_mem_available_kib"] = x if peak["min_mem_available_kib"] is None else min(x, peak["min_mem_available_kib"])
                # This is a host-health guard, not numerical or throughput acceptance.
                records.write(json.dumps(sample,sort_keys=True,allow_nan=False)+"\n")
                records.flush()
                if x < 8*1024*1024:
                    aborted = "ordinary MemAvailable below8GiB runtime reserve"
                    entry = json.loads(safety.output(["docker","inspect",cid]))[0]
                    original.container_proof(entry,cid,owner)
                    result = subprocess.run(["docker","stop","--time","30",cid], capture_output=True,text=True,timeout=45)
                    safety.write_new(audit/"memory-abort-stop.json",dict(id=cid,exit_code=result.returncode,
                        stdout=result.stdout,stderr=result.stderr,deleted=False))
                    require(result.returncode == 0, "owned memory-abort stop failed")
                    break
                try: require_deadline()
                except RuntimeError as error:
                    aborted = str(error)
                    break
                if time.monotonic()-started > original.TIMEOUTS["on"]:
                    aborted = "on timeout; no retry"
                    break
                time.sleep(5)
            if aborted:
                raise RuntimeError(aborted)
            require(proc.wait(timeout=30) == 0, "on failed; preserve first evidence")
        finally:
            safety.write_new(audit/"on.receipt.json",dict(argv=argv,exit_code=proc.poll(),
                seconds=time.monotonic()-started,abort_reason=aborted,ordinary_memory=peak,
                automatic_retry=False))
            if proc.poll() is None:
                # Terminate only the local docker-exec CLI; outer finally owns container stop.
                proc.terminate()
                try: proc.wait(timeout=10)
                except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=10)

def finalize(on, audit, original, smoke_path, smoke_sha, container_id):
    """Independent parent-controller lock; no fitted-plan selection here."""
    from damp_capture.contract import load_manifest
    from damp_capture.validate import validate
    from damp_calibrate.evidence import COMMON, lock_source, report_receipt
    manifest = load_manifest(original.MANIFEST)
    smoke, smoke_audit = source_bound_smoke(smoke_path,smoke_sha)
    _, smoke_receipt = report_receipt(dict(path=str(smoke_path),sha256=smoke_sha),
        "smoke", smoke["requests"])
    parity = validate(on, manifest, OFF)
    require(parity["mode"] == "full" and parity["requests"] == 36, "full36 parity required")
    safety = original.helper()
    parity_path = audit / "FULL_PAIR_VALIDATION.json"
    safety.write_new(parity_path, parity)
    ranks = []
    common = None
    for rank in range(4):
        path = on / ("rank-"+str(rank)) / "events.jsonl"
        started = []
        with path.open() as f:
            for line in f:
                if line.strip():
                    e = json.loads(line)
                    if e["event"] == "worker_started": started.append(e)
        require(len(started) == 1, "worker source must be unique")
        s = started[0]["source"]
        selected = {key:s[key] for key in COMMON}
        require(common is None or selected == common, "four-rank source disagreement")
        common = selected
        ranks.append(dict(rank=rank,events_path=str(path),events_sha256=sha(path),source=s))
    lock = dict(schema="damp.source-lock/v1",created_by="parent-controller",
        model_config_sha256=manifest["model_hashes"]["config.json"], image_id=original.IMAGE,
        model_weight_byte_identity="NOT previously bound; config/tokenizer/runtime only",
        manifest=dict(path=str(original.MANIFEST),file_sha256=sha(original.MANIFEST),semantic_sha256=digest(manifest)),
        capture_root=str(on),ranks=ranks,
        smoke_validation=dict(path=str(smoke_path),sha256=smoke_receipt["sha256"],requests=smoke["requests"]),
        native_output_parity=dict(path=str(parity_path),sha256=sha(parity_path),dense_root=str(OFF)),
        smoke_source_audit=smoke_audit,
        recovery=dict(original_off_root=str(OFF),fresh_on_root=str(on),fresh_container_id=container_id,
            source_files28_sha256=digest(read_json(OLD_LAUNCH/"source.json")["files"]),
            deadline_unchanged=DEADLINE,not_proven=EXCLUSIONS))
    path = audit / "SOURCE_LOCK.json"
    safety.write_new(path, lock)
    source, proof = lock_source(path, original.MANIFEST, manifest, on.resolve())
    safety.write_new(audit/"SOURCE_LOCK_RECHECK.json",dict(status="pass",proof=proof))
    return dict(path=str(path),sha256=sha(path),scope="FP32-full-TRAIN-reference-only")

def execute(args, original, lock, manifest):
    require_deadline()
    audit, on, name = new_identity(args.run_id)
    original.absent([audit,on])
    require(Path.cwd().resolve() == REPO, "canonical repository cwd required")
    # Only the already accepted NEW source-bound recovery sidecar, not the
    # original failed validator or a newly invented smoke.
    _, smoke_proof = source_bound_smoke(args.smoke_report,args.smoke_sha256)
    smoke = Path(smoke_proof["sidecar"]["path"])
    args.smoke_sha256 = smoke_proof["sidecar"]["sha256"]
    original.NAME, original.AUDIT = name, audit
    safety = original.helper()
    # No old handle/name is restarted. New nonce/name/root for this one attempt.
    collision = subprocess.run(["docker","container","inspect",name],capture_output=True,text=True,timeout=30)
    require(collision.returncode != 0 and (
        "No such object: "+name in collision.stderr or "No such container: "+name in collision.stderr),
        "fresh container-name absence not proven")
    image = json.loads(safety.output(["docker","image","inspect",original.IMAGE]))[0]
    require(image["Id"] == original.IMAGE and image["Architecture"] == "arm64", "image drift")
    old_entry = json.loads(safety.output(["docker","inspect",OLD_ID]))[0]
    require(old_entry["Id"] == OLD_ID and old_entry["Image"] == original.IMAGE and
        old_entry["Name"] == "/qwen36_damp_full_capture_tp4_20261006_v1" and
        old_entry["State"]["Status"] == "exited" and not old_entry["State"]["Running"],
        "original owned container must remain stopped; never restart/delete it")
    audit.mkdir(exist_ok=False)
    safety.write_new(audit/"original-container-fresh.json",old_entry)
    safety.write_new(audit/"OFF_REUSE_LOCK.json",lock)
    safety.write_new(audit/"LEGACY_SOURCE_BOUND_SMOKE_REUSE.json",smoke_proof)
    safety.write_new(audit/"MEMORY_PLAN.json",memory_plan(manifest))
    safety.write_new(audit/"PROTOCOL.json",dict(schema="damp.reference-on-recovery/v1",
        off_root=str(OFF),on_root=str(on),batch_size=4,memory_utilization=.80,
        generation=manifest["generation"],enforce_eager=True,prefix_cache=False,chunked_prefill=False,
        deadline_unchanged=DEADLINE,automatic_retry=False,source_lock_issued=False,
        smoke_scope=smoke_proof["scope"],not_proven=EXCLUSIONS))
    safety.write_new(audit/"recovery-source.json",dict(
        files={str(p.relative_to(REPO)):sha(p) for p in sorted(Path(__file__).parent.iterdir()) if p.is_file()},
        frozen28=read_json(OLD_LAUNCH/"source.json")["files"]))
    owner = uuid.uuid4().hex
    command = list(read_json(OLD_LAUNCH/"create-command.json")["argv"])
    command[command.index("--name")+1] = name
    command[command.index("--label")+1] = original.LABEL+"="+owner
    safety.write_new(audit/"create-command.json",dict(argv=command))
    cid = None; attempted = False; failed = None; source_lock = None
    try:
        original.fresh(safety,"prelaunch")
        assert_original_unchanged(lock["original_evidence"])
        attempted=True; original.stage(safety,"create",command)
        cid=(audit/"create.log").read_text().strip()
        require(re.fullmatch("[a-f0-9]{64}",cid), "unknown create result; no automatic retry")
        original.container_proof(json.loads(safety.output(["docker","inspect",cid]))[0],cid,owner)
        original.stage(safety,"start",["docker","start",cid])
        # Exact original source/import and manifest owning-function checks, not copied guesses.
        for label in ("import_source","manifest_identity"):
            old = read_json(OLD_LAUNCH/(label+".receipt.json"))
            require(old["exit_code"] == 0 and old["argv"][0:3] ==
                ["docker","exec","qwen36_damp_full_capture_tp4_20261006_v1"],
                "original successful preflight command changed")
            argv=list(old["argv"]);argv[2]=name;original.stage(safety,label,argv)
        sizes=safety.python_in_container("-c","import json,sys; print(json.dumps({'float':sys.getsizeof(0.0),'tuple12':sys.getsizeof(tuple(0.0 for _ in range(12)))}))")
        original.TIMEOUTS["object_sizes"] = 60
        original.stage(safety,"object_sizes",sizes)
        size_rows=[json.loads(line) for line in (audit/"object_sizes.log").read_text().splitlines()
                   if line.startswith("{")]
        require(len(size_rows)==1 and set(size_rows[0])=={"float","tuple12"} and
            all(type(x) is int and x>0 for x in size_rows[0].values()),"same-image object sizes malformed")
        measured=memory_plan(manifest,size_rows[0]["float"],size_rows[0]["tuple12"])
        measured["object_sizes_measured_in_this_image"]=True
        measured["model_loading_peak_measured"]=False
        safety.write_new(audit/"SAME_IMAGE_MEMORY_ESTIMATE.json",measured)
        original.fresh(safety,"canary")
        old=read_json(OLD_LAUNCH/"canary.receipt.json");require(old["exit_code"]==0,"old canary receipt invalid")
        argv=list(old["argv"]);require(argv[0:3]==["docker","exec","qwen36_damp_full_capture_tp4_20261006_v1"],"old canary owning container differs")
        argv[2]=name;original.stage(safety,"canary",argv)
        require("python" not in safety.output(["docker","top",cid,"-eo","pid,args"]),"unexpected worker before on")
        original.fresh(safety,"on")
        require_deadline()
        assert_original_unchanged(lock["original_evidence"])
        monitored_on(original,safety,cid,owner,audit,safety.python_in_container("-m","damp_capture.run",
            "--manifest",str(original.MANIFEST),"--output-dir",str(on),"--capture","on",
            "--batch-size","4","--memory-utilization","0.80"))
        require("python" not in safety.output(["docker","top",cid,"-eo","pid,args"]),"orphaned model before validation")
        source_lock = finalize(on,audit,original,smoke,args.smoke_sha256,cid)
        assert_original_unchanged(lock["original_evidence"])
        current_lock, _ = off_lock(original)
        require(current_lock == lock, "frozen28/source/off identity drift during recovery")
        require_deadline()
    except Exception as error:
        failed=error
        original_checked = None
        original_error = None
        try:
            assert_original_unchanged(lock["original_evidence"])
            original_checked = True
        except Exception as verification_error:
            original_checked = False
            original_error = str(verification_error)
        safety.write_new(audit/"FAILURE.json",dict(error_type=type(error).__name__,detail=str(error),
            automatic_retry=False,partial_reference_not_accepted=True,
            original_evidence_unchanged=original_checked,original_verification_error=original_error))
    finally:
        try:
            if cid is None and attempted:
                p=subprocess.run(["docker","inspect",name],capture_output=True,text=True,timeout=30)
                if p.returncode==0:
                    entry=json.loads(p.stdout)[0];original.container_proof(entry,entry["Id"],owner);cid=entry["Id"]
            if cid is not None: original.stop_owned(safety,cid,owner)
        except Exception as error:
            safety.write_new(audit/"STOP_FAILURE.json",dict(error_type=type(error).__name__,detail=str(error),
                parent_attention_required=True,no_delete=True))
            if failed is None: failed=error
    if failed: raise failed
    safety.write_new(audit/"RESULT.json",dict(status="pass",scope="FP32-full-TRAIN-reference-only",
        off_reused=True,on_fresh=True,source_lock=source_lock,original_failure_preserved=True,
        owned_container_stopped_and_retained=True,deadline_unchanged=DEADLINE,not_proven=EXCLUSIONS))
    print(json.dumps(dict(status="pass",source_lock=source_lock,not_proven=EXCLUSIONS),sort_keys=True))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan",action="store_true",help="default: no Docker/NPU/output writes")
    p.add_argument("--execute",action="store_true",help="MAIN only; new attempt; never off")
    p.add_argument("--run-id")
    p.add_argument("--smoke-report",help="optional: fixed accepted NEW sidecar only")
    p.add_argument("--smoke-sha256",help="optional: exact accepted NEW sidecar SHA only")
    a=p.parse_args()
    require(not (a.plan and a.execute),"choose plan or execute")
    original=frozen();lock,manifest=off_lock(original)
    if not a.execute:
        print(json.dumps(dict(status="preparation-only",reuse=lock,memory=memory_plan(manifest),
            deadline_unchanged=DEADLINE,no_docker_or_npu=True),sort_keys=True,allow_nan=False))
        return
    execute(a,original,lock,manifest)

if __name__=="__main__":
    main()
