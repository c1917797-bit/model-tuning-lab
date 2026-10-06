"""Read-only, stdlib-only adapter for the frozen full-reference selector."""
import hashlib
import importlib
import json
from pathlib import Path
import sys

REPO = Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT = REPO / "projects/damp-ascend"
RESULTS = Path("/cache/cch/qwen36-damp-20261006")
MANIFEST = RESULTS / "calibration-inputs/full-training-36x1024-v3.json"
MANIFEST_SHA = "f348e0b0404e2f3a619b986f5c1152427c52f1a3550386ee1f894eafa6986b33"
MANIFEST_SEMANTIC = "6791283f69290789555d4391312e8d8511fee7787d2ea4257599302486f34bb7"
AUDIT = RESULTS / "full-reference-resume-v1-launch"
CAPTURE = RESULTS / "full-reference-resume-v1-on"
LOCK = AUDIT / "SOURCE_LOCK.json"
PLANS = RESULTS / "calibration-plans-v1"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
MODEL_CONFIG = "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c"
LAYERS = tuple(i for i in range(64) if i % 4 != 3)
PINS = {
    "projects/damp-ascend/calibration/damp_calibrate/__init__.py": "80b39b73c5d07f972c967fd052e5a7f23d7ca75f36ea48ec8f7312fce03a15ca",
    "projects/damp-ascend/calibration/damp_calibrate/evidence.py": "3141314904cd5d3abbbedc15aed7c0f97a2370b9a435824cd7505073df16f5fa",
    "projects/damp-ascend/calibration/damp_calibrate/numerics.py": "b6a238b17ccebb45b15ef3c8e29a99e035fb3294d44fdbd613ba8c6a2c89c3a4",
    "projects/damp-ascend/calibration/damp_calibrate/pipeline.py": "641052ababa29c46440ab86fdc20fd6894737c8bf9afa9b240f4b687d1e35a55",
    "projects/damp-ascend/calibration/damp_calibrate/rules.py": "98285137bfdf6c327a8695488e960678063d7dca907100ce03c60f42e9eca85b",
    "projects/damp-ascend/collector/damp_capture/bindings.py": "137c71b0a3f2b4dac5d82be53a25d01de39b78a77b14db4d8b9e470181003525",
    "projects/damp-ascend/collector/damp_capture/contract.py": "e56b6b47e66b3bec946eda96a51205a779c506edcb8b713730d42c03237e2a57",
    "projects/damp-ascend/collector/damp_capture/identity.py": "8873f833c6dab835af5079ec269e82efa100b1695bef707a78f1cb82210a37db",
    "projects/damp-ascend/collector/damp_capture/text_positions.py": "333aa0c09130b9f6c27459b04a4ae36a7743b9b77275beddc02655252d244354",
    "projects/damp-ascend/collector/damp_capture/validate.py": "2daf0cefe7311431baf9bb0a2aa1dbebe62543598ddcec0bada55796d4be4b8c",
    "projects/damp-ascend/integration/damp_integration/contract.py": "06b91ab27f03ea5cfc231443fbd3790a7e331e1662ef6f837fef8e9151b02dc6",
    "projects/damp-ascend/integration/damp_integration/plan.py": "ccc4f8690caed74ebb7511b75ef2a744ae923d949e3fbb17d4ddbcf56e0d47d9",
    "projects/damp-ascend/operator/production_integer_compaction_v1/tests/candidate_adapter.py": "43d4639d1ac0d737392fab8526aba14af0b1e50161a1940855b71822b18e6a7c",
    "projects/damp-ascend/operator/production_integer_compaction_v1/tests/protocols.py": "7a0747c8c1a1f246f32ec3ad32ab53cd7a5027339a5c8584d5552ae1508f7340",
    "projects/damp-ascend/operator/production_integer_compaction_v1/tests/run_npu_gate.py": "9d2ff5e8eed33c5ec3719dcee2748908924c8ce7151a2e3d2b4d582d285c1c1c",
    "projects/damp-ascend/tools/resume_reference_v1/controller.py": "d20889ce69e1eb1d2d49fff5e2d65803b9f63bff444115587dc21b562641454e",
    "projects/damp-ascend/tools/run_full_capture.py": "9ad5e359766578a24f06e127a990ab93d1e86555baa15d1abb7bb2b3ffc51122"
}

