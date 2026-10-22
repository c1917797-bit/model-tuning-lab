"""Read saved projection partials; diagnose reduction arithmetic without Torch.

Never returns a numerical/performance acceptance. The exact-sum comparison is
complete; BF16-tree membership is explicitly bounded diagnostic coverage.
"""
import argparse
from array import array
import hashlib
import json
import math
import os
from pathlib import Path
import sys

_MATH_PATH = Path(__file__).resolve().with_name("reduction_math.py")
_MATH_BYTES = _MATH_PATH.read_bytes()
_MATH_REF = dict(path=str(_MATH_PATH), bytes=len(_MATH_BYTES),
                 sha256=hashlib.sha256(_MATH_BYTES).hexdigest())
_MATH_SCOPE = {"__name__": "_bole_independent_reduction_math", "__file__": str(_MATH_PATH)}
exec(compile(_MATH_BYTES, str(_MATH_PATH), "exec"), _MATH_SCOPE)
bf16_tree_results = _MATH_SCOPE["bf16_tree_results"]
exact_sum = _MATH_SCOPE["exact_sum"]
is_finite = _MATH_SCOPE["is_finite"]


def need(condition, message):
    if not condition:
        raise ValueError(message)


def reference(path):
    path = Path(path)
    raw = path.read_bytes()
    return dict(path=str(path.resolve()), bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest())


def read_ref(ref, maximum):
    need(type(ref) is dict and set(ref) == {"path", "bytes", "sha256"},
         "complete Ref3 required")
    path = Path(ref["path"])
    need(path.is_absolute() and not any(p.is_symlink() for p in (path, *path.parents)),
         "ordinary absolute input")
    need(type(ref["bytes"]) is int and 0 <= ref["bytes"] <= maximum,
         "bounded input bytes")
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    need(identity(before) == identity(after) and len(raw) == ref["bytes"]
         and hashlib.sha256(raw).hexdigest() == ref["sha256"], "exact stable Ref bytes")
    return raw


def load_words(ref, count):
    raw = read_ref(ref, 2 * 1024 ** 2)
    need(len(raw) == count * 2, "complete BF16 tensor bytes")
    words = array("H")
    words.frombytes(raw)
    if sys.byteorder != "little":
        words.byteswap()
    return words


