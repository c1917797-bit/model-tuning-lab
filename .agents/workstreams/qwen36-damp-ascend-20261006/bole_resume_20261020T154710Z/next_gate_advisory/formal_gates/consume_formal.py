"""Pure-stdlib, default-OFF final evidence reader. No inference or NPU calls.

Composes predeclared executed independent validators; see EVIDENCE_SCHEMA.md.
This source contains no official-scoring substitute and no measured data.
"""
import argparse
import hashlib
import json
import math
import os
import statistics
from fractions import Fraction
from pathlib import Path

MAX_JSON_BYTES = 128 * 2**20
TASKS = ("GSM8K", "HumanEval", "MMLU", "LongBench-v2")
PROTOCOLS = {
 "USER_72H_PROTOCOL_20261009.json": (1379, "b605d2a01118c4087e3450b3d800ef5bf40f6d0f882c1606a1e9117ed56151d1"),
 "NEW24H_AUTHORITY_20261016.json": (3481, "e8c373b6664a4bdd80012428b686227a6f15c0535b3c57a7654fb7996c02cf28"),
}
_HASHED = {}


def need(value, message):
 if not value: raise ValueError(message)


def integer(value, minimum=0):
 need(type(value) is int and value >= minimum, "nonnegative integer ABI")
 return value


def ref_key(reference):
 need(type(reference) is dict and set(reference) == {"path", "bytes", "sha256"}, "exact Ref3")
 integer(reference["bytes"])
 digest = reference["sha256"]
 need(type(digest) is str and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest), "SHA256 ABI")
 return reference["bytes"], digest


def same_ref(a, b):
 return ref_key(a) == ref_key(b)


def checked(reference):
 size, digest = ref_key(reference)
 path = Path(reference["path"])
 need(path.is_absolute() and path.is_file()
      and not any(p.is_symlink() for p in (path, *path.parents)), "ordinary absolute Ref3 path")
 before = path.stat()
 stamp = before.st_ino, before.st_size, before.st_mtime_ns
 key = str(path), size, digest
 if _HASHED.get(key) != stamp:
  actual = hashlib.sha256()
  with path.open("rb") as handle:
   for block in iter(lambda: handle.read(2**20), b""): actual.update(block)
  after = path.stat()
  need(stamp == (after.st_ino, after.st_size, after.st_mtime_ns)
       and before.st_size == size and actual.hexdigest() == digest, "stable actual Ref3 bytes")
  _HASHED[key] = stamp
 return path


def _unique(pairs):
 result = {}
 for key, value in pairs:
  need(key not in result, "duplicate JSON key")
  result[key] = value
 return result


def _constant(value):
 raise ValueError("nonfinite JSON constant " + value)


def obj(reference):
 path = checked(reference)
 need(reference["bytes"] <= MAX_JSON_BYTES, "bounded individual JSON document")
 wire = path.read_bytes()
 need(len(wire) == reference["bytes"] and hashlib.sha256(wire).hexdigest() == reference["sha256"], "JSON bytes still match Ref3")
 return json.loads(wire, object_pairs_hook=_unique, parse_constant=_constant)


def all_refs(value, depth=0):
 need(depth <= 32, "bounded reference nesting")
 if type(value) is dict:
  if set(value) == {"path", "bytes", "sha256"}: checked(value)
  else:
   for item in value.values(): all_refs(item, depth+1)
 elif type(value) is list:
  for item in value: all_refs(item, depth+1)


def rational(value):
 need(type(value) is dict and set(value) == {"n", "d"}, "exact rational ABI")
 integer(value["n"]); integer(value["d"], 1)
 return Fraction(value["n"], value["d"])


def exact(value):
 return {"n": value.numerator, "d": value.denominator, "decimal": float(value)}


def losses(baseline, candidate):
 need(0 <= baseline <= 1 and 0 <= candidate <= 1, "normalized task metrics")
 positive = max(Fraction(0), baseline-candidate)
 relative = None if baseline == 0 else 100*positive/baseline
 return dict(baseline=exact(baseline), candidate=exact(candidate),
             signed_delta_pp=exact(100*(candidate-baseline)), pp_loss=exact(100*positive),
             relative_loss_percent=None if relative is None else exact(relative),
             passed=bool(100*positive <= 1 and relative is not None and relative <= 1))


