"""CPU-only deterministic project-derived TRAIN context builder; never author sample claims."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from .contract import (INPUT_ROOT, MODEL, MODEL_HASHES, base_manifest, canonical, digest,
                       file_digest, require, token_digest, validate_manifest)
from .training_sources import PLAN, artifact_path, index_for, validate_plan

SEED = "damp-project-train-1024-v1"
SPLITS = ("fit", "tune", "validation")
MAX_CONTEXT_CANDIDATES = 4


class NoExactBoundary(ValueError):
    def __init__(self, audit):
        super().__init__("no exact1024 original-codepoint/native-template boundary; never add padding")
        self.audit = audit


def native_chat(tokenizer, text):
    return list(tokenizer.apply_chat_template(
        [{"role": "user", "content": text}], tokenize=True, return_dict=False,
        add_generation_prompt=True, enable_thinking=False))


def _legacy_fixed_chat(tokenizer, context, target, length=1024):
    """Truncate REAL context only; preserve target and native no-thinking template."""
    suffix = "\nTarget problem:\n" + target + "\nSolve the target problem."
    base = native_chat(tokenizer, suffix)
    require(len(base) < length, "target too long for context-calibration input")
    tokens = tokenizer.encode(context, add_special_tokens=False)
    require(len(native_chat(tokenizer, context + suffix)) >= length, "insufficient TRAIN context")
    estimate = length - len(base)
    # Actual encode/decode+template, not fabricated pad IDs or a cut assistant suffix.
    # Boundary merges are allowed only when verified by the native full template.
    for distance in range(0, 257):
        candidates = (estimate,) if distance == 0 else (estimate-distance, estimate+distance)
        for count in candidates:
            if not 1 <= count <= len(tokens):
                continue
            prefix = tokenizer.decode(tokens[:count], skip_special_tokens=False,
                                      clean_up_tokenization_spaces=False)
            if "\ufffd" in prefix:
                continue  # never replace an incomplete UTF8 token sequence
            text = prefix + suffix
            ids = native_chat(tokenizer, text)
            if len(ids) == length:
                require(text.endswith(suffix), "target/template preservation failed")
                return text, ids, dict(context_prefix_tokens=count,
                                       context_full_tokens=len(tokens),
                                       context_trim="native decode then full chat retokenization")
    raise ValueError("no exact1024 native-template boundary; never add synthetic padding")


def fixed_chat(tokenizer, context, target, length=1024):
    """Preserve original Unicode context prefix, complete target and native template."""
    require(length == 1024, "full calibration length must stay exactly1024")
    suffix = "\nTarget problem:\n" + target + "\nSolve the target problem."
    base_length = len(native_chat(tokenizer, suffix))
    require(base_length < length, "target too long for context-calibration input")
    require(len(native_chat(tokenizer, context + suffix)) >= length, "insufficient TRAIN context")
    proof = character_probes(tokenizer, context, target, length)
    if not proof["exact_codepoint_boundaries"]:
        raise NoExactBoundary(dict(context_sha256=proof["original_context_sha256"],
                                   context_codepoints=len(context), base_tokens=base_length,
                                   binary_bracket=proof["binary_bracket"], probe_count=len(proof["probes"]),
                                   nearest_lengths=[p for p in proof["probes"] if abs(p[1] - length) <= 4],
                                   probe_sha256=digest(proof["probes"])))
    end = min(proof["exact_codepoint_boundaries"])
    prefix = context[:end]  # never tokenizer.decode, fabricated token IDs or a target cut
    text = prefix + suffix
    ids = native_chat(tokenizer, text)
    require(len(ids) == length and text.endswith(suffix) and context.startswith(prefix),
            "exact original-prefix/target/template verification failed")
    return text, ids, dict(context_prefix_codepoints=end, context_full_codepoints=len(context),
                           context_prefix_utf8_bytes=len(prefix.encode()),
                           context_prefix_tokens=len(tokenizer.encode(prefix, add_special_tokens=False)),
                           context_full_tokens=len(tokenizer.encode(context, add_special_tokens=False)),
                           context_full_sha256=proof["original_context_sha256"],
                           context_prefix_sha256=hashlib.sha256(prefix.encode()).hexdigest(),
                           context_trim="exact original Unicode codepoint prefix then native full-chat verification",
                           boundary_probe_count=len(proof["probes"]))


def render_context(records):
    return "Independent training-domain reference questions follow.\n" + "".join(
        "\nReference question:\n" + r["text"] + "\n" for r in records)


def fit_context(tokenizer, target_text, contexts, context_pool):
    """At a proven gap, prepend <=3 NEW same-partition TRAIN records; no retry loop."""
    contexts, rejected = list(contexts), []
    require(contexts and all(r["source"]["split"] == "train" for r in contexts),
            "real TRAIN context required")
    for attempt in range(MAX_CONTEXT_CANDIDATES):
        context = render_context(contexts)
        try:
            text, ids, trim = fixed_chat(tokenizer, context, target_text)
            trim.update(boundary_candidate_attempt=attempt, maximum_context_candidates=MAX_CONTEXT_CANDIDATES,
                        rejected_context_candidates=rejected,
                        context_selection="initial TRAIN context; on exact-boundary gap prepend next unused same-partition TRAIN record")
            return text, ids, trim, contexts
        except NoExactBoundary as error:
            rejected.append(dict(attempt=attempt, **error.audit,
                                 context_records=[r["source"] for r in contexts]))
            if attempt + 1 == MAX_CONTEXT_CANDIDATES:
                raise ValueError("all four bounded TRAIN context candidates lack exact1024 boundary; " +
                                 json.dumps(rejected, sort_keys=True)) from error
            try:
                extra = next(context_pool)
            except StopIteration as exhausted:
                raise ValueError("no unused same-partition TRAIN reference after exact-boundary gap") from exhausted
            require(extra["source"]["split"] == "train" and extra["domain"] == contexts[0]["domain"] and
                    extra["key"] not in {r["key"] for r in contexts}, "new context provenance/identity mismatch")
            # Iterator consumption permanently removes each inspected record from
            # all later candidates. Retained old+new records remain in row provenance.
            contexts.insert(0, extra)
    raise AssertionError("finite candidate loop exhausted unexpectedly")


def question(domain, record):
    if domain == "math":
        return str(record["problem"])
    if domain == "code":
        return str(record["question"])
    choices = record["choices"]
    require(len(choices["label"]) == len(choices["text"]), "ARC choice cardinality differs")
    return str(record["question"]) + "\n" + "\n".join(
        str(label) + ": " + str(text) for label,text in zip(choices["label"],choices["text"]))


def source_record(artifact, number, raw):
    domain = artifact["domain"]
    if domain == "general":
        rid = str(raw["id"])
    elif domain == "code":
        rid = str(raw.get("problem_id", number))
    else:
        rid = str(Path(artifact["path"]).parent) + ":" + str(number)
    record_hash = digest(raw)
    text = question(domain,raw)
    return dict(domain=domain, text=text, source=dict(
        dataset=artifact["dataset"], split="train", revision=artifact["revision"],
        record_id=rid, record_sha256=record_hash, artifact_sha256=artifact["sha256"],
        artifact_path=artifact["artifact_path"], license=artifact["license"],
        url=artifact["resolve_url"], provenance_url=artifact["provenance_url"]),
        key=(artifact["dataset"],rid))


def read_training(index_path):
    path = Path(index_path).resolve()
    require(path.is_relative_to(INPUT_ROOT.resolve()), "index outside approved input root")
    actual = json.loads(path.read_text())
    expected = index_for(path.parent)
    require(actual == expected, "source index differs from exact publisher pins/local bytes")
    pools = {d: [] for d in ("math","code","general")}
    seen = set()
    for artifact in actual["artifacts"]:
        if artifact["format"] == "parquet":
            import pyarrow.parquet as pq
            table = pq.read_table(artifact["artifact_path"])
            records = enumerate(table.to_pylist())
        else:
            records = ((i,json.loads(line)) for i,line in
                       enumerate(Path(artifact["artifact_path"]).read_text().splitlines()) if line.strip())
        for number,raw in records:
            row = source_record(artifact,number,raw)
            require(row["key"] not in seen, "duplicate source identity")
            seen.add(row["key"])
            pools[row["domain"]].append(row)
    return pools


def build_rows(tokenizer, pools, on_boundary_failure=None, legacy_boundaries=False):
    rows, used = [], set()
    special = tuple(t for t in getattr(tokenizer,"all_special_tokens",()) if t)
    for domain in ("math","code","general"):
        available = [r for r in pools[domain] if r["text"].strip() and
                     not any(t in r["text"] for t in special)]
        ordered = sorted(available,key=lambda r:digest([SEED,r["source"]["dataset"],
                                                       r["source"]["record_id"],r["source"]["record_sha256"]]))
        for part_index,split in enumerate(SPLITS):
            pool = ordered[part_index::3]  # disjoint raw-record pools BEFORE selecting context
            targets = []
            for record in pool:
                base = native_chat(tokenizer,"\nTarget problem:\n"+record["text"]+"\nSolve the target problem.")
                if len(base) < 900:
                    targets.append(record)
                    if len(targets) == 4:
                        break
            require(len(targets) == 4, "insufficient admissible TRAIN targets: "+domain+"/"+split)
            target_keys = {r["key"] for r in targets}
            context_pool = iter(r for r in pool if r["key"] not in target_keys)
            for i,target in enumerate(targets):
                context = "Independent training-domain reference questions follow.\n"
                contexts = []
                suffix = "\nTarget problem:\n"+target["text"]+"\nSolve the target problem."
                while len(native_chat(tokenizer,context+suffix)) < 1100:
                    try:
                        record = next(context_pool)
                    except StopIteration as error:
                        raise ValueError("insufficient disjoint TRAIN context: "+domain+"/"+split) from error
                    contexts.append(record)
                    context += "\nReference question:\n"+record["text"]+"\n"
                try:
                    if legacy_boundaries:
                        text,ids,trim = _legacy_fixed_chat(tokenizer,context,target["text"])
                    else:
                        text,ids,trim,contexts = fit_context(tokenizer,target["text"],contexts,context_pool)
                        trim["selection_identity_sha256"] = digest(
                            [SEED, domain, split, i, target["source"], [r["source"] for r in contexts],
                             token_digest(ids), trim["boundary_candidate_attempt"]])
                except ValueError as error:
                    if on_boundary_failure is not None:
                        on_boundary_failure(tokenizer, context, target, contexts,
                                            domain, split, i, str(error))
                    raise
                all_records = [target] + contexts
                for r in all_records:
                    require(r["key"] not in used, "TRAIN record leaked across targets/partitions")
                    used.add(r["key"])
                rows.append(dict(id=f"{domain}-{split}-{i:02d}", domain=domain,split=split,
                                 input_ids=ids,input_ids_sha256=token_digest(ids),
                                 prompt_text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                                 source=target["source"],
                                 context_records=[r["source"] for r in contexts],
                                 prompt_text=text,context_policy=trim))
    require(len(rows) == 36, "not36 target prompts")
    return rows


def character_probes(tokenizer, context, target, length=1024, radius=512):
    """Diagnostic only: exact ORIGINAL codepoint prefixes, bounded binary+local search."""
    suffix = "\nTarget problem:\n" + target + "\nSolve the target problem."
    require(len(context) <= 65536 and radius == 512, "diagnostic character budget exceeded")
    counts = {}
    def count(end):
        if end not in counts:
            counts[end] = len(native_chat(tokenizer, context[:end] + suffix))
        return counts[end]
    left, right = 0, len(context)
    while right - left > 1:
        middle = (left + right) // 2
        if count(middle) < length:
            left = middle
        else:
            right = middle
    # BPE prefix counts are not assumed monotonic; scan a bounded neighborhood
    # even when binary crossing skips an exact length. No replacement characters.
    candidates = (range(max(1, left - radius), min(len(context), right + radius) + 1))
    for end in candidates:
        count(end)
    return dict(binary_bracket=[left, right], radius_codepoints=radius,
                probes=[[end, counts[end]] for end in sorted(counts)],
                exact_codepoint_boundaries=[end for end in sorted(counts) if counts[end] == length],
                original_context_sha256=hashlib.sha256(context.encode()).hexdigest())


def boundary_diagnostic(tokenizer, context, target):
    """Reproduce old failure; describe token-roundtrip gaps separately from raw text."""
    suffix = "\nTarget problem:\n" + target + "\nSolve the target problem."
    base_length = len(native_chat(tokenizer, suffix))
    tokens = tokenizer.encode(context, add_special_tokens=False)
    estimate = 1024 - base_length
    probes = []
    for distance in range(257):
        for count in ((estimate,) if distance == 0 else (estimate - distance, estimate + distance)):
            if not 1 <= count <= len(tokens):
                continue
            prefix = tokenizer.decode(tokens[:count], skip_special_tokens=False,
                                      clean_up_tokenization_spaces=False)
            probes.append(dict(context_tokens=count, decoded_codepoints=len(prefix),
                               replacement_character="\ufffd" in prefix,
                               exact_original_prefix=context.startswith(prefix),
                               native_chat_tokens=len(native_chat(tokenizer, prefix + suffix))))
    return dict(base_tokens=base_length, full_context_tokens=len(tokens),
                full_chat_tokens=len(native_chat(tokenizer, context + suffix)), estimate=estimate,
                token_roundtrip_probes=probes,
                token_roundtrip_exact_counts=[p["context_tokens"] for p in probes
                                             if not p["replacement_character"] and p["native_chat_tokens"] == 1024],
                raw_character_probes=character_probes(tokenizer, context, target))


def diagnose(index_path, output):
    """Parent-run NO-device investigation; not a manifest and not model execution."""
    import glob
    import os
    require(os.environ.get("DAMP_NO_DEVICE_TOKENIZER_GATE") == "1" and
            os.environ.get("ASCEND_RT_VISIBLE_DEVICES", "") == "" and
            not glob.glob("/dev/davinci[0-9]*"), "boundary diagnosis requires explicit NO-device process")
    output = Path(output).resolve()
    require(output.is_relative_to(INPUT_ROOT.resolve()) and not output.exists(),
            "diagnostic output outside root or already exists")
    for filename, sha in MODEL_HASHES.items():
        require(file_digest(Path(MODEL) / filename) == sha, "model/tokenizer changed")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=False, local_files_only=True)
    pools = read_training(index_path)
    captured = []
    def record(tok, context, target, contexts, domain, split, index, error):
        value = dict(schema="damp-boundary-diagnostic/v1", status="old-builder-failure-reproduced",
                     scope="NO-device-tokenizer-only-not-calibration", selection_seed=SEED,
                     builder_sha256=file_digest(__file__), source_index_sha256=file_digest(index_path),
                     domain=domain, split=split, target_index=index, target_source=target["source"],
                     context_sources=[r["source"] for r in contexts],
                     target_text_sha256=hashlib.sha256(target["text"].encode()).hexdigest(),
                     context_text_sha256=hashlib.sha256(context.encode()).hexdigest(), error=error,
                     detail=boundary_diagnostic(tok, context, target["text"]))
        with output.open("xb") as stream:
            stream.write(canonical(value) + b"\n")
        captured.append(value)
    try:
        build_rows(tokenizer, pools, on_boundary_failure=record, legacy_boundaries=True)
    except ValueError:
        require(len(captured) == 1, "failure occurred outside fixed_chat; no diagnostic produced")
        return captured[0]
    raise ValueError("old deterministic failure did not reproduce; do not claim diagnosis")


def build(index_path, output):
    output = Path(output).resolve()
    require(output.is_relative_to(INPUT_ROOT.resolve()) and not output.exists(),
            "output outside root or already exists")
    for filename,sha in MODEL_HASHES.items():
        require(file_digest(Path(MODEL)/filename) == sha, "model/tokenizer changed")
    pools = read_training(index_path)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL,trust_remote_code=False,local_files_only=True)
    manifest = base_manifest("full")
    manifest["rows"] = build_rows(tokenizer,pools)
    manifest["prompt_builder_sha256"] = file_digest(__file__)
    manifest["source_index_sha256"] = file_digest(index_path)
    manifest["selection_seed"] = SEED
    manifest["builder_policy"] = "original-codepoint-boundary-with-at-most4-disjoint-TRAIN-context-candidates/v2"
    manifest["prompt_construction"] = (
        "project-derived disjoint TRAIN target/context records; native Qwen3.6 template "
        "enable_thinking=False; truncate exact original Unicode context prefixes only, "
        "verify native full chat to exactly1024 IDs; on proven gap prepend at most3 next "
        "unused same-partition TRAIN references; preserve complete target and assistant prefix; "
        "no padding, no final-evaluation data, no author-exact sample claim")
    validate_manifest(manifest)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("xb") as stream:
        stream.write(canonical(manifest)+b"\n")
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-index",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--diagnose-boundaries", action="store_true",
                   help="reproduce first fixed_chat failure and emit exclusive tokenizer-only diagnostic")
    a=p.parse_args()
    if a.diagnose_boundaries:
        result=diagnose(a.source_index,a.output)
        print(json.dumps(dict(status=result["status"], domain=result["domain"],split=result["split"],
                              target_index=result["target_index"],
                              old_exact=result["detail"]["token_roundtrip_exact_counts"],
                              raw_character_exact=result["detail"]["raw_character_probes"]["exact_codepoint_boundaries"],
                              diagnostic_sha256=file_digest(a.output)),sort_keys=True))
        return
    result=build(a.source_index,a.output)
    print(json.dumps(dict(rows=len(result["rows"]),input_tokens=1024,output_tokens=4096,
                          provenance=result["provenance"],source_index_sha256=result["source_index_sha256"],
                          manifest_sha256=digest(result)),sort_keys=True))


if __name__ == "__main__":
    main()
