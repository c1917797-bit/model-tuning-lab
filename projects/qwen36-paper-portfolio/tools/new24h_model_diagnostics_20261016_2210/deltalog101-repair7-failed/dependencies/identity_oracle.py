"""Identity only, never a model/numerical/performance admission."""
import base64, hashlib, json
from pathlib import Path

def require(value, message):
    if not value:
        raise ValueError(message)

def read_ref(ref):
    require(set(ref) == {"path", "bytes", "sha256"}, "exact Ref required")
    p = Path(ref["path"])
    require(p.is_absolute() and p.is_file() and not p.is_symlink(), "regular absolute Ref")
    b = p.read_bytes()
    require(len(b) == ref["bytes"], "Ref bytes drift")
    require(hashlib.sha256(b).hexdigest() == ref["sha256"], "Ref SHA drift")
    return b

def expected_server_id(header_id, body_id):
    # If both are absent a runtime-generated base UUID must be observed, not predicted.
    if header_id is not None:
        require(isinstance(header_id, str), "header ID type")
        return "cmpl-" + header_id
    if body_id is not None:
        require(isinstance(body_id, str), "body ID type")
        return "cmpl-" + body_id
    return None

def validate_assignment(server_id, profile, event):
    require(profile == {"endpoint": "/v1/completions", "prompt_count": 1,
                        "n": 1, "beam_search": False, "streaming_input": False},
            "unsupported fanout/beam/streaming profile")
    require(isinstance(server_id, str) and server_id.startswith("cmpl-"), "actual server ID")
    passed = server_id + "-0"
    require(event["schema"] == "vllm023.actual-assignment/v1", "actual assignment schema")
    require(event["before_external_req_id"] is None, "assign already used")
    require(event["before_request_id"] == passed, "completion passed ID mismatch")
    require(event["after_external_req_id"] == passed, "external mapping mismatch")
    disabled = event["disable_request_id_randomization"]
    require(type(disabled) is bool, "actual environment boolean required")
    assigned = event["after_request_id"]
    require(isinstance(assigned, str), "actual assigned ID")
    if disabled:
        require(assigned == passed, "randomization OFF must keep passed ID")
    else:
        require(assigned.startswith(passed + "-") and len(assigned) == len(passed) + 9,
                "actual randomized assignment shape; suffix not predicted")
    require(event["source_sha256"] == ASSIGN_SHA, "assignment source identity")
    return passed, assigned

ASSIGN_SHA = "c5673988c0f7cfec268220e3f044e718702c015a4f236c020937cfd40a793f15"
NPU_SHA = "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"

def replay_sse(raw, record_format):
    require(record_format in ("line", "raw_base64"), "declared wire record format")
    parts = []
    for line in raw.splitlines():
        record = json.loads(line)
        require(isinstance(record.get("receipt"), dict), "actual wire receipt required")
        if record_format == "line":
            text = record["line"]
            require(isinstance(text, str), "wire line")
            parts.append((text if text.endswith("\n") else text + "\n").encode("utf-8"))
        else:
            parts.append(base64.b64decode(record["raw_base64"], validate=True))
    text = b"".join(parts).decode("utf-8")
    ids, done = [], 0
    for line in text.splitlines():
        if not line or line.startswith(":"):
            continue
        require(line.startswith("data:"), "unsupported SSE field")
        payload = line[5:].strip()
        if payload == "[DONE]":
            done += 1
            continue
        require(done == 0, "data after DONE")
        obj = json.loads(payload)
        require("error" not in obj and isinstance(obj.get("id"), str), "error/missing server ID")
        ids.append(obj["id"])
    require(done == 1 and ids and len(set(ids)) == 1, "complete single-ID SSE required")
    return ids[0]

