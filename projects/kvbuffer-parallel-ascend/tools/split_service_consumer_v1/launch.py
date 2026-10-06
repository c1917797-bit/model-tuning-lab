#!/usr/bin/env python3
"""Explicit same-eager P1 diagnostic launcher; old observer/bench/config are unchanged."""
from __future__ import annotations
import argparse
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
import re
import sys
import traceback
from datetime import datetime, timezone
import consumer as c

SERVICE = c.PROJECT / "tools/service"


def mount_binding(entry, path, *, writable=False, same_absolute=True):
    p = Path(path)
    matches = [m for m in entry["Mounts"] if m.get("Type") == "bind" and
               (p == Path(m["Destination"]) or Path(m["Destination"]) in p.parents)]
    c.require(matches, "missing actual inspected evidence/output bind mount: " + str(path))
    m = max(matches, key=lambda x: len(Path(x["Destination"]).parts))
    c.require(m.get("RW") is writable, "deepest actual mount RO/RW mismatch")
    if same_absolute:
        c.require(m["Source"] == m["Destination"], "no invented host/image path alias")
    return m

def evidence_paths(value):
    if isinstance(value, dict):
        if set(value) == {"path", "sha256"}:
            yield value["path"]
        else:
            for child in value.values():
                yield from evidence_paths(child)
    elif isinstance(value, list):
        for child in value:
            yield from evidence_paths(child)