def require(ok, message):
    if not ok:
        raise ValueError(message)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()

def checked(path, expected):
    path = Path(path).resolve(strict=True)
    require(path.is_file() and sha(path) == expected, "missing or drifted bytes: " + str(path))
    return path

def read_json(path, maximum=8*1024*1024):
    path = Path(path).resolve(strict=True)
    require(path.is_file() and path.stat().st_size <= maximum, "missing/oversized JSON")
    return json.loads(path.read_text(encoding="utf-8"))

def frozen_modules():
    # No Torch/runtime import. The imported collector/selector evidence is stdlib-only.
    for name, expected in PINS.items():
        checked(REPO / name, expected)
    for relative in ("collector", "calibration"):
        path = str(PROJECT / relative)
        if path not in sys.path:
            sys.path.insert(0, path)
    contract = importlib.import_module("damp_capture.contract")
    evidence = importlib.import_module("damp_calibrate.evidence")
    rules = importlib.import_module("damp_calibrate.rules")
    require(Path(contract.__file__).resolve() == PROJECT/"collector/damp_capture/contract.py"
            and Path(evidence.__file__).resolve() == PROJECT/"calibration/damp_calibrate/evidence.py"
            and Path(rules.__file__).resolve() == PROJECT/"calibration/damp_calibrate/rules.py",
            "import shadowing is not source binding")
    return contract, evidence, rules

def manifest_identity():
    checked(MANIFEST, MANIFEST_SHA)
    manifest = read_json(MANIFEST)
    require(digest(manifest) == MANIFEST_SEMANTIC, "semantic input drift")
    return manifest

def finalized(lock_sha, result_sha):
    require(isinstance(lock_sha, str) and len(lock_sha) == 64
            and isinstance(result_sha, str) and len(result_sha) == 64,
            "MAIN must supply independently observed SOURCE_LOCK and RESULT hashes")
    checked(LOCK, lock_sha)
    result = read_json(checked(AUDIT/"RESULT.json", result_sha))
    require(not (AUDIT/"FAILURE.json").exists() and not (AUDIT/"STOP_FAILURE.json").exists(),
            "parent finalize failed; a partial SOURCE_LOCK is not admission")
    require(result.get("status") == "pass" and result.get("scope") == "FP32-full-TRAIN-reference-only"
            and result.get("owned_container_stopped_and_retained") is True
            and result.get("source_lock") == {
                "path": str(LOCK), "sha256": lock_sha, "scope": "FP32-full-TRAIN-reference-only"},
            "SOURCE_LOCK must be bound to successful independent parent finalize")
    lock = read_json(LOCK)
    require(lock.get("created_by") == "parent-controller" and lock.get("schema") == "damp.source-lock/v1"
            and lock.get("image_id") == IMAGE and lock.get("model_config_sha256") == MODEL_CONFIG
            and lock.get("capture_root") == str(CAPTURE), "source lock identity drift")
    return lock

def full_evidence(lock_sha, result_sha):
    finalized(lock_sha, result_sha)
    contract, evidence, _ = frozen_modules()
    manifest_identity()
    capture = evidence.Capture(MANIFEST, CAPTURE, LOCK)
    require(len(capture.index) == 36*48*4*6 and len(capture.provenance["ranks"]) == 4
            and all(r["anchors"] == r["futures"] == 36*48*6
                    for r in capture.provenance["ranks"]), "complete TP4 reference matrix missing")
    return capture

def absent_output(path):
    path = Path(path)
    require(path.is_absolute() and path.parent.resolve() == RESULTS and path.name
            and not path.exists() and not path.is_symlink(), "new direct result child required")
    return path

def calibration_command(python, output):
    require(Path(python).is_absolute(), "absolute Python required")
    return [str(python), "-B", "-m", "damp_calibrate.pipeline",
        "--manifest", str(MANIFEST), "--capture-root", str(CAPTURE),
        "--source-lock", str(LOCK), "--output-dir", str(output), "--cpu-threads", "8"]