def weighted_task_score(items, case_map, outputs):
 seen = set(); numerator = denominator = Fraction(0)
 for item in items:
  case_id = item["case_id"]
  need(case_id in outputs and case_id not in seen and same_ref(item["output"],outputs[case_id]), "each scored actual completion exactly once")
  value, weight = rational(item["value"]), rational(case_map[case_id]["metric_weight"])
  need(value in (0,1) and weight > 0, "official binary item outcome and frozen positive metric weight")
  seen.add(case_id); numerator += value*weight; denominator += weight
 need(seen == set(outputs) and denominator > 0, "no excluded failed or truncated scored cases")
 return numerator/denominator


def summarize(values):
 need(values, "nonempty metric summary")
 ordered = sorted(values)
 return dict(mean=float(sum(values)/len(values)), median=float(statistics.median(values)),
             p95_nearest_rank=float(ordered[math.ceil(.95*len(values))-1]))


def pair_summary(pairs):
 need(len(pairs) == 3, "exact three formal matched rounds")
 ratios = [on["throughput"]/off["throughput"] for off, on in pairs]
 off_pooled = Fraction(sum(off["output_tokens"] for off, _ in pairs)*10**9,
                       sum(off["elapsed_ns"] for off, _ in pairs))
 on_pooled = Fraction(sum(on["output_tokens"] for _, on in pairs)*10**9,
                      sum(on["elapsed_ns"] for _, on in pairs))
 return dict(pair_ratios=[exact(v) for v in ratios],
             pooled_token_count_time_ratio=exact(on_pooled/off_pooled),
             arithmetic_mean_ratio=exact(sum(ratios)/3), median_ratio=exact(statistics.median(ratios)),
             geometric_mean_ratio=math.exp(sum(math.log(float(v)) for v in ratios)/3),
             prospective_all_three_pairs_pass=all(v >= Fraction(11, 10) for v in ratios))


def peak_inflight(intervals):
 events = [(start, 1) for start, _ in intervals] + [(end, -1) for _, end in intervals]
 current = peak = 0
 for _, delta in sorted(events):
  current += delta
  need(current >= 0, "valid request intervals")
  peak = max(peak, current)
 need(current == 0, "all requests completed")
 return peak


def validate_policy(manifest):
 policy_ref = manifest["policy"]
 p = obj(policy_ref)
 need(p["schema"] == "bole.formal-acceptance-policy/v1" and p["prepared_only"] is False,
      "actual fully populated policy frozen before measurements; proposal is not executable evidence")
 need(p["formal_rounds"] == 3 and p["performance_output_tokens"] == 1024
      and p["task_max_tokens"] == 2048 and set(p["tasks"]) == set(TASKS)
      and rational(p["throughput_threshold"]) == Fraction(11, 10), "unaltered protocol thresholds/task union")
 need(p["aggregation"]["prospective_acceptance"] == "all_three_pair_ratios"
      and p["aggregation"]["protocol_specifies_aggregation"] is False,
      "explicit supported prospective aggregation, no retrospective selection")
 need(p["physical_npus"] == [4,5,6,7] and p["protected_npus"] == [0,1,2,3], "authorized hardware scope")
 need(p["timing"]["arrival_policy"] == "closed_loop"
      and p["timing"]["profile_off"] is True and p["timing"]["diagnostic_capture"] is False
      and p["timing"]["warmup_required"] is True, "frozen common timing policy")
 need(p["timing"]["throughput"] == "total_actual_output_tokens/(last_measured_end_ns-first_measured_submit_ns)"
      and p["timing"]["TTFT"] == "first_nonempty_token_delta_ns-submit_ns"
      and p["timing"]["TPOT"] == "(last_nonempty_token_delta_ns-first_nonempty_token_delta_ns)/(output_tokens-1)"
      and p["timing"]["clock"] == "CLOCK_MONOTONIC", "prospective definitions match actual consumer arithmetic")
 need(rational(p["accuracy"]["max_pp_loss"]) == 1
      and rational(p["accuracy"]["max_relative_loss_percent"]) == 1
      and p["accuracy"]["baseline_zero_policy"] == "block_undefined", "conservative original accuracy limits")
 for name, expected in PROTOCOLS.items():
  need(ref_key(manifest["protocols"][name]) == expected
       and (p["protocols"][name]["bytes"], p["protocols"][name]["sha256"]) == expected,
       "unchanged exact historical protocol " + name)
  obj(manifest["protocols"][name])
 all_refs(p)
 authority = obj(p["current_authority"])
 need(authority["authorization_text"] == "请帮我继续穿刺一直到成功"
      and authority["historical_sources_outputs_cutoffs_immutable"] is True
      and authority["admission_horizon_is_user_deadline"] is False,
      "current user authority preserved separately from historical/technical cutoffs")
 composed = p["composition"]["applies"]
 need(type(composed) is bool, "prospective explicit composition decision")
 decision = obj(p["composition"]["decision_ref"])
 need(decision["composition_applies"] is composed and type(decision["rationale"]) is str
      and len(decision["rationale"]) >= 20, "source-bound actual composition rationale")
 variants = ("D", "A", "B", "A+B") if composed else ("OFF", "ON")
 need(set(p["variant_profiles"]) == set(variants), "complete real declared variants")
 for kind in ("model_qualification", "runtime", "lineage", "activation", "resources", "prompt_render", "task_score"):
  reader = obj(p["readers"][kind]); all_refs(reader)
  need(reader["schema"] == "bole.independent-reader-source/v1", "actual audited validator source package")
 if composed:
  need(set(p["composition"]["component_sources"]) == {"A", "B"}, "actual A/B source mapping")
  obj(p["readers"]["composition"])
 stack = obj(p["common_stack"])
 need(p["image_id"] == "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
      and p["model_config_sha256"] == "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c", "original actual image and protocol-pinned model")
 need(stack["schema"] == "bole.formal-common-stack/v1" and stack["image_id"] == p["image_id"]
      and stack["model_config_sha256"] == p["model_config_sha256"]
      and stack["model_type"] == "qwen3_5" and stack["tp"] == 4
      and stack["physical_npus"] == [4,5,6,7], "actual common model/image/TP4 stack")
 weights = obj(stack["weights_full_manifest"])
 need(weights["config_only"] is False and len(weights["weight_files"]) > 0,
      "retained full checkpoint manifest, not config hash alone")
 for weight in weights["weight_files"]: ref_key(weight)
 return p, variants