def analyze(config):
    need(config["schema"] == "bole.projection-reduction-diagnostic-input/v1",
         "diagnostic input schema")
    need(config["consumer_sources"] == [reference(__file__), _MATH_REF] and
         reference(_MATH_PATH) == _MATH_REF, "exact independently frozen consumer bytes")
    need(config["generations"] == [1, 2] and config["ranks"] == [0, 1, 2, 3],
         "two original generations and all four ranks")
    shape = config["shape"]
    need(type(shape) is list and len(shape) == 2 and
         all(type(x) is int and x > 0 for x in shape), "actual matrix shape")
    count = math.prod(shape)
    need(count * 2 <= 2 * 1024 ** 2, "bounded complete tensor")
    cap = config["tree_coordinate_cap"]
    need(type(cap) is int and 0 <= cap <= 16384, "bounded tree diagnostic")
    records = {}
    raw_refs, missing = [], []
    for ref in config["projection_records"]:
        obj = json.loads(read_ref(ref, 128 * 1024))
        need(obj["schema"] == "bole.native-prefill-boundary-repeatability/v1"
             and obj["event"] == "PROJECTION-INTERNAL", "actual projection record")
        key = (obj["generation"], obj["rank"])
        need(key[0] in config["generations"] and key[1] in config["ranks"]
             and key not in records, "one record per generation/rank")
        rec = obj["record"]
        need(rec["generation"] == key[0] and rec["diagnostic_only"] is True,
             "consistent actual generation and diagnostic scope")
        records[key] = (ref, obj)
        for stage in ("pre_reduce", "post_reduce"):
            meta = rec["stages"][stage]
            need(meta["full_actual_tensor"] is True and meta["dtype"] == "torch.bfloat16"
                 and meta["shape"] == shape and meta["bytes"] == count * 2,
                 "actual full BF16 stage with exact shape")
            if "raw" not in meta:
                missing.append(dict(generation=key[0], rank=key[1], stage=stage))
            else:
                need(meta["raw"]["bytes"] == meta["bytes"] and
                     meta["raw"]["sha256"] == meta["sha256"],
                     "saved raw identity equals observed full tensor")
                raw_refs.append(meta["raw"])
    need(set(records) == {(g, r) for g in config["generations"] for r in config["ranks"]},
         "complete four-rank generation record set")
    need(len({o["source_sha256"] for _, o in records.values()}) == 1,
         "one probe source identity")
    result = dict(schema="bole.projection-reduction-diagnostic/v1",
                  diagnostic_only=True, numerical_qualified=False,
                  candidate_qualification=False, formal_performance=False,
                  task_accuracy=False, data_complete=not missing, missing_raw=missing,
                  consumer_sources=config["consumer_sources"],
                  input_records=config["projection_records"], raw_refs=raw_refs,
                  exact_sum_contract="integer multiples of 2**-133; final BF16 nearest/ties-even",
                  tree_contract="all binary orders with BF16 rounding at each add",
                  modeling_limits=[
                      "Tree membership is per coordinate, not one shared tensor-wide tree.",
                      "FP32/FP16 accumulation, partitioning and final cast are not modeled.",
                      "Tree membership or exclusion cannot identify an HCCL implementation defect.",
                      "Warmup versus measured generations do not prove warmed repeatability."],
                  shape=shape, generations=[], cross_generation=None)
    if missing:
        return result
    data = {}
    for (g, r), (_, obj) in records.items():
        for stage in ("pre_reduce", "post_reduce"):
            data[g, r, stage] = load_words(obj["record"]["stages"][stage]["raw"], count)
    for g in config["generations"]:
        partials = [data[g, r, "pre_reduce"] for r in config["ranks"]]
        posts = [data[g, r, "post_reduce"] for r in config["ranks"]]
        report = dict(generation=g, elements=count, nonfinite_partial=0,
                      nonfinite_post=[0] * 4, exact_sum_mismatch=[0] * 4,
                      numeric_zero_only_difference=[0] * 4,
                      post_rank_disagreement=[0] * 4, tree_needed=0,
                      tree_analyzed=0, tree_outside=[0] * 4, first_differences=[])
        for i in range(count):
            words = tuple(a[i] for a in partials)
            for rank in range(4):
                report["nonfinite_post"][rank] += not is_finite(posts[rank][i])
                report["post_rank_disagreement"][rank] += posts[rank][i] != posts[0][i]
            if not all(is_finite(x) for x in words):
                report["nonfinite_partial"] += 1
                continue
            expected = exact_sum(words)
            differs = [posts[r][i] != expected for r in range(4)]
            for rank in range(4):
                report["exact_sum_mismatch"][rank] += differs[rank]
                report["numeric_zero_only_difference"][rank] += (
                    differs[rank] and (posts[rank][i] & 0x7FFF) == (expected & 0x7FFF) == 0)
            if any(differs):
                report["tree_needed"] += 1
                if report["tree_analyzed"] < cap:
                    allowed = bf16_tree_results(words)
                    report["tree_analyzed"] += 1
                    for rank in range(4):
                        report["tree_outside"][rank] += posts[rank][i] not in allowed
                    if len(report["first_differences"]) < 8:
                        report["first_differences"].append(dict(
                            flat_index=i, input_words=words, expected_word=expected,
                            post_words=[a[i] for a in posts],
                            allowed_bf16_tree_words=sorted(allowed)))
        report["tree_coverage_complete"] = report["tree_analyzed"] == report["tree_needed"]
        result["generations"].append(report)
    result["cross_generation"] = {
        stage: [sum(x != y for x, y in zip(data[1, r, stage], data[2, r, stage]))
                for r in config["ranks"]]
        for stage in ("pre_reduce", "post_reduce")}
    return result


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--inputs-ref", type=json.loads)
    parser.add_argument("--output")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(enabled=False, NPU=False)))
        return
    need(args.inputs_ref and args.output, "exact inputs and fresh result path required")
    result = analyze(json.loads(read_ref(args.inputs_ref, 128 * 1024)))
    # Reopen original inputs after the computation, including all raw arrays.
    for ref in (args.inputs_ref, *result["input_records"], *result["raw_refs"]):
        read_ref(ref, 2 * 1024 ** 2)
    result["inputs_ref"] = args.inputs_ref
    need([reference(__file__), reference(_MATH_PATH)] == result["consumer_sources"],
         "executed consumer sources remain unchanged")
    raw = (json.dumps(result, sort_keys=True, allow_nan=False) + "\n").encode()
    need(len(raw) <= 1024 ** 2, "bounded complete report")
    output = Path(args.output)
    need(output.is_absolute() and output.parent.is_dir() and
         not any(p.is_symlink() for p in (output, *output.parents)), "ordinary output")
    with output.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(reference(output), sort_keys=True))


if __name__ == "__main__":
    main()