def fresh_identity(ident, checked_ref, arm, port, old, h, helper, read=c.read_file):
    # Reuse the original arm/protocol/TOTAL/freshness contract, not its obsolete gate parser.
    old.validate_identity(ident, checked_ref["sha256"], arm, port)
    c.require(ident.get("native_gate_kind") == "split-kernel-prerequisite" and
              ident.get("diagnostic_scope") == "same-eager-P1-lifecycle-screen" and
              ident.get("formal_performance_authorized") is False,
              "MAIN explicit diagnostic identity, not new formal-service authority")
    evidence = ident["evidence"]
    inspect = c.obj(evidence["container_inspect"], read)
    resources = c.obj(evidence["host_resources"], read)
    # These are MAIN's fresh original reads, not historical numerical-job device proofs.
    c.require(type(inspect) is list and len(inspect) == 1, "fresh actual one TP4 container inspect")
    e = inspect[0]; cid = e["Id"]; hc = e["HostConfig"]
    c.require(re.fullmatch("[0-9a-f]{64}", cid) and e["Image"] == old.IMAGE and
              hc.get("Privileged") is False and not hc.get("DeviceRequests") and
              hc.get("IpcMode") != "host" and hc.get("Memory", 0) > 0 and
              hc.get("MemorySwap") == hc["Memory"] and hc.get("NanoCpus", 0) > 0,
              "actual nonprivileged bounded/no-swap TP4 container")
    wanted = {"/dev/davinci%d"%p: "/dev/davinci%d"%i for i,p in enumerate((4,5,6,7))}
    wanted.update({"/dev/"+n: "/dev/"+n for n in ("davinci_manager", "devmm_svm", "hisi_hdc")})
    c.require(len(hc.get("Devices", [])) == 7 and
              {x["PathOnHost"]:x["PathInContainer"] for x in hc["Devices"]} == wanted,
              "real inspect mapping physical4-7 only, protect0-3")
    env = dict(x.split("=",1) for x in e["Config"].get("Env",[]) if "=" in x)
    c.require(env.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3" and
              os.environ.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3",
              "fresh actual TP4 visible devices")
    mem = re.search(r"^MemAvailable:\s*(\d+)\s+kB", resources["meminfo"], re.M)
    c.require(mem is not None and int(mem[1])*1024 >= 72*c.GIB,
              "unchanged actual ordinary RAM72GiB model floor; no HugeTLB substitution")
    c.require(resources.get("ordinary_available_bytes") == int(mem[1])*1024,
              "actual raw ordinary memory agrees with parsed proof")
    ncpu = resources["docker_info"]["NCPU"]
    c.require(type(ncpu) is int and ncpu >= 1 and hc["NanoCpus"] <= ncpu*10**9,
              "fresh Docker CPU capability; MAIN aggregate reserve still required")
    rows = h.parse_processes(resources["npu_smi"])
    telemetry = helper.telemetry(resources["npu_smi"])
    for card in (4,5,6,7):
        c.require(not rows[card] and telemetry[card]["aicore"] == 0 and
                  telemetry[card]["hbm_mib"] <= 3165, "fresh actual empty0core/idle3165 target envelope")
    seen = datetime.fromtimestamp(resources["observed_ns"]/1e9, timezone.utc)
    c.require(0 <= (datetime.now(timezone.utc)-seen).total_seconds() <= 600,
              "fresh MAIN host resources, not historical gate proof")
    # Source-canary raw bytes are retained; MAIN must bind its actual four-card/source result.
    # We do not claim generic parsing of an unspecified existing canary schema.
    c.raw(evidence["source_canary"], read)
    c.raw(evidence["model_manifest"], read)
    c.require(all(type(x) is dict for x in (evidence["source_canary"], evidence["model_manifest"])),
              "real MAIN source-canary/model-manifest Refs")
    return {"container_id": cid, "inspect": evidence["container_inspect"],
            "host_resources": evidence["host_resources"], "source_canary": evidence["source_canary"],
            "model_manifest": evidence["model_manifest"],
            "scope": "fresh MAIN raw identity; aggregate cap/disk/mount/source ownership remains MAIN admission"}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ("manifest", "inputs", "checked", "identity"):
        p.add_argument("--"+n, type=Path); p.add_argument("--"+n+"-sha256")
    p.add_argument("--arm", choices=("dense", "candidate"))
    p.add_argument("--output-dir", type=Path); p.add_argument("--port", type=int)
    p.add_argument("--model", type=Path, default=Path("/models/Qwen3.6-27B"))
    p.add_argument("--library", type=Path, default=Path(
        "/cache/cch/qwen36-kvbuffer-parallel-20261006/build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so"))
    p.add_argument("--prepare-only", action="store_true")
    p.add_argument("--execute-diagnostic", action="store_true")
    a = p.parse_args()
    if not a.prepare_only and not a.execute_diagnostic:
        print(json.dumps({"enabled": False, "launches_model": False, "service_ready": False,
                          "scope": "same-eager-P1 diagnostic preparation",
                          "remaining": ["actual split reports", "MAIN raw TP4 identity/RAM72GiB",
                                        "true T2-15 numerical", "model lifecycle", "paired E2E", "task accuracy"]}))
        return
    c.require(all(getattr(a,n) is not None and getattr(a,n+"_sha256") is not None
                  for n in ("manifest", "inputs", "checked", "identity")) and
              a.arm is not None and a.output_dir is not None and a.port is not None,
              "MAIN explicit source/raw prerequisite/fresh identity Refs and new arm output")
    if a.execute_diagnostic:
        c.require(os.environ.get("KVBUFFER_SPLIT_SERVICE_DIAGNOSTIC") == "1",
                  "default OFF; MAIN explicit diagnostic opt-in")
    refs = {n: {"path": str(getattr(a,n)), "sha256": getattr(a,n+"_sha256")}
            for n in ("manifest", "inputs", "checked", "identity")}
    supplied = c.obj(refs["checked"])
    replay = c.validate(c.obj(refs["inputs"]), refs["manifest"], enabled=True)
    replay["input_ref"] = refs["inputs"]
    c.require(supplied == replay, "inside image must revalidate exact original raw authority, not host status")
    packet,pins,_,_,d,h,helper = c.sources(refs["manifest"])
    old = c.module(SERVICE/"contract.py", pins[str(SERVICE/"contract.py")],
                   "kvbp_original_service_contract", c.read_file)
    ident = c.obj(refs["identity"])
    external = fresh_identity(ident, refs["checked"], a.arm, a.port, old, h, helper)
    inspected = c.obj(ident["evidence"]["container_inspect"])[0]
    # Every historical host Ref is visible at its ORIGINAL absolute path through an inspected RO bind.
    paths = set(evidence_paths([refs, supplied, packet["artifacts"], ident["evidence"]]))
    paths.add(str(c.ROOT))
    paths.add(str(Path(replay["joint"]["path"]).parent))
    for path in sorted(paths):
        if path.startswith(str(c.ROOT)) or path.startswith("/cache/"):
            mount_binding(inspected, path)
    mount_binding(inspected, "/kvbuffer-results", writable=True, same_absolute=False)
    mount_binding(inspected, a.model, writable=False, same_absolute=False)
    root = a.output_dir.resolve()
    c.require(Path("/kvbuffer-results") in root.parents and not root.exists(),
              "new arm output under only RW result mount, never overwrite")
    c.require(old.sha(a.library) == old.LIBRARY_SHA, "same actual compiled candidate binary")
    sys.path.insert(0, str(c.PROJECT/"plugin"))
    from kvbuffer_parallel.contract import source_identity, MODEL_CONFIG
    c.require(old.sha(a.model/"config.json") == MODEL_CONFIG, "original model config identity")
    runtime_sources = source_identity()
    general = {e.name for e in importlib.metadata.entry_points(group="vllm.general_plugins")}
    platform = {e.name for e in importlib.metadata.entry_points(group="vllm.platform_plugins")}
    c.require({"ascend_kv_connector","ascend_model","ascend_model_loader",
               "kvbuffer_parallel","kvbuffer_service"} <= general and "ascend" in platform,
              "actual grouped plugin inventory, not all-six-general")
    grouped_plugins = {"general": sorted(general), "platform": sorted(platform)}
    c.require({path:old.sha(path) for path in old.COMPLETION_SOURCES} == old.COMPLETION_SOURCES,
              "original token-ID/streaming source identity")
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(c.PROJECT/"plugin")+":"+str(SERVICE)+(":"+existing if existing else "")
    env.update(VLLM_PLUGINS="ascend,ascend_kv_connector,ascend_model,ascend_model_loader,kvbuffer_parallel,kvbuffer_service",
               VLLM_USE_V1="1", VLLM_WORKER_MULTIPROC_METHOD="spawn", PYTHONDONTWRITEBYTECODE="1",
               QWEN36_KVBP_ENABLE="1" if a.arm == "candidate" else "0",
               QWEN36_KVBP_LIBRARY=str(a.library), QWEN36_KVBP_LIBRARY_SHA256=old.LIBRARY_SHA,
               QWEN36_KVBP_MODEL_CONFIG=str(a.model/"config.json"),
               QWEN36_KVBP_AUDIT=str(root/"candidate-evidence.jsonl"),
               QWEN36_KVBP_AUX_BUDGET_BYTES=str(old.budget(a.arm)["auxiliary_reserved_bytes"]),
               QWEN36_KVBP_TOTAL_BUDGET_BYTES=str(old.budget(a.arm)["common_total_bytes"]),
               KVBP_SERVICE_EVIDENCE="1", KVBP_SERVICE_ARM=a.arm, KVBP_SERVICE_OUTPUT=str(root))
    argv = [sys.executable, "-m", "vllm.entrypoints.openai.api_server", "--model", str(a.model),
            "--served-model-name", "qwen36-kvbp-p1", "--tensor-parallel-size", "4",
            "--data-parallel-size", "1", "--dtype", "bfloat16", "--seed", "0",
            "--max-model-len", "40960", "--max-num-batched-tokens", "40960", "--max-num-seqs", "16",
            "--no-enable-prefix-caching", "--mamba-cache-mode", "none", "--no-enable-chunked-prefill",
            "--enforce-eager", "--disable-log-stats", "--kv-cache-memory-bytes",
            str(old.budget(a.arm)["native_bytes"]), "--host", "127.0.0.1", "--port", str(a.port)]
    manifest = dict(schema="kvbp.service-arm/v1", arm=a.arm, common=old.COMMON, image_id=old.IMAGE,
        model_config_sha256=MODEL_CONFIG, native_gate_sha256=refs["checked"]["sha256"],
        native_gate_kind="split-kernel-prerequisite", grouped_plugin_inventory=grouped_plugins, library_sha256=old.LIBRARY_SHA,
        plugin_sha256=old.PLUGIN_SHA, sources=runtime_sources, identity_sha256=refs["identity"]["sha256"],
        budget=old.budget(a.arm), argv=argv, completion_sources=old.COMPLETION_SOURCES,
        service_sources={str(x.relative_to(SERVICE)):old.sha(x) for x in SERVICE.rglob("*") if x.is_file()},
        common_runtime_env={k:env.get(k) for k in ("VLLM_USE_V1", "VLLM_PLUGINS",
            "VLLM_WORKER_MULTIPROC_METHOD", "ASCEND_RT_VISIBLE_DEVICES", "ASCEND_LAUNCH_BLOCKING",
            "VLLM_ASCEND_ENABLE_FLASHCOMM1", "VLLM_ASCEND_ENABLE_FLASHCOMM2",
            "VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE", "HCCL_OP_BASE_FFTS_MODE", "PYTHONPATH", "LD_LIBRARY_PATH")},
        evidence_scope="same-eager-prefix-off-P1-screen-not-final-acceptance",
        evidence_observer="same-metadata-runner-wrapper-both-arms-no-NPU-read-or-sync",
        prepare_only=a.prepare_only, consumer_source_manifest=refs["manifest"],
        raw_split_inputs=refs["inputs"], checked_split_prerequisite=refs["checked"],
        fresh_main_raw_identity=external, formal_performance_authorized=False,
        model_lifecycle_verified=False, other_batches_verified=False, task_accuracy_verified=False)
    root.mkdir(parents=True, exist_ok=False)
    c.write_new(root/"ARM.json", manifest)
    if a.prepare_only:
        print(json.dumps(manifest, sort_keys=True)); return
    # Preserve original exec exception; a secondary evidence write must never replace it.
    try:
        os.execve(sys.executable, argv, env)
    except BaseException as primary:
        original_trace = traceback.format_exc()
        try:
            c.write_new(root/"LAUNCH_FAILURE.json", {"error": repr(primary), "traceback": original_trace,
                        "argv": argv, "no_retry": True, "service_ready": False})
        except BaseException as secondary:
            print("KVBP_SECONDARY_LAUNCH_EVIDENCE_ERROR "+repr(secondary), file=sys.stderr)
        raise

if __name__ == "__main__":
    main()