def proof(entry, kind, subject, p):
 result = obj(entry["result"]); owner = obj(entry["owner"])
 expected = p["readers"][kind]
 need(result["schema"] == "bole.formal-independent-proof/v1" and result["kind"] == kind
      and result["passed"] is True and same_ref(result["subject"], subject)
      and same_ref(result["reader_source"], expected), "executed exact independent proof subject/source/kind")
 need(same_ref(result["source_before"], expected) and same_ref(result["source_after"], expected), "reader source unchanged")
 inputs = {ref_key(r) for r in result["inputs"]}
 need(ref_key(subject) in inputs, "actual proof reads its subject")
 for reference in result["inputs"]: checked(reference)
 need(owner["schema"] == "bole.formal-CPU-owner/v1" and owner["primary"] is None
      and owner["secondary"] == [] and owner["exit_code"] == 0
      and owner["devices"] == owner["device_nodes"] == [] and owner["image_id"] == p["image_id"],
      "real owned Devices[] independent CPU validation completion")
 need(same_ref(owner["reader_source"], expected)
      and same_ref(owner["source_before"], expected) and same_ref(owner["source_after"], expected)
      and ref_key(entry["result"]) in {ref_key(r) for r in owner["outputs"]}
      and inputs <= {ref_key(r) for r in owner["inputs"]}, "owned execution source/input/output lineage")
 identity = result["producer_identity"]
 need(identity == owner["identity"] and integer(identity["pid"], 1)
      and integer(identity["start_ticks"], 1) and identity["cgroup"] and identity["boot_id"],
      "actual stable independent CPU producer identity")
 need(integer(owner["finished_epoch_ns"], 1) > integer(owner["started_epoch_ns"], 1), "actual CPU execution lifetime")
 all_refs(owner)
 return result