def validate_worker_retirement(assigned, traces, bindings):
    # bindings come from caller's independently consumed exact-owned all4 controller
    # authority. This function does not manufacture/validate Docker/NPU admission.
    require(set(bindings) == {0, 1, 2, 3}, "actual all4 authority required")
    require(len(traces) == 4, "all4 trace count")
    seen_ranks = set()
    for trace in traces:
        rank = trace["rank"]
        require(type(rank) is int and rank in bindings and rank not in seen_ranks, "unique actual rank")
        seen_ranks.add(rank)
        expected = bindings[rank]
        require(set(expected) == {"pid", "start_ticks", "cgroup"} and type(expected["pid"]) is int
                and expected["pid"] > 0 and type(expected["start_ticks"]) is int
                and isinstance(expected["cgroup"], str), "actual namespace process binding")
        require(trace["identity"] == expected, "rank PID/start/cgroup/CID authority mismatch")
        require(trace["schema"] == "vllm023.actual-worker-retirement/v1", "worker trace schema")
        active, retired, last_seq = False, False, -1
        for e in trace["events"]:
            require(e["schema"] == "vllm023.actual-worker-update/v1" and e["rank"] == rank,
                    "actual worker event schema/rank")
            require(e["source_sha256"] == NPU_SHA, "worker source identity")
            require(e["identity"] == expected, "event process identity mismatch")
            seq = e["seq"]
            require(type(seq) is int and seq > last_seq, "strict worker event order")
            last_seq = seq
            scheduled = e["num_scheduled_tokens"]
            require(isinstance(scheduled, dict) and all(type(v) is int and v >= 0 for v in scheduled.values()),
                    "actual scheduled token map")
            require(type(e["total_num_scheduled_tokens"]) is int and e["total_num_scheduled_tokens"] >= 0
                    and sum(scheduled.values()) == e["total_num_scheduled_tokens"], "schedule sum mismatch")
            if assigned in e["new_req_ids"] or assigned in e["cached_req_ids"] or assigned in scheduled:
                require(not retired, "retired ID reused in this bundle")
                require(assigned in e["requests_after"] and assigned in e["batch_after"], "real worker ingress absent")
                active = True
            if assigned in e["finished_req_ids"]:
                require(active and not retired, "unseen/duplicate worker finish")
                require(assigned not in scheduled and assigned not in e["new_req_ids"], "same-ID resubmit needs new generation")
                require(assigned in e["requests_before"], "finish must own cached request")
                require(assigned not in e["requests_after"] and assigned not in e["batch_after"],
                        "finished-only cache/batch not retired")
                retired = True
        require(active and retired, "HTTP completion is not worker retirement")
    return True

def consume_bundle(bundle, load_ref=read_ref):
    require(bundle["schema"] == "vllm023.completion-identity-bundle/v1", "bundle schema")
    require(bundle["controller_authority_independently_consumed"] is True,
            "caller must consume actual controller authority")
    require(set(bundle["rank_bindings"]) == {"0", "1", "2", "3"}, "exact all4 string rank keys")
    bindings = {int(k): v for k, v in bundle["rank_bindings"].items()}
    assignment_binding = bundle["assignment_process_binding"]
    require(set(assignment_binding) == {"pid", "start_ticks", "cgroup"}
            and type(assignment_binding["pid"]) is int and assignment_binding["pid"] > 0
            and type(assignment_binding["start_ticks"]) is int
            and isinstance(assignment_binding["cgroup"], str), "actual frontend process binding")
    expected_keys = bundle["ordered_request_keys"]
    require(len(expected_keys) == len(set(expected_keys)), "duplicate request keys")
    require([r["request_key"] for r in bundle["rows"]] == expected_keys, "ordered complete rows")
    assigned_ids, passed_ids = set(), set()
    for row in bundle["rows"]:
        observed_server = replay_sse(load_ref(row["raw_sse_ref"]).decode("utf-8"), row["wire_record_format"])
        require(observed_server == row["actual_server_response_id"], "raw SSE ID mismatch")
        expected_server = expected_server_id(row["header_request_id"], row["body_request_id"])
        require(expected_server is None or expected_server == observed_server, "header/body/server precedence")
        assignment = json.loads(load_ref(row["assignment_ref"]))
        require(assignment["identity"] == assignment_binding, "assignment process authority mismatch")
        passed, assigned = validate_assignment(observed_server, bundle["profile"], assignment)
        require(row["actual_engine_request_id"] == assigned and row["passed_request_id"] == passed,
                "SSE is not internal engine ID")
        require(passed not in passed_ids and assigned not in assigned_ids, "duplicate admission/ABA unsupported")
        passed_ids.add(passed); assigned_ids.add(assigned)
        traces = [json.loads(load_ref(ref)) for ref in row["worker_trace_refs"]]
        validate_worker_retirement(assigned, traces, bindings)
    return {"schema": "vllm023.completion-identity-result/v1", "identity_mapping_verified": True,
            "all4_worker_retirement_verified": True, "rows": len(expected_keys),
            "model_numeric_authorized": False, "performance_authorized": False,
            "task_score_authorized": False}
