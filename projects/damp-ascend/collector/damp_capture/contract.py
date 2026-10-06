"""Stdlib corpus/protocol contract. No implicit fallback to evaluation data."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

MODEL = "/cache/efim/Qwen3.6-27B"
INPUT_ROOT = Path("/cache/cch/qwen36-damp-20261006/calibration-inputs")
RESULT_ROOT = Path("/cache/cch/qwen36-damp-20261006")
LAYERS = tuple(i for i in range(64) if i % 4 != 3)
GDN_SHA = "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"
RUNNER_SHA = "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
MODEL_HASHES = {
    "config.json": "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c",
    "tokenizer_config.json": "5186f0defcd7f232382c7f0aebcd2252d073bb921ab240e407b7ae8745d2b29b",
    "tokenizer.json": "5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42",
    "chat_template.jinja": "e84f32a23fdda27689f868aa4a1a5621f41133e51a48d7f3efcbea2839574259",
}
DOMAINS = {"math": "MATH", "code": "APPS", "general": "ARC-Challenge"}
FULL_ANCHORS = (256, 512, 768, 2304, 2560, 2816)
STATE_BYTES = 12 * 128 * 128 * 4

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def file_digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def is_hash(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None

def token_digest(ids):
    require(isinstance(ids, (list, tuple)) and bool(ids), "empty/non-list token IDs")
    require(all(type(x) is int and 0 <= x < 248320 for x in ids), "invalid token ID")
    return digest(list(ids))

def validate_manifest(m, *, verify_files=True):
    require(m.get("schema") == "damp-calibration-input/v1", "wrong corpus schema")
    require(m.get("mode") in ("smoke", "full"), "mode must be smoke/full")
    require(m.get("model_path") == MODEL and m.get("model_hashes") == MODEL_HASHES,
            "model/tokenizer identity differs")
    require(m.get("runtime_hashes") == {"gdn": GDN_SHA, "runner": RUNNER_SHA},
            "runtime source requires re-audit")
    require(m.get("tp_size") == 4 and m.get("physical_npus") == [4, 5, 6, 7],
            "only TP4/physical4-7 admitted")
    require(m.get("layers") == list(LAYERS), "all48 GDN layers required")
    require(m.get("native_state_shape") == [12, 128, 128], "wrong Hv/Dv/Dk geometry")
    gen = m.get("generation", {})
    require(gen.get("temperature") == 0 and gen.get("seed") == 0
            and gen.get("thinking") is False and gen.get("ignore_eos") is True,
            "reference generation protocol differs")
    n, anchors, horizon = gen.get("max_tokens"), m.get("anchors", []), m.get("horizon")
    require(type(n) is int and n == gen.get("min_tokens"), "fixed output required")
    require(type(horizon) is int and horizon > 0, "bad horizon")
    require(bool(anchors) and all(type(a) is int and a > 0 for a in anchors)
            and anchors == sorted(set(anchors)), "bad anchors")
    # Prefill emits the first output token; n outputs permit n-1 decode updates.
    require(max(anchors) + horizon <= n - 1, "output does not cover futures")
    rows = m.get("rows", [])
    require(isinstance(rows, list) and bool(rows), "no corpus")
    ids, prompts, records, hashes = set(), set(), set(), {}
    for row in rows:
        rid = row.get("id")
        require(isinstance(rid, str) and re.fullmatch(r"[a-zA-Z0-9_.-]{1,80}", rid),
                "unsafe row ID")
        require(rid not in ids, "duplicate row ID")
        ids.add(rid)
        sha = token_digest(row.get("input_ids"))
        require(sha == row.get("input_ids_sha256") and sha not in prompts,
                "incorrect/duplicate token fingerprint")
        prompts.add(sha)
        require(is_hash(row.get("prompt_text_sha256")), "missing prompt hash")
        if m["mode"] == "full":
            require(len(row["input_ids"]) == 1024, "full input must be1024 incl.template")
            require(row.get("domain") in DOMAINS and row.get("split") in
                    ("fit", "tune", "validation"), "missing training partition")
            s = row.get("source", {})
            require(s.get("dataset") == DOMAINS[row["domain"]] and s.get("split") == "train",
                    "not the paper TRAIN source")
            require(isinstance(s.get("revision"), str) and
                    re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", s["revision"]),
                    "source revision not immutable")
            require(is_hash(s.get("record_sha256")) and is_hash(s.get("artifact_sha256")),
                    "missing source hashes")
            require(s.get("license") and s.get("url") and s.get("record_id") is not None
                    and str(s["record_id"]),
                "missing provenance/license")
            key = (s["dataset"], str(s["record_id"]))
            require(key not in records, "source record reused across partitions")
            records.add(key)
            p = Path(s.get("artifact_path", "")).resolve()
            require(p.is_relative_to(INPUT_ROOT.resolve()), "artifact outside input root")
            if verify_files:
                require(p.is_file(), "training artifact missing")
                if p not in hashes:
                    hashes[p] = file_digest(p)
                require(hashes[p] == s["artifact_sha256"], "source bytes changed")
    require(is_hash(m.get("prompt_builder_sha256")), "missing builder hash")
    if m["mode"] == "full":
        require(len(rows) == 36 and n == 4096 and anchors == list(FULL_ANCHORS)
                and horizon == 256, "full calibration dimensions differ")
        require(Counter((r["split"], r["domain"]) for r in rows) ==
                Counter({(s, d): 4 for s in ("fit", "tune", "validation") for d in DOMAINS}),
                "not36 balanced disjoint TRAIN rows")
        require(m.get("provenance") == "project-selected-paper-training-domains",
                "cannot claim unpublished author sample IDs")
    else:
        require(len(rows) <= 12 and n <= 33 and max(anchors) + horizon <= 32,
                "smoke must stay bounded")
        require(m.get("provenance") == "project-smoke-not-calibration", "smoke mislabeled")
    if verify_files:
        for name, sha in MODEL_HASHES.items():
            require(file_digest(Path(MODEL) / name) == sha, "model drift: " + name)
    return m

def load_manifest(path):
    p = Path(path).resolve()
    require(p.is_file(), "missing manifest; no fallback corpus")
    return validate_manifest(json.loads(p.read_text(encoding="utf-8")))

def base_manifest(mode):
    n = 4096 if mode == "full" else 9
    return {"schema": "damp-calibration-input/v1", "mode": mode,
            "model_path": MODEL, "model_hashes": dict(MODEL_HASHES),
            "runtime_hashes": {"gdn": GDN_SHA, "runner": RUNNER_SHA},
            "tp_size": 4, "physical_npus": [4, 5, 6, 7], "layers": list(LAYERS),
            "native_state_shape": [12, 128, 128],
            "generation": {"temperature": 0, "seed": 0, "thinking": False,
                           "ignore_eos": True, "max_tokens": n, "min_tokens": n},
            "anchors": list(FULL_ANCHORS) if mode == "full" else [2, 4],
            "horizon": 256 if mode == "full" else 2,
            "provenance": "project-selected-paper-training-domains" if mode == "full"
                          else "project-smoke-not-calibration"}