def common_record(record, ref, entry, p, manifest, purpose):
 need(same_ref(record["stack"], p["common_stack"])
      and same_ref(record["candidate_source"], p["candidate_source"])
      and same_ref(record["feature_profile"], p["variant_profiles"][record["variant"]]), "matched actual stack/candidate/feature profile")
 source = obj(record["source_packet"])
 need(source["schema"] == "bole.formal-source/v1" and source["purpose"] == purpose
      and source["variant"] == record["variant"] and same_ref(source["policy"], manifest["policy"])
      and same_ref(source["current_authority"], p["current_authority"])
      and same_ref(source["candidate_source"], p["candidate_source"])
      and same_ref(source["stack"], p["common_stack"])
      and same_ref(source["feature_profile"], record["feature_profile"]), "prospective exact launched source packet")
 need(integer(source["created_epoch_ns"], 1) <= integer(record["started_epoch_ns"], 1)
      < integer(record["finished_epoch_ns"], 1), "actual freeze precedes measurement lifetime")
 runtime = proof(entry["proofs"]["runtime"], "runtime", ref, p)
 for key in ("profile_off", "diagnostics_off", "unchanged_image", "weights_full_identity_verified",
             "explicit_optin", "no_training", "no_distillation", "source_packet_frozen_before_launch"):
  need(runtime[key] is True, "actual runtime gate " + key)
 need(same_ref(runtime["stack"], p["common_stack"]) and same_ref(runtime["source_packet"], record["source_packet"]), "actual runtime/launch source join")
 resources = proof(entry["proofs"]["resources"], "resources", ref, p)
 for key in ("observed_exclusive_target", "protected_untouched", "monitoring_complete", "owned_cleanup_complete"):
  need(resources[key] is True, "actual resource gate " + key)
 need(resources["physical_npus"] == [4,5,6,7] and resources["protected_npus"] == [0,1,2,3], "actual monitored physical ownership")
 lineage = proof(entry["proofs"]["lineage"], "lineage", ref, p)
 need(lineage["all_actual_frontend_engine_worker_joins"] is True
      and lineage["all4_ranks"] is True and lineage["raw_records_independently_parsed"] is True,
      "independent raw request/response/frontend/engine/worker joins")
 return source


def stream_request(ref, expected, phase, clock):
 r = obj(ref)
 need(r["schema"] == "bole.formal-stream-request/v1" and r["phase"] == phase
      and r["request_key"] == expected["request_key"] and same_ref(r["clock"], clock), "actual declared stream request and clock")
 prompt = expected["prompt_token_ids"]
 need(prompt and all(type(x) is int and x >= 0 for x in prompt), "actual frozen prompt token IDs")
 body = obj(r["request_body"]); checked(r["raw_stream"])
 need(body == obj(expected["request_body"]), "every actual sampling/body field matches frozen performance request")
 need(body["prompt"] == prompt == r["prompt_token_ids"] and body["max_tokens"] == 1024
      and body["ignore_eos"] is True and body["stream"] is True
      and body["return_token_ids"] is True and body["n"] == 1
      and body["temperature"] == 0 and body["top_p"] == 1, "actual matched fixed1024 streaming request")
 need(r["http_status"] == 200 and r["error"] is None and r["done_received"] is True
      and r["finish_reason"] == "length", "complete actual fixed-length HTTP/SSE response")
 start, end = integer(r["submit_ns"], 1), integer(r["end_ns"], 1)
 need(end > start, "positive actual request duration")
 tokens, bearing, previous = [], [], start
 for ordinal, event in enumerate(r["events"]):
  at = integer(event["received_ns"], 1)
  need(event["ordinal"] == ordinal and previous <= at <= end
       and event["response_id"] == r["response_id"] and event["choice_index"] == 0, "actual ordered same-response SSE events")
  delta = event["token_ids"]
  need(type(delta) is list and all(type(x) is int and x >= 0 for x in delta), "actual SSE token delta ABI")
  tokens.extend(delta)
  if delta: bearing.append((at, len(delta)))
  previous = at
 need(len(tokens) == 1024 and tokens == r["final_output_token_ids"]
      and r["usage"]["completion_tokens"] == 1024 and r["usage"]["prompt_tokens"] == len(prompt), "all actual output token IDs/counts, no partial requests")
 return dict(request_key=r["request_key"], engine_request_id=r["engine_request_id"], phase=phase,
             submit_ns=start, end_ns=end, output_tokens=1024,
             ttft_ns=Fraction(bearing[0][0]-start),
             tpot_ns=Fraction(bearing[-1][0]-bearing[0][0], 1023),
             token_bearing_chunks=len(bearing), first_chunk_tokens=bearing[0][1])


