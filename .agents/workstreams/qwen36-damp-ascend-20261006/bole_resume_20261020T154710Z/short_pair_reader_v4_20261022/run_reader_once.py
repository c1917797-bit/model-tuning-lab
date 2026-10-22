"""Run the retained-evidence reader once; never create or start a device owner."""
import argparse, hashlib, json, os, resource, subprocess, sys, time
from pathlib import Path

SOURCE_SHA = {
    "cleanup_summary.py": "1c2e014303bec214cff2e19d8c428eee1a13d69c3f8b525308b3ae958faf9687",
    "compare_completed_short.py": "dd653ae8be7d83f3b83c0f1d069b64af4d4be2a72ec5d60dff49f0024a21d8df",
    "test_cleanup_summary.py": "a61245c9774fa80bc185cbd9830356102856f958c3e52193c6ba50589c6dfdfc",
}
BASE = Path("/opt/host/vnf/austinov")
WORK = BASE / "model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z"
PARENT = WORK / "bole_performance_profile_prepare_20261021/successor_layer"
SOURCE_REFS = {
    "ON": {"path": str(PARENT / "bound-short-ON-v2/SOURCE_BOUND.json"), "bytes": 1503149,
           "sha256": "a285ac43d953cf257255ec4848d8719b613010bf339491e2a39d20d2f3b73b8f"},
    "OFF": {"path": str(PARENT / "bound-short-OFF-v2/SOURCE_BOUND.json"), "bytes": 1503858,
            "sha256": "ee9c2633dd33ccf449dd881d65e6100d478bc4439b4e966bf19961b69e2c2b70"},
}

def ref(path):
    p = Path(path)
    assert p.is_file() and p.is_absolute() and not any(x.is_symlink() for x in (p, *p.parents))
    before = p.stat()
    assert before.st_size <= 8 * 2**20
    h = hashlib.sha256()
    size = 0
    with p.open("rb") as stream:
        for chunk in iter(lambda: stream.read(2**20), b""):
            h.update(chunk)
            size += len(chunk)
            assert size <= 8 * 2**20
    after = p.stat()
    assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    assert size == before.st_size
    return {"path": str(p), "bytes": size, "sha256": h.hexdigest()}

def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")

def child_limits():
    resource.setrlimit(resource.RLIMIT_AS, (512 * 2**20, 512 * 2**20))
    resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 2**20, 16 * 2**20))

def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"enabled": False, "NPU": False}))
        return 0
    start = time.monotonic()
    root = Path(__file__).resolve().parent
    out = args.output
    assert out.parent == BASE and out.name.startswith("run-bole-short-pair-reader-v4-")
    assert not out.exists() and not out.is_symlink()
    own = [ref(root / name) for name in SOURCE_SHA]
    assert all(r["sha256"] == SOURCE_SHA[Path(r["path"]).name] for r in own)
    own.append(ref(__file__))
    paths = set()
    for arm, sr in SOURCE_REFS.items():
        assert ref(sr["path"]) == sr
        paths.add(sr["path"])
        m = json.loads(Path(sr["path"]).read_bytes())
        for name in ("compare_state_digest.py", "short_state_digest.py", "bole_performance_profile.py"):
            assert ref(m["files"][name]["path"]) == m["files"][name]
            paths.add(m["files"][name]["path"])
        arm_root = Path(m["output_root"])
        for suffix in ("RESULT.json", "cpu-preflight/cleanup.json", "dense/cleanup.json",
                       "dense/performance-client/HTTP_RESULT.json"):
            paths.add(str(arm_root / suffix))
        for pattern in ("STATE-*.json", "PERF-COMPLETE-GEN-2-RANK-*.json", "PERF-FAILURE-*.json"):
            paths.update(str(p) for p in (arm_root / "dense/receipts").glob(pattern))
    before = [ref(p) for p in sorted(paths)]
    out.mkdir()
    (out / "tmp").mkdir()
    write(out / "INPUTS_BEFORE.json", {"source": own, "retained_inputs": before})
    records = []
    for label, argv, budget in (
        ("regression", ["/usr/bin/python3", "-I", "-B", str(root / "test_cleanup_summary.py")], 30),
        ("pair", ["/usr/bin/python3", "-I", "-B", str(root / "compare_completed_short.py"),
                  "--execute", "--output", str(out / "PAIR_RESULT.json")], 90),
    ):
        env = dict(os.environ, TMPDIR=str(out / "tmp"), PYTHONDONTWRITEBYTECODE="1")
        begun = time.time()
        with (out / (label + ".stdout")).open("xb") as stdout, (out / (label + ".stderr")).open("xb") as stderr:
            try:
                proc = subprocess.run(argv, cwd=str(root), env=env, stdout=stdout, stderr=stderr,
                                      timeout=min(budget, max(1, 150 - (time.monotonic() - start))),
                                      preexec_fn=child_limits)
                item = {"label": label, "argv": argv, "exit_code": proc.returncode, "timed_out": False}
            except subprocess.TimeoutExpired:
                item = {"label": label, "argv": argv, "exit_code": None, "timed_out": True}
        item.update(started_epoch=begun, ended_epoch=time.time(),
                    stdout=ref(out / (label + ".stdout")), stderr=ref(out / (label + ".stderr")))
        records.append(item)
        if item["exit_code"] != 0:
            break
    after = [ref(p) for p in sorted(paths)]
    source_after = [ref(r["path"]) for r in own]
    unchanged = before == after and own == source_after
    write(out / "INPUTS_AFTER.json", {"source": source_after, "retained_inputs": after})
    success = unchanged and len(records) == 2 and all(r["exit_code"] == 0 for r in records)
    result = {
        "schema": "bole.retained-short-pair-reader-execution/v4", "NPU_executed": False,
        "container_action": False, "original_inputs_unchanged": unchanged, "commands": records,
        "source": own, "input_count": len(before), "elapsed": time.monotonic() - start,
        "reader_and_pair_passed": success, "formal_performance": False, "task_accuracy": False,
        "performance_admitted": False, "failure_preserved": str(WORK / "SHORT_STATE_PAIR_READER_V3_FAILURE.json"),
    }
    if (out / "PAIR_RESULT.json").is_file():
        result["pair_result"] = ref(out / "PAIR_RESULT.json")
    write(out / "EXECUTION.json", result)
    print(json.dumps({"execution": ref(out / "EXECUTION.json"), "passed": success,
                      "original_inputs_unchanged": unchanged, "NPU_executed": False}))
    return 0 if success else 1

if __name__ == "__main__":
    raise SystemExit(main())
