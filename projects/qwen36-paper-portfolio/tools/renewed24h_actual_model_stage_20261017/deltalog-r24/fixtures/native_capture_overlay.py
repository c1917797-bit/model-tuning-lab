"""MXR-specific guest overlay for MAIN's admitted TP4 container; not a host scheduler.

Reuse the observed native eager server argv, replacing ONLY the KIVI custom
worker with the original Ascend worker. No KIVI algorithm module is installed.
"""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

UPSTREAM_ROOT = "/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-direct-d8-fp32-model-boundary-r87-v1-011"
UPSTREAM_PINS = {
    "server_entry.py": "be314a47a6c440960632d3fa88d18f4ff1b80c02356dd8a5fc45c321a7164e9f",
    "config_cpu.py": "c082d535f9bd29a4e828ff98796560ea915d86cf132034d0da7df39c2aca6349",
    "cann_python.py": "cee927f1107fe6714e86ab1dceecafeff800980a00b8df9fcc47ff6831ba5104",
}
CAPTURE_MANIFEST_SHA = "f88e44fe7f7fa6b61ef6d5043a3a335a565dc59a6dac57acf5d24ff18779fc4e"
NATIVE_WORKER = "vllm_ascend.worker.worker.NPUWorker"
MODEL_CONFIG_SHA = "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c"
MODEL_MANIFEST = "/cache/cch/qwen36-paper-preparation-20261007/sparse/actual-input-inventory-v1-001/MAIN-original-checkpoint-fullhash-20261008-001/ACTUAL_MODEL_MANIFEST.json"
MODEL_MANIFEST_SHA = "11ac18fa31878609b6b56a9c9213d12729cdb466d14c587efcf6d261566a706c"
AUTHORITY = "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/R118_NEW12H_AUTHORITY_20261013.json"
AUTHORITY_SHA = "32b3d57baa8f5f843d95675de57e0e8d5579dd8766c9d3d9bd320f834af05a72"
START = 1791879730
CUTOFF = 1791922930


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for part in iter(lambda: handle.read(1048576), b""):
            digest.update(part)
    return digest.hexdigest()


def need(value, reason):
    if not value:
        raise ValueError(reason)


def load_source(root, name):
    root = Path(root)
    path = root / name
    need(root.is_absolute() and not root.is_symlink() and not path.is_symlink(), "ordinary exact source path")
    need(sha(path) == UPSTREAM_PINS[name], "observed native launcher/helper source mismatch")
    spec = importlib.util.spec_from_file_location("_mxr_source_only_" + name[:-3], path)
    module = importlib.util.module_from_spec(spec)
    # Both verified files have only stdlib imports and definitions at import.
    # Their KIVI main()/loader/worker paths are never called here.
    spec.loader.exec_module(module)
    return module


def native_argv(upstream_root, port):
    old = load_source(upstream_root, "server_entry.py").native_argv(port, 6 * 1024**3)
    need(old[-2:] == ["--worker-cls", "kivi_firstdecode_bootstrap.FirstDecodeWorker"], "observed original sole worker argument")
    result = list(old)
    result[-1] = NATIVE_WORKER
    need(sum(a != b for a, b in zip(old, result)) == 1 and old[:-1] == result[:-1], "one native worker replacement only")
    return result


def frozen_capture(root):
    root = Path(root)
    need(root.is_absolute() and root.is_dir() and not root.is_symlink(), "ordinary deployed frozen capture source")
    manifest = root / "SOURCE_MANIFEST.json"
    need(sha(manifest) == CAPTURE_MANIFEST_SHA, "frozen capture package identity")
    value = json.loads(manifest.read_text("utf-8"))
    for row in value["files"]:
        leaf = Path(row["path"])
        need(not leaf.is_absolute() and ".." not in leaf.parts, "bounded manifest path")
        path = root / leaf
        need(not path.is_symlink() and path.stat().st_size == row["bytes"] and sha(path) == row["sha256"], "frozen capture source drift")
    return value


def environment(base, source, output, run_id):
    need(re.fullmatch(r"[A-Za-z0-9_-]{1,100}", run_id) is not None, "unique bounded MAIN run id")
    result = dict(base)
    need(base.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3", "MAIN must prove physical4--7 -> logical0--3")
    # Refuse inherited research installations instead of pretending an unknown
    # candidate environment is the dense/native path.
    for key, value in base.items():
        if key.startswith(("QWEN36_KIVI_", "QWEN36_SPARQ_", "QWEN36_SKVQ_", "QWEN36_ADAKV_")):
            need(value in ("", "0"), "foreign experiment environment: " + key)
    result.update(MST_MXR_CAPTURE_ENABLE="1", MST_MXR_SOLVE_ENABLE="0",
                  MST_MXR_CAPTURE_ROOT=str(output), MST_MXR_CAPTURE_RUN_ID=run_id,
                  MST_MXR_CAPTURE_CASES_PER_WORKER="1", MST_MXR_CAPTURE_BYTES_PER_WORKER="67108864",
                  VLLM_WORKER_MULTIPROC_METHOD="spawn", TORCH_DEVICE_BACKEND_AUTOLOAD="0",
                  PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    source = str(source)
    result["PYTHONPATH"] = source + (":" + base["PYTHONPATH"] if base.get("PYTHONPATH") else "")
    if "VLLM_PLUGINS" in base:
        plugins = [name for name in base["VLLM_PLUGINS"].split(",") if name]
        need(plugins, "empty explicit base-plugin filter")
        result["VLLM_PLUGINS"] = ",".join(dict.fromkeys(plugins + ["mxr_source_bound_capture"]))
    return result


def prompt_ids(config, count=129):
    need(type(count) is int and count in (16, 129), "only bounded new diagnostic input lengths")
    need(config.get("model_type") == "qwen3_5" and isinstance(config.get("text_config"), dict), "actual checkpoint architecture")
    vocab = config["text_config"].get("vocab_size")
    need(type(vocab) is int and vocab > 0, "actual model vocabulary")
    # This is an explicitly NEW short diagnostic slice of the observed source
    # token recipe, not original benchmark equivalence or invented GDN tensors.
    ids = [1000 + j % 257 for j in range(count)]
    need(all(0 <= value < vocab for value in ids), "raw token IDs outside actual checkpoint vocabulary")
    return ids


def shadow_environment(base, source, output, run_id, gate, gate_sha):
    result = environment(base, source, output, run_id)
    need(Path(gate).is_absolute() and sha(gate) == gate_sha, "actual replay gate ref required")
    result.update(MST_MXR_CAPTURE_ENABLE="0", MST_MXR_SOLVE_ENABLE="1", MST_MXR_MODEL_STAGE="diagnostic",
                  MST_MXR_SOLVE_GATE=str(gate), MST_MXR_SOLVE_GATE_SHA256=gate_sha,
                  MST_MXR_SOLVE_EVIDENCE_ROOT=str(output), MST_MXR_MODEL_RUN_ID=run_id,
                  MST_MXR_MODEL_CASES_PER_WORKER="1", MST_MXR_MODEL_MAX_TOKENS="256")
    if "VLLM_PLUGINS" in base:
        plugins = [p for p in base["VLLM_PLUGINS"].split(",") if p]
        result["VLLM_PLUGINS"] = ",".join(dict.fromkeys(plugins + ["mxr_source_bound_solve"]))
    return result


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write("\n")