def activation(entry, subject, p, rows, profile_ref, performance):
 result = proof(entry, "activation", subject, p)
 profile = obj(profile_ref)
 need(profile["schema"] == "bole.formal-feature-profile/v1"
      and profile["expect_bole_decode"] in ("all", "none", "component-only")
      and same_ref(result["feature_profile"], profile_ref), "actual declared feature profile")
 actual = result["rows"]
 keys = [(r["phase"], r["request_key"]) for r in rows]
 need(len(actual) == len(keys) and {(r["phase"],r["request_key"]) for r in actual} == set(keys), "activation evidence for every actual request")
 mapped = {(r["phase"], r["request_key"]): r for r in rows}
 for row in actual:
  expected = mapped[row["phase"], row["request_key"]]
  need(row["engine_request_id"] == expected["engine_request_id"] and len(row["ranks"]) == 4
       and {x["rank"] for x in row["ranks"]} == {0,1,2,3}, "all4 actual ranks and genuine engine request identity")
  for rank in row["ranks"]:
   required = integer(rank["required_decode_inputs"])
   if performance: need(required == 1023, "exact every fixed1024 decode input accounted")
   else: need(required <= 2048, "bounded actual task native decode accounting")
   bole, native = integer(rank["bole_processed_inputs"]), integer(rank["native_processed_inputs"])
   need(integer(rank["unattributed_decode_inputs"]) == 0 and bole+native == required, "no hidden/unattributed decode fallback")
   if profile["expect_bole_decode"] == "all": need(bole == required and native == 0, "all eligible decode inputs actually executed through BOLE")
   elif profile["expect_bole_decode"] == "none": need(bole == 0 and native == required, "real feature-OFF baseline")
   need(integer(rank["tree_steps"]) > 0 if bole else rank["tree_steps"] == 0, "real tree steps match activation")
   for component in profile["required_components"]:
    need(integer(rank["component_calls"][component]) > 0 if required else rank["component_calls"][component] == 0, "actual required composition component calls")
  need(len({rank["required_decode_inputs"] for rank in row["ranks"]}) == 1, "all4 same actual decode accounting")
 return True


def perf_run(entry, p, manifest, workload):
 ref = entry["record"]; r = obj(ref)
 need(r["schema"] == "bole.formal-perf-run/v1" and 1 <= integer(r["round_id"],1) <= 3, "actual formal round")
 source = common_record(r, ref, entry, p, manifest, "performance")
 need(same_ref(r["workload"], manifest["workload"])
      and same_ref(source["workload"], manifest["workload"]), "all variants use exact frozen workload")
 clock = obj(r["clock"])
 need(clock["clock"] == "CLOCK_MONOTONIC" and clock["boot_id"] and clock["time_namespace"], "actual unambiguous monotonic clock origin")
 need(len(r["request_records"]) == len(workload["measured_requests"])
      and len(r["warmup_records"]) == len(workload["warmup_requests"]), "all declared measured and warmup requests")
 rows = [stream_request(ref, expected, "measured", r["clock"])
         for ref, expected in zip(r["request_records"], workload["measured_requests"])]
 warm = [stream_request(ref, expected, "warmup", r["clock"])
         for ref, expected in zip(r["warmup_records"], workload["warmup_requests"])]
 need([x["submit_ns"] for x in rows] == sorted(x["submit_ns"] for x in rows)
      and [x["submit_ns"] for x in warm] == sorted(x["submit_ns"] for x in warm), "actual request dispatch order matches frozen input order")
 need(rows and warm and max(x["end_ns"] for x in warm) <= min(x["submit_ns"] for x in rows), "real warmup completed before measurement")
 need(len({x["engine_request_id"] for x in rows+warm}) == len(rows+warm), "distinct actual request identities, no hidden retries/reuse")
 concurrency = peak_inflight([(x["submit_ns"],x["end_ns"]) for x in rows])
 need(concurrency == workload["concurrency"], "actual measured concurrency matches prospective profile")
 activation(entry["proofs"]["activation"], ref, p, rows+warm, r["feature_profile"], True)
 elapsed = max(x["end_ns"] for x in rows)-min(x["submit_ns"] for x in rows)
 count = sum(x["output_tokens"] for x in rows)
 return dict(round_id=r["round_id"], variant=r["variant"], output_tokens=count, elapsed_ns=elapsed,
             throughput=Fraction(count*10**9,elapsed), concurrency=concurrency,
             TTFT_seconds=summarize([x["ttft_ns"]/10**9 for x in rows]),
             TPOT_seconds=summarize([x["tpot_ns"]/10**9 for x in rows]),
             per_request=[dict(request_key=x["request_key"],TTFT_seconds=float(x["ttft_ns"]/10**9),
                TPOT_seconds=float(x["tpot_ns"]/10**9),token_bearing_chunks=x["token_bearing_chunks"],
                first_chunk_tokens=x["first_chunk_tokens"]) for x in rows])


def task_run(entry, p, manifest):
 ref = entry["record"]; r = obj(ref)
 need(r["schema"] == "bole.formal-task-run/v1" and r["task"] in TASKS and r["stage"] in ("smoke","full"), "actual frozen task/stage")
 source = common_record(r, ref, entry, p, manifest, "task_"+r["stage"])
 data = obj(r["dataset_manifest"]); profile = obj(r["generation_profile"])
 need(data["schema"] == "bole.formal-task-dataset/v1" and data["task"] == r["task"]
      and data["complete_declared_split"] is True and data["official_source"] and data["source_revision"] and data["split"] and data["metric"], "complete frozen official dataset/split/metric provenance")
 checked(data["official_snapshot"]); checked(data["scorer_source"]); obj(r["prompt_policy"])
 for field in ("dataset_manifest","prompt_policy","generation_profile"):
  need(same_ref(source[field],r[field]), "actual task/scorer/prompt settings frozen before launch")
 need(same_ref(source["scorer_source"],data["scorer_source"]), "official scorer source frozen before inference")
 if r["stage"] == "full": need(same_ref(source["smoke_record"],r["smoke_record"]), "full launch binds already consumed smoke")
 need(profile["thinking"] is False and profile["max_tokens"] == 2048 and profile["normal_eos"] is True
      and profile["temperature"] == 0 and profile["top_p"] == 1 and profile["n"] == 1
      and profile["stop"] == profile["stop_token_ids"] == [] and profile["return_token_ids"] is True,
      "actual final thinkingOFF/max2048/normalEOS matched generation profile")
 cases = data["cases"]
 need(cases and len({x["case_id"] for x in cases}) == len(cases), "unique complete frozen official cases")
 expected_ids = [x["case_id"] for x in cases] if r["stage"] == "full" else data["smoke_case_ids"]
 need(expected_ids and len(set(expected_ids)) == len(expected_ids)
      and set(expected_ids) <= {x["case_id"] for x in cases}, "frozen nonempty smoke/full case coverage")
 case_map = {x["case_id"]:x for x in cases}; outputs = {}; rows = []; truncated = 0; max_context = 0
 for output_ref in r["outputs"]:
  output = obj(output_ref); case_id = output["case_id"]
  need(output["schema"] == "bole.formal-task-output/v1" and case_id in expected_ids and case_id not in outputs
       and output["phase"] == r["stage"] and output["http_status"] == 200
       and output["error"] is None and output["stream_complete"] is True, "exact actual task completion, no missing/duplicate/retried rows")
  case = case_map[case_id]; prompt = obj(case["prompt_record"])
  checked(case["source_item"]); checked(case["gold"]); checked(output["raw_response"])
  ids = prompt["token_ids"]
  need(prompt["schema"] == "bole.formal-prompt/v1" and prompt["task"] == r["task"]
       and prompt["case_id"] == case_id and ids == output["prompt_token_ids"]
       and ids and all(type(x) is int and x >= 0 for x in ids), "actual source-pinned rendered task token inputs")
  body = obj(output["request_body"])
  need(body == obj(prompt["request_body"]), "every actual task sampling/body field matches prospective prompt/profile")
  need(body["prompt"] == ids and body["max_tokens"] == 2048 and body["ignore_eos"] is False
       and body["temperature"] == 0 and body["top_p"] == 1 and body["n"] == 1
       and body["return_token_ids"] is True, "actual normalEOS task request body")
  tokens = output["output_token_ids"]
  need(type(tokens) is list and len(tokens) <= 2048 and all(type(x) is int and x >= 0 for x in tokens), "actual bounded task output token IDs")
  if output["finish_reason"] == "length":
   need(output["termination"] == "max_tokens" and len(tokens) == 2048, "actual truncated task completion kept in scoring")
   truncated += 1
  else: need(output["finish_reason"] == "stop" and output["termination"] == "eos", "actual normal EOS, no artificial stop policy")
  max_context = max(max_context,len(ids)+2048)
  outputs[case_id] = output_ref
  rows.append(dict(request_key=output["request_key"],phase=r["stage"],engine_request_id=output["engine_request_id"]))
 need(set(outputs) == set(expected_ids) and len(rows) == len(expected_ids), "every frozen task case retained in denominator")
 need(len({x["request_key"] for x in rows}) == len(rows)
      and len({x["engine_request_id"] for x in rows}) == len(rows), "unique genuine task request identities")
 render = proof(entry["proofs"]["prompt_render"], "prompt_render", ref, p)
 need(render["actual_thinking_disabled"] is True and render["all_actual_token_inputs_joined"] is True
      and same_ref(render["prompt_policy"], r["prompt_policy"]), "thinkingOFF at actual tokenizer/template boundary, not output stripping")
 activation(entry["proofs"]["activation"], ref, p, rows, r["feature_profile"], False)
 scoring = proof(entry["proofs"]["task_score"], "task_score", ref, p)
 need(scoring["official_full_split_validated"] is True and scoring["independent_execution"] is True
      and same_ref(scoring["score_items"],r["score_items"])
      and same_ref(scoring["scorer_source"],data["scorer_source"]), "actual independent official scorer and frozen full-split validation")
 items = obj(r["score_items"])
 need(items["schema"] == "bole.independent-task-items/v1" and items["task"] == r["task"]
      and same_ref(items["dataset_manifest"],r["dataset_manifest"])
      and same_ref(items["scorer_source"],data["scorer_source"]), "independent item scores exact task/data/scorer join")
 score = weighted_task_score(items["items"],case_map,outputs)
 return dict(task=r["task"],variant=r["variant"],stage=r["stage"],score=score,
             cases=len(outputs),truncated_cases=truncated,max_total_tokens=max_context,
             concurrency=integer(r["concurrency"],1),record=ref,source=r,
             dataset_manifest=r["dataset_manifest"],prompt_policy=r["prompt_policy"],generation_profile=r["generation_profile"])


def consume(manifest_ref):
 manifest = obj(manifest_ref)
 need(manifest["schema"] == "bole.formal-evidence/v1", "exact formal evidence manifest")
 p, variants = validate_policy(manifest)
 workload = obj(manifest["workload"])
 need(workload["schema"] == "bole.formal-workload/v1" and workload["arrival_policy"] == "closed_loop", "actual prospectively frozen workload")
 concurrency = integer(workload["concurrency"],1)
 need(len(workload["measured_requests"]) >= concurrency and workload["warmup_requests"], "real saturating workload and warmup")
 for phase in ("measured_requests","warmup_requests"):
  need(len({x["request_key"] for x in workload[phase]}) == len(workload[phase]), "unique frozen workload logical requests")
 model = proof(manifest["model_qualification"],"model_qualification",p["candidate_source"],p)
 need(model["model_ready"] is True and same_ref(model["candidate_source"],p["candidate_source"]), "actual same-source broader production model qualification")
 baseline, candidate = ("D","A+B") if p["composition"]["applies"] else ("OFF","ON")
 need(obj(p["variant_profiles"][baseline])["expect_bole_decode"] == "none"
      and obj(p["variant_profiles"][candidate])["expect_bole_decode"] == "all", "real OFF and all-request ON profiles")
 if p["composition"]["applies"]:
  need(set(manifest["composition_qualification"]) == {"A","B"}, "actual both component numerical qualifications")
  for name, source in p["composition"]["component_sources"].items():
   q = proof(manifest["composition_qualification"][name],"composition",source,p)
   need(q["numerically_qualified"] is True and same_ref(q["component_source"],source), "same-source real component numerical qualification")
 perf = {}
 for entry in manifest["runs"]:
  result = perf_run(entry,p,manifest,workload); key = result["round_id"],result["variant"]
  need(key not in perf and key[1] in variants,"unique complete real formal variants")
  perf[key] = result
 need(set(perf) == {(n,v) for n in (1,2,3) for v in variants}, "exact three matched complete variant rounds")
 summary = pair_summary([(perf[n,baseline],perf[n,candidate]) for n in (1,2,3)])
 task_results = {}
 for entry in manifest["tasks"]:
  result = task_run(entry,p,manifest); key = result["task"],result["variant"],result["stage"]
  need(key not in task_results and key[1] in (baseline,candidate),"unique actual full/smoke baseline/candidate task")
  task_results[key] = result
 need(set(task_results) == {(task,v,stage) for task in TASKS for v in (baseline,candidate) for stage in ("smoke","full")}, "all four full task comparisons and prior consumed smokes")
 comparisons = {}; required_context = max(len(x["prompt_token_ids"])+1024 for x in workload["measured_requests"]+workload["warmup_requests"])
 for task in TASKS:
  for variant in (baseline,candidate):
   full, smoke = task_results[task,variant,"full"],task_results[task,variant,"smoke"]
   for field in ("dataset_manifest","prompt_policy","generation_profile"):
    need(same_ref(full[field],smoke[field]),"actual same-source/profile smoke before full")
   need(same_ref(full["source"]["smoke_record"],smoke["record"])
        and smoke["source"]["finished_epoch_ns"] <= full["source"]["started_epoch_ns"], "actual consumed smoke precedes full evaluation")
   required_context = max(required_context,full["max_total_tokens"])
   concurrency = max(concurrency,full["concurrency"])
  off,on = task_results[task,baseline,"full"],task_results[task,candidate,"full"]
  for field in ("dataset_manifest","prompt_policy","generation_profile"):
   need(same_ref(off[field],on[field]),"matched full task inputs, scorer and generation profile")
  comparisons[task] = dict(losses(off["score"],on["score"]),baseline_cases=off["cases"],candidate_cases=on["cases"],
                           baseline_truncated=off["truncated_cases"],candidate_truncated=on["truncated_cases"])
 scope = model["scope"]
 need(integer(scope["max_generated_tokens"],1) >= 2048
      and integer(scope["max_total_tokens"],1) >= required_context
      and integer(scope["max_concurrency"],1) >= concurrency
      and scope["all_request_reuse"] is True and scope["normal_eos"] is True,
      "four-token/first-request qualification cannot admit this formal workload")
 passed = summary["prospective_all_three_pairs_pass"] and all(value["passed"] for value in comparisons.values())
 public_runs = []
 for key in sorted(perf):
  r = dict(perf[key]);r["throughput"] = exact(r["throughput"]);public_runs.append(r)
 return dict(schema="bole.formal-acceptance-audit/v1",inputs=manifest_ref,policy=manifest["policy"],
             formal_acceptance_pass=bool(passed),performance_pass=summary["prospective_all_three_pairs_pass"],
             task_accuracy_pass=all(value["passed"] for value in comparisons.values()),
             aggregation_origin="prospectively frozen stronger engineering rule; protocol aggregation unspecified",
             performance=summary,runs=public_runs,tasks=comparisons,
             all_independent_identity_runtime_activation_resource_gates_pass=True,
             current_service_flags_modified=False)


def main():
 parser = argparse.ArgumentParser(allow_abbrev=False)
 parser.add_argument("--execute",action="store_true")
 parser.add_argument("--manifest-ref")
 parser.add_argument("--output",type=Path)
 args = parser.parse_args()
 if not args.execute:
  print('{"enabled":false,"NPU":false,"measured_data_created":false}')
  return 0
 need(args.manifest_ref is not None and args.output is not None,"explicit exact manifest and fresh output")
 need(os.environ.get("ASCEND_RT_VISIBLE_DEVICES") == "" and os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD") == "0"
      and not list(Path("/dev").glob("davinci[0-9]*")),"executed independent Devices[] CPU reader")
 need(args.output.is_absolute() and args.output.parent.is_dir()
      and not any(x.is_symlink() for x in (args.output,*args.output.parents)),"ordinary precreated absolute output leaf")
 result = consume(json.loads(args.manifest_ref,object_pairs_hook=_unique,parse_constant=_constant))
 with args.output.open("x",encoding="utf8",newline="\n") as handle:
  json.dump(result,handle,sort_keys=True,allow_nan=False);handle.write("\n")
 print(json.dumps({"formal_acceptance_pass":result["formal_acceptance_pass"],"output":str(args.output)},sort_keys=True))
 return 0 if result["formal_acceptance_pass"] else 2


if __name__ == "__main__":
 raise SystemExit(main())
